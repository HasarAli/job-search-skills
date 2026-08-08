# JobSpy Guide — install, search pass, failure handling

[python-jobspy](https://github.com/speedyapply/JobSpy) scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, Naukri, and BDJobs through one `scrape_jobs()` call returning a pandas DataFrame. The site list and per-site capabilities change between releases — read the installed version's README before relying on either.

## Install

Python ≥ 3.10. Package name is `python-jobspy`; the import is `jobspy`.

```
python -m venv .venv
.venv/Scripts/activate      # Windows; source .venv/bin/activate elsewhere
pip install -r <search-skill-dir>/scripts/requirements.txt
```

The pins live with the scripts, so a cron run reproduces an interactive one. `<search-skill-dir>` is the installed `search` skill's directory — resolve it once and reuse the absolute path.

## The search pass

`scripts/search_jobs.py` ships with the `search` skill — read-only engine code, never copied into the user's repo. One invocation = one role × one region pass. Every command runs from the repo root so relative output paths land in the user's cache.

| Flag | Meaning |
|---|---|
| `--search-term` | required; one role target |
| `--location` | defaults to `Remote` |
| `--sites` | comma list: `linkedin,indeed,glassdoor,zip_recruiter,google,bayt,naukri` |
| `--hours-old` | only postings from the last N hours (the newest-first policy); default 72 |
| `--results` | per-site result cap; default 25 |
| `--remote` | remote-only pass |
| `--country-indeed` | required for indeed/glassdoor, e.g. `canada`, `germany` |
| `--full-descriptions` | fetch full JDs; much slower, more rate-limit exposure |
| `--out` | write results as JSON lines to this path instead of stdout |

Rows come back sorted on `date_posted` descending, carrying `site`, `title`, `company`, `location`, `date_posted`, `min_amount`, `max_amount`, `currency`, `job_url`.

Example passes:

```
python <search-skill-dir>/scripts/search_jobs.py --search-term "<role target>" --location "United States" --remote --hours-old 72 --out .agents/cache/raw/us.jsonl
python <search-skill-dir>/scripts/search_jobs.py --search-term "<role target>" --location "Berlin" --sites indeed,linkedin --country-indeed germany --hours-old 72 --out .agents/cache/raw/de.jsonl
```

JSON lines is the exchange format between the search subagent and the main session: one object per job, ISO dates, comp as `min_amount`/`max_amount`/`currency` where the board exposes it (often null).

## Rate limits & failure notes

- **LinkedIn limits hardest** — HTTP 429 after bursts, especially with `--full-descriptions`. Hold `results_wanted` at 25–50 per pass, space passes a few seconds apart, and leave full descriptions off on unattended runs.
- **Indeed and Glassdoor need `country_indeed`** matching the target market; without it results are wrong or empty.
- **Public listings only.** JobSpy scrapes what is public. Authenticating a personal account to scrape risks a ban on the real account — for deeper access to a board, take an official API or MCP route instead ([boards.md](boards.md)).
- One site failing throws or empties for that site alone: catch per pass and continue, per the failure rule in SKILL.md.
- `date_posted` is null on some boards. Treat null as oldest, keep the job, and mark its date "unknown" in the shortlist.

## Windows notes

- Set UTF-8 before running, or non-ASCII titles and locations crash pandas printing under the default console codepage:
  - PowerShell: `$env:PYTHONUTF8 = "1"` (or `$env:PYTHONIOENCODING = "utf-8"`)
  - cmd/cron wrapper: `set PYTHONUTF8=1`
- Use forward slashes or quoted paths in script args. Task Scheduler runs need absolute paths and the venv's `python.exe` (`.venv\Scripts\python.exe`).
