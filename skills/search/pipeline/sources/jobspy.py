"""JobSpy adapter — one library covering five aggregator boards.

JobSpy is imported lazily inside ``list()`` (it pulls in pandas and a scraping
stack). Each board named in the source block's ``site_names`` is one tenant:
a failing board becomes a :class:`Failure` for that board while the others
still contribute postings.

Server-side pushdown (and the Indeed/LinkedIn "only one filter" trap, per the
source survey): ``search_term`` (or one scrape per query role), ``location``,
and — when ``query.remote`` is set — ``is_remote``; otherwise ``hours_old`` for
the freshness window. Everything else is filtered locally by the shared cheap
filters.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pipeline.model import CompRange, Failure, Posting, Query
from pipeline.sources.base import (
    DEFAULT_BACKOFF,
    DEFAULT_RETRIES,
    BaseAdapter,
    coerce_bool,
    coerce_datetime,
    coerce_float,
    filter_locally,
    none_if_na,
    retry_call,
)

#: How many results per (board, term) scrape JobSpy is asked for.
RESULTS_WANTED = 100


class JobSpyAdapter(BaseAdapter):
    name = "jobspy"

    def __init__(self, block: dict[str, Any]) -> None:
        raw_sites = block.get("site_names") or []
        self.site_names = [s for s in raw_sites if isinstance(s, str) and s.strip()]
        self.search_term = block.get("search_term") or None

    # -- Adapter -------------------------------------------------------------

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]:
        if not self.site_names:
            return [], []
        import jobspy  # heavy: pandas + scraping stack

        postings: list[Posting] = []
        failures: list[Failure] = []
        seen: set[tuple[str, str]] = set()

        for site in self.site_names:
            failed = False
            for term in self._search_terms(query):
                try:
                    rows = self._scrape(jobspy, site, term, query)
                except Exception as exc:  # noqa: BLE001 — one Failure per board
                    if not failed:
                        failures.append(
                            Failure(
                                source=self.name,
                                tenant=site,
                                error=f"{type(exc).__name__}: {exc}",
                            )
                        )
                        failed = True
                    continue
                for row in rows:
                    posting = self._to_posting(row)
                    if posting is None:
                        continue
                    key = (posting.source, posting.source_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    postings.append(posting)

        return filter_locally(postings, query), failures

    # -- internals -----------------------------------------------------------

    def _search_terms(self, query: Query) -> list[str]:
        if self.search_term:
            return [self.search_term]
        return [r for r in query.roles if r.strip()]

    def _scrape(self, jobspy: Any, site: str, term: str, query: Query) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "site_name": site,
            "search_term": term,
            "location": query.region,
            "results_wanted": RESULTS_WANTED,
        }
        # Indeed/LinkedIn allow only ONE of (hours_old | is_remote | easy_apply).
        # Prefer is_remote when the query asks, otherwise push the date window;
        # the unpushed half is satisfied locally by ``filter_locally``.
        if query.remote is not None:
            kwargs["is_remote"] = query.remote
        elif query.posted_since is not None:
            hours = self._hours_since(query.posted_since)
            if hours:
                kwargs["hours_old"] = hours

        df = retry_call(
            lambda: jobspy.scrape_jobs(**kwargs),
            retries=DEFAULT_RETRIES,
            backoff=DEFAULT_BACKOFF,
        )
        if df is None:
            return []
        return df.to_dict("records")

    @staticmethod
    def _hours_since(since: datetime) -> int | None:
        seconds = (datetime.now(timezone.utc) - since).total_seconds()
        if seconds < 0:
            return None
        return max(1, int(seconds // 3600))

    def _to_posting(self, row: dict[str, Any]) -> Posting | None:
        source_id = self._source_id(row)
        if not source_id:
            return None

        company = none_if_na(row.get("company") or row.get("company_name"))
        url = none_if_na(row.get("job_url") or row.get("job_url_direct"))

        comp: CompRange | None = None
        mn = coerce_float(row.get("min_amount"))
        mx = coerce_float(row.get("max_amount"))
        currency = none_if_na(row.get("currency"))
        if mn is not None or mx is not None:
            comp = CompRange(
                min=mn,
                max=mx,
                currency=str(currency) if currency else None,
            )

        return Posting(
            source=self.name,
            source_id=source_id,
            title=none_if_na(row.get("title")) or "",
            company=company or "",
            url=url or "",
            location=none_if_na(row.get("location")),
            remote=coerce_bool(row.get("is_remote")),
            posted_at=coerce_datetime(row.get("date_posted")),
            stated_comp=comp,
        )

    @staticmethod
    def _source_id(row: dict[str, Any]) -> str | None:
        """Prefer JobSpy's stable site-prefixed ``id``; fall back to the direct
        employer URL (which often carries the underlying ATS id), then the
        board URL."""
        for key in ("id", "job_url_direct", "job_url"):
            value = none_if_na(row.get(key))
            if value is not None and str(value).strip():
                return str(value).strip()
        return None
