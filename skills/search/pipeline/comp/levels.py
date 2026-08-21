"""Levels.fyi ``.md`` client.

``lookup`` resolves a company's job family to its Levels.fyi slug and parses the
level ladder (name + median total comp) into a :class:`~pipeline.model.CompRecord`.

Flow (per spec):

* GET ``/companies/{company}/salaries.md`` — the company page lists job families;
  used to resolve the family slug when the caller's family is not already a slug.
* GET ``/companies/{company}/salaries/{family}.md`` — the family ladder.

A "miss" is any of: a non-200 status, a 200 with zero bytes, or a 200 whose
content-type is not ``text/markdown``. All misses return ``None`` — this module
never raises and never caches empties (caching is the caller's job, in
``enrich.py``). ``requests`` is imported lazily inside ``lookup``; importing
this module makes no network calls.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pipeline.model import CompLevel, CompRecord

if TYPE_CHECKING:
    pass

_BASE_URL = "https://www.levels.fyi"
_TIMEOUT = 20.0
_CURRENCY = "USD"

# A family link on the company index page, e.g.
#   [Software Engineer](/companies/google/salaries/software-engineer.md)
# or the absolute form. Group 1 = display name, group 2 = slug.
_INDEX_LINK_RE = re.compile(
    r"\[([^\]]*)\]\(([^)]*?/companies/[^/]+/salaries/([a-z0-9\-]+)\.md[^)]*)\)",
    re.IGNORECASE,
)

# "$270,000", "$270K", "$1.2M" — group 1 = digits, group 2 = optional suffix.
_MONEY_RE = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)\s*([KMB])?", re.IGNORECASE)
_MONEY_MULT = {"": 1.0, "k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}

_LEVEL_ALIASES = ("level", "levels", "band", "grade", "ladder", "name")
_COMP_ALIASES = (
    "median total compensation",
    "total compensation",
    "median total comp",
    "total comp",
    "annual compensation",
    "compensation",
    "total pay",
    "comp",
    "total",
)


def _slugify(text: str) -> str:
    """Lowercase and turn any run of non-alphanumerics into a single dash."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def _get_markdown(url: str, attribution: str) -> str | None:
    """GET one markdown page. Returns the text on a hit, ``None`` on any miss.

    A miss is a non-200, a 200 with zero bytes, or a 200 whose content-type is
    not ``text/markdown``. Never raises (network errors are swallowed).
    """
    try:
        import requests
    except ImportError:  # optional dep missing -> treat as a miss
        return None

    headers = {
        "User-Agent": attribution or _BASE_URL,
        "Accept": "text/markdown, text/plain, */*",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type != "text/markdown":
        return None
    body = resp.content
    if not body or not body.strip():
        return None
    return resp.text


def _resolve_family_slug(index_markdown: str | None, family: str) -> str | None:
    """Find the family's slug in the company index page (markdown links)."""
    if not index_markdown:
        return None
    want = _slugify(family)
    if not want:
        return None
    for text, _url, slug in _INDEX_LINK_RE.findall(index_markdown):
        if slug == want or _slugify(text) == want:
            return slug
    return None


def _parse_money(text: str) -> float | None:
    """Parse a dollar figure like ``$270,000`` / ``$270K`` / ``$1.2M``."""
    m = _MONEY_RE.search(text or "")
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return value * _MONEY_MULT[(m.group(2) or "").lower()]


def _norm_header(cell: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (cell or "").lower()).strip()


def _find_column(header: list[str], aliases: tuple[str, ...]) -> int | None:
    """First column whose header matches an alias, most-specific alias first."""
    for alias in aliases:
        for i, cell in enumerate(header):
            norm = _norm_header(cell)
            if norm and (norm == alias or alias in norm):
                return i
    return None


def _strip_markup(name: str) -> str:
    return re.sub(r"[*_`#\[\]]+", "", name).strip()


def _parse_ladder(markdown: str) -> list[CompLevel]:
    """Parse the level ladder (name + median total comp) from markdown.

    Handles the common pipe-delimited table (a "level"-ish column plus a
    "total compensation"-ish column); falls back to a loose per-line scan for
    lines that carry a name and a dollar figure.
    """
    lines = (markdown or "").splitlines()

    # --- table form ---
    table: list[list[str]] = []
    for line in lines:
        if "|" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table.append(cells)
    if len(table) >= 2:
        header = table[0]
        level_idx = _find_column(header, _LEVEL_ALIASES)
        comp_idx = _find_column(header, _COMP_ALIASES)
        if level_idx is not None and comp_idx is not None and level_idx != comp_idx:
            levels: list[CompLevel] = []
            for row in table[1:]:
                if len(row) <= max(level_idx, comp_idx):
                    continue
                if all(set(c) <= {"-", ":", " "} for c in row if c):
                    continue  # separator row
                name = _strip_markup(row[level_idx])
                money = _parse_money(row[comp_idx])
                if name and money is not None:
                    levels.append(CompLevel(name=name, total_comp=money, currency=_CURRENCY))
            if levels:
                return levels

    # --- fallback: any line pairing a name with a dollar figure ---
    levels = []
    for line in lines:
        money = _parse_money(line)
        if money is None:
            continue
        name = line.split("$", 1)[0]
        name = re.sub(r"^[#*\-|>\s]+", "", name).strip(" :-—–\t")
        if not name or len(name) > 48:
            continue
        levels.append(CompLevel(name=name, total_comp=money, currency=_CURRENCY))
    return levels


def lookup(company: str, family: str, attribution: str) -> CompRecord | None:
    """Resolve ``company``/``family`` on Levels.fyi and return its ladder.

    ``attribution`` is sent as the request ``User-Agent`` (and documented here
    as the attribution string). Returns ``None`` on any miss; never raises and
    never caches (the caller caches).
    """
    company_slug = _slugify(company)
    if not company_slug:
        return None

    family = (family or "").strip()
    family_slug = _slugify(family)
    if not family_slug:
        return None

    # Resolve the family slug from the company index only when the caller's
    # family is not already a clean slug (the index lists families by name).
    if family != family_slug:
        index_md = _get_markdown(f"{_BASE_URL}/companies/{company_slug}/salaries.md", attribution)
        resolved = _resolve_family_slug(index_md, family)
        family_slug = resolved if resolved is not None else family_slug

    ladder_md = _get_markdown(
        f"{_BASE_URL}/companies/{company_slug}/salaries/{family_slug}.md", attribution
    )
    if ladder_md is None:
        return None

    ladder = _parse_ladder(ladder_md)
    if not ladder:
        return None

    floor = min(level.total_comp for level in ladder)
    return CompRecord(
        provenance="levels",
        floor_value=floor,
        currency=ladder[0].currency,
        ladder=ladder,
        range=None,
        employer=company,
    )
