from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pipeline.http import DeadlineExceeded, FetchError, HttpClient
from pipeline import http as http_module


class FakeResponse:
    def __init__(self, status=200, body=b'{"ok": true}', headers=None):
        self.status_code = status
        self.content = body
        self.text = body.decode()
        self.headers = headers or {}
        self.url = "https://example.test/path"
        self.closed = False

    def close(self):
        self.closed = True

    def iter_content(self, chunk_size=8192):
        yield self.content


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return next(self.responses)

    def close(self):
        self.closed = True


def client(session, now=None, sleeps=None):
    values = list(now or [0.0])
    cursor = [0]
    def monotonic():
        value = values[min(cursor[0], len(values) - 1)]
        cursor[0] += 1
        return value
    waits = sleeps if sleeps is not None else []
    return HttpClient(session=session, pace=None, monotonic=monotonic, sleep=waits.append, retries=2)


def test_request_buffers_success_and_json():
    response = FakeResponse(body=json.dumps({"jobs": [1]}).encode())
    session = FakeSession([response])
    result = client(session).request("GET", "https://example.test/path", params={"q": "x"})
    assert result.status_code == 200
    assert result.json() == {"jobs": [1]}
    assert response.closed
    assert session.calls[0][2]["params"] == {"q": "x"}


def test_503_is_reported_and_not_returned_as_empty_data():
    with pytest.raises(FetchError) as caught:
        client(FakeSession([FakeResponse(503), FakeResponse(503), FakeResponse(503)])).request("GET", "https://example.test/path")
    assert caught.value.kind == "http"
    assert caught.value.status_code == 503
    assert caught.value.attempts == 3


def test_429_stops_host_after_bounded_attempts():
    session = FakeSession([FakeResponse(429), FakeResponse(429), FakeResponse(429)])
    http = client(session)
    with pytest.raises(FetchError) as caught:
        http.request("GET", "https://example.test/path")
    assert caught.value.kind == "rate_limit"
    with pytest.raises(FetchError) as stopped:
        http.request("GET", "https://example.test/other")
    assert stopped.value.kind == "rate_limit"
    assert len(session.calls) == 3


def test_post_is_not_retried_unless_explicitly_safe():
    session = FakeSession([FakeResponse(503), FakeResponse(200)])
    http = client(session)
    with pytest.raises(FetchError):
        http.post_json("https://example.test/path", json={"x": 1})
    assert len(session.calls) == 1
    assert http.post_json("https://example.test/path", retry_safe=True) == {"ok": True}


def test_budget_raises_before_request_and_bounds_timeout():
    session = FakeSession([FakeResponse()])
    http = client(session, now=[0, 0, 0.25, 0.25, 0.25])
    with http.budget(1):
        http.request("GET", "https://example.test/path")
    assert session.calls[0][2]["timeout"] == pytest.approx(0.75)


def test_stream_closes_on_error():
    response = FakeResponse(body=b"abc")
    http = client(FakeSession([response]))
    with pytest.raises(RuntimeError):
        with http.stream("GET", "https://example.test/path") as stream:
            assert list(stream.iter_content()) == [b"abc"]
            raise RuntimeError("consumer failed")
    assert response.closed


def test_expired_budget_makes_no_network_call():
    session = FakeSession([FakeResponse()])
    http = HttpClient(session=session, pace=None, monotonic=lambda: 5.0)
    with http.budget(0):
        with pytest.raises(DeadlineExceeded):
            http.request("GET", "https://example.test/path")
    assert session.calls == []


def test_retry_after_503_honors_wait_and_closes_retry_response():
    first = FakeResponse(503, headers={"retry-after": "2"})
    session = FakeSession([first, FakeResponse()])
    waits = []
    http = client(session, sleeps=waits)
    http.request("GET", "https://user:secret@example.test/path")
    assert first.closed
    assert waits == [2.0]


def test_fetch_error_redacts_userinfo_and_query_and_session_closes():
    session = FakeSession([FakeResponse(403)])
    http = client(session)
    with pytest.raises(FetchError) as caught:
        http.request("GET", "https://user:secret@example.test/path?token=secret")
    assert caught.value.kind == "blocked"
    assert caught.value.url == "https://example.test/path"
    assert "secret" not in str(caught.value)
    http.close()
    assert session.closed


class Clock:
    now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def test_retry_after_http_date_is_honored(monkeypatch):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(1970, 1, 1, tzinfo=timezone.utc)

    monkeypatch.setattr(http_module, "datetime", FrozenDatetime)
    clock = Clock()
    session = FakeSession([FakeResponse(429, headers={"retry-after": "Thu, 01 Jan 1970 00:00:05 GMT"}), FakeResponse()])
    with HttpClient(session=session, pace=None, monotonic=clock.monotonic, sleep=clock.sleep) as http:
        assert http.get_json("https://example.test/path") == {"ok": True}
    assert clock.now == 5.0
    assert session.closed


@pytest.mark.parametrize("status", [401, 403, 999])
def test_block_suppresses_same_host_but_keeps_healthy_host(status):
    session = FakeSession([FakeResponse(status), FakeResponse()])
    with client(session) as http:
        with pytest.raises(FetchError, match="blocked"):
            http.request("GET", "https://example.test/path")
        with pytest.raises(FetchError, match="blocked"):
            http.request("GET", "https://example.test/another")
        assert http.get_json("https://healthy.test/path") == {"ok": True}
    assert len(session.calls) == 2


def test_retry_after_beyond_budget_defers_host_without_early_retry():
    clock = Clock()
    session = FakeSession([FakeResponse(429, headers={"Retry-After": "20"})])
    with HttpClient(session=session, pace=None, monotonic=clock.monotonic, sleep=clock.sleep) as http:
        with http.budget(10), pytest.raises(FetchError, match="rate_limit"):
            http.request("GET", "https://example.test/path")
        with pytest.raises(FetchError, match="rate_limit"):
            http.request("GET", "https://example.test/next")
    assert clock.now == 0
    assert len(session.calls) == 1


def test_pacing_waits_only_for_remaining_interval():
    clock = Clock()
    session = FakeSession([FakeResponse(), FakeResponse(), FakeResponse()])
    with HttpClient(session=session, pace=(3, 3), monotonic=clock.monotonic, sleep=clock.sleep) as http:
        http.request("GET", "https://example.test/a")
        first = clock.now
        http.request("GET", "https://example.test/b")
        assert clock.now == first + 3
        clock.sleep(10)
        before = clock.now
        http.request("GET", "https://example.test/c")
        assert clock.now == before


def test_safe_post_retries_and_reuses_json_body():
    session = FakeSession([FakeResponse(503), FakeResponse()])
    with client(session) as http:
        assert http.post_json("https://example.test/path", json={"offset": 20}, retry_safe=True) == {"ok": True}
    assert len(session.calls) == 2
    assert [call[2]["json"] for call in session.calls] == [{"offset": 20}, {"offset": 20}]


def test_session_reuse_and_identity_are_scoped_to_host():
    created = []
    def factory(impersonate):
        session = FakeSession([FakeResponse(), FakeResponse()])
        created.append((impersonate, session))
        return session
    with HttpClient(session_factory=factory, pace=None) as http:
        http.request("GET", "https://first.test/a", impersonate="chrome")
        http.request("GET", "https://first.test/b", impersonate="chrome")
        http.request("GET", "https://second.test/a")
    assert [mode for mode, _ in created] == ["chrome", None]
    assert [len(session.calls) for _, session in created] == [2, 1]
    assert all(session.closed for _, session in created)


def test_transport_retries_are_bounded_and_diagnostics_hide_secrets():
    class BrokenSession(FakeSession):
        def request(self, method, url, **kwargs):
            self.calls.append(url)
            raise OSError("secret credential in transport error")
    clock = Clock()
    session = BrokenSession([])
    with HttpClient(session=session, pace=None, monotonic=clock.monotonic, sleep=clock.sleep) as http:
        with pytest.raises(FetchError) as caught:
            http.request("GET", "https://example.test/path?secret=value")
    assert caught.value.kind == "transport"
    assert "secret" not in str(caught.value)
    assert len(session.calls) == 3
    assert clock.now == 3
