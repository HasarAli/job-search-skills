import pytest

from pipeline.comp import levels
from pipeline.http import FetchError, HttpClient


class Response:
    def __init__(self, status, body=b"", headers=None):
        self.status_code = status
        self.content = body
        self.text = body.decode()
        self.headers = headers or {}
        self.url = "https://www.levels.fyi/"

    def close(self):
        pass


class Session:
    def __init__(self, response):
        self.response = response

    def request(self, method, url, **kwargs):
        return self.response

    def close(self):
        pass


def client(response):
    return HttpClient(session=Session(response), retries=0, pace=None)


def test_404_is_a_genuine_absence():
    assert levels.lookup("Acme", "software-engineer", "agent", http=client(Response(404))) is None


def test_503_is_reported():
    with pytest.raises(FetchError) as caught:
        levels.lookup("Acme", "software-engineer", "agent", http=client(Response(503)))
    assert caught.value.status_code == 503


def test_wrong_content_type_is_reported():
    response = Response(200, b"| Level | Total Comp |\n|---|---|\n| L3 | $100K |", {"Content-Type": "text/html"})
    with pytest.raises(FetchError) as caught:
        levels.lookup("Acme", "software-engineer", "agent", http=client(response))
    assert caught.value.kind == "content_type"
