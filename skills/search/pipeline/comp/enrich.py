"""Compensation cascade (stage 4).

In place, one lookup per (company, family); cache hits in the ledger. Cascade
per posting, in order:

1. ``stated_comp`` present -> ``provenance="stated"`` (stated wins however wide;
   ``floor_value`` = stated min, ``ladder=[]``, ``range`` = the stated range).
2. Non-US location -> ``provenance="none"``, skip both lookups.
3. Levels.fyi -> :func:`pipeline.comp.levels.lookup`, cached in the ledger keyed
   ``(company, family)``, TTL 7d (enforced by the ledger). Never cache an empty
   result; an empty result gets one retry after ~2s, then falls through.
4. Visa wages -> :func:`pipeline.comp.visa_wages.lookup`, exact-normalised
   employer match only.
5. Fall through -> ``provenance="none"``.

``floor_value`` from a ladder is the lowest level's median (min total comp over
the ladder). ``family`` is derived from the title conservatively: lowercase,
strip a small seniority/level stop-word list, keep the core family — no
title→level mapping.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pipeline.model import CompLevel, CompRange, CompRecord, Posting

from . import levels, visa_wages

# store/ledger.py lands in parallel; the import below is the exact shape the
# store exposes. Fall back to duck-typing (annotations are lazy strings) if it
# has not landed yet — enrich only calls get_cached_comp/put_cached_comp.
try:
    from pipeline.store.ledger import Ledger
except ModuleNotFoundError:  # pragma: no cover
    Ledger = Any  # type: ignore[assignment]

if TYPE_CHECKING:
    from pipeline.config import Config

_RETRY_DELAY = 2.0

# Seniority/level tokens stripped from the title when deriving a family.
# Deliberately small and conservative (see spec: no title→level mapping).
_FAMILY_STOP_WORDS = frozenset(
    {
        "senior", "sr", "staff", "principal", "lead", "junior", "jr",
        "associate", "mid", "entry", "intern", "level", "levels",
        "ii", "iii", "iv", "v", "vi",
        "1", "2", "3", "4", "5", "6", "7", "8", "9",
    }
)

# Country/region hints that positively identify a non-US location. Unknown or
# US locations are left alone (pass-on-unknown: we only skip when confident).
_NON_US_HINTS = (
    "united kingdom", "england", "scotland", "wales", "london",
    "canada", "toronto", "vancouver", "montreal", "ottawa", "ontario",
    "alberta", "quebec", "british columbia",
    "india", "bangalore", "bengaluru", "mumbai", "hyderabad", "pune", "delhi",
    "germany", "berlin", "munich", "france", "paris",
    "netherlands", "amsterdam", "spain", "madrid", "barcelona",
    "italy", "milan", "poland", "warsaw", "ireland", "dublin",
    "switzerland", "zurich", "sweden", "stockholm", "norway", "oslo",
    "denmark", "copenhagen", "finland", "helsinki",
    "australia", "sydney", "melbourne", "new zealand", "auckland",
    "singapore", "japan", "tokyo", "china", "beijing", "shanghai",
    "south korea", "seoul", "brazil", "sao paulo",
    "mexico city", "guadalajara", "monterrey",
    "argentina", "colombia", "chile", "israel", "tel aviv",
    "united arab emirates", "dubai", "portugal", "lisbon",
    "austria", "vienna", "belgium", "brussels", "czech", "prague",
    "romania", "bucharest", "ukraine", "kyiv", "turkey", "istanbul",
    "pakistan", "bangladesh", "philippines", "manila", "vietnam",
    "thailand", "malaysia", "indonesia", "hong kong", "taiwan",
    "emea", "apac", "latam", "europe", "asia",
)
_NON_US_RE = re.compile(
    r"\b(" + "|".join(re.escape(hint) for hint in _NON_US_HINTS) + r")\b",
    re.IGNORECASE,
)


def _none_record() -> CompRecord:
    return CompRecord(
        provenance="none", floor_value=None, currency=None, ladder=None, range=None, employer=None
    )


def _is_non_us(location: str | None) -> bool:
    """Conservative non-US test: only true when a known non-US country/region
    is named. Unknown or US locations return False (proceed with lookups)."""
    if not location:
        return False
    return _NON_US_RE.search(location) is not None


def _derive_family(title: str | None) -> str:
    """Derive a core job family from a title: lowercase, strip punctuation and
    a small seniority/level stop-word list, keep the rest ("senior software
    engineer" -> "software engineer"). No title→level mapping."""
    if not title:
        return ""
    core = [
        token
        for token in re.split(r"[^a-z0-9]+", (title or "").lower())
        if token and token not in _FAMILY_STOP_WORDS
    ]
    return " ".join(core)


def _comp_from_payload(payload: dict) -> CompRecord:
    """Reconstruct a :class:`CompRecord` from the ledger's JSON cache payload."""
    ladder = None
    raw_ladder = payload.get("ladder")
    if raw_ladder is not None:
        ladder = [
            CompLevel(name=lvl["name"], total_comp=lvl["total_comp"], currency=lvl["currency"])
            for lvl in raw_ladder
        ]
    rng = None
    raw_range = payload.get("range")
    if raw_range is not None:
        rng = CompRange(min=raw_range.get("min"), max=raw_range.get("max"), currency=raw_range.get("currency"))
    return CompRecord(
        provenance=payload.get("provenance", "none"),
        floor_value=payload.get("floor_value"),
        currency=payload.get("currency"),
        ladder=ladder,
        range=rng,
        employer=payload.get("employer"),
    )


def _finalise_ladder(record: CompRecord) -> CompRecord:
    """Ensure ``floor_value`` is the lowest level's median for a ladder record."""
    if record.provenance == "levels" and record.ladder:
        record.floor_value = min(lvl.total_comp for lvl in record.ladder)
    return record


def _levels_with_cache(company: str, family: str, attribution: str, ledger: Ledger) -> CompRecord | None:
    cached = ledger.get_cached_comp(company, family)
    if cached is not None:
        return _finalise_ladder(_comp_from_payload(cached))

    record = levels.lookup(company, family, attribution)
    if record is None:
        time.sleep(_RETRY_DELAY)
        record = levels.lookup(company, family, attribution)
    if record is None:
        return None  # never cache empties

    ledger.put_cached_comp(company, family, record.to_dict())
    return _finalise_ladder(record)


def _enrich_one(posting: Posting, attribution: str, wages_sqlite: Path | None, ledger: Ledger) -> CompRecord:
    if posting.stated_comp is not None:
        return CompRecord(
            provenance="stated",
            floor_value=posting.stated_comp.min,
            currency=posting.stated_comp.currency,
            ladder=[],
            range=posting.stated_comp,
            employer=None,
        )

    if _is_non_us(posting.location):
        return _none_record()

    family = _derive_family(posting.title)
    if family:
        record = _levels_with_cache(posting.company, family, attribution, ledger)
        if record is not None:
            return record

    if wages_sqlite is not None:
        record = visa_wages.lookup(posting.company, wages_sqlite)
        if record is not None:
            return record

    return _none_record()


def enrich(postings: list[Posting], config, ledger: Ledger) -> list[Posting]:
    """Fill ``posting.comp`` in place via the stated → levels → visa-wages cascade.

    One lookup per (company, family); levels results are cached in the ledger
    (TTL enforced there). Returns the (possibly mutated) list.
    """
    attribution = getattr(config, "levels_attribution", None) or "https://www.levels.fyi"
    wages_dir = getattr(config, "visa_wages_dir", None)
    wages_sqlite = (wages_dir / "wage-index.sqlite") if wages_dir is not None else None

    for posting in postings:
        posting.comp = _enrich_one(posting, attribution, wages_sqlite, ledger)
    return postings
