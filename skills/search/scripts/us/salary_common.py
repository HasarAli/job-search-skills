#!/usr/bin/env python3
"""Shared helpers for the US DOL LCA salary index (build + lookup).

The index is derived from the Office of Foreign Labor Certification (OFLC) LCA
disclosure files: every H-1B/E-3 Labor Condition Application employers file with
the DOL, published quarterly as one national XLSX per program. Wages are the
employer-committed BASE pay floor (no equity/bonus) — treat results as a
conservative lower bound, not expected total comp. See the `search` skill.

Generated data (downloaded XLSX + built SQLite) lives OUTSIDE the skill. Its path
comes from the SALARY_DB env var, defaulting to the data repo's gitignored cache;
resolved against the CWD (run from the data-repo root).
"""
import os
import re
from pathlib import Path

DB_PATH = Path(os.environ.get("SALARY_DB", ".agents/cache/salary/salary_index.sqlite")).resolve()
CACHE_DIR = DB_PATH.parent
PERF_PAGE = "https://www.dol.gov/agencies/eta/foreign-labor/performance"
DOL_HOST = "https://www.dol.gov"

# Columns pulled from the 98-column disclosure sheet (names stable since FY2020).
KEEP_COLS = [
    "CASE_STATUS", "EMPLOYER_NAME", "JOB_TITLE", "SOC_CODE", "SOC_TITLE",
    "WAGE_RATE_OF_PAY_FROM", "WAGE_RATE_OF_PAY_TO", "WAGE_UNIT_OF_PAY",
    "PREVAILING_WAGE", "PW_WAGE_LEVEL", "WORKSITE_CITY", "WORKSITE_STATE",
    "FULL_TIME_POSITION", "BEGIN_DATE",
]

# WAGE_UNIT_OF_PAY -> multiplier to annualize. Unknown unit => row skipped, never guessed.
UNIT_TO_ANNUAL = {
    "year": 1, "yr": 1, "annual": 1,
    "hour": 2080, "hr": 2080,
    "week": 52, "wk": 52,
    "bi-weekly": 26, "biweekly": 26,
    "month": 12, "mo": 12,
}

# Corporate suffixes stripped so "Acme, Inc." and "ACME" collapse to one key.
_SUFFIX = re.compile(
    r"[\s,.]+(inc|incorporated|llc|l\.l\.c|corp|corporation|co|company|"
    r"ltd|limited|lp|llp|plc|gmbh|holdings?|group|usa|us)\b\.?",
    re.I,
)
_NONWORD = re.compile(r"[^a-z0-9]+")


def norm_employer(name: str) -> str:
    """Deterministic employer key: lowercase, drop corporate suffixes + punctuation."""
    if not name:
        return ""
    s = name.lower()
    prev = None
    while prev != s:  # peel repeated suffixes: "foo inc llc" -> "foo"
        prev = s
        s = _SUFFIX.sub("", s)
    return _NONWORD.sub(" ", s).strip()


def to_float(v) -> float | None:
    """Coerce a wage cell (number or '$1,234.00') to float; None if unparseable."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^0-9.]", "", str(v))
    try:
        return float(s) if s else None
    except ValueError:
        return None


def annualize(amount: float | None, unit: str | None) -> float | None:
    """Convert a wage amount in the given unit to an annual figure; None if not usable."""
    if amount is None or not unit:
        return None
    mult = UNIT_TO_ANNUAL.get(str(unit).strip().lower())
    if mult is None:
        return None
    val = amount * mult
    # Drop obvious data errors (mis-keyed unit, placeholder zeros).
    return val if 10_000 <= val <= 2_000_000 else None
