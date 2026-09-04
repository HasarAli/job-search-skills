"""Adapter contract + shared helpers for the collection stage.

Every source adapter normalises its rows to :class:`search_shared.model.Posting`
and reports problems as :class:`search_shared.model.Failure`. The :class:`Adapter`
protocol is the seam the runner talks to; the helpers below implement the
"cheap guarantees" from the adapter contract — role / region / remote / date
filtering over list-response data and coercion shared by the concrete adapters.

Heavy third-party libraries (``feedparser``, ``curl_cffi``) are
imported lazily inside the functions that need them, so importing this package
never drags them in.
"""

from __future__ import annotations

import email.utils
import re
from datetime import date, datetime, time as datetime_time, timezone
from typing import Any, Protocol

from pipeline.filters import BUILTINS
from pipeline.http import DeadlineExceeded, HttpClient
from search_shared.model import Failure, Posting, Query

# ---- protocol --------------------------------------------------------------


class Adapter(Protocol):
    """What the runner calls on every source adapter.

    ``list()`` returns only results matching ``query``'s role/region/remote as
    far as the source can answer, normalised to :class:`Posting`. Isolation is
    per tenant: a dead tenant yields a :class:`Failure` for that tenant and
    healthy tenants still contribute postings. ``fetch_detail()`` returns the
    full description text (or ``None``); the comp stage parses it for salary.
    """

    name: str

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]: ...

    def fetch_detail(self, posting: Posting) -> str | None: ...


class BaseAdapter:
    """Source adapter with optional detail fetching and a shared HTTP client.

    Standalone callers that omit ``http`` close the adapter when finished.
    The runner owns and closes its shared client instead.
    """

    name: str = ""

    def __init__(self, block: dict[str, Any], *, http: HttpClient | None = None) -> None:
        self.http = http if http is not None else HttpClient()
        self._owns_http = http is None

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def fetch_detail(self, posting: Posting) -> str | None:
        return None


# ---- coercion helpers ------------------------------------------------------

def none_if_na(value: Any) -> Any:
    """Return ``None`` for pandas/numpy NaN and NaT (``value != value``)."""
    if value is None:
        return None
    try:
        if value != value:  # noqa: PLR0124 — NaN/NaT test, scalar values only
            return None
    except Exception:  # noqa: BLE001 — comparison may not be defined
        pass
    return value


def coerce_bool(value: Any) -> bool | None:
    """Best-effort boolean coercion; unknown strings become ``None``."""
    value = none_if_na(value)
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"1", "true", "yes", "remote", "on"}:
            return True
        if s in {"0", "false", "no", "on-site", "onsite", "on site"}:
            return False
        return None
    try:
        return bool(value)
    except (TypeError, ValueError):
        return None


def coerce_float(value: Any) -> float | None:
    """Best-effort numeric coercion; booleans are not numbers here."""
    value = none_if_na(value)
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_dt_string(s: str) -> datetime | None:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    try:
        return email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def coerce_datetime(value: Any) -> datetime | None:
    """Coerce ISO-8601 / RFC-822 strings, ``datetime``/``date`` to an aware UTC
    datetime (naive values are assumed UTC so freshness comparisons never blow
    up on tz mismatch)."""
    value = none_if_na(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, datetime_time.min)
    elif isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        dt = _parse_dt_string(s)
        if dt is None:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---- cheap local filters (the adapter-contract guarantees) -----------------


def matches_role(posting: Posting, roles: list[str]) -> bool:
    """Keep if the title contains any role (case-insensitive substring);
    unknown/empty titles pass."""
    if not roles:
        return True
    title = (posting.title or "").strip().lower()
    if not title:
        return True
    return any(r.strip().lower() in title for r in roles if r and r.strip())


def matches_region(posting: Posting, region: str) -> bool:
    """Delegates to the built-in predicate."""
    if not region:
        return True
    return BUILTINS["region"](posting, region)


def matches_remote(posting: Posting, remote: bool | None) -> bool:
    """Delegates to the built-in predicate."""
    return BUILTINS["remote"](posting, remote)


def matches_freshness(posting: Posting, since: datetime | None) -> bool:
    """Delegates to the built-in predicate."""
    return BUILTINS["freshness"](posting, since)


# ---- US/CA remote region helper (adapter-level, no catch-all) --------------

#: Country tokens that positively identify a US/CA posting.
_US_CA_COUNTRY_RE = re.compile(r"\b(?:united states|u\.s\.|usa|us|canada)(?=\W|$)", re.IGNORECASE)

#: Two-letter US state / Canadian province code, anywhere in the string
#: (permissive: "New York, NY (HQ)" and "US, CA, Santa Clara" both match).
_US_CA_CODE_RE = re.compile(r"\b([A-Z]{2})\b")

#: Coarse "N Locations" placeholder some boards emit when a role spans offices.
_LOCATIONS_PLACEHOLDER_RE = re.compile(r"\d+\s*location(s)?", re.IGNORECASE)

#: US/CA metropolitan areas, common metro abbreviations, and full state/province
#: names. Word-bounded so "chi" does not match "Chicago" and "new york" does not
#: match "New Yorktown". Positive identification only — a foreign veto still drops.
_US_CA_PLACE_RE = re.compile(
    r"\b(?:"
    r"san francisco|oakland|san jose|los angeles|san diego|sacramento|seattle|portland"
    r"|phoenix|tucson|denver|colorado springs|salt lake city|las vegas|albuquerque"
    r"|dallas|austin|houston|san antonio|fort worth|oklahoma city|kansas city"
    r"|minneapolis|saint paul|st\. louis|chicago|milwaukee|indianapolis|columbus"
    r"|cincinnati|cleveland|detroit|pittsburgh|nashville|memphis|atlanta|charlotte"
    r"|raleigh|miami|tampa|orlando|jacksonville|washington|baltimore|philadelphia"
    r"|new york|boston|newark|hartford|providence|buffalo"
    r"|toronto|vancouver|montreal|ottawa|calgary|edmonton|winnipeg|hamilton"
    r"|kitchener|waterloo|mississauga|brampton|halifax|victoria|quebec|saskatoon|regina"
    r"|sf|nyc|sea|chi"
    r"|alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware"
    r"|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana"
    r"|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana"
    r"|nebraska|nevada|new hampshire|new jersey|new mexico|north carolina|north dakota"
    r"|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota"
    r"|tennessee|texas|utah|vermont|virginia|west virginia|wisconsin|wyoming"
    r"|ontario|quebec|british columbia|alberta|manitoba|saskatchewan|nova scotia"
    r"|new brunswick|newfoundland|prince edward island|yukon|northwest territories|nunavut"
    r")\b",
    re.IGNORECASE,
)

_US_CA_CODES = frozenset(
    {
        # US states + District of Columbia
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
        "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
        "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
        "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        # Canadian provinces/territories
        "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC",
        "SK", "YT",
    }
)

#: Non-US/CA tokens that veto a "remote" location.
_NON_US_CA_RE = re.compile(
    r"\b(?:emea|apac|latam|europe|asia|"
    r"india|uk|ireland|germany|united kingdom|london|australia|"
    r"england|scotland|wales|new zealand|auckland|sydney|melbourne|"
    r"bangalore|bengaluru|mumbai|hyderabad|pune|delhi|"
    r"berlin|munich|france|paris|netherlands|amsterdam|spain|madrid|barcelona|"
    r"italy|milan|poland|warsaw|dublin|switzerland|zurich|sweden|stockholm|"
    r"norway|oslo|denmark|copenhagen|finland|helsinki|"
    r"singapore|japan|tokyo|china|beijing|shanghai|south korea|seoul|"
    r"brazil|sao paulo|mexico city|guadalajara|monterrey|argentina|colombia|chile|"
    r"israel|tel aviv|united arab emirates|dubai|portugal|lisbon|austria|vienna|"
    r"belgium|brussels|czech|prague|romania|bucharest|ukraine|kyiv|turkey|istanbul|"
    r"pakistan|bangladesh|philippines|manila|vietnam|thailand|malaysia|indonesia|"
    r"hong kong|taiwan)\b",
    re.IGNORECASE,
)


def matches_us_ca_remote(posting: Posting) -> bool:
    """True when ``posting.location`` looks like US/Canada remote (or unknown).

    A location passes when it is empty/unknown (keep), a "N Locations"
    placeholder (no geographic token, keep), names a US/CA country token,
    carries a 2-letter US state / Canadian province code anywhere in the
    string, contains "remote" without a non-US/CA token, or matches a US/CA
    metro / state / province name. An obvious non-US/CA token (the veto list)
    drops before the weaker metro/state-name match. This is adapter-level and
    deliberately not a catch-all: boards that cannot pin geography
    server-side filter their own rows with this.
    """
    location = (posting.location or "").strip()
    if not location:
        return True  # unknown -> keep
    if _LOCATIONS_PLACEHOLDER_RE.fullmatch(location):
        return True  # "6 Locations" — no geographic token; unknown -> keep
    if _US_CA_COUNTRY_RE.search(location):
        return True
    code = _US_CA_CODE_RE.search(location)
    if code and code.group(1) in _US_CA_CODES:
        return True
    # Obvious non-US/CA drops BEFORE the weaker metro/state-name match, so
    # "Victoria, Australia" drops while "Victoria, BC" keeps (code, above).
    if _NON_US_CA_RE.search(location):
        return False
    if "remote" in location.casefold():
        return True
    if _US_CA_PLACE_RE.search(location):
        return True
    return False


def filter_locally(
    postings: list[Posting],
    query: Query,
) -> list[Posting]:
    """Apply the cheap role/region/remote/date guarantees to a list in place.

    A ``prescreened`` posting skips the freshness and US/CA-remote checks
    because whoever handed it in already made those decisions; role/region/
    remote still apply. A ``skip_freshness`` posting (ATS boards that list all
    open roles) skips only the freshness check — it still gets the US/CA-remote
    check.
    """
    kept: list[Posting] = []
    for posting in postings:
        if not matches_role(posting, query.roles):
            continue
        if not matches_region(posting, query.region):
            continue
        if not matches_remote(posting, query.remote):
            continue
        if not posting.prescreened and not posting.skip_freshness and not matches_freshness(posting, query.posted_since):
            continue
        if not posting.prescreened and not matches_us_ca_remote(posting):
            continue
        kept.append(posting)
    return kept


def collect_tenants(
    source_name: str,
    tenant_fetches: list[tuple[str, Any]],
    normalise: Any,
    query: Query,
) -> tuple[list[Posting], list[Failure]]:
    """Run each ``(label, fetch)`` pair in isolation; normalise, in-run dedup, filter locally.

    ``fetch(label, query)`` returns rows; ``normalise(label, row)`` returns a
    :class:`Posting` or ``None``. A raising fetch yields one :class:`Failure`
    for that label; healthy labels still contribute. Per-tenant isolation +
    in-run identity dedup + the cheap local filters is the shared concern every
    tenant-looping adapter implements.
    """
    postings: list[Posting] = []
    failures: list[Failure] = []
    seen: set[tuple[str, str]] = set()
    for label, fetch in tenant_fetches:
        try:
            rows = fetch(label, query)
        except DeadlineExceeded as exc:
            failures.append(Failure(source=source_name, tenant=label, error=str(exc)))
            break
        except Exception as exc:  # noqa: BLE001 — per-tenant isolation
            failures.append(
                Failure(
                    source=source_name,
                    tenant=label,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        for row in rows:
            posting = normalise(label, row)
            if posting is None:
                continue
            key = (posting.source, posting.source_id)
            if key in seen:
                continue
            seen.add(key)
            postings.append(posting)
    return filter_locally(postings, query), failures
