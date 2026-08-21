"""The comp cascade — stated wins, non-US skips, lowest-median floor, no empty cache.

Lookups are stubbed at the ``levels.lookup`` / ``visa_wages.lookup`` boundary; the
ledger is real (SQLite is deterministic). A wrong cascade fails silently: a
posting priced from the wrong source, or priced at the wrong level.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.comp import enrich as enrich_mod
from pipeline.model import CompLevel, CompRange, CompRecord, Posting
from pipeline.store.ledger import Ledger


def _posting(**kw) -> Posting:
    defaults = dict(
        source="s", source_id="1",
        title="Senior Software Engineer", company="Acme", url="u",
        location="San Francisco, CA",
    )
    defaults.update(kw)
    return Posting(**defaults)


def _config(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(levels_attribution="https://www.levels.fyi", visa_wages_dir=Path(tmp_path))


@pytest.fixture
def ledger(tmp_path) -> Ledger:
    return Ledger(tmp_path / "ledger.db")


def _stub_lookups(monkeypatch, levels_result=None, wages_result=None, record_calls=False):
    calls = []
    monkeypatch.setattr(
        enrich_mod.levels, "lookup",
        (lambda *a, **k: calls.append("levels") or levels_result)
        if record_calls else
        (lambda *a, **k: levels_result),
    )
    monkeypatch.setattr(
        enrich_mod.visa_wages, "lookup",
        (lambda *a, **k: calls.append("visa_wages") or wages_result)
        if record_calls else
        (lambda *a, **k: wages_result),
    )
    return calls


def test_stated_comp_wins_and_skips_lookups(monkeypatch, ledger, tmp_path):
    calls = _stub_lookups(monkeypatch, record_calls=True)
    p = _posting(stated_comp=CompRange(min=80000, max=400000, currency="USD"))
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "stated"
    assert p.comp.floor_value == 80000            # stated min, however wide
    assert p.comp.ladder == []
    assert calls == []                            # no lookups happened


def test_non_us_skips_lookups(monkeypatch, ledger, tmp_path):
    calls = _stub_lookups(monkeypatch, record_calls=True)
    p = _posting(location="London, United Kingdom")
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "none"
    assert p.comp.floor_value is None
    assert calls == []                            # 006: skip both lookups


def test_levels_hit_floor_is_lowest_median(monkeypatch, ledger, tmp_path):
    record = CompRecord(
        provenance="levels", floor_value=999999, currency="USD",
        ladder=[
            CompLevel("L3", 100000, "USD"),
            CompLevel("L4", 150000, "USD"),
            CompLevel("L5", 220000, "USD"),
        ],
        range=None, employer="Acme",
    )
    _stub_lookups(monkeypatch, levels_result=record)
    p = _posting()
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "levels"
    assert p.comp.floor_value == 100000            # lowest level's median, not the placeholder
    assert ledger.get_cached_comp("Acme", "software engineer") is not None


def test_levels_miss_falls_to_visa_wages_and_never_caches(monkeypatch, ledger, tmp_path):
    monkeypatch.setattr(enrich_mod.time, "sleep", lambda s: None)
    _stub_lookups(
        monkeypatch,
        levels_result=None,
        wages_result=CompRecord(provenance="visa-wages", floor_value=50000, currency="USD",
                                ladder=None, range=None, employer="Acme"),
    )
    p = _posting()
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "visa-wages"
    assert p.comp.floor_value == 50000
    assert ledger.get_cached_comp("Acme", "software engineer") is None  # miss never cached


def test_total_miss_is_none(monkeypatch, ledger, tmp_path):
    monkeypatch.setattr(enrich_mod.time, "sleep", lambda s: None)
    _stub_lookups(monkeypatch, levels_result=None, wages_result=None)
    p = _posting()
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "none"
    assert p.comp.floor_value is None


def test_cached_levels_avoids_lookup(monkeypatch, ledger, tmp_path):
    record = CompRecord(
        provenance="levels", floor_value=180000, currency="USD",
        ladder=[CompLevel("L3", 180000, "USD"), CompLevel("L4", 260000, "USD")],
        range=None, employer="Acme",
    )
    ledger.put_cached_comp("Acme", "software engineer", record.to_dict())
    monkeypatch.setattr(
        enrich_mod.levels, "lookup",
        lambda *a, **k: pytest.fail("lookup must not run on a cache hit"),
    )
    p = _posting()
    enrich_mod.enrich([p], _config(tmp_path), ledger)
    assert p.comp.provenance == "levels"
    assert p.comp.floor_value == 180000            # lowest median, recomputed from cache
