# JobSpy Guide — install, script template, failure handling

> Seed/default only — customize `search/scripts/search_jobs.py` in your data repo, not this file; skill updates overwrite it.

[python-jobspy](https://github.com/speedyapply/JobSpy) scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, Naukri, and BDJobs through one `scrape_jobs()` call returning a pandas DataFrame. Site list and per-site capabilities change between releases — check the README of the installed version rather than trusting this page.

## Install

Python ≥ 3.10.

```
pip install -U python-jobspy
```

Or in the data repo with a virtualenv:

```
python -m venv .venv
.venv/Scripts/activate      # Windows; source .venv/bin/activate elsewhere
pip install -U python-jobspy
```

Pin it in the data repo's root `requirements.txt` so cron runs are reproducible.

## Script template

Materialized to `search/scripts/` on first run: the skill copies this template to `search/scripts/search_jobs.py` in the data repo, then always executes (and, if it needs edits, edits) that copy — never this reference. One invocation = one role × one region pass; the skill loops over the user's role targets.

```python
import argparse
import json
import sys

from jobspy import scrape_jobs


def main():
    p = argparse.ArgumentParser(description="JobSpy search pass")
    p.add_argument("--search-term", required=True)
    p.add_argument("--location", default="Remote")
    p.add_argument("--sites", default="linkedin,indeed",
                   help="comma list: linkedin,indeed,glassdoor,zip_recruiter,google,bayt,naukri")
    p.add_argument("--hours-old", type=int, default=72,
                   help="only postings from the last N hours (newest-first policy)")
    p.add_argument("--results", type=int, default=25, help="per-site result cap")
    p.add_argument("--remote", action="store_true")
    p.add_argument("--country-indeed", default=None,
                   help="required for indeed/glassdoor, e.g. 'canada', 'germany'")
    p.add_argument("--full-descriptions", action="store_true",
                   help="fetch full JDs (much slower; more rate-limit exposure)")
    p.add_argument("--out", default=None, help="write results as JSON lines to this path")
    args = p.parse_args()

    kwargs = dict(
        site_name=args.sites.split(","),
        search_term=args.search_term,
        location=args.location,
        results_wanted=args.results,
        hours_old=args.hours_old,
        is_remote=args.remote,
        linkedin_fetch_description=args.full_descriptions,
    )
    if args.country_indeed:
        kwargs["country_indeed"] = args.country_indeed

    jobs = scrape_jobs(**kwargs)

    cols = ["site", "title", "company", "location", "date_posted",
            "min_amount", "max_amount", "currency", "job_url"]
    cols = [c for c in cols if c in jobs.columns]
    jobs = jobs.sort_values("date_posted", ascending=False)

    if args.out:
        jobs[cols].to_json(args.out, orient="records", lines=True,
                           date_format="iso", force_ascii=False)
        print(f"{len(jobs)} jobs -> {args.out}")
    else:
        jobs[cols].to_json(sys.stdout, orient="records", lines=True,
                           date_format="iso", force_ascii=False)


if __name__ == "__main__":
    main()
```

Example passes:

```
python search/scripts/search_jobs.py --search-term "senior data engineer" --location "United States" --remote --hours-old 72 --out search/raw-us.jsonl
python search/scripts/search_jobs.py --search-term "senior data engineer" --location "Berlin" --sites indeed,linkedin --country-indeed germany --hours-old 72 --out search/raw-de.jsonl
```

## Output handling → shortlist markdown

- JSON lines is the exchange format between the search subagent and the orchestrator: one object per job, ISO dates, comp as `min_amount`/`max_amount`/`currency` when the board exposes it (often null).
- The orchestrator (not the script) merges passes, dedups against `seen-jobs.json`, applies filters, and writes the numbered `shortlist-YYYY-MM-DD.md` per SKILL.md.
- Dedup key: lowercase `job_url` stripped of query params; fall back to `company|title|location` slug for cross-board duplicates of the same posting.

## Rate limits & failure notes

- **LinkedIn is the most aggressive limiter** — expect HTTP 429 after bursts, especially with `--full-descriptions`. Keep `results_wanted` ≤ 25–50 per pass, space passes a few seconds apart, and skip full descriptions on unattended runs.
- **Indeed/Glassdoor require `country_indeed`** matching the target market or results are wrong/empty.
- **Do not log in.** JobSpy scrapes public listings; authenticating a personal account to scrape risks that account. If deeper access to a board is needed, prefer an official API/MCP endpoint (see `boards.md`).
- Proxies: `scrape_jobs(proxies=[...])` exists for hard-limited environments; unnecessary for daily-volume runs.
- A single site failing throws or returns empty for that site only — catch per-pass, note the failed source in the shortlist header, and continue.
- `date_posted` can be null (some boards omit it). Treat null as oldest, keep the job, and mark the date "unknown" in the shortlist.
- Thin results (< ~5 fresh jobs per role): rerun with `--hours-old 168`, then `336`, per the SKILL.md widening rule.

## Windows notes

- Set UTF-8 before running, or non-ASCII titles/locations crash pandas printing under the default console codepage:
  - PowerShell: `$env:PYTHONUTF8 = "1"` (or `$env:PYTHONIOENCODING = "utf-8"`)
  - cmd/cron wrapper: `set PYTHONUTF8=1`
- Use forward slashes or quoted paths in script args; Task Scheduler runs need absolute paths and the venv's `python.exe` (`.venv\Scripts\python.exe`).
