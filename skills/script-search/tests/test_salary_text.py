"""Bank-driven tests for the salary-range regex.

Every real-world salary phrase we've encountered lives in
``tests/bank/salary.json``. A posting whose range is missed gets added there,
then the regex in ``pipeline.comp.salary_text`` is strengthened until the bank
passes — never a one-off fix in the adapter.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.comp.salary_text import extract_salary

BANK = Path(__file__).resolve().parent / "bank" / "salary.json"


def _cases():
    return json.loads(BANK.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["text"][:60])
def test_salary_bank(case):
    comp = extract_salary(case["text"])
    expected = case["expected"]
    if expected is None:
        assert comp is None, f"expected no range, got {comp}: {case['text']!r}"
        return
    assert comp is not None, f"expected {expected}, got None: {case['text']!r}"
    assert comp.min == expected[0], f"{case['text']!r}"
    assert comp.max == expected[1], f"{case['text']!r}"
    assert comp.currency == expected[2], f"{case['text']!r}"
