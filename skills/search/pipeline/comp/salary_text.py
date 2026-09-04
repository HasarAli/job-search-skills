"""Salary-range text parsing — standalone, independently testable.

Extracts a stated base-salary range from free text. Pure stdlib (``re``) plus
:class:`search_shared.model.CompRange`; imports no adapter, ``curl_cffi``, or
``beautifulsoup4``, so the bank-driven tests in ``tests/test_salary_text.py``
load only this module.

Every real-world form is pinned in ``tests/bank/salary.json``. When a posting's
range is missed, add it to the bank and strengthen the regex until it passes —
never a one-off fix in the adapter.
"""

from __future__ import annotations

import re

from search_shared.model import CompRange

#: Currency codes, optionally before/after the range.
_CURRENCY_CODE = r"(?:USD|CAD)"

#: One salary amount. A bare number is NOT an amount — it must carry a ``$``, a
#: thousands comma, or a ``k``/``K`` suffix, so "5-7 years" never matches while
#: "$160" (as in "$160-190k") does.
_SALARY_AMOUNT = (
    _CURRENCY_CODE + r"?\s*"
    r"(?:"
    r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?\s*[kK]?"          # "$160", "$160k", "$160,000"
    r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*[kK]?"           # "160,000" (comma)
    r"|\d+(?:\.\d+)?\s*[kK]"                            # "160k", "209.5K"
    r")"
)

#: Range separator: en/em dash, tilde, hyphen, or the words "to"/"and".
_SALARY_SEP = r"\s*(?:–|—|~|-|\bto\b|\band\b)\s*"

#: Annual-unit suffix that may follow either amount ("$170,000/year",
#: "$200,000 per year", "$165,000 annually"). Consumed as part of the match so
#: the range still parses when the unit sits between the two amounts. Hourly
#: units are deliberately absent — they stay in the tail for the post-reject.
_UNIT = r"\s*/?\s*(?:years?|yrs?|annual(?:ly)?|per\s+(?:year|annum)|a\s+year)"

_SALARY_RANGE_RE = re.compile(
    rf"(?<![\w$])(?P<min>{_SALARY_AMOUNT}){_UNIT}?"
    rf"{_SALARY_SEP}"
    rf"(?P<max>{_SALARY_AMOUNT}){_UNIT}?"
    rf"(?:\s*{_CURRENCY_CODE}\b)?"
    rf"(?![\w$])",
    re.IGNORECASE,
)

_CURRENCY_RE = re.compile(rf"\b({_CURRENCY_CODE})\b", re.IGNORECASE)

#: A range is NOT a base salary when the SECOND amount is itself qualified as
#: hourly pay, equity/stock, or a bonus/commission — checked only right after
#: the match, so "… $200K–$270K + Equity" (equity ON TOP of base) still matches,
#: and "plus equity/bonus" further down the sentence is additional comp, not a
#: veto.
_POST_RANGE_REJECT_RE = re.compile(
    r"^\s*"
    r"(?:"
    r"per\s+hour|an\s+hour|hourly|/hour|/hr"
    r"|(?:in\s+|of\s+|worth\s+of\s+)?(?:equity|stock|options?|rsus?|shares)"
    r"|(?:(?:signing|performance|annual|target|cash|discretionary)\s+)*(?:bonus|commission)"
    r")\b",
    re.IGNORECASE,
)


def _amount_value(raw: str) -> float:
    """``"$100,000"`` / ``"$100k"`` / ``"USD $100k"`` -> numeric amount."""
    value = raw.strip()
    value = re.sub(r"^(?:USD|CAD)\s*", "", value, flags=re.IGNORECASE)
    value = value.replace("$", "").replace(",", "").strip()
    if value and value[-1] in "kK":
        return float(value[:-1]) * 1000
    return float(value)


def _has_k(raw: str) -> bool:
    """True when the amount text carries a ``k``/``K`` suffix."""
    return "k" in raw.lower()


def extract_salary(text: str) -> CompRange | None:
    """Return a stated base-salary range from ``text``, or ``None`` — never a guess.

    Matches two explicit amounts joined by a dash/em-dash/hyphen/``to``/``and``
    (``$100k–$150k``, ``$160-190k``, ``$100,000 and $200,000``, optional
    ``$``/``USD``/``CAD``), rejects the match when the second amount is itself
    hourly/equity/bonus, and carries a one-sided "k" across to the other amount
    ("$160-190k" → $160k–$190k). A false match would print a fabricated number
    as "stated", which is worse than no number.
    """
    if not text:
        return None
    for match in _SALARY_RANGE_RE.finditer(text):
        if _POST_RANGE_REJECT_RE.match(text[match.end():]):
            continue
        min_raw = match.group("min")
        max_raw = match.group("max")
        try:
            low = _amount_value(min_raw)
            high = _amount_value(max_raw)
        except (TypeError, ValueError):
            continue
        # "k" on one side only: "$160-190k" means $160k–$190k.
        if _has_k(max_raw) and not _has_k(min_raw) and low < 1000:
            low *= 1000
        if _has_k(min_raw) and not _has_k(max_raw) and high < 1000:
            high *= 1000
        if low > high:
            low, high = high, low
        currency = None
        code = _CURRENCY_RE.search(match.group(0))
        if code:
            currency = code.group(1).upper()
        return CompRange(min=low, max=high, currency=currency)
    return None
