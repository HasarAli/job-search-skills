"""Source adapters exercised through the shared transport seam, without network."""

import json
from pathlib import Path

import pytest
from pipeline.http import HttpClient
from search_shared.model import Query
from pipeline.sources.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter, WorkdayAdapter
from pipeline.sources.feed import WwrAdapter
from pipeline.sources.linkedin import LinkedInAdapter


class Response:
    def __init__(self, status=200, *, data=None, text="", url="https://example.test/jobs"):
        self.status_code = status
        self.text = json.dumps(data) if data is not None else text
        self.content = self.text.encode()
        self.headers = {}
        self.url = url

    def close(self):
        pass


class Session:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return next(self.responses)

    def close(self):
        pass


def http_for(session):
    return HttpClient(session=session, sleep=lambda delay: None, pace=None, retries=0)


QUERY = Query(roles=["engineer"], region="Remote", remote=True, posted_since=None)


def test_greenhouse_postings_use_shared_json_fetching():
    session = Session(Response(data={"jobs": [{
        "id": 1, "title": "Software Engineer", "location": {"name": "Remote, United States"},
        "absolute_url": "https://example.test/job/1",
    }]}))
    with http_for(session) as http:
        postings, failures = GreenhouseAdapter({"tenants": ["acme"]}, http=http).list(QUERY)
    assert failures == []
    assert [(p.source_id, p.title) for p in postings] == [("1", "Software Engineer")]
    assert session.calls[0][0] == "GET"


def test_linkedin_http_error_is_failure_not_empty_success():
    session = Session(Response(503))
    with http_for(session) as http:
        postings, failures = LinkedInAdapter({}, http=http).list(QUERY)
    assert postings == []
    assert len(failures) == 1
    assert "503" in failures[0].error


def test_lever_only_falls_back_to_eu_for_missing_tenant():
    session = Session(Response(404), Response(data=[]))
    with http_for(session) as http:
        postings, failures = LeverAdapter({"tenants": ["acme"]}, http=http).list(QUERY)
    assert (postings, failures) == ([], [])
    assert [call[1].split("/")[2] for call in session.calls] == ["api.lever.co", "api.eu.lever.co"]


def test_lever_rate_limit_does_not_probe_eu_or_next_tenant():
    session = Session(Response(429))
    with http_for(session) as http:
        postings, failures = LeverAdapter({"tenants": ["acme", "other"]}, http=http).list(QUERY)
    assert postings == []
    assert failures
    assert "rate_limit" in failures[0].error
    assert len(session.calls) == 1


def test_wwr_http_error_is_reported_before_feed_parsing():
    session = Session(Response(503, text="<html>Unavailable</html>"))
    with http_for(session) as http:
        postings, failures = WwrAdapter({}, http=http).list(QUERY)
    assert postings == []
    assert len(failures) == 1
    assert "503" in failures[0].error


def test_wwr_parses_feed_bytes_from_shared_fetch():
    session = Session(Response(text="""<rss version="2.0"><channel><title>Jobs</title>
    <item><title>Acme: Software Engineer</title><guid>https://example.test/job/1</guid>
    <link>https://example.test/job/1</link></item></channel></rss>"""))
    with http_for(session) as http:
        postings, failures = WwrAdapter({}, http=http).list(QUERY)
    assert failures == []
    assert [(p.company, p.title) for p in postings] == [("Acme", "Software Engineer")]


def test_workday_read_only_post_uses_shared_fetch():
    session = Session(Response(data={"total": 1, "jobPostings": [{
        "title": "Software Engineer", "externalPath": "/job/123",
        "locationsText": "Remote, United States", "bulletFields": ["123"],
    }]}))
    with http_for(session) as http:
        postings, failures = WorkdayAdapter({"tenants": ["acme.wd5.Jobs"]}, http=http).list(QUERY)
    assert failures == []
    assert len(postings) == 1
    assert session.calls[0][0] == "POST"
    assert session.calls[0][2]["json"]["offset"] == 0


def test_linkedin_block_suppresses_later_searches_to_host():
    fixture = Path(__file__).parent / "fixtures" / "linkedin_search.html"
    session = Session(Response(), Response(429), Response(text=fixture.read_text()))
    with http_for(session) as http:
        postings, failures = LinkedInAdapter({"geo_ids": [103644278, 101174742]}, http=http).list(QUERY)
    assert postings == []
    assert failures
    assert "rate_limit" in failures[0].error
    assert len(session.calls) == 2


def test_linkedin_authwall_stops_next_lookup():
    session = Session(Response(url="https://www.linkedin.com/authwall"))
    with http_for(session) as http:
        adapter = LinkedInAdapter({}, http=http)
        _, first_failures = adapter.list(QUERY)
        _, second_failures = adapter.list(QUERY)
    assert "blocked" in first_failures[0].error
    assert "blocked" in second_failures[0].error
    assert len(session.calls) == 1


@pytest.mark.parametrize("adapter,tenant", [
    (GreenhouseAdapter, "acme"), (AshbyAdapter, "acme"),
    (WorkdayAdapter, "acme.wd5.Jobs"), (LeverAdapter, "acme"),
])
def test_unrecognized_payload_is_not_empty_success(adapter, tenant):
    session = Session(Response(data={"error": "unexpected response"}))
    with http_for(session) as http:
        postings, failures = adapter({"tenants": [tenant]}, http=http).list(QUERY)
    assert postings == []
    assert len(failures) == 1
    assert "list" in failures[0].error
    assert len(session.calls) == 1
