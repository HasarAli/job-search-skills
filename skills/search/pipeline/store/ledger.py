"""SQLite storage for the pipeline's persistent state.

This module is the ONLY place in the project that touches ``sqlite3``. It owns
two concerns:

* ``sightings`` — every posting the pipeline has seen, keyed by
  ``(source, source_id)``. This drives dedup and keeps an honest ``first_seen``.
* ``comp_cache`` — ``CompRecord`` JSON payloads keyed by ``(company, family)``,
  with a 7-day TTL.

Connections are short-lived (one per call) and committed explicitly; the class
is intended for sequential use and is not synchronised.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from ..model import Posting

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sightings (
  source TEXT NOT NULL,
  source_id TEXT NOT NULL,
  first_seen TEXT NOT NULL,       -- ISO8601
  outcome TEXT NOT NULL,          -- "shortlisted" | "filtered:<name>" | "applied" | "dismissed"
  reason TEXT,                    -- for filtered: the observed value (built-ins) or NULL (user filters)
  company TEXT, title TEXT, url TEXT,   -- denormalised context
  expires_at TEXT,                -- NULL = terminal (never expires); else ISO8601
  PRIMARY KEY (source, source_id)
);

CREATE TABLE IF NOT EXISTS comp_cache (
  company TEXT NOT NULL,
  family TEXT NOT NULL,
  payload TEXT NOT NULL,          -- JSON of CompRecord
  fetched_at TEXT NOT NULL,
  PRIMARY KEY (company, family)
);
"""

# Expiry windows (spec: store/ledger.py)
TRANSIENT_EXPIRY_DAYS = 60
COMP_TTL_DAYS = 7
TERMINAL_OUTCOMES = frozenset({"applied", "dismissed"})


def _now_iso() -> str:
    """Current UTC time as an ISO8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value: str) -> datetime:
    """Parse an ISO8601 string into a tz-aware datetime (naive -> assumed UTC)."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _default_expires_at(outcome: str, expires_at: str | None) -> str | None:
    """Resolve an expiry for a sighting.

    Terminal outcomes (``applied``, ``dismissed``) never expire; transient ones
    (``shortlisted``, ``filtered:*``, anything else) default to 60 days when no
    explicit ``expires_at`` is supplied.
    """
    if expires_at is not None:
        return expires_at
    if outcome in TERMINAL_OUTCOMES:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=TRANSIENT_EXPIRY_DAYS)).isoformat()


class Ledger:
    """SQLite-backed sighting ledger and comp cache.

    ``path`` comes from ``Config.seen_db_path`` (``.agents/search/seen.db``). The schema is created on first
    use; the database runs in WAL mode for durable, atomic commits.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        parent = str(Path(self.path).expanduser().parent)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(_SCHEMA)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection. Callers close it via ``closing()``."""
        return sqlite3.connect(self.path)

    # ---- sightings ---------------------------------------------------------

    def is_seen(self, source: str, source_id: str) -> bool:
        """True if ``(source, source_id)`` is recorded and not yet expired.

        A transient sighting whose ``expires_at`` is in the past has aged out:
        it stops suppressing (003) and its row is pruned here so a later
        re-sighting records a fresh ``first_seen``. Terminal outcomes
        (``expires_at`` NULL) never expire.
        """
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT expires_at FROM sightings WHERE source = ? AND source_id = ? LIMIT 1",
                (source, source_id),
            ).fetchone()
            if row is None:
                return False
            expires_at = row[0]
            if expires_at is None:
                return True  # terminal — never expires
            try:
                if _parse_dt(expires_at) > datetime.now(timezone.utc):
                    return True
            except ValueError:
                return True  # unparseable expiry — treat as still active
            conn.execute(
                "DELETE FROM sightings WHERE source = ? AND source_id = ?",
                (source, source_id),
            )
            conn.commit()
            return False

    def record(
        self,
        posting: Posting,
        outcome: str,
        reason: str | None = None,
        expires_at: str | None = None,
    ) -> None:
        """Record one sighting as an upsert that only writes the FIRST time.

        Later calls for the same ``(source, source_id)`` are ignored so
        ``first_seen`` stays honest. Transient outcomes default to a 60-day
        expiry; terminal outcomes (``applied``, ``dismissed``) never expire.
        """
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sightings "
                "(source, source_id, first_seen, outcome, reason, company, title, url, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    posting.source,
                    posting.source_id,
                    _now_iso(),
                    outcome,
                    reason,
                    posting.company,
                    posting.title,
                    posting.url,
                    _default_expires_at(outcome, expires_at),
                ),
            )
            conn.commit()

    def record_sightings(self, rows: list[tuple]) -> None:
        """Write many sightings in ONE transaction.

        Called once, after output. A run that dies before this call writes
        nothing — atomicity is the point. Each row is a 9-tuple in schema
        column order::

            (source, source_id, first_seen, outcome, reason, company, title, url, expires_at)

        ``first_seen`` may be ``None`` (now is used); ``expires_at`` follows the
        same default as :meth:`record` (60 days for transient outcomes, never
        for terminal ones). Existing sightings are left untouched.
        """

        def _normalise() -> Iterator[tuple]:
            for row in rows:
                source, source_id, first_seen, outcome, reason, company, title, url, expires_at = row
                yield (
                    source,
                    source_id,
                    first_seen or _now_iso(),
                    outcome,
                    reason,
                    company,
                    title,
                    url,
                    _default_expires_at(outcome, expires_at),
                )

        conn = self._connect()
        try:
            with conn:  # one transaction: commits on success, rolls back on error
                conn.executemany(
                    "INSERT OR IGNORE INTO sightings "
                    "(source, source_id, first_seen, outcome, reason, company, title, url, expires_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    _normalise(),
                )
        finally:
            conn.close()

    # ---- comp cache --------------------------------------------------------

    def get_cached_comp(self, company: str, family: str) -> dict | None:
        """Return the cached JSON payload, or None if missing, stale, or empty.

        Entries older than :data:`COMP_TTL_DAYS` are treated as expired. An
        empty payload never comes back (the spec forbids caching empty results,
        but this guards against one slipping in).
        """
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT payload, fetched_at FROM comp_cache WHERE company = ? AND family = ?",
                (company, family),
            ).fetchone()
        if row is None:
            return None
        payload_raw, fetched_at = row
        if not self._fresh(fetched_at):
            return None
        try:
            payload = json.loads(payload_raw)
        except (TypeError, ValueError):
            return None
        if not payload:
            return None
        return payload

    def put_cached_comp(self, company: str, family: str, payload: dict) -> None:
        """Upsert a comp payload for ``(company, family)`` with a fresh timestamp."""
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT INTO comp_cache (company, family, payload, fetched_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(company, family) DO UPDATE SET "
                "payload = excluded.payload, fetched_at = excluded.fetched_at",
                (company, family, json.dumps(payload), _now_iso()),
            )
            conn.commit()

    @staticmethod
    def _fresh(fetched_at: str | None) -> bool:
        """True if ``fetched_at`` is a valid timestamp within the TTL window."""
        if not fetched_at:
            return False
        try:
            dt = _parse_dt(fetched_at)
        except ValueError:
            return False
        return (datetime.now(timezone.utc) - dt) < timedelta(days=COMP_TTL_DAYS)
