from pathlib import Path

import pytest

from pipeline.comp import visa_wages
from pipeline.http import FetchError, HttpClient


class Response:
    def __init__(self, status=200, chunks=()):
        self.status_code = status
        self.headers = {}
        self.url = "https://www.dol.gov/file"
        self._chunks = chunks

    def iter_content(self, chunk_size=0):
        yield from self._chunks

    def close(self):
        pass


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append(url)
        return next(self.responses)

    def close(self):
        pass


def test_rate_limit_does_not_try_fallback(tmp_path):
    session = Session([Response(429)])
    http = HttpClient(session=session, retries=0, pace=None)
    with pytest.raises(FetchError):
        visa_wages._download("LCA_Disclosure_Data_FY2026_Q1.xlsx", tmp_path, http=http)
    assert len(session.calls) == 1


def test_interrupted_download_preserves_existing_file_and_cleans_temp(tmp_path):
    destination = tmp_path / "LCA_Disclosure_Data_FY2026_Q1.xlsx"
    destination.write_bytes(b"existing")

    class BrokenResponse(Response):
        def iter_content(self, chunk_size=0):
            yield b"PK\x03\x04partial"
            raise OSError("connection reset")

    http = HttpClient(session=Session([BrokenResponse()]), retries=0, pace=None)
    with pytest.raises(FetchError) as caught:
        visa_wages._download(destination.name, tmp_path, http=http)
    assert caught.value.kind == "transport"
    assert destination.read_bytes() == b"existing"
    assert list(tmp_path.glob("*.part")) == []


def test_missing_download_only_tries_distinct_urls_and_keeps_cause(tmp_path):
    session = Session([Response(404), Response(404)])
    with HttpClient(session=session, retries=0, pace=None) as http:
        with pytest.raises(FetchError) as caught:
            visa_wages._download("LCA_Disclosure_Data_FY2026_Q1.xlsx", tmp_path, http=http)
    assert caught.value.status_code == 404
    assert len(session.calls) == len(set(session.calls)) == 2
    assert list(tmp_path.glob("*.part")) == []


def test_non_spreadsheet_response_is_reported_without_url_fallback(tmp_path):
    session = Session([Response(chunks=[b"<html>blocked</html>"])])
    with HttpClient(session=session, retries=0, pace=None) as http:
        with pytest.raises(FetchError, match="content"):
            visa_wages._download("LCA_Disclosure_Data_FY2026_Q1.xlsx", tmp_path, http=http)
    assert len(session.calls) == 1
    assert list(tmp_path.glob("*.part")) == []
