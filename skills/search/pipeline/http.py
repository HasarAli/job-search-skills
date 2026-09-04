"""Small, polite HTTP seam for search source adapters.

The transport is deliberately kept here: source adapters deal in source data,
while this module owns sessions, retry policy, pacing, and cooperative stops.
The native ``curl_cffi`` import is lazy so offline filtering and tests stay
cheap.
"""

from __future__ import annotations

import contextlib
import email.utils
import math
import random
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator


class FetchError(RuntimeError):
    """A sanitized, actionable failure from the fetch seam."""

    def __init__(self, kind: str, status_code: int | None, url: str, attempts: int) -> None:
        self.kind = kind
        self.status_code = status_code
        self.url = _safe_url(url)
        self.attempts = attempts
        super().__init__(self._message())

    def _message(self) -> str:
        status = f" HTTP {self.status_code}" if self.status_code is not None else ""
        return f"{self.kind}{status} fetching {self.url} after {self.attempts} attempt(s)"


class DeadlineExceeded(FetchError):
    """The cooperative budget expired before another attempt could start."""

    def __init__(self, url: str, attempts: int) -> None:
        super().__init__("deadline", None, url, attempts)


@dataclass(frozen=True)
class BufferedResponse:
    """The response data retained after a non-streaming request closes."""

    status_code: int
    headers: dict[str, str]
    text: str
    content: bytes
    url: str = ""
    attempts: int = 1

    def json(self) -> Any:
        import json

        return json.loads(self.text)


class _StreamingResponse:
    def __init__(self, client: "HttpClient", response: Any, url: str) -> None:
        self._client, self._response, self._url = client, response, url

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    def iter_content(self, *args: Any, **kwargs: Any) -> Iterator[bytes]:
        try:
            for chunk in self._response.iter_content(*args, **kwargs):
                self._client.check_budget(self._url)
                yield chunk
        except FetchError:
            raise
        except Exception as exc:
            raise FetchError("transport", None, self._url, 1) from exc

    def close(self) -> None:
        self._response.close()


def _safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or parsed.netloc
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urllib.parse.urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def _host(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or parsed.netloc
    return f"{host}:{parsed.port}".lower() if parsed.port is not None else host.lower()


def _retry_after(headers: Any) -> float | None:
    value = next((v for k, v in (headers or {}).items() if str(k).lower() == "retry-after"), None)
    if value is None:
        return None
    try:
        delay = float(str(value).strip())
        return max(0.0, delay) if math.isfinite(delay) else None
    except (TypeError, ValueError):
        try:
            parsed = email.utils.parsedate_to_datetime(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            delay = (parsed - datetime.now(timezone.utc)).total_seconds()
            return max(0.0, delay) if math.isfinite(delay) else None
        except (TypeError, ValueError, OverflowError):
            return None


class HttpClient:
    """Reusable lazy ``curl_cffi`` client with bounded polite retries."""

    def __init__(
        self,
        *,
        impersonate: str | None = None,
        retries: int = 2,
        pace: tuple[float, float] | None = (0.5, 1.0),
        session: Any = None,
        session_factory: Any = None,
        sleep: Any = time.sleep,
        monotonic: Any = time.monotonic,
        random_uniform: Any = random.uniform,
    ) -> None:
        self.impersonate = impersonate
        self.retries = max(0, retries)
        self.pace = pace
        self._session = session
        self._sessions: dict[str, Any] = {}
        self._session_factory = session_factory
        self._sleep = sleep
        self._monotonic = monotonic
        self._uniform = random_uniform
        self._deadline: float | None = None
        self._stopped: dict[str, str] = {}
        self._last_request: dict[str, float] = {}
        self._last_attempts = 0

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _ensure_session(self, host: str, impersonate: str | None = None) -> Any:
        if self._session is not None:
            return self._session
        if host in self._sessions:
            return self._sessions[host]
        if self._session_factory is not None:
            session = self._session_factory(impersonate or self.impersonate)
        else:
            from curl_cffi.requests import Session

            options = {"impersonate": impersonate or self.impersonate} if impersonate or self.impersonate else {}
            session = Session(**options)
        self._sessions[host] = session
        return session

    def close(self) -> None:
        sessions = list(self._sessions.values())
        if self._session is not None:
            sessions.append(self._session)
        for session in {id(session): session for session in sessions}.values():
            session.close()
        self._sessions.clear()
        self._session = None

    @contextlib.contextmanager
    def budget(self, seconds: float) -> Iterator["HttpClient"]:
        previous = self._deadline
        new_deadline = self._monotonic() + max(0.0, seconds)
        self._deadline = min(previous, new_deadline) if previous is not None else new_deadline
        try:
            yield self
        finally:
            self._deadline = previous

    def check_budget(self, url: str = "", attempts: int = 0) -> None:
        if self._deadline is not None and self._monotonic() >= self._deadline:
            raise DeadlineExceeded(url, attempts)

    def stop_host(self, url: str, reason: str = "blocked") -> None:
        self._stopped[_host(url)] = reason if reason in {"blocked", "rate_limit"} else "blocked"

    def _wait(self, host: str, pace: tuple[float, float] | None) -> None:
        if pace is None:
            return
        now = self._monotonic()
        delay = self._uniform(*pace)
        last = self._last_request.get(host)
        if last is not None:
            delay = max(0.0, last + delay - now)
        self.check_budget()
        if self._deadline is not None:
            delay = min(delay, max(0.0, self._deadline - now))
        if delay > 0:
            self._sleep(delay)

    def _request(self, method: str, url: str, *, stream: bool, pace: tuple[float, float] | None, retry_safe: bool, **kwargs: Any) -> Any:
        host = _host(url)
        if host in self._stopped:
            raise FetchError(self._stopped[host], None, url, 0)
        method = method.upper()
        attempts = 0
        retryable_method = method in {"GET", "HEAD", "PUT", "DELETE", "OPTIONS"} or retry_safe
        last_status: int | None = None
        while attempts <= self.retries:
            self.check_budget(url, attempts)
            self._wait(host, pace)
            self.check_budget(url, attempts)
            attempts += 1
            request_kwargs = dict(kwargs)
            if self._deadline is not None:
                remaining = self._deadline - self._monotonic()
                request_kwargs["timeout"] = min(float(request_kwargs.get("timeout", 20)), max(0.001, remaining))
            request_kwargs["stream"] = stream
            try:
                response = self._ensure_session(host, request_kwargs.get("impersonate")).request(method, url, **request_kwargs)
            except Exception:
                self._last_request[host] = self._monotonic()
                if not retryable_method or attempts > self.retries:
                    raise FetchError("transport", None, url, attempts)
                self._retry_sleep(attempts, url)
                continue
            self._last_request[host] = self._monotonic()
            last_status = getattr(response, "status_code", None)
            if 200 <= (last_status or 0) < 300:
                self._last_attempts = attempts
                return response
            delay = _retry_after(response.headers)
            response.close()
            if last_status in {401, 403, 999}:
                self.stop_host(url, "blocked")
                raise FetchError("blocked", last_status, url, attempts)
            transient = last_status in {408, 425, 429, 500, 502, 503, 504}
            if transient and delay is not None and (
                delay > 30 or (
                    self._deadline is not None
                    and self._monotonic() + delay >= self._deadline
                )
            ):
                self.stop_host(url, "rate_limit")
                raise FetchError("rate_limit" if last_status == 429 else "deferred", last_status, url, attempts)
            if retryable_method and transient and attempts <= self.retries:
                self._retry_sleep(attempts, url, delay)
                continue
            if last_status == 429:
                self.stop_host(url, "rate_limit")
            raise FetchError("rate_limit" if last_status == 429 else "http", last_status, url, attempts)
        raise FetchError("http", last_status, url, attempts)

    def _retry_sleep(self, attempts: int, url: str, delay: float | None = None) -> None:
        if delay is None:
            delay = min(1.0 * (2 ** (attempts - 1)), 8.0)
        if self._deadline is not None:
            delay = min(delay, max(0.0, self._deadline - self._monotonic()))
        self.check_budget(url, attempts)
        if delay:
            self._sleep(delay)

    def request(self, method: str, url: str, *, params: dict[str, Any] | None = None, json: Any = None, headers: dict[str, str] | None = None, timeout: float = 20, retry_safe: bool = False, pace: tuple[float, float] | None = None, impersonate: str | None = None) -> BufferedResponse:
        request_kwargs: dict[str, Any] = {"params": params, "json": json, "headers": headers, "timeout": timeout}
        if impersonate is not None:
            request_kwargs["impersonate"] = impersonate
        response = self._request(method, url, stream=False, pace=self.pace if pace is None else pace, retry_safe=retry_safe, **request_kwargs)
        try:
            return BufferedResponse(
                response.status_code, dict(response.headers or {}), response.text,
                bytes(response.content), url=response.url or url, attempts=self._last_attempts,
            )
        finally:
            response.close()

    def get_json(self, url: str, **kwargs: Any) -> Any:
        response = self.request("GET", url, **kwargs)
        try:
            return response.json()
        except Exception as exc:
            raise FetchError("content", response.status_code, url, response.attempts) from exc

    def post_json(self, url: str, **kwargs: Any) -> Any:
        response = self.request("POST", url, **kwargs)
        try:
            return response.json()
        except Exception as exc:
            raise FetchError("content", response.status_code, url, response.attempts) from exc

    @contextlib.contextmanager
    def stream(self, method: str, url: str, **kwargs: Any) -> Iterator[Any]:
        pace = kwargs.pop("pace", None)
        kwargs.setdefault("timeout", 20)
        response = self._request(method, url, stream=True, pace=self.pace if pace is None else pace, retry_safe=kwargs.pop("retry_safe", False), **kwargs)
        try:
            yield _StreamingResponse(self, response, url)
        finally:
            response.close()
