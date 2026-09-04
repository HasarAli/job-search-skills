"""Exercise the public runner with real adapters and an offline HTTP transport."""

import json

import search
from pipeline.http import HttpClient


class Clock:
    now = 0.0

    def time(self):
        return self.now

    def sleep(self, delay):
        self.now += delay


class Response:
    def __init__(self, status=200, *, data=None, text="", elapsed=0):
        self.status_code = status
        self.text = json.dumps(data) if data is not None else text
        self.content = self.text.encode()
        self.headers = {}
        self.elapsed = elapsed
        self.url = ""

    def close(self):
        pass


class Session:
    def __init__(self, responses, clock):
        self.responses = iter(responses)
        self.clock = clock
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = next(self.responses)
        response.url = url
        self.clock.now += response.elapsed
        return response

    def close(self):
        self.closed = True


def run(tmp_path, monkeypatch, capsys, sources, responses, budget=1800):
    config = {
        "query": {"roles": ["engineer"], "region": "Remote", "remote": True,
                  "posted_since_hours": None},
        "sources": sources, "filters": [], "post_enrichment_filters": [],
    }
    (tmp_path / "config.yaml").write_text(json.dumps(config))
    (tmp_path / "filters.py").write_text("")
    monkeypatch.setenv("SEARCH_STATE_DIR", str(tmp_path))
    clock = Clock()
    session = Session(responses, clock)
    http = HttpClient(session=session, monotonic=clock.time, sleep=clock.sleep,
                      random_uniform=lambda low, high: low, pace=None, retries=0)
    monkeypatch.setattr(search, "HttpClient", lambda: http)
    monkeypatch.setattr(search, "ADAPTER_TIMEOUT", budget)
    code = search.main([])
    output = capsys.readouterr()
    return code, json.loads(output.out), output.err, session


HEALTHY_JOBS = {"jobs": [{"id": 1, "title": "Software Engineer",
                         "location": {"name": "Remote, Canada"},
                         "absolute_url": "https://example.test/jobs/1"}]}


def test_run_keeps_healthy_source_and_reports_failed_source(tmp_path, monkeypatch, capsys):
    code, output, stderr, session = run(tmp_path, monkeypatch, capsys,
        [{"name": "lever", "tenants": ["blocked", "other"]},
         {"name": "greenhouse", "tenants": ["healthy"]}],
        [Response(429), Response(data=HEALTHY_JOBS)])
    assert code == 0
    assert [row["source"] for row in output["rows"]] == ["greenhouse"]
    assert "source lever[blocked]:" in stderr and "429" in stderr
    assert len(session.calls) == 2
    assert session.closed
    assert set(output) == {"schema_version", "generated_at", "query", "counts", "rows"}


def test_run_deadline_prevents_next_tenant_request(tmp_path, monkeypatch, capsys):
    code, output, stderr, session = run(tmp_path, monkeypatch, capsys,
        [{"name": "greenhouse", "tenants": ["first", "next"]}],
        [Response(data=HEALTHY_JOBS, elapsed=2)], budget=1)
    assert code == 0
    assert len(output["rows"]) == 1
    assert "deadline" in stderr
    assert len(session.calls) == 1
    assert session.calls[0][2]["timeout"] <= 1
    assert session.closed


def test_run_reports_empty_success_without_http_failure(tmp_path, monkeypatch, capsys):
    code, output, stderr, session = run(tmp_path, monkeypatch, capsys,
        [{"name": "greenhouse", "tenants": ["empty"]}], [Response(data={"jobs": []})])
    assert code == 1  # Existing CLI contract: nothing collected.
    assert output["rows"] == []
    assert "zero results: greenhouse" in stderr
    assert "source greenhouse" not in stderr
    assert session.closed


def test_run_failed_details_keep_collected_posting(tmp_path, monkeypatch, capsys):
    card = """<div data-entity-urn="urn:li:jobPosting:123">
    <span class="sr-only">Software Engineer</span>
    <h4 class="base-search-card__subtitle"><a>Acme</a></h4>
    <span class="job-search-card__location">Remote, Canada</span></div>"""
    code, output, stderr, session = run(tmp_path, monkeypatch, capsys,
        [{"name": "linkedin", "geo_ids": [103644278], "max_pages": 1}],
        [Response(), Response(text=card), Response(503)])
    assert code == 0
    assert [row["source_id"] for row in output["rows"]] == ["urn:li:jobPosting:123"]
    assert "detail urn:li:jobPosting:123" in stderr and "503" in stderr
    assert len(session.calls) == 3
    assert session.closed
