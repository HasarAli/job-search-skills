"""Company check: names, labels, memory, evidence, boards, placement, board lists."""

import json
from datetime import datetime, timedelta, timezone

import pytest

import search
from pipeline.companies import boards, tenants
from pipeline.companies.check import CompanyCheck
from pipeline.companies.evidence import Matcher
from pipeline.companies.settings import CheckSettings, parse
from pipeline.http import FetchError, HttpClient
from pipeline.sources.linkedin import LinkedInAdapter
from search_shared import companies as rules
from search_shared.ledger import Ledger
from search_shared.model import CompRange, Posting

from test_run_fetching import Clock, Response, Session

SETTINGS = CheckSettings(
    home="Canada",
    home_terms=["canada", "toronto", "montreal", "british columbia"],
    home_codes=["CA"],
    pay_terms=["CAD", "CA$", "C$"],
    region_terms=["north america", "us or canada", "us/canada"],
    away_terms=["must reside in the us", "us-based candidates only", "anywhere in the us"],
    linkedin_geo_id=101174742,
    manage_tenants=True,
)


def _iso(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _posting(company="Acme", title="Senior Frontend Engineer", location="United States", **kw):
    return Posting(source="linkedin", source_id=kw.pop("source_id", f"{company}-{title}"),
                   title=title, company=company, url=kw.pop("url", "https://www.linkedin.com/jobs/view/1/"),
                   location=location, **kw)


# ---- names and labels --------------------------------------------------------


@pytest.mark.parametrize("raw, key", [
    ("Scribd, Inc.", "scribd"),
    ("Honeycomb.io", "honeycomb"),
    ("Montréal Labs Ltd", "montreal labs"),
    ("SS&C Technologies", "ss and c technologies"),
    ("Mercury Insurance Company", "mercury insurance"),
])
def test_normalise_name(raw, key):
    assert rules.normalise_name(raw) == key


def test_slug_candidates_most_likely_first():
    assert rules.slug_candidates("Lyra Health") == ["lyrahealth", "lyra-health", "lyra"]
    assert rules.slug_candidates("honeycomb.io")[:2] == ["honeycomb", "honeycombio"]


def test_label_precedence_and_aging():
    ev = lambda kind, days: {"kind": kind, "seen_at": _iso(days)}
    assert rules.label([]) == "unknown"
    assert rules.label([ev("people", 1)]) == "likely"
    assert rules.label([ev("people", 1), ev("away_only", 1)]) == "no"
    assert rules.label([ev("away_only", 1), ev("eor", 1)]) == "confirmed"
    # Evidence past the window stops counting.
    assert rules.label([ev("home_role", rules.EVIDENCE_DAYS + 1)]) == "unknown"


def test_due_for_check():
    assert rules.due_for_check("confirmed", None) is False
    assert rules.due_for_check("unknown", None) is True
    assert rules.due_for_check("no", _iso(1)) is False
    assert rules.due_for_check("likely", _iso(rules.RECHECK_DAYS + 1)) is True


# ---- memory ------------------------------------------------------------------


def test_evidence_keys_by_normalised_name_and_moves_forward(tmp_path):
    ledger = Ledger(tmp_path / "seen.db")
    ledger.record_evidence("Scribd, Inc.", "home_role", "Engineer — Toronto", seen_at=_iso(10))
    ledger.record_evidence("scribd", "home_role", "Engineer — Toronto", seen_at=_iso(20))
    company = ledger.company("SCRIBD")
    assert company["label"] == "confirmed"
    assert len(company["evidence"]) == 1
    assert company["evidence"][0]["seen_at"][:10] == _iso(10)[:10]  # never moves back


def test_unknown_kind_writes_nothing(tmp_path):
    ledger = Ledger(tmp_path / "seen.db")
    with pytest.raises(ValueError):
        ledger.record_evidence_many([("A", "home_role", "x", None, None), ("B", "vibes", "y", None, None)])
    assert ledger.companies() == []


def test_board_slug_merges_company_recorded_under_it(tmp_path):
    ledger = Ledger(tmp_path / "seen.db")
    ledger.record_evidence("scribdinc", "home_role", "Engineer — Toronto")
    ledger.set_company_board("Scribd, Inc.", "ashby:scribdinc")
    assert [c["name"] for c in ledger.companies()] == ["Scribd, Inc."]
    assert ledger.company("scribdinc")["label"] == "confirmed"
    assert ledger.company_for_board("ashby:scribdinc") == "Scribd, Inc."


def test_link_company_merges_other_name(tmp_path):
    ledger = Ledger(tmp_path / "seen.db")
    ledger.record_evidence("Velora", "home_role", "Engineer — Canada (Remote)")
    ledger.mark_company_checked("Aplos")
    ledger.link_company("Aplos", "Velora")
    company = ledger.company("Velora")
    assert company["name"] == "Aplos" and company["label"] == "confirmed"
    assert "velora" in company["aliases"]


# ---- settings ----------------------------------------------------------------


def test_settings_off_and_errors():
    assert parse(None) == (None, [])
    settings, errors = parse({"home": "", "home_terms": [], "colour": "red", "people_check_cap": -1})
    assert settings is None
    assert {e[0] for e in errors} == {
        "company_check.home", "company_check.home_terms", "company_check.colour",
        "company_check.people_check_cap",
    }


# ---- evidence ----------------------------------------------------------------


def test_location_evidence():
    m = Matcher(SETTINGS)
    assert m.location_evidence("Toronto, Ontario, Canada") == [("home_role", "Toronto, Ontario, Canada")]
    assert m.location_evidence("Montréal") == [("home_role", "Montréal")]
    assert m.location_evidence("Remote - North America") == [("region", "Remote - North America")]
    assert m.location_evidence("San Francisco, CA") == []


def test_text_evidence_needs_a_location_cue():
    m = Matcher(SETTINGS)
    assert m.text_evidence("We sell to customers across North America and Europe.") == []
    kinds = [k for k, _ in m.text_evidence("This role is remote and open to candidates in Canada.")]
    assert kinds == ["region"]


def test_text_evidence_pay_eor_and_away():
    m = Matcher(SETTINGS)
    hits = dict(m.text_evidence(
        "Base pay CA$183K - CA$251K. We hire internationally through Deel. "
        "We use CAD tools daily."))
    assert set(hits) == {"home_pay", "eor"}
    assert "CA$183K" in hits["home_pay"]
    assert [k for k, _ in m.text_evidence("Applicants must reside in the US.")] == ["away_only"]


def test_away_phrase_inside_an_opening_is_ignored():
    m = Matcher(SETTINGS)
    kinds = [k for k, _ in m.text_evidence("Remote: you must reside in the US or Canada.")]
    assert kinds == ["region"]


def test_board_evidence_per_platform():
    m = Matcher(SETTINGS)
    gh = [{"title": "Engineer", "location": {"name": "Remote - Canada"}, "absolute_url": "u1",
           "pay_input_ranges": [{"currency_type": "CAD"}]},
          {"title": "PM", "location": {"name": "New York"}}]
    kinds = {k for k, _, _ in m.board_evidence("greenhouse", "acme", gh)}
    assert kinds == {"home_role", "home_pay"}
    ashby = [{"title": "Eng", "location": "San Francisco",
              "secondaryLocations": [{"location": "Remote - North America"}]}]
    assert [k for k, _, _ in m.board_evidence("ashby", "acme", ashby)] == ["region"]
    lever = [{"text": "Eng", "categories": {"location": "Remote"}, "country": "CA", "hostedUrl": "u"}]
    assert m.board_evidence("lever", "acme", lever) == [("home_role", "Eng — country CA", "u")]


def test_board_evidence_is_capped_per_kind():
    m = Matcher(SETTINGS)
    rows = [{"title": f"Role {i}", "location": {"name": "Toronto"}} for i in range(20)]
    assert len(m.board_evidence("greenhouse", "acme", rows)) == 5


# ---- boards ------------------------------------------------------------------


@pytest.mark.parametrize("url, expected", [
    ("https://job-boards.greenhouse.io/tailscale/jobs/4721713005", ("greenhouse", "tailscale")),
    ("https://boards.greenhouse.io/embed/job_app?for=acme&token=1", ("greenhouse", "acme")),
    ("https://jobs.ashbyhq.com/cohere/7e0e08ed", ("ashby", "cohere")),
    ("https://jobs.lever.co/acme/123", ("lever", "acme")),
    ("https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/x",
     ("workday", "nvidia.wd5.NVIDIAExternalCareerSite")),
    ("https://wd1.myworkdaysite.com/recruiting/ssctech/SSCTechnologies/job/x",
     ("workday", "ssctech.wd1.SSCTechnologies")),
    ("https://jobs.gem.com/senpilot/am9i", ("gem", "senpilot")),
    ("https://apply.workable.com/acme/j/1/", ("workable", "acme")),
    ("https://careers.circle.com/us/en/job/1", ("custom", "careers.circle.com")),
    ("https://www.linkedin.com/jobs/view/1/", None),
    ("", None),
])
def test_parse_board_url(url, expected):
    assert boards.parse_board_url(url) == expected


def test_titles_match():
    assert boards.titles_match("Senior Software Engineer - Cards", "Senior Software Engineer, Cards")
    assert boards.titles_match("Senior Frontend Engineer, Design Systems (Remote)",
                               "Senior Frontend Engineer, Design Systems")
    assert not boards.titles_match("Software Engineer", "Senior Software Engineer")


def test_find_board_guesses_and_requires_the_same_title(monkeypatch):
    calls = []

    def fake_fetch(platform, slug, http):
        calls.append((platform, slug))
        if (platform, slug) == ("greenhouse", "acmehealth"):
            return [{"title": "Office Manager"}]  # a board, but not this company's role
        if (platform, slug) == ("ashby", "acme-health"):
            return [{"title": "Senior Frontend Engineer"}]
        raise FetchError("http", 404, slug, 1)

    monkeypatch.setattr(boards, "fetch_rows", fake_fetch)
    board = boards.find_board("Acme Health", "Senior Frontend Engineer", http=None)
    assert board.ref == "ashby:acme-health"
    assert calls[:2] == [("greenhouse", "acmehealth"), ("ashby", "acmehealth")]
    assert boards.find_board("Acme Health", None, http=None) is None  # nothing to verify against


# ---- placement -----------------------------------------------------------------


def _check(tmp_path, monkeypatch, rows_by_board=None, linkedin=None):
    rows_by_board = rows_by_board or {}
    linkedin = linkedin if linkedin is not None else []

    def fake_fetch(platform, slug, http):
        if (platform, slug) in rows_by_board:
            return rows_by_board[(platform, slug)]
        raise FetchError("http", 404, slug, 1)

    def fake_linkedin(self, company, geo_id):
        if isinstance(linkedin, Exception):
            raise linkedin
        return linkedin

    monkeypatch.setattr(boards, "fetch_rows", fake_fetch)
    monkeypatch.setattr(LinkedInAdapter, "company_jobs", fake_linkedin)
    return CompanyCheck(SETTINGS, Ledger(tmp_path / "seen.db"), http=None)


def _card(company, location, page):
    return Posting(source="linkedin", source_id=f"urn:li:jobPosting:{company}{location}", title="Account Executive",
                   company=company, url="https://ca.linkedin.com/jobs/view/x-1?position=1",
                   location=location, company_url=f"https://www.linkedin.com/company/{page}")


def test_linkedin_confirms_a_custom_site_company_by_its_page(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch, linkedin=[
        _card("Procom", "Toronto, Ontario, Canada", "procom"),
        _card("Procore Technologies", "Toronto, Ontario, Canada", "procore-technologies"),
    ])
    posting = _posting(company="Procore Technologies", url="https://careers.procore.com/jobs/1",
                       company_url="https://www.linkedin.com/company/procore-technologies/life/")
    kept, _ = check.check([posting], {})
    info = kept[0].company_check
    assert info["label"] == "confirmed" and info["board"] == "custom:careers.procore.com"
    assert info["evidence"][0]["detail"] == "Account Executive — Toronto, Ontario, Canada (LinkedIn)"
    assert info["evidence"][0]["url"] == "https://ca.linkedin.com/jobs/view/x-1"
    assert check.ledger.company("Procom") is None  # a lookalike's card is not this company's evidence


def test_linkedin_matches_by_name_without_a_page(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch, linkedin=[_card("Uber", "Montreal, Quebec, Canada", "uber-com")])
    kept, _ = check.check([_posting(company="Uber")], {})
    assert kept[0].company_check["label"] == "confirmed"


def test_linkedin_failure_leaves_label_and_reports(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch, linkedin=FetchError("blocked", 999, "x", 1))
    kept, _ = check.check([_posting(company="Mystery")], {})
    assert kept[0].company_check["label"] == "unknown"
    assert "LinkedIn search" in check.failures[0].error
    assert check.ledger.company("Mystery")["checked_at"] is not None


def test_home_posting_stays_and_confirms(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    kept, cut = check.check([_posting(location="Toronto, Ontario, Canada")], {})
    assert len(kept) == 1 and cut == []
    assert kept[0].company_check["label"] == "confirmed"
    assert kept[0].company_check["posting_in_home"] is True


def test_us_posting_from_company_with_canadian_board_stays_confirmed(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch, {
        ("greenhouse", "acme"): [{"title": "Senior Frontend Engineer", "location": {"name": "US-Remote"}},
                                 {"title": "Designer", "location": {"name": "Toronto"}}],
    })
    kept, cut = check.check([_posting()], {})
    info = kept[0].company_check
    assert info["label"] == "confirmed" and info["board"] == "greenhouse:acme"
    assert info["evidence"][0]["detail"] == "Designer — Toronto"


def test_posting_text_limited_elsewhere_is_cut(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    posting = _posting()
    kept, cut = check.check([posting], {id(posting): "Fully remote, anywhere in the US."})
    assert kept == [] and "anywhere in the US" in cut[0][1]
    assert check.ledger.company("Acme")["label"] == "no"


def test_no_company_is_cut_and_unknown_flags_people_check(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    check.ledger.record_evidence("NoCo", "rejected", "Rejected: requires US work authorization")
    check.ledger.mark_company_checked("NoCo")
    kept, cut = check.check([_posting(company="NoCo"), _posting(company="Mystery")], {})
    assert [p.company for p, _ in cut] == ["NoCo"]
    assert cut[0][1].startswith("company: no")
    assert kept[0].company_check["label"] == "unknown"
    assert kept[0].company_check["people_check"] is True


def test_active_check_runs_once_per_company_per_run(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(boards, "fetch_rows", lambda p, s, h: calls.append((p, s)) or (_ for _ in ()).throw(FetchError("http", 404, s, 1)))
    check.check([_posting(title="A role"), _posting(title="B role")], {})
    assert calls and len(set(calls)) == len(calls)
    assert check.ledger.company("Acme")["checked_at"] is not None


class _WorkdayStub:
    name = "workday"

    def __init__(self, rows):
        self.scanned = {"bigco.wd5.Careers": rows}


def test_harvest_searches_a_capped_workday_board_for_home(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    searched = []
    monkeypatch.setattr(boards, "search_rows", lambda p, s, text, h: searched.append(text) or
                        [{"title": "Engineer", "locationsText": "Canada, Toronto"}])
    scanned = check.harvest([], [_WorkdayStub([{"title": "Engineer", "locationsText": "US, CA, Santa Clara"}])])
    assert searched == ["Canada"]
    assert scanned == {"workday:bigco.wd5.Careers"}
    assert check.ledger.company("bigco")["label"] == "confirmed"


def test_harvest_failed_search_keeps_board_off_the_removal_list(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)

    def boom(*args):
        raise FetchError("http", 500, "x", 1)

    monkeypatch.setattr(boards, "search_rows", boom)
    assert check.harvest([], [_WorkdayStub([{"title": "Engineer", "locationsText": "US, Remote"}])]) == set()


def test_home_pay_from_stated_comp(tmp_path, monkeypatch):
    check = _check(tmp_path, monkeypatch)
    posting = _posting(stated_comp=CompRange(min=180000, max=230000, currency="CAD"))
    kept, _ = check.check([posting], {})
    assert kept[0].company_check["label"] == "confirmed"


# ---- board lists ----------------------------------------------------------------

CONFIG_TEXT = """\
# my settings
sources:
  - name: linkedin
    geo_ids: [103644278]
  - name: greenhouse
    tenants: [stripe, figma]   # keep this comment
  - name: ashby
    tenants:
      - ramp
      - notion

filters: []
"""


def test_plan_adds_confirmed_and_removes_lapsed(tmp_path):
    ledger = Ledger(tmp_path / "seen.db")
    for name, board, kind in [("Stripe", "greenhouse:stripe", "home_role"), ("Figma", "greenhouse:figma", None),
                              ("Ramp", "ashby:ramp", "region"), ("Notion", "ashby:notion", None),
                              ("Linear", "ashby:linear", "region"), ("Gemco", "gem:gemco", "eor"),
                              ("Gemtwo", "gem:gemtwo", "home_role"), ("Circle", "custom:careers.circle.com", "home_role")]:
        ledger.set_company_board(name, board)
        if kind:
            ledger.record_evidence(name, kind, f"{name} evidence")
    sources = [{"name": "greenhouse", "tenants": ["stripe", "figma"]}, {"name": "ashby", "tenants": ["ramp", "notion"]}]
    report = tenants.plan(sources, ledger, scanned={"greenhouse:stripe", "greenhouse:figma", "ashby:ramp"})
    assert report["added"] == {"ashby": ["linear"]}
    assert report["removed"] == {"greenhouse": ["figma"]}  # notion's board wasn't read this run
    assert report["reader_needed"] == {"gem": ["Gemco", "Gemtwo"]}


def test_apply_edits_flow_and_block_lists_and_adds_blocks(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(CONFIG_TEXT, encoding="utf-8")
    tenants.apply(path, added={"ashby": ["linear"], "lever": ["acme"]},
                  removed={"greenhouse": ["figma"], "ashby": ["notion"]})
    text = path.read_text(encoding="utf-8")
    assert "tenants: [stripe]   # keep this comment" in text
    assert "      - ramp\n      - linear\n" in text and "notion" not in text
    assert "  - name: lever\n    tenants: [acme]\n" in text
    assert text.startswith("# my settings") and text.rstrip().endswith("filters: []")


def test_apply_refuses_a_list_it_cannot_edit_safely(tmp_path):
    path = tmp_path / "config.yaml"
    original = "sources:\n  - name: greenhouse\n    tenants: [a,\n      b]\n"
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError):
        tenants.apply(path, added={"greenhouse": ["c"]}, removed={})
    assert path.read_text(encoding="utf-8") == original


# ---- the run -------------------------------------------------------------------

RUN_CONFIG = """\
query:
  roles: [engineer]
  region: Remote
  remote: true
  posted_since_hours: null
sources:
  - name: greenhouse
    tenants: [canco, usonly]   # boards
filters: []
post_enrichment_filters: []
company_check:
  home: Canada
  home_terms: [canada, toronto]
  manage_tenants: true
"""


def test_run_labels_rows_and_drops_board_without_home_roles(tmp_path, monkeypatch, capsys):
    (tmp_path / "config.yaml").write_text(RUN_CONFIG, encoding="utf-8")
    (tmp_path / "filters.py").write_text("")
    monkeypatch.setenv("SEARCH_STATE_DIR", str(tmp_path))
    clock = Clock()
    canco = {"jobs": [{"id": 1, "title": "Software Engineer", "company_name": "CanCo",
                       "location": {"name": "Remote, Canada"}, "absolute_url": "https://x.test/1"}]}
    usonly = {"jobs": [{"id": 2, "title": "Software Engineer", "company_name": "US Only",
                        "location": {"name": "San Francisco, CA"}, "absolute_url": "https://x.test/2"}]}
    session = Session([Response(data=canco), Response(data=usonly)], clock)
    http = HttpClient(session=session, monotonic=clock.time, sleep=clock.sleep,
                      random_uniform=lambda low, high: low, pace=None, retries=0)
    monkeypatch.setattr(search, "HttpClient", lambda: http)

    assert search.main([]) == 0
    output = json.loads(capsys.readouterr().out)
    labels = {row["company"]: row["company_check"]["label"] for row in output["rows"]}
    assert labels == {"CanCo": "confirmed", "US Only": "unknown"}
    board_calls = [url for _, url, _ in session.calls if "greenhouse" in url]
    assert len(board_calls) == 2  # a board read this run is not checked again
    assert output["companies"]["removed"] == {"greenhouse": ["usonly"]}
    assert output["companies"]["applied"] is True
    assert "tenants: [canco]   # boards" in (tmp_path / "config.yaml").read_text(encoding="utf-8")


def test_company_commands(tmp_path, monkeypatch, capsys):
    (tmp_path / "config.yaml").write_text(RUN_CONFIG, encoding="utf-8")
    (tmp_path / "filters.py").write_text("")
    monkeypatch.setenv("SEARCH_STATE_DIR", str(tmp_path))
    assert search.main(["--record-evidence", "Acme", "--kind", "people",
                        "--detail", "12 employees in Canada 💵"]) == 0
    out = capsys.readouterr().out
    assert out.isascii()  # a Windows console can't print the emoji raw
    assert json.loads(out)["label"] == "likely"
    assert search.main(["--link-company", "Acme", "Acme Labs"]) == 0
    capsys.readouterr()
    assert search.main(["--companies", "--label", "likely"]) == 0
    assert [c["name"] for c in json.loads(capsys.readouterr().out)] == ["Acme"]
    assert search.main(["--record-evidence", "Acme", "--kind", "people"]) == 2
