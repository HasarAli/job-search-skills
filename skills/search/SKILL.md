---
name: search
description: Run the daily job search and produce a newest-first shortlist. Use when the user says "find jobs", "run the job search", "today's shortlist", "search for roles", or wants fresh postings matching their targets and filters. Also runs unattended (cron) and leaves the shortlist for review.
---

# Search — daily shortlist, newest-first

Source fresh postings via JobSpy (plus optional per-region board adapters), dedup against everything already seen, and write a numbered shortlist the `apply` skill references by number.

## Prerequisites

1. Read `state.md`. Requires `onboard:targets` and `onboard:filters` complete. If `search/search-config.md`, `search/job-search-filters.md`, or `context/role-preferences.md` is missing, point the user at the `onboard` skill — do not improvise filters.
2. JobSpy environment: see `references/jobspy-guide.md` for install and setup. **Seeds, not state:** `references/jobspy-guide.md` is a seed/default only. On first run, materialize its script template into `search/scripts/search_jobs.py` in the data repo. Every subsequent run executes and, if needed, edits that data-repo script — never re-reads or edits the skill's reference.

## Flow

1. **Read inputs**: `search/search-config.md` (country, platforms), `search/job-search-filters.md` (comp, location, company type, logistics), `context/role-preferences.md` (role list — one query per target role; skip anything under "Do not pursue").
2. **Run queries — delegate to a subagent.** Spawn one subagent to execute `search/scripts/search_jobs.py` (one pass per role × region) and any board adapters from `references/boards.md` that `search-config.md` calls for. The subagent returns structured results only (company, title, location, posted date, comp if listed, url, source) — no raw dumps into the main context.
3. **Newest-first (binding)**: default window `hours_old` = 24–72h; sort by posted date descending. Widen the window (7d, then 14d) only when the fresh window returns thin results — note the widened window in the shortlist header.
4. **Dedup**: load `search/seen-jobs.json`; drop any result whose normalized URL or company+title+location key is already cached. Append every newly surfaced job to the cache (key, company, title, url, `first_seen` date).
5. **Filter**: apply `job-search-filters.md` constraints (comp floor, remote/location, company type). Borderline cases go in a "Watch" section, not silently dropped.
6. **Write the shortlist** and update `state.md` (`search` stage: last run date).

## Output — `search/shortlists/shortlist-YYYY-MM-DD.md`

Numbered entries, newest-first. **Numbers are the `apply` skill's default references — never reorder after writing.**

```
# Shortlist — YYYY-MM-DD
Sources: <sites/boards>, window: <hours_old>. Filters: job-search-filters.md.

1. **<Company> — <Role>** — <location> — posted <date> — <comp or "not listed">
   <url>
   Fit: <one line: why it matches the role targets/filters>
```

Group into "Apply now" and "Watch / borderline" if useful, but keep numbering continuous across sections.

## Unattended / cron mode

Designed to run without a user present: no questions, no confirmations. Apply the filters as written, leave judgment calls in "Watch", and finish by writing the shortlist — the user reviews it later. If a source fails (rate limit, network), note it in the shortlist header and continue with the remaining sources; never abort the whole run for one source.

## File contracts

| File | Read/Write | Notes |
|---|---|---|
| `search/search-config.md`, `search/job-search-filters.md`, `context/role-preferences.md` | read | inputs |
| `search/scripts/search_jobs.py` | materialize once, then read + execute | seeded from `references/jobspy-guide.md` on first run; edit only this copy thereafter |
| `search/seen-jobs.json` | read + append | dedup cache, gitignored |
| `search/shortlists/shortlist-YYYY-MM-DD.md` | write | daily output, gitignored |
| `state.md` | update | `search` stage: last run date |

References: `references/jobspy-guide.md` (env setup, script template, failure handling), `references/boards.md` (per-region boards beyond JobSpy, adapter pattern).
