"""Company check vocabulary: can a company employ someone where the user lives?

Shared by both search modes. Evidence about each company is stored in the
ledger (``ledger.py``); this module owns the evidence kinds, the name
normalisation that keys them, and the rules that turn evidence into a label.

Labels, in the order the rules apply:

* ``confirmed`` — any high-confidence evidence: a role located in the home
  country, pay in the home currency, a posting open to a region that includes
  home ("US or Canada", "North America"), or an employer-of-record mention.
* ``no`` — evidence against and nothing for: a posting restricted to another
  country, or a rejection that cited work authorization there.
* ``likely`` — circumstantial evidence only: employees living in the home
  country (LinkedIn People tab).
* ``unknown`` — nothing within the evidence window.

Each piece of evidence counts for :data:`EVIDENCE_DAYS`. A ``confirmed`` company
is not checked again until its evidence ages out; any other company is checked
when it has never been, then at most every :data:`RECHECK_DAYS`. ``no`` stays
checkable because one posting's restriction says little about the company's
other roles.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping

#: Evidence that settles the question on its own.
HIGH = ("home_role", "home_pay", "region", "eor")
#: Evidence against: a posting restricted elsewhere, or a rejection citing it.
NEGATIVE = ("away_only", "rejected")
#: Evidence that only suggests openness.
CIRCUMSTANTIAL = ("people",)
KINDS = HIGH + NEGATIVE + CIRCUMSTANTIAL

LABELS = ("confirmed", "likely", "unknown", "no")

EVIDENCE_DAYS = 90
RECHECK_DAYS = 30

_LEGAL_SUFFIXES = frozenset({
    "inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation",
    "co", "company", "plc", "gmbh", "ag", "sa", "bv", "pty", "lp", "llp",
})
#: Domain-style suffixes in brand names ("honeycomb.io" is "honeycomb").
_DOMAIN_SUFFIX_RE = re.compile(r"\.(?:io|ai|com|co|app|dev|so|hq)\b")


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def normalise_name(name: str) -> str:
    """Company key: lowercase ASCII words, legal and domain suffixes dropped.

    "Scribd, Inc." and "scribd" share a key, as do "Honeycomb.io" and
    "honeycomb". Names that differ in substance ("Velora" and "Aplos") need an
    alias in the ledger.
    """
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    text = _DOMAIN_SUFFIX_RE.sub(" ", text.casefold()).replace("&", " and ")
    words = re.sub(r"[^a-z0-9]+", " ", text).split()
    while len(words) > 1 and words[-1] in _LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


def slug_candidates(name: str) -> list[str]:
    """Likely job-board slugs for a company name, most likely first."""
    words = normalise_name(name).split()
    if not words:
        return []
    raw = re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", name or "")
                 .encode("ascii", "ignore").decode().casefold())
    candidates = ["".join(words), "-".join(words), raw]
    if len(words) > 1 and len(words[0]) >= 4:
        candidates.append(words[0])
    seen: list[str] = []
    for slug in candidates:
        if slug and slug not in seen:
            seen.append(slug)
    return seen


def fresh_kinds(evidence: Iterable[Mapping], now: datetime | None = None) -> set[str]:
    """Kinds of evidence seen within :data:`EVIDENCE_DAYS`."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=EVIDENCE_DAYS)
    kinds: set[str] = set()
    for row in evidence:
        try:
            if _parse_dt(row["seen_at"]) >= cutoff:
                kinds.add(row["kind"])
        except (KeyError, TypeError, ValueError):
            continue
    return kinds


def label(evidence: Iterable[Mapping], now: datetime | None = None) -> str:
    """The company's label from its evidence (see the module docstring)."""
    kinds = fresh_kinds(evidence, now)
    if kinds & set(HIGH):
        return "confirmed"
    if kinds & set(NEGATIVE):
        return "no"
    if kinds & set(CIRCUMSTANTIAL):
        return "likely"
    return "unknown"


def due_for_check(company_label: str, checked_at: str | None, now: datetime | None = None) -> bool:
    """True when an active check (board scan, People tab) is worth running."""
    if company_label == "confirmed":
        return False
    if not checked_at:
        return True
    now = now or datetime.now(timezone.utc)
    try:
        return now - _parse_dt(checked_at) >= timedelta(days=RECHECK_DAYS)
    except ValueError:
        return True
