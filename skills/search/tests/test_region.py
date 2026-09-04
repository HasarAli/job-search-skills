"""Bank-driven tests for the US/CA-remote region check in ``base.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from search_shared.model import Posting
from pipeline.sources.base import matches_us_ca_remote

BANK = Path(__file__).resolve().parent / "bank" / "region.json"


def _cases():
    return json.loads(BANK.read_text(encoding="utf-8"))


def _posting(location):
    return Posting(
        source="t", source_id="t", title="t", company="t", url="t", location=location
    )


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["location"] or "<empty>")
def test_region_bank(case):
    assert matches_us_ca_remote(_posting(case["location"])) is case["keep"], case
