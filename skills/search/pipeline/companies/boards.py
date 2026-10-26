"""Job boards: recognise their links, read them, and find a company's board.

A board is ``"<platform>:<slug>"``. Greenhouse, Ashby, Lever and Workday are
readable: the same adapters the search uses fetch every listed role. Other
recognised platforms are recorded so the shortlist can say when one is worth
a reader. Anything else is ``custom:<host>``, a company's own careers site.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Any

from pipeline.http import DeadlineExceeded, FetchError, HttpClient
from pipeline.sources.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter, WorkdayAdapter
from search_shared.companies import slug_candidates

READERS = {
    "greenhouse": GreenhouseAdapter,
    "ashby": AshbyAdapter,
    "lever": LeverAdapter,
    "workday": WorkdayAdapter,
}
#: Platforms whose board names can be guessed from a company name.
GUESSABLE = ("greenhouse", "ashby", "lever")
MAX_GUESSES = 3

#: (host pattern, platform, where the slug is: "path" = first path segment,
#: "sub" = first host label).
_HOSTS = (
    (r"(?:job-)?boards(?:\.eu)?\.greenhouse\.io", "greenhouse", "path"),
    (r"jobs\.ashbyhq\.com", "ashby", "path"),
    (r"jobs(?:\.eu)?\.lever\.co", "lever", "path"),
    (r"apply\.workable\.com", "workable", "path"),
    (r"[^.]+\.workable\.com", "workable", "sub"),
    (r"(?:jobs|careers)\.smartrecruiters\.com", "smartrecruiters", "path"),
    (r"[^.]+\.recruitee\.com", "recruitee", "sub"),
    (r"[^.]+\.bamboohr\.com", "bamboohr", "sub"),
    (r"jobs\.gem\.com", "gem", "path"),
    (r"ats\.rippling\.com", "rippling", "path"),
    (r"[^.]+\.breezy\.hr", "breezy", "sub"),
    (r"[^.]+\.applytojob\.com", "jazzhr", "sub"),
    (r"[^.]+\.teamtailor\.com", "teamtailor", "sub"),
    (r"jobs\.jobvite\.com", "jobvite", "path"),
    (r"[^.]+\.pinpointhq\.com", "pinpoint", "sub"),
    (r"[^.]+\.jobs\.personio\.(?:de|com)", "personio", "sub"),
    (r"(?:www\.)?wellfound\.com", "wellfound", "company"),
    (r"[^.]+\.icims\.com", "icims", "sub"),
)
_IGNORED_HOSTS = re.compile(r"(?:^|\.)(?:linkedin\.com|lnkd\.in|indeed\.com|glassdoor\.[a-z.]+)$")


@dataclass
class Board:
    platform: str
    slug: str
    rows: list[dict[str, Any]] | None = None   # None = not read (unreadable or failed)

    @property
    def ref(self) -> str:
        return f"{self.platform}:{self.slug}"

    @property
    def readable(self) -> bool:
        return self.platform in READERS


def parse_board_url(url: str | None) -> tuple[str, str] | None:
    """``(platform, slug)`` for a job-board link; None for job sites and junk."""
    if not url:
        return None
    parts = urllib.parse.urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if not host or _IGNORED_HOSTS.search(host):
        return None
    segments = [s for s in parts.path.split("/") if s]

    m = re.fullmatch(r"([^.]+)\.(wd\d+)\.myworkdayjobs\.com", host)
    if m:
        site = next((s for s in segments if not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", s)), None)
        return ("workday", f"{m.group(1)}.{m.group(2)}.{site}") if site else None
    m = re.fullmatch(r"(wd\d+)\.myworkdaysite\.com", host)
    if m and len(segments) >= 3 and segments[0] == "recruiting":
        return "workday", f"{segments[1]}.{m.group(1)}.{segments[2]}"

    for pattern, platform, where in _HOSTS:
        if not re.fullmatch(pattern, host):
            continue
        if where == "sub":
            return platform, host.split(".")[0]
        if where == "company":
            if len(segments) >= 2 and segments[0] == "company":
                return platform, segments[1]
            return None
        if platform == "greenhouse" and segments[:1] == ["embed"]:
            slug = urllib.parse.parse_qs(parts.query).get("for", [""])[0]
            return (platform, slug) if slug else None
        return (platform, segments[0]) if segments else None
    return "custom", host


# ---- reading board rows -------------------------------------------------------


def fetch_rows(platform: str, slug: str, http: HttpClient) -> list[dict[str, Any]]:
    """Every listed role on a readable board, as the board returns it."""
    adapter = READERS[platform]({"name": platform, "tenants": [slug]}, http=http)
    return adapter.board_rows(slug)


def search_rows(platform: str, slug: str, text: str, http: HttpClient) -> list[dict[str, Any]] | None:
    """Rows a board's own search returns for ``text``; None where boards have no search.

    Only Workday needs it: its listing stops at 2000 rows, and a large
    company's roles in one country can sit past that cap.
    """
    if platform != "workday":
        return None
    adapter = READERS[platform]({"name": platform, "tenants": [slug]}, http=http)
    return adapter.search_rows(slug, text)


def row_title(platform: str, row: dict[str, Any]) -> str:
    value = row.get("text") if platform == "lever" else row.get("title")
    return str(value or "")


def row_url(platform: str, slug: str, row: dict[str, Any]) -> str | None:
    if platform == "greenhouse":
        return row.get("absolute_url")
    if platform == "ashby":
        return row.get("jobUrl")
    if platform == "lever":
        return row.get("hostedUrl")
    if platform == "workday":
        external = (row.get("externalPath") or "").strip()
        if not external:
            return None
        name, dc = slug.split(".")[:2]
        return f"https://{name}.{dc}.myworkdayjobs.com{external}"
    return None


def row_locations(platform: str, row: dict[str, Any]) -> list[str]:
    """Every location string a row names."""
    found: list[Any] = []
    if platform == "greenhouse":
        location = row.get("location")
        found.append(location.get("name") if isinstance(location, dict) else location)
        for office in row.get("offices") or []:
            if isinstance(office, dict):
                found.append(office.get("location") or office.get("name"))
    elif platform == "ashby":
        found.append(row.get("location"))
        for extra in row.get("secondaryLocations") or []:
            if isinstance(extra, dict):
                found.append(extra.get("location"))
        address = ((row.get("address") or {}).get("postalAddress") or {})
        found.append(address.get("addressCountry"))
    elif platform == "lever":
        categories = row.get("categories") or {}
        found.append(categories.get("location"))
        found.extend(categories.get("allLocations") or [])
    elif platform == "workday":
        found.append(row.get("locationsText"))
    return [str(x).strip() for x in found if isinstance(x, str) and x.strip()]


def row_codes(platform: str, row: dict[str, Any]) -> list[str]:
    """ISO country codes a row carries (Lever only)."""
    code = row.get("country") if platform == "lever" else None
    return [code.strip().upper()] if isinstance(code, str) and code.strip() else []


def row_currencies(platform: str, row: dict[str, Any]) -> list[str]:
    """Pay currencies a row states."""
    found: list[Any] = []
    if platform == "greenhouse":
        found.extend(r.get("currency_type") for r in row.get("pay_input_ranges") or [] if isinstance(r, dict))
    elif platform == "ashby":
        for tier in (row.get("compensation") or {}).get("compensationTiers") or []:
            for component in (tier or {}).get("components") or []:
                if isinstance(component, dict):
                    found.append(component.get("currencyCode"))
    elif platform == "lever":
        found.append((row.get("salaryRange") or {}).get("currency"))
    return sorted({str(c).strip().upper() for c in found if isinstance(c, str) and c.strip()})


def row_pay_text(platform: str, row: dict[str, Any]) -> str:
    """Free-text pay summary, where the board gives one."""
    if platform == "ashby":
        compensation = row.get("compensation") or {}
        return str(compensation.get("compensationTierSummary") or compensation.get("scrapeableCompensationSalarySummary") or "")
    return ""


# ---- finding a company's board -----------------------------------------------


def _title_key(title: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (title or "").casefold()).split())


def titles_match(a: str, b: str) -> bool:
    """Same role title, ignoring punctuation; a 4+ word title may sit inside the other."""
    ka, kb = _title_key(a), _title_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    shorter, longer = sorted((ka, kb), key=len)
    return len(shorter.split()) >= 4 and f" {shorter} " in f" {longer} "


def find_board(
    name: str,
    title: str | None,
    http: HttpClient,
    *,
    hint: tuple[str, str] | None = None,
) -> Board | None:
    """The company's board, read when readable.

    A ``hint`` (the posting's own board link, or one already on record) is
    trusted. Without one, board names are guessed from the company name on the
    guessable platforms, and a guess counts only when that board lists the
    same role ``title`` — a shared slug is not proof of a shared company.
    """
    if hint is not None:
        platform, slug = hint
        board = Board(platform, slug)
        if board.readable:
            try:
                board.rows = fetch_rows(platform, slug, http)
            except DeadlineExceeded:
                raise
            except Exception:  # noqa: BLE001 — a dead hint leaves the board unread
                board.rows = None
        return board
    if not title:
        return None
    for slug in slug_candidates(name)[:MAX_GUESSES]:
        for platform in GUESSABLE:
            try:
                rows = fetch_rows(platform, slug, http)
            except DeadlineExceeded:
                raise
            except (FetchError, ValueError, RuntimeError):
                continue
            if any(titles_match(title, row_title(platform, row)) for row in rows):
                return Board(platform, slug, rows)
    return None


def board_company_name(platform: str, slug: str, rows: list[dict[str, Any]]) -> str:
    """The company's name as its board states it, else the slug."""
    if platform == "greenhouse":
        for row in rows:
            name = row.get("company_name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    return slug.split(".")[0]
