"""Adapter contract + shared helpers for the collection stage.

Every source adapter normalises its rows to :class:`pipeline.model.Posting`
and reports problems as :class:`pipeline.model.Failure`. The :class:`Adapter`
protocol is the seam the runner talks to; the helpers below implement the
"cheap guarantees" from the adapter contract — role / region / remote / date
filtering over list-response data — plus coercion and HTTP/retry utilities
shared by the concrete adapters.

Heavy third-party libraries (``jobspy``, ``feedparser``, ``requests``) are
imported lazily inside the functions that need them, so importing this package
never drags them in.
"""

from __future__ import annotations

import email.utils
import time
from datetime import date, datetime, time, timezone
from typing import Any, Protocol

from pipeline.model import Failure, Posting, Query

# ---- protocol --------------------------------------------------------------


class Adapter(Protocol):
    """What the runner calls on every source adapter.

    ``list()`` returns only results matching ``query``'s role/region/remote as
    far as the source can answer, normalised to :class:`Posting`. Isolation is
    per tenant: a dead tenant yields a :class:`Failure` for that tenant and
    healthy tenants still contribute postings. ``fetch_detail()`` is not used
    in the default run (it would fetch a full description after dedup).
    """

    name: str

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]: ...

    def fetch_detail(self, posting: Posting) -> str | None: ...


class BaseAdapter:
    """Mixin providing the default ``fetch_detail`` (no detail fetch in v1)."""

    name: str = ""

    def fetch_detail(self, posting: Posting) -> str | None:
        return None


# ---- coercion helpers ------------------------------------------------------

#: Default HTTP read timeout per request. The runner owns the hard per-call
#: timeout; this only stops a single request from hanging forever.
DEFAULT_HTTP_TIMEOUT = 20.0

#: Default retry policy: attempts = retries + 1, exponential backoff.
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.0


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
        dt = datetime.combine(value, time.min)
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
    """Keep if ``location`` contains the region (case-insensitive substring);
    missing location passes."""
    if not region:
        return True
    location = posting.location
    if location is None or not str(location).strip():
        return True
    return region.lower() in str(location).lower()


def matches_remote(posting: Posting, remote: bool | None) -> bool:
    """Keep if the posting's remote flag is compatible; unknown (None) passes.

    ``remote=True`` keeps anything not known on-site; ``remote=False`` keeps
    anything not known remote; ``None`` keeps everything.
    """
    if remote is None:
        return True
    if remote is True:
        return posting.remote is not False
    return posting.remote is not True


def matches_freshness(posting: Posting, since: datetime | None) -> bool:
    """Keep if ``posted_at >= since`` OR the posting is undated (a None date is
    not a failure)."""
    if since is None:
        return True
    if posting.posted_at is None:
        return True
    return posting.posted_at >= since


def filter_locally(
    postings: list[Posting],
    query: Query,
    *,
    apply_freshness: bool = True,
) -> list[Posting]:
    """Apply the cheap role/region/remote/date guarantees to a list in place.

    ``apply_freshness=False`` is used by ``agent-json``: handing the file in IS
    the freshness decision, so the adapter must not apply ``posted_since``.
    """
    kept: list[Posting] = []
    for posting in postings:
        if not matches_role(posting, query.roles):
            continue
        if not matches_region(posting, query.region):
            continue
        if not matches_remote(posting, query.remote):
            continue
        if apply_freshness and not matches_freshness(posting, query.posted_since):
            continue
        kept.append(posting)
    return kept


# ---- retry + HTTP helpers --------------------------------------------------


def retry_call(fn: Any, *, retries: int = DEFAULT_RETRIES, backoff: float = DEFAULT_BACKOFF) -> Any:
    """Run ``fn`` with simple exponential backoff; re-raise the last error.

    Retry policy is the adapter's to own; this is the shared loop. There is no
    status-code vocabulary here — callers that can distinguish permanent from
    transient failures should use the HTTP helpers below instead.
    """
    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — adapter-owned retry policy
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    assert last_exc is not None  # loop always runs at least once
    raise last_exc


def http_get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> Any:
    """GET ``url`` and parse JSON, retrying transient failures only.

    4xx is treated as permanent (raised immediately, so a Lever 404 can fall
    through to the EU host); 429/5xx and network errors retry with backoff.
    """
    import requests  # lazy: requests is heavy and not needed to import package

    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            continue
        if resp.status_code in {429, 500, 502, 503, 504}:
            last_exc = requests.HTTPError(
                f"HTTP {resp.status_code} from {url}", response=resp
            )
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            continue
        resp.raise_for_status()  # 4xx -> permanent, raise immediately
        try:
            return resp.json()
        except ValueError as exc:
            raise requests.RequestException(f"non-JSON response from {url}") from exc
    if last_exc is not None:
        raise last_exc
    raise requests.RequestException(f"GET {url} failed after {retries} retries")


def http_post_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> Any:
    """POST JSON to ``url`` and parse the response, retrying transient failures."""
    import requests  # lazy

    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            continue
        if resp.status_code in {429, 500, 502, 503, 504}:
            last_exc = requests.HTTPError(
                f"HTTP {resp.status_code} from {url}", response=resp
            )
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            continue
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError as exc:
            raise requests.RequestException(f"non-JSON response from {url}") from exc
    if last_exc is not None:
        raise last_exc
    raise requests.RequestException(f"POST {url} failed after {retries} retries")
