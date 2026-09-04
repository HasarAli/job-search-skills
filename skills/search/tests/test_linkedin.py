"""Offline LinkedIn adapter tests — the guest-API card parser.

No network: both fixtures were captured once from LinkedIn's guest API and are
parsed verbatim here. A wrong selector fails silently as empty rows. The
salary-range regex lives in ``pipeline.comp.salary_text`` and is bank-tested in
``test_salary_text.py``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from pipeline.comp.salary_text import extract_salary
from pipeline.sources.linkedin import (
    description_from_html,
    job_id_from_source,
    parse_search_html,
)

HERE = Path(__file__).resolve().parent
SEARCH_FIXTURE = HERE / "fixtures" / "linkedin_search.html"
DETAIL_FIXTURE = HERE / "fixtures" / "linkedin_detail.html"

#: LinkedIn search cards carry ``"City, ST"`` locations.
_CITY_ST = re.compile(r"^[^,]+, [A-Z]{2}$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_search_page_parses_ten_postings():
    postings = parse_search_html(_read(SEARCH_FIXTURE))
    assert len(postings) == 10

    now = datetime.now(timezone.utc)
    for posting in postings:
        assert posting.source == "linkedin"
        assert posting.source_id.startswith("urn:li:jobPosting:")
        assert posting.title
        assert posting.company
        assert posting.location
        assert _CITY_ST.match(posting.location), posting.location
        assert posting.url.startswith("https://www.linkedin.com/jobs/view/")
        assert posting.remote is True
        assert posting.posted_at is not None
        assert posting.posted_at.tzinfo is not None
        assert posting.posted_at <= now
        assert posting.stated_comp is None  # salary is never on the card


def test_detail_fixture_extracts_and_range():
    description = description_from_html(_read(DETAIL_FIXTURE))
    assert description  # the fixture carries a description
    # The GM fixture states the range as "$160,000 and $200,000" — an "and"
    # form, which is a real base-salary range and must be extracted.
    assert "$160,000" in description
    assert "$200,000" in description
    comp = extract_salary(description)
    assert comp is not None
    assert comp.min == 160000.0
    assert comp.max == 200000.0


def test_source_id_extracts_numeric_id():
    assert job_id_from_source("urn:li:jobPosting:4419969671") == "4419969671"
    assert job_id_from_source("4419969671") == "4419969671"
    assert job_id_from_source("urn:li:jobPosting:") is None
    assert job_id_from_source("urn:li:jobPosting:abc") is None
    assert job_id_from_source("") is None
