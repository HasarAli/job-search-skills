"""Run envelope → JSON on stdout (stage 9).

``emit`` prints the shortlist envelope to stdout. The agent driving the search
skill reads that JSON and renders the markdown shortlist; the JSON itself is
not saved. The envelope is exactly: ``schema_version``, ``generated_at``
(ISO8601), ``query``, ``counts``, ``rows``. There is no diagnostics/failures
section — failures are console-only; the shortlist is pure data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from pipeline.model import Posting


def _sort_key(posting: Posting) -> tuple[int, float]:
    """Newest-first by ``posted_at`` desc; ``None`` dates sort last."""
    if posting.posted_at is None:
        return (1, 0.0)
    return (0, -posting.posted_at.timestamp())


def _query_dict(config) -> dict:
    query = getattr(config, "query", None)
    roles = getattr(query, "roles", None) or []
    region = getattr(query, "region", None) or ""
    remote = getattr(query, "remote", None)
    posted_since = getattr(query, "posted_since", None)
    return {
        "roles": list(roles),
        "region": region,
        "remote": remote,
        "posted_since": posted_since.isoformat() if posted_since is not None else None,
    }


def emit(shortlist: list[Posting], config, counts: dict) -> None:
    """Print the run envelope to stdout (newest-first; ``None`` dates last).

    This is the machine output the agent consumes — it is not written to disk.
    """
    rows = sorted(shortlist, key=_sort_key)
    envelope = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": _query_dict(config),
        "counts": dict(counts),
        "rows": [posting.to_dict() for posting in rows],
    }
    print(json.dumps(envelope, indent=2, ensure_ascii=False))
