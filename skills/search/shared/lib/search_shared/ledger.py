"""SQLite storage for the pipeline's persistent state.

This module is the ONLY place in the project that touches ``sqlite3``. It owns
three concerns:

* ``sightings`` — every posting the pipeline has seen, keyed by
  ``(source, source_id)``. This drives dedup and keeps an honest ``first_seen``.
* ``comp_cache`` — ``CompRecord`` JSON payloads keyed by ``(company, family)``,
  with a 7-day TTL.
* ``companies`` / ``company_aliases`` / ``company_evidence`` — the company
  check's memory: whether each company can employ the user where they live.
  Rules and vocabulary live in ``companies.py``.

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
from typing import Any, Iterable, Iterator

from . import companies as company_rules
from .model import Posting

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

CREATE TABLE IF NOT EXISTS companies (
  key TEXT PRIMARY KEY,           -- companies.normalise_name()
  name TEXT NOT NULL,             -- display name as first recorded
  board TEXT,                     -- "<platform>:<slug>", e.g. "ashby:cohere"; NULL = not found
  checked_at TEXT                 -- last active check (board scan, People tab); NULL = never
);

CREATE TABLE IF NOT EXISTS company_aliases (
  alias TEXT PRIMARY KEY,         -- another normalised name, or a board slug
  key TEXT NOT NULL               -- companies.key
);

CREATE TABLE IF NOT EXISTS company_evidence (
  key TEXT NOT NULL,              -- companies.key
  kind TEXT NOT NULL,             -- companies.KINDS
  detail TEXT NOT NULL,           -- observed text, verbatim where possible
  url TEXT,
  seen_at TEXT NOT NULL,          -- ISO8601; moves forward when seen again
  PRIMARY KEY (key, kind, detail)
);
"""

# Shared expiry windows.
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


def _currently_suppressing(conn: sqlite3.Connection, source: str, source_id: str) -> bool:
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
    return False


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
            result = _currently_suppressing(conn, source, source_id)
            conn.commit()
            return result

    def unseen_identities(self, identities: set[tuple[str, str]]) -> set[tuple[str, str]]:
        """Return the subset of ``identities`` not currently sighted (or expired).

        One connection for the whole batch — the batch counterpart to
        :meth:`is_seen`. Expired transient rows are pruned here, so a later
        re-sighting records a fresh ``first_seen``.
        """
        if not identities:
            return set()
        unseen: set[tuple[str, str]] = set()
        conn = self._connect()
        try:
            for source, source_id in identities:
                if not _currently_suppressing(conn, source, source_id):
                    unseen.add((source, source_id))
            conn.commit()
            return unseen
        finally:
            conn.close()

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

    # ---- company check -----------------------------------------------------

    @staticmethod
    def _company_key(conn: sqlite3.Connection, name: str) -> str:
        """Normalised name, followed through ``company_aliases``."""
        key = company_rules.normalise_name(name)
        row = conn.execute("SELECT key FROM company_aliases WHERE alias = ?", (key,)).fetchone()
        return row[0] if row else key

    def _ensure_company(self, conn: sqlite3.Connection, name: str) -> str | None:
        key = self._company_key(conn, name)
        if not key:
            return None
        conn.execute("INSERT OR IGNORE INTO companies (key, name) VALUES (?, ?)", (key, name.strip()))
        return key

    @staticmethod
    def _merge_company(conn: sqlite3.Connection, from_key: str, into_key: str) -> None:
        """Move everything recorded under ``from_key`` onto ``into_key``."""
        conn.execute(
            "INSERT INTO company_evidence (key, kind, detail, url, seen_at) "
            "SELECT ?, kind, detail, url, seen_at FROM company_evidence WHERE key = ? AND true "
            "ON CONFLICT(key, kind, detail) DO UPDATE SET seen_at = MAX(seen_at, excluded.seen_at)",
            (into_key, from_key),
        )
        conn.execute("DELETE FROM company_evidence WHERE key = ?", (from_key,))
        row = conn.execute("SELECT board, checked_at FROM companies WHERE key = ?", (from_key,)).fetchone()
        if row is not None:
            conn.execute(
                "UPDATE companies SET board = COALESCE(board, ?), "
                "checked_at = NULLIF(MAX(COALESCE(checked_at, ''), COALESCE(?, '')), '') WHERE key = ?",
                (row[0], row[1], into_key),
            )
            conn.execute("DELETE FROM companies WHERE key = ?", (from_key,))
        conn.execute("UPDATE company_aliases SET key = ? WHERE key = ?", (into_key, from_key))
        conn.execute("INSERT OR REPLACE INTO company_aliases (alias, key) VALUES (?, ?)", (from_key, into_key))

    def record_evidence(
        self, name: str, kind: str, detail: str, url: str | None = None, seen_at: str | None = None,
    ) -> None:
        """Record one piece of company evidence (see :meth:`record_evidence_many`)."""
        self.record_evidence_many([(name, kind, detail, url, seen_at)])

    def record_evidence_many(self, rows: Iterable[tuple]) -> None:
        """Write ``(name, kind, detail, url, seen_at)`` rows in ONE transaction.

        The company is created on first evidence. Seeing the same evidence
        again moves ``seen_at`` forward, never back; ``seen_at`` None means now.
        An unknown kind raises :class:`ValueError` before anything is written.
        """
        rows = list(rows)
        for row in rows:
            if row[1] not in company_rules.KINDS:
                raise ValueError(f"unknown evidence kind {row[1]!r}; expected one of {company_rules.KINDS}")
        conn = self._connect()
        try:
            with conn:
                for name, kind, detail, url, seen_at in rows:
                    key = self._ensure_company(conn, name)
                    if key is None or not (detail or "").strip():
                        continue
                    when = _parse_dt(seen_at).astimezone(timezone.utc).isoformat() if seen_at else _now_iso()
                    conn.execute(
                        "INSERT INTO company_evidence (key, kind, detail, url, seen_at) VALUES (?, ?, ?, ?, ?) "
                        "ON CONFLICT(key, kind, detail) DO UPDATE SET "
                        "seen_at = MAX(seen_at, excluded.seen_at), url = COALESCE(excluded.url, url)",
                        (key, kind, detail.strip(), url, when),
                    )
        finally:
            conn.close()

    def set_company_board(self, name: str, board: str) -> None:
        """Record the company's job board (``"<platform>:<slug>"``).

        The board's slug becomes another name for the company, so postings
        collected from that board find the same memory. A company already
        recorded under that slug is merged in.
        """
        platform, _, slug = board.partition(":")
        with closing(self._connect()) as conn:
            key = self._ensure_company(conn, name)
            if key is None:
                return
            conn.execute("UPDATE companies SET board = ? WHERE key = ?", (board, key))
            slug_key = company_rules.normalise_name(slug.split(".")[0]) if platform != "custom" else ""
            if slug_key and slug_key != key:
                existing = conn.execute(
                    "SELECT board FROM companies WHERE key = ?", (slug_key,)
                ).fetchone()
                aliased = conn.execute(
                    "SELECT key FROM company_aliases WHERE alias = ?", (slug_key,)
                ).fetchone()
                if existing is not None and existing[0] in (None, board):
                    self._merge_company(conn, slug_key, key)
                elif existing is None and aliased is None:
                    conn.execute("INSERT INTO company_aliases (alias, key) VALUES (?, ?)", (slug_key, key))
            conn.commit()

    def link_company(self, name: str, other: str) -> None:
        """Treat ``other`` as another name for ``name``, merging its memory."""
        with closing(self._connect()) as conn:
            key = self._ensure_company(conn, name)
            other_key = self._company_key(conn, other)
            if key and other_key and other_key != key:
                self._merge_company(conn, other_key, key)
            conn.commit()

    def mark_company_checked(self, name: str, when: str | None = None) -> None:
        """Stamp an active check, whether or not it found evidence."""
        with closing(self._connect()) as conn:
            key = self._ensure_company(conn, name)
            if key is not None:
                conn.execute("UPDATE companies SET checked_at = ? WHERE key = ?", (when or _now_iso(), key))
            conn.commit()

    def company_for_board(self, board: str) -> str | None:
        """Display name of the company whose job board is ``board``."""
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT name FROM companies WHERE board = ? LIMIT 1", (board,)).fetchone()
        return row[0] if row else None

    def company(self, name: str) -> dict[str, Any] | None:
        """The company's memory, label and whether a check is due; None if never recorded."""
        with closing(self._connect()) as conn:
            return self._company_dict(conn, self._company_key(conn, name))

    def companies(self) -> list[dict[str, Any]]:
        """Every recorded company, as :meth:`company` returns it."""
        with closing(self._connect()) as conn:
            keys = [row[0] for row in conn.execute("SELECT key FROM companies ORDER BY key")]
            return [c for c in (self._company_dict(conn, key) for key in keys) if c is not None]

    @staticmethod
    def _company_dict(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT key, name, board, checked_at FROM companies WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        evidence = [
            {"kind": kind, "detail": detail, "url": url, "seen_at": seen_at}
            for kind, detail, url, seen_at in conn.execute(
                "SELECT kind, detail, url, seen_at FROM company_evidence WHERE key = ? "
                "ORDER BY seen_at DESC", (key,),
            )
        ]
        aliases = [a for (a,) in conn.execute("SELECT alias FROM company_aliases WHERE key = ? ORDER BY alias", (key,))]
        company_label = company_rules.label(evidence)
        return {
            "key": row[0],
            "name": row[1],
            "board": row[2],
            "checked_at": row[3],
            "label": company_label,
            "due": company_rules.due_for_check(company_label, row[3]),
            "aliases": aliases,
            "evidence": evidence,
        }
