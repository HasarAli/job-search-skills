"""We Work Remotely adapter (RSS via feedparser).

The ``remote-jobs.rss`` feed is a round-robin sampler capped at 10 per category;
it is the canonical all-jobs feed and the only one this adapter reads. There is
no server-side filter of any kind, so role/region/remote/date are all applied
locally by the shared cheap filters. ``title`` packs company and role into one
string and is split on the first ``": "``; ``guid`` (== ``link``, the canonical
posting URL) is the stable ``source_id``. Everything on WWR is remote by
construction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pipeline.model import Failure, Posting, Query
from pipeline.sources.base import BaseAdapter, coerce_datetime, filter_locally, none_if_na

FEED_URL = "https://weworkremotely.com/remote-jobs.rss"


class WwrAdapter(BaseAdapter):
    name = "wwr"

    def __init__(self, block: dict[str, Any]) -> None:
        # WWR has no tenant/params beyond its ``name``; the block is accepted
        # for registry symmetry and ignored.
        _ = block

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]:
        import feedparser  # lazy: feedparser is heavy and not needed to import package

        try:
            parsed = feedparser.parse(FEED_URL)
        except Exception as exc:  # noqa: BLE001 — one adapter-level Failure
            return [], [Failure(source=self.name, tenant=None, error=f"{type(exc).__name__}: {exc}")]

        # feedparser flags malformed feeds on `bozo` but often still has entries;
        # only a fetch that yielded nothing is a failure.
        if getattr(parsed, "bozo", 0) and not getattr(parsed, "entries", []):
            bozo = getattr(parsed, "bozo_exception", None)
            return [], [Failure(source=self.name, tenant=None, error=f"feed parse error: {bozo}")]

        postings: list[Posting] = []
        for entry in parsed.entries:
            posting = self._to_posting(entry)
            if posting is not None:
                postings.append(posting)

        return filter_locally(postings, query), []

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _to_posting(entry: Any) -> Posting | None:
        guid = none_if_na(entry.get("guid")) or none_if_na(entry.get("link"))
        source_id = str(guid).strip() if guid is not None and str(guid).strip() else None
        if not source_id:
            return None

        title = none_if_na(entry.get("title")) or ""
        company, role = WwrAdapter._split_title(title)
        link = none_if_na(entry.get("link"))

        return Posting(
            source=WwrAdapter.name,
            source_id=source_id,
            title=role,
            company=company,
            url=link or source_id,
            location=none_if_na(entry.get("region")),
            remote=True,  # WWR is remote-only by construction
            posted_at=WwrAdapter._pub_date(
                entry.get("published_parsed") or entry.get("published") or entry.get("pubDate")
            ),
            stated_comp=None,
        )

    @staticmethod
    def _split_title(title: str) -> tuple[str, str]:
        """``"Company: Role"`` -> ``(company, role)``; no colon -> ``("", title)``."""
        if ": " in title:
            company, role = title.split(": ", 1)
            return company.strip(), role.strip()
        return "", title.strip()

    @staticmethod
    def _pub_date(value: Any) -> datetime | None:
        value = none_if_na(value)
        if value is None:
            return None
        if isinstance(value, (datetime, str)):
            return coerce_datetime(value)
        # feedparser gives ``published_parsed`` as a UTC ``time.struct_time``.
        if hasattr(value, "tm_year"):
            try:
                return datetime(
                    value.tm_year, value.tm_mon, value.tm_mday,
                    value.tm_hour, value.tm_min, value.tm_sec,
                    tzinfo=timezone.utc,
                )
            except (TypeError, ValueError):
                return None
        return None
