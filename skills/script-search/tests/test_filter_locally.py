"""``skip_freshness`` behaviour in ``filter_locally``.

ATS boards list all-open roles, so a posting marked ``skip_freshness`` must
survive the cheap local filters even when its ``posted_at`` is older than the
query's ``posted_since`` window. The flag skips only the freshness check —
role/region/remote and the US/CA-remote gate still apply.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from search_shared.model import Posting, Query
from pipeline.sources.base import filter_locally


def _posting(*, skip_freshness: bool) -> Posting:
    return Posting(
        source="ashby",
        source_id="1",
        title="Senior Software Engineer",
        company="cohere",
        url="https://example.com/job",
        location="San Francisco",
        remote=True,
        posted_at=datetime.now(timezone.utc) - timedelta(days=30),
        skip_freshness=skip_freshness,
    )


def _query() -> Query:
    return Query(
        roles=["engineer"],
        region="San Francisco",
        remote=True,
        posted_since=datetime.now(timezone.utc),
    )


def test_skip_freshness_survives_stale_posting():
    kept = filter_locally([_posting(skip_freshness=True)], _query())
    assert [p.source_id for p in kept] == ["1"]


def test_stale_posting_dropped_without_skip_freshness():
    assert filter_locally([_posting(skip_freshness=False)], _query()) == []
