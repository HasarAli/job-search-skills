"""LinkedIn guest-API adapter (unauthenticated, remote-only, US/CA pinned).

``list()`` scrapes the unauthenticated guest search endpoint one page at a time
(``seeMoreJobPostings/search``), one scrape per (role × geoId), and normalises
each card to :class:`Posting`. ``fetch_detail()`` fetches the description page
(``jobPosting/<id>``) and returns the description text for the comp stage to
parse — never over the card, which carries no salary.

Constraints (spec): no login/session cookie, ``f_WT=2`` for remote, ``f_TPR``
recency windows, geography pinned by an explicit geoId list (default United
States + Canada). ``sortBy`` is deliberately not sent — the guest endpoint
ignores it and returns relevance order; the pipeline sorts newest-first
locally. Guest limits are undocumented, so the harness throttles 3–8s between
requests. The shared fetching module stops further requests to a blocked host.
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, time, timedelta, timezone
from typing import Any

from bs4 import BeautifulSoup

from pipeline.http import FetchError, HttpClient
from search_shared.model import Failure, Posting, Query
from pipeline.sources.base import BaseAdapter, collect_tenants

# ---- endpoints -------------------------------------------------------------

GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api"
SEARCH_URL = f"{GUEST_API}/seeMoreJobPostings/search"
DETAIL_URL_TEMPLATE = GUEST_API + "/jobPosting/{job_id}"
VIEW_URL_TEMPLATE = "https://www.linkedin.com/jobs/view/{job_id}"

#: Default geoIds: United States (103644278), Canada (101174742).
DEFAULT_GEO_IDS = [103644278, 101174742]
DEFAULT_MAX_PAGES = 10
PAGE_SIZE = 10
MAX_START = 975  # hard safety bound on ``start``

#: Recency windows the guest API honors; the smallest covering the query window
#: is sent, and a window older than 30 days is omitted (no ``f_TPR``).
_F_TPR_WINDOWS = (86400, 604800, 2592000)  # r86400 / r604800 / r2592000

#: Relative-posted text ("2 hours ago") -> seconds per unit. Weeks ≈ 7d,
#: months ≈ 30d (spec).
_RELATIVE_RE = re.compile(
    r"\b(\d+)\s+(second|minute|hour|day|week|month)s?\s+ago\b", re.IGNORECASE
)
_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 7 * 86400,
    "month": 30 * 86400,
}

#: Description containers tried in order; falling back to the whole page text.#: Description containers tried in order; falling back to the whole page text.
_DESCRIPTION_SELECTORS = (
    ".show-more-less-html__markup",
    ".description__text",
    ".decorated-job-posting__details",
    "#job-details",
)


# ---- parse helpers (module-level so the offline tests can call them) -------


def parse_search_html(html: str) -> list[Posting]:
    """Parse a guest search-page body into :class:`Posting` rows (no network)."""
    soup = BeautifulSoup(html, "html.parser")
    return _parse_cards(soup)


def description_from_html(html: str) -> str:
    """Extract the job-description text from a guest detail-page body."""
    soup = BeautifulSoup(html, "html.parser")
    return _description_text(soup)


def job_id_from_source(source_id: str) -> str | None:
    """``urn:li:jobPosting:NNNN`` -> ``NNNN`` (``None`` when malformed)."""
    value = (source_id or "").strip()
    if value.startswith("urn:li:jobPosting:"):
        job_id = value[len("urn:li:jobPosting:") :].strip()
        if job_id.isdigit():
            return job_id
        return None
    if value.isdigit():
        return value
    return None


def _parse_cards(soup: BeautifulSoup) -> list[Posting]:
    postings: list[Posting] = []
    # The urn + card classes live on the inner <div>, not the <li>; select the
    # attribute broadly and gate on the jobPosting prefix.
    for card in soup.select("div[data-entity-urn]"):
        urn = (card.get("data-entity-urn") or "").strip()
        if not urn.startswith("urn:li:jobPosting:"):
            continue
        posting = _parse_card(card, urn)
        if posting is not None:
            postings.append(posting)
    return postings


def _parse_card(card: BeautifulSoup, urn: str) -> Posting | None:
    title_el = card.select_one("span.sr-only")
    company_el = card.select_one("h4.base-search-card__subtitle a")
    location_el = card.select_one(".job-search-card__location")
    time_el = card.select_one("time.job-search-card__listdate")

    title = title_el.get_text(" ", strip=True) if title_el else ""
    company = company_el.get_text(" ", strip=True) if company_el else ""
    location = location_el.get_text(" ", strip=True) if location_el else None

    return Posting(
        source="linkedin",
        source_id=urn,
        title=title,
        company=company,
        url=_card_url(card, urn),
        location=location,
        remote=True,  # f_WT=2 enforces remote server-side
        posted_at=_parse_posted_at(time_el),
        stated_comp=None,  # salary is never on the card; fetch_detail sets it
    )


def _card_url(card: BeautifulSoup, urn: str) -> str:
    link = card.select_one("a.base-card__full-link[href]")
    href = link.get("href") if link else None
    if href:
        return urllib.parse.urljoin("https://www.linkedin.com/", href)
    job_id = job_id_from_source(urn)
    return VIEW_URL_TEMPLATE.format(job_id=job_id or "")


def _parse_posted_at(time_el: Any) -> datetime | None:
    """Relative text first ("2 hours ago"), else the date-only ``datetime``
    attr as END of day (23:59:59 UTC) — midnight would make a "yesterday" job
    read as >24h old and get freshness-dropped. Unparseable -> ``None``."""
    if time_el is None:
        return None
    relative = (time_el.get_text(" ", strip=True) or "").strip()
    match = _RELATIVE_RE.search(relative)
    if match:
        amount = int(match.group(1))
        seconds = _UNIT_SECONDS[match.group(2).lower()] * amount
        return datetime.now(timezone.utc) - timedelta(seconds=seconds)
    attr = (time_el.get("datetime") or "").strip()
    if attr:
        try:
            day = datetime.fromisoformat(attr)
        except ValueError:
            day = None
        if day is not None:
            return datetime.combine(day.date(), time(23, 59, 59), tzinfo=timezone.utc)
    return None


def _description_text(soup: BeautifulSoup) -> str:
    for selector in _DESCRIPTION_SELECTORS:
        node = soup.select_one(selector)
        if node is not None:
            text = node.get_text(" ", strip=True)
            if text:
                return text
    return soup.get_text(" ", strip=True)


def _f_tpr(posted_since: datetime | None) -> str | None:
    """Smallest ``f_TPR`` window covering ``posted_since``; ``None`` if omitted.

    Seconds are floored to an int so a window computed as exactly ``168h``
    (``posted_since_hours: 168``) still maps to ``r604800`` even after the few
    microseconds between config load and the scrape.
    """
    if posted_since is None:
        return None
    seconds = int((datetime.now(timezone.utc) - posted_since).total_seconds())
    if seconds < 0:
        return None
    for window in _F_TPR_WINDOWS:
        if seconds <= window:
            return f"r{window}"
    return None


def _parse_geo_ids(raw: Any) -> list[int]:
    """Coerce the source block's ``geo_ids``; default US + Canada when empty."""
    ids: list[int] = []
    if isinstance(raw, list):
        for value in raw:
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                ids.append(value)
            elif isinstance(value, str) and value.strip().isdigit():
                ids.append(int(value.strip()))
    return ids or list(DEFAULT_GEO_IDS)


def _parse_max_pages(raw: Any) -> int:
    if isinstance(raw, bool):
        return DEFAULT_MAX_PAGES
    if isinstance(raw, int) and raw > 0:
        return raw
    return DEFAULT_MAX_PAGES


# ---- adapter ---------------------------------------------------------------


class LinkedInAdapter(BaseAdapter):
    name = "linkedin"
    keys = {"name", "geo_ids", "max_pages"}

    def __init__(self, block: dict[str, Any], *, http: HttpClient | None = None) -> None:
        super().__init__(block, http=http)
        self.geo_ids = _parse_geo_ids(block.get("geo_ids"))
        self.max_pages = _parse_max_pages(block.get("max_pages"))

    # -- Adapter -------------------------------------------------------------

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]:
        roles = [r for r in query.roles if r.strip()]
        if not roles or not self.geo_ids:
            return [], []

        try:
            self._page(SEARCH_URL)
        except Exception as exc:  # noqa: BLE001 — adapter-level failure
            return [], [
                Failure(source=self.name, tenant=None, error=f"{type(exc).__name__}: {exc}")
            ]

        fetches = [
            (f"{role}@{geo_id}", (lambda t, r=role, g=geo_id: self._fetch(r, g, query)))
            for role in roles
            for geo_id in self.geo_ids
        ]
        return collect_tenants(self.name, fetches, lambda label, row: row, query)

    def fetch_detail(self, posting: Posting) -> str | None:
        """Fetch the JD text and return it (or ``None``); no mutation.

        The comp stage parses the returned text for a stated salary. Failed
        fetches are reported by the runner without discarding the posting.
        """
        job_id = job_id_from_source(posting.source_id)
        if job_id is None:
            return None
        soup = self._page(DETAIL_URL_TEMPLATE.format(job_id=job_id))
        return _description_text(soup) or None

    # -- internals -----------------------------------------------------------

    def _page(self, url: str, params: dict[str, str] | None = None) -> BeautifulSoup:
        response = self.http.request(
            "GET", url, params=params, pace=(3.0, 8.0), impersonate="chrome",
        )
        path = urllib.parse.urlsplit(response.url).path.lower()
        if "/login" in path or "/authwall" in path:
            self.http.stop_host(url, "blocked")
            raise FetchError("blocked", response.status_code, url, response.attempts)
        return BeautifulSoup(response.text, "html.parser")

    def _fetch(self, role: str, geo_id: int, query: Query) -> list[Posting]:
        params = self._params(role, geo_id, query)
        rows: list[Posting] = []
        start = 0
        for _ in range(self.max_pages):
            if start > MAX_START:
                break
            soup = self._page(SEARCH_URL, {**params, "start": str(start)})
            cards = _parse_cards(soup)
            if not cards:
                break  # empty page ends pagination
            rows.extend(cards)
            start += PAGE_SIZE
        return rows

    @staticmethod
    def _params(role: str, geo_id: int, query: Query) -> dict[str, str]:
        params: dict[str, str] = {
            "keywords": role,
            "geoId": str(geo_id),
        }
        if query.remote is True:
            params["f_WT"] = "2"
        window = _f_tpr(query.posted_since)
        if window is not None:
            params["f_TPR"] = window
        return params
