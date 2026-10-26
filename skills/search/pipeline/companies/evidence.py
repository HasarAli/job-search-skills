"""Turn what a posting or a job board shows into company evidence.

Finders return ``(kind, detail)`` pairs (board rows add the role's link).
``detail`` is the observed text, cut to a short window, so the shortlist can
quote it and a person can judge it. Kinds are ``search_shared.companies.KINDS``.

Matching is deliberately narrow. A place name in a description counts only
near a word about where the work happens ("remote", "based", "office"...), so
"customers across North America" is not evidence. A phrase limiting the role
elsewhere is ignored when the same passage also opens it to home ("must reside
in the US or Canada").
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from pipeline.companies import boards
from pipeline.companies.settings import CheckSettings

#: Words that make a nearby place name a statement about where the work happens.
_CUES = (
    "remote", "remotely", "based", "located", "location", "locations", "reside", "residing",
    "resident", "residents", "work from", "working from", "anywhere in", "candidates in",
    "candidates from", "open to", "hiring in", "office", "offices", "hub", "hubs",
)
_CUE_WINDOW = 60
_SNIPPET = 70
#: Most details kept per kind from one board, so a large board stays a few rows.
BOARD_DETAILS_PER_KIND = 5


def _fold(text: str) -> str:
    """Lowercase and strip accents, keeping one character per character."""
    return "".join(
        unicodedata.normalize("NFKD", ch)[0] if unicodedata.combining(ch) == 0 else ch
        for ch in text
    ).lower()


def _terms_re(terms: Iterable[str]) -> re.Pattern[str] | None:
    parts = sorted({_fold(t.strip()) for t in terms if t and t.strip()}, key=len, reverse=True)
    if not parts:
        return None
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(p) for p in parts) + r")(?![a-z0-9])")


def _pay_re(terms: Iterable[str]) -> re.Pattern[str] | None:
    """A home-currency mark next to an amount: "CAD 180,000", "CA$183K", "180k CAD"."""
    parts = sorted({_fold(t.strip()) for t in terms if t and t.strip()}, key=len, reverse=True)
    if not parts:
        return None
    marks = "|".join(re.escape(p) for p in parts)
    return re.compile(
        rf"(?<![a-z0-9])(?:{marks})\s?\$?\s?\d|\d[\d,.]*\s?k?\s?(?:{marks})(?![a-z0-9])"
    )


def _snippet(original: str, start: int, end: int) -> str:
    lo, hi = max(0, start - _SNIPPET), min(len(original), end + _SNIPPET)
    text = " ".join(original[lo:hi].split())
    return ("…" if lo else "") + text + ("…" if hi < len(original) else "")


class Matcher:
    """Evidence finders for one ``company_check`` configuration."""

    def __init__(self, settings: CheckSettings) -> None:
        self.settings = settings
        self.home_re = _terms_re(settings.home_terms)
        self.region_re = _terms_re(settings.region_terms)
        self.away_re = _terms_re(settings.away_terms)
        self.eor_re = _terms_re(settings.eor_terms)
        self.pay_re = _pay_re(settings.pay_terms)
        self.cue_re = _terms_re(_CUES)
        self.codes = {c.strip().upper() for c in settings.home_codes}
        self.currencies = {t.strip().upper() for t in settings.pay_terms}

    # -- locations -----------------------------------------------------------

    def is_home(self, location: str | None) -> bool:
        return bool(location and self.home_re and self.home_re.search(_fold(location)))

    def is_home_currency(self, currency: str | None) -> bool:
        return bool(currency) and currency.strip().upper() in self.currencies

    def location_evidence(self, location: str | None) -> list[tuple[str, str]]:
        """A location in the home country, or a region that includes it."""
        if not location or not location.strip():
            return []
        folded = _fold(location)
        if self.home_re and self.home_re.search(folded):
            return [("home_role", location.strip())]
        if self.region_re and self.region_re.search(folded):
            return [("region", location.strip())]
        return []

    # -- posting text --------------------------------------------------------

    def _near_cue(self, folded: str, start: int, end: int) -> bool:
        if self.cue_re is None:
            return False
        window = folded[max(0, start - _CUE_WINDOW): end + _CUE_WINDOW]
        return bool(self.cue_re.search(window))

    def text_evidence(self, text: str | None) -> list[tuple[str, str]]:
        """Evidence a posting's description states about where it can be done."""
        if not text:
            return []
        folded = _fold(text)
        hits: list[tuple[str, str]] = []
        opened: list[tuple[int, int]] = []
        for regex in (self.region_re, self.home_re):
            if regex is None:
                continue
            for m in regex.finditer(folded):
                if self._near_cue(folded, m.start(), m.end()):
                    opened.append((m.start(), m.end()))
        if opened:
            start, end = opened[0]
            hits.append(("region", _snippet(text, start, end)))
        for kind, regex in (("eor", self.eor_re), ("home_pay", self.pay_re)):
            m = regex.search(folded) if regex else None
            if m:
                hits.append((kind, _snippet(text, m.start(), m.end())))
        if self.away_re:
            for m in self.away_re.finditer(folded):
                if any(abs(m.start() - s) <= 2 * _CUE_WINDOW for s, _ in opened):
                    continue
                hits.append(("away_only", _snippet(text, m.start(), m.end())))
                break
        return hits

    # -- job boards ----------------------------------------------------------

    def board_evidence(self, platform: str, slug: str, rows: list[dict[str, Any]]) -> list[tuple[str, str, str | None]]:
        """Home-located roles and home-currency pay across a board's rows."""
        found: dict[str, list[tuple[str, str, str | None]]] = {}

        def add(kind: str, detail: str, url: str | None) -> None:
            bucket = found.setdefault(kind, [])
            if len(bucket) < BOARD_DETAILS_PER_KIND and all(d != detail for _, d, _ in bucket):
                bucket.append((kind, detail, url))

        for row in rows:
            title = boards.row_title(platform, row) or "(untitled role)"
            url = boards.row_url(platform, slug, row)
            for location in boards.row_locations(platform, row):
                for kind, detail in self.location_evidence(location):
                    add(kind, f"{title} — {detail}", url)
            for code in boards.row_codes(platform, row):
                if code in self.codes:
                    add("home_role", f"{title} — country {code}", url)
            for currency in boards.row_currencies(platform, row):
                if self.is_home_currency(currency):
                    add("home_pay", f"{title} — pay in {currency}", url)
            pay_text = boards.row_pay_text(platform, row)
            if pay_text and self.pay_re and self.pay_re.search(_fold(pay_text)):
                add("home_pay", f"{title} — {pay_text.strip()}", url)
        return [item for bucket in found.values() for item in bucket]
