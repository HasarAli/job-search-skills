"""ATS tenant adapters: Greenhouse, Ashby, Lever, Workday.

Each adapter takes a list of tenant slugs from its source block and pulls every
listed posting. Isolation is per tenant: a dead or renamed tenant becomes one
:class:`Failure` for that tenant while healthy tenants still contribute.
An empty tenant list returns ``([], [])`` with no network call.

All four normalise their board's response to :class:`Posting` and extract
``stated_comp`` where the board provides structured pay:

* Greenhouse — ``pay_input_ranges[]`` (cents; widest band across geo zones).
* Ashby — ``compensation.compensationTiers[].components[]`` (Salary rows only).
* Lever — ``salaryRange`` (documented, rarely populated in the wild).
* Workday — no comp, and its list response has no machine date (``posted_at``
  stays ``None``), so only ``list()`` is implemented; ``fetch_detail()`` stays
  the default ``None``.

Workday pagination traps (limit silently caps at 20, ``total`` caps at 2000,
offsets past the end wrap to page one) are handled by stopping at
``min(total, 2000)`` and by a "first id repeated" termination guard.
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from pipeline.model import CompRange, Failure, Posting, Query
from pipeline.sources.base import (
    BaseAdapter,
    coerce_bool,
    coerce_datetime,
    coerce_float,
    filter_locally,
    http_get_json,
    http_post_json,
    none_if_na,
)

_WORKDAY_LIMIT = 20        # silently fails above 20
_WORKDAY_TOTAL_CAP = 2000  # "total" caps here even when the board is larger


class _TenantAdapter(BaseAdapter):
    """Shared tenant-loop: fetch per tenant, isolate failures, filter locally."""

    name: str = ""

    def __init__(self, block: dict[str, Any]) -> None:
        raw = block.get("tenants") or []
        self.tenants = [t for t in raw if isinstance(t, str) and t.strip()]

    # -- Adapter -------------------------------------------------------------

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]:
        if not self.tenants:
            return [], []

        postings: list[Posting] = []
        failures: list[Failure] = []
        seen: set[tuple[str, str]] = set()

        for tenant in self.tenants:
            try:
                rows = self._fetch(tenant, query)
            except Exception as exc:  # noqa: BLE001 — per-tenant isolation
                failures.append(
                    Failure(
                        source=self.name,
                        tenant=tenant,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            for row in rows:
                posting = self._normalise(tenant, row)
                if posting is None:
                    continue
                key = (posting.source, posting.source_id)
                if key in seen:
                    continue
                seen.add(key)
                postings.append(posting)

        return filter_locally(postings, query), failures

    # -- overridden per board ------------------------------------------------

    def _fetch(self, tenant: str, query: Query) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _normalise(self, tenant: str, row: dict[str, Any]) -> Posting | None:
        raise NotImplementedError


# ---- Greenhouse ------------------------------------------------------------


class GreenhouseAdapter(_TenantAdapter):
    name = "greenhouse"

    def _fetch(self, tenant: str, query: Query) -> list[dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{tenant}/jobs"
        data = http_get_json(url, params={"content": "false", "pay_transparency": "true"})
        return data.get("jobs") or []

    def _normalise(self, tenant: str, job: dict[str, Any]) -> Posting | None:
        source_id = self._source_id(job)
        if not source_id:
            return None
        location = job.get("location") or {}
        return Posting(
            source=self.name,
            source_id=source_id,
            title=job.get("title") or "",
            company=job.get("company_name") or tenant,
            url=job.get("absolute_url") or "",
            location=location.get("name") if isinstance(location, dict) else None,
            remote=None,
            posted_at=coerce_datetime(job.get("first_published") or job.get("updated_at")),
            stated_comp=self._comp(job.get("pay_input_ranges") or []),
        )

    @staticmethod
    def _source_id(job: dict[str, Any]) -> str | None:
        jid = job.get("id")
        if jid is not None and str(jid).strip():
            return str(jid).strip()
        for key in ("requisition_id", "internal_job_id"):
            value = none_if_na(job.get(key))
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    @staticmethod
    def _comp(ranges: list[Any]) -> CompRange | None:
        """Widest band across ``pay_input_ranges[]`` geo zones, cents -> units."""
        mins: list[float] = []
        maxs: list[float] = []
        currency: str | None = None
        for r in ranges:
            if not isinstance(r, dict):
                continue
            mn = coerce_float(r.get("min_cents"))
            mx = coerce_float(r.get("max_cents"))
            if mn is not None:
                mins.append(mn / 100)
            if mx is not None:
                maxs.append(mx / 100)
            if currency is None and r.get("currency_type"):
                currency = str(r.get("currency_type"))
        if not mins and not maxs:
            return None
        return CompRange(min=min(mins) if mins else None, max=max(maxs) if maxs else None, currency=currency)


# ---- Ashby -----------------------------------------------------------------


class AshbyAdapter(_TenantAdapter):
    name = "ashby"

    def _fetch(self, tenant: str, query: Query) -> list[dict[str, Any]]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{tenant}"
        data = http_get_json(url, params={"includeCompensation": "true"})
        return data.get("jobs") or []

    def _normalise(self, tenant: str, job: dict[str, Any]) -> Posting | None:
        # ``isListed: false`` means "direct-link only, do not display publicly".
        if job.get("isListed") is False:
            return None
        jid = job.get("id")
        source_id = str(jid).strip() if jid is not None and str(jid).strip() else None
        if not source_id:
            return None
        return Posting(
            source=self.name,
            source_id=source_id,
            title=job.get("title") or "",
            company=tenant,
            url=job.get("jobUrl") or job.get("applyUrl") or "",
            location=job.get("location"),
            remote=coerce_bool(job.get("isRemote")),
            posted_at=coerce_datetime(job.get("publishedAt")),
            stated_comp=self._comp(job.get("compensation") or {}),
        )

    @staticmethod
    def _comp(compensation: dict[str, Any]) -> CompRange | None:
        mins: list[float] = []
        maxs: list[float] = []
        currency: str | None = None
        for tier in compensation.get("compensationTiers") or []:
            if not isinstance(tier, dict):
                continue
            for component in tier.get("components") or []:
                if not isinstance(component, dict):
                    continue
                if component.get("compensationType") != "Salary":
                    continue
                mn = coerce_float(component.get("minValue"))
                mx = coerce_float(component.get("maxValue"))
                if mn is not None:
                    mins.append(mn)
                if mx is not None:
                    maxs.append(mx)
                if currency is None and component.get("currencyCode"):
                    currency = str(component.get("currencyCode"))
        if not mins and not maxs:
            return None
        return CompRange(min=min(mins) if mins else None, max=max(maxs) if maxs else None, currency=currency)


# ---- Lever -----------------------------------------------------------------


class LeverAdapter(_TenantAdapter):
    name = "lever"

    def _fetch(self, tenant: str, query: Query) -> list[dict[str, Any]]:
        # Two instances: a tenant on EU residency 404s on the global host.
        for host in ("api.lever.co", "api.eu.lever.co"):
            url = f"https://{host}/v0/postings/{tenant}"
            try:
                data = http_get_json(url, params={"mode": "json"})
            except Exception:  # noqa: BLE001 — 404/etc. falls through to EU host
                continue
            if isinstance(data, list):
                return data
        raise RuntimeError(f"no response from api.lever.co or api.eu.lever.co for {tenant!r}")

    def _normalise(self, tenant: str, job: dict[str, Any]) -> Posting | None:
        jid = job.get("id")
        source_id = str(jid).strip() if jid is not None and str(jid).strip() else None
        if not source_id:
            return None
        categories = job.get("categories") or {}
        location = categories.get("location") if isinstance(categories, dict) else None
        all_locations = categories.get("allLocations") if isinstance(categories, dict) else None
        if isinstance(all_locations, list) and all_locations:
            location = ", ".join(str(x) for x in all_locations if x)
        return Posting(
            source=self.name,
            source_id=source_id,
            title=job.get("text") or "",
            company=tenant,
            url=job.get("hostedUrl") or job.get("applyUrl") or "",
            location=location,
            remote=self._remote(job.get("workplaceType")),
            posted_at=self._created(job.get("createdAt")),
            stated_comp=self._comp(job.get("salaryRange")),
        )

    @staticmethod
    def _remote(workplace_type: Any) -> bool | None:
        if not isinstance(workplace_type, str):
            return None
        t = workplace_type.strip().lower()
        if t == "remote":
            return True
        if t in {"on-site", "onsite", "on site"}:
            return False
        return None  # hybrid / unspecified -> unknown

    @staticmethod
    def _created(value: Any) -> datetime | None:
        ms = coerce_float(value)  # epoch millis
        if ms is None:
            return None
        try:
            return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    @staticmethod
    def _comp(salary_range: Any) -> CompRange | None:
        if not isinstance(salary_range, dict):
            return None
        mn = coerce_float(salary_range.get("min"))
        mx = coerce_float(salary_range.get("max"))
        if mn is None and mx is None:
            return None
        return CompRange(min=mn, max=mx, currency=salary_range.get("currency"))


# ---- Workday ---------------------------------------------------------------


class WorkdayAdapter(_TenantAdapter):
    name = "workday"

    def _fetch(self, tenant: str, query: Query) -> list[dict[str, Any]]:
        slug, dc, site = self._parse_tenant(tenant)
        host = f"{slug}.{dc}.myworkdayjobs.com"
        url = f"https://{host}/wday/cxs/{slug}/{site}/jobs"

        jobs: list[dict[str, Any]] = []
        offset = 0
        first_ids: set[str] = set()
        while True:
            data = http_post_json(
                url,
                payload={
                    "appliedFacets": {},
                    "limit": _WORKDAY_LIMIT,
                    "offset": offset,
                    "searchText": "",
                },
            )
            page = self._jobs(data)
            if not page:
                break

            # Belt-and-braces: offsets past the end silently wrap to page one,
            # so a repeated first id terminates pagination even when `total` lies.
            first_id = self._first_id(page[0])
            if first_id and first_id in first_ids:
                break
            if first_id:
                first_ids.add(first_id)

            jobs.extend(page)

            total = data.get("total")
            if isinstance(total, int) and offset + _WORKDAY_LIMIT >= min(total, _WORKDAY_TOTAL_CAP):
                break
            offset += _WORKDAY_LIMIT
        return jobs

    @staticmethod
    def _jobs(data: Any) -> list[dict[str, Any]]:
        for key in ("jobPostings", "jobs", "postings"):
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, list):
                return value
        return []

    @staticmethod
    def _first_id(job: dict[str, Any]) -> str | None:
        # externalPath carries the requisition id and is the stable, unique
        # identity; bulletFields[0] is display text (often the posting title)
        # and is not stable enough for a source_id (003 requires stability).
        external = (job.get("externalPath") or "").strip()
        if external:
            return external
        bullets = job.get("bulletFields") or []
        if bullets and bullets[0]:
            return str(bullets[0]).strip()
        return None

    def _normalise(self, tenant: str, job: dict[str, Any]) -> Posting | None:
        source_id = self._first_id(job)
        if not source_id:
            return None
        slug, dc, _site = self._parse_tenant(tenant)
        host = f"{slug}.{dc}.myworkdayjobs.com"
        external = (job.get("externalPath") or "").strip()
        return Posting(
            source=self.name,
            source_id=source_id,
            title=job.get("title") or "",
            company=slug,
            url=f"https://{host}{external}" if external else "",
            location=job.get("locationsText"),
            remote=None,
            posted_at=None,  # list response has no machine date
            stated_comp=None,  # Workday carries no comp
        )

    @staticmethod
    def _slug(tenant: str) -> str:
        t = tenant.strip()
        if "://" in t:
            return (urllib.parse.urlsplit(t).hostname or "").split(".")[0]
        return t.split(".")[0]

    @staticmethod
    def _parse_tenant(tenant: str) -> tuple[str, str, str]:
        """Accept ``"{slug}.{wdN}.{siteId}"`` (e.g. ``nvidia.wd5.NVIDIAExternalCareerSite``)
        or a full careers URL, returning ``(slug, dc, siteId)``."""
        t = tenant.strip()
        if "://" not in t:
            parts = t.split(".")
            if len(parts) >= 3 and re.fullmatch(r"wd\d+", parts[1], re.IGNORECASE):
                return parts[0], parts[1].lower(), parts[2]
            raise ValueError(
                f"unparseable Workday tenant {tenant!r}: expected '{{slug}}.{{wdN}}.{{siteId}}' "
                "(e.g. 'nvidia.wd5.NVIDIAExternalCareerSite')"
            )
        parsed = urllib.parse.urlsplit(t)
        host = (parsed.hostname or "").lower()
        m = re.match(r"^([^.]+)\.(wd\d+)\.myworkdayjobs\.com$", host)
        if not m:
            raise ValueError(f"unrecognised Workday host in {tenant!r}")
        slug, dc = m.group(1), m.group(2)
        segments = [s for s in parsed.path.split("/") if s]
        site = slug
        try:
            i = segments.index("cxs")
            site = segments[i + 2]
        except (ValueError, IndexError):
            pass
        return slug, dc, site
