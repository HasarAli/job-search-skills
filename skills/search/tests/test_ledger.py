"""Ledger invariants — identity, expiry, first-record-wins, comp-cache TTL.

These are the load-bearing rules: a bug here fails silently (a job suppressed
forever, or a stale comp number reused).
"""

import sqlite3
from datetime import datetime, timedelta, timezone

from pipeline.model import Posting
from pipeline.store.ledger import Ledger


def _posting(source_id: str = "1", **kw) -> Posting:
    defaults = dict(source="s", source_id=source_id, title="t", company="c", url="u")
    defaults.update(kw)
    return Posting(**defaults)


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).isoformat()


def test_identity_unseen_then_seen(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    assert ledger.is_seen("s", "1") is False
    ledger.record(_posting("1"), "shortlisted")
    assert ledger.is_seen("s", "1") is True


def test_transient_expiry_stops_suppressing(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    ledger.record(
        _posting("1"), "filtered:comp_floor", reason="140000",
        expires_at=_iso(timedelta(days=-1)),
    )
    # Aged out: the stale rejection no longer hides the job.
    assert ledger.is_seen("s", "1") is False
    # Re-sighting records a fresh row.
    ledger.record(_posting("1"), "shortlisted")
    assert ledger.is_seen("s", "1") is True


def test_terminal_outcome_never_expires(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    for outcome in ("applied", "dismissed"):
        ledger.record(_posting(outcome), outcome)
    assert ledger.is_seen("s", "applied") is True
    assert ledger.is_seen("s", "dismissed") is True


def test_first_record_wins(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    ledger.record(_posting("1"), "filtered:comp_floor", reason="140000")
    ledger.record(_posting("1"), "shortlisted")  # later sighting must not overwrite
    with sqlite3.connect(str(tmp_path / "ledger.db")) as conn:
        outcome, reason = conn.execute(
            "SELECT outcome, reason FROM sightings WHERE source='s' AND source_id='1'"
        ).fetchone()
    assert outcome == "filtered:comp_floor"
    assert reason == "140000"


def test_comp_cache_hit_and_ttl(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    ledger.put_cached_comp("Acme", "software engineer", {"provenance": "levels", "floor_value": 200000})
    assert ledger.get_cached_comp("Acme", "software engineer")["floor_value"] == 200000

    # Age it past the 7-day TTL directly, then it must read as a miss.
    with sqlite3.connect(str(tmp_path / "ledger.db")) as conn:
        conn.execute(
            "UPDATE comp_cache SET fetched_at = ? WHERE company='Acme' AND family='software engineer'",
            (_iso(timedelta(days=-8)),),
        )
    assert ledger.get_cached_comp("Acme", "software engineer") is None


def test_empty_cache_payload_never_returned(tmp_path):
    ledger = Ledger(tmp_path / "ledger.db")
    ledger.put_cached_comp("Acme", "software engineer", {})
    assert ledger.get_cached_comp("Acme", "software engineer") is None
