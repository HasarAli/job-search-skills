"""Offline end-to-end smoke test for the job search pipeline.

Runs ``search.py`` once against a temp ``SEARCH_STATE_DIR`` whose config uses
ONLY the ``agent-json`` source (no network) pointing at the fixture in
``tests/fixtures/agent.json``. Verifies the exit code, the JSON envelope on
stdout, and the exact survivors.

Run from ``.agents/skills/search/``::

    python tests/smoke_test.py

Requires only the standard library + pyyaml (the agent-json adapter makes no
network calls; jobspy/feedparser/requests are never imported).
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .agents/skills/search/tests
SEARCH_DIR = HERE.parent                        # .agents/skills/search/
FIXTURE = HERE / "fixtures" / "agent.json"

# Filters the temp home's filters.py defines. ``not_agency`` runs pre-enrich
# (cheap); ``drops_high_salary`` runs post-enrich and reads ``posting.comp``.
FILTERS_PY = """\
from pipeline.model import Posting


def not_agency(posting: Posting) -> bool:
    return "staffing" not in (posting.company or "").lower()


def drops_high_salary(posting: Posting) -> bool:
    comp = posting.comp
    if comp is not None and comp.floor_value is not None and comp.floor_value >= 250000:
        return False
    return True
"""


def _config_yaml(fixture_path: Path) -> str:
    return f"""\
query:
  roles: [engineer, scientist, manager, recruiter]
  region: Remote
  remote: null
  posted_since_hours: null
sources:
  - name: agent-json
    path: "{fixture_path}"
filters:
  - not_agency
post_enrichment_filters:
  - drops_high_salary
comp_floor: 100000
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / "config.yaml").write_text(_config_yaml(FIXTURE), encoding="utf-8")
        (home / "filters.py").write_text(FILTERS_PY, encoding="utf-8")

        env = dict(os.environ)
        env["SEARCH_STATE_DIR"] = str(home)

        result = subprocess.run(
            [sys.executable, str(SEARCH_DIR / "search.py"), "--config", str(home / "config.yaml")],
            cwd=SEARCH_DIR,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("search.py exited", result.returncode, file=sys.stderr)
            print("--- stderr ---", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("--- stdout ---", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            return 1

        envelope = json.loads(result.stdout)

        assert envelope["schema_version"] == 1, envelope["schema_version"]
        assert envelope["counts"] == {
            # gamma-003 (Berlin, remote:false) is cut at collection by the
            # region pushdown, so it never enters the pipeline.
            "collected": 5,
            "unseen": 5,
            "filtered": 3,   # not_agency + comp_floor + drops_high_salary
            "enriched": 4,   # every cheap-filter survivor gets posting.comp set
            "emitted": 2,
        }, envelope["counts"]

        rows = envelope["rows"]
        assert len(rows) == 2, [row["source_id"] for row in rows]
        # Newest-first by posted_at; the undated posting sorts last.
        assert [row["source_id"] for row in rows] == ["acme-001", "beta-002"], rows

        first, second = rows
        assert first["posted_at"] is not None
        assert first["comp"]["provenance"] == "stated"
        assert first["comp"]["floor_value"] == 150000
        assert second["posted_at"] is None  # the undated survivor
        assert second["comp"]["provenance"] == "none"

        # The ledger recorded the three eliminations + two shortlists in one
        # atomic write.
        with sqlite3.connect(str(home / "seen.db")) as conn:
            by_outcome = dict(
                conn.execute(
                    "SELECT outcome, COUNT(*) FROM sightings GROUP BY outcome"
                ).fetchall()
            )
        assert by_outcome.get("shortlisted") == 2, by_outcome
        assert by_outcome.get("filtered:not_agency") == 1, by_outcome
        assert by_outcome.get("filtered:comp_floor") == 1, by_outcome
        assert by_outcome.get("filtered:drops_high_salary") == 1, by_outcome

        print("OK: 2 survivors ->", [row["source_id"] for row in rows])
        print("    counts ->", envelope["counts"])

        # --- scenario 2: agent-json is freshness-exempt ---
        # 004: handing the file in IS the freshness decision. A posting the
        # agent handed over must survive even a narrow freshness window.
        home2 = Path(tmp) / "home2"
        home2.mkdir()
        stale_fixture = home2 / "stale.json"
        stale_fixture.write_text(json.dumps([{
            "source": "greenhouse",
            "source_id": "old-001",
            "title": "Backend Engineer",
            "company": "OldCo",
            "url": "https://example.com/old-001",
            "location": "Remote, United States",
            "remote": True,
            "posted_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "stated_comp": {"min": 150000, "max": 180000, "currency": "USD"},
        }]), encoding="utf-8")
        (home2 / "config.yaml").write_text(f"""query:
  roles: [engineer]
  region: Remote
  remote: null
  posted_since_hours: 24
sources:
  - name: agent-json
    path: "{stale_fixture}"
filters: []
post_enrichment_filters: []
comp_floor: null
""", encoding="utf-8")
        (home2 / "filters.py").write_text("", encoding="utf-8")

        env2 = dict(os.environ)
        env2["SEARCH_STATE_DIR"] = str(home2)
        result2 = subprocess.run(
            [sys.executable, str(SEARCH_DIR / "search.py"), "--config", str(home2 / "config.yaml")],
            cwd=SEARCH_DIR, env=env2, capture_output=True, text=True,
        )
        if result2.returncode != 0:
            print("freshness-exemption run exited", result2.returncode, file=sys.stderr)
            print(result2.stderr, file=sys.stderr)
            return 1
        envelope2 = json.loads(result2.stdout)
        assert [row["source_id"] for row in envelope2["rows"]] == ["old-001"], envelope2["rows"]
        assert envelope2["counts"]["emitted"] == 1, envelope2["counts"]
        print("OK: freshness-exempt posting survived (30d old, 24h window)")
    return 0


def test_end_to_end():
    """pytest entry — the whole pipeline, offline, both scenarios."""
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
