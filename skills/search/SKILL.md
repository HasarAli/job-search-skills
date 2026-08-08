---
name: search
description: >-
  Run the job search into a numbered shortlist — pull fresh postings for the
  user's role targets from every configured board, dedup against everything
  already seen, and rank newest-first with a comp figure on every row. Use when
  the user says "find jobs", "run the search", or wants today's shortlist, and
  for unattended cron runs that leave the shortlist for later review. Applying
  to shortlisted roles belongs to `apply`; reading inbound recruiter threads
  belongs to `inbox`; adding a board, adapter, feed, or channel belongs to
  `sources`.
---

**Newest-first** binds the whole run: every pass windows on posted date, every output sorts on it descending.

**Prerequisites** — `goals/search-filters.md` and `goals/role-preferences.md` both present; a missing one stops the run and hands off to `goals`. `.agents/config/sources.json` present; a missing registry hands off to `sources`.

**Scripts** — the search engine ships with this skill under `scripts/`. `<skill-dir>` below is the directory holding this file; resolve it once and reuse the absolute path. Run every command from the user's repo root so the `.agents/` paths resolve. Dependencies are pinned in `<skill-dir>/scripts/requirements.txt`.

## Run

1. **Read inputs.** `goals/search-filters.md` → country, platform list, comp floor, remote/location rules, company type. `goals/role-preferences.md` → one search term per role target, skipping everything under "Do not pursue". Done when: every non-excluded role target carries a search term and every filter value — comp floor, remote rule, company type — is in hand.

2. **Run the passes in a subagent.** Spawn one subagent and hand it the search terms, regions, windows, platform list, and the resolved `<skill-dir>/scripts` path *in the prompt* — the `goals/` docs stay in the main session. It runs `scripts/search_jobs.py` once per role × region, plus the board adapters `goals/search-filters.md` names, and returns JSON-lines rows (`site`, `title`, `company`, `location`, `date_posted`, `min_amount`, `max_amount`, `currency`, `job_url`).

   Window: start at `hours_old` 24–72; widen to 168, then 336, for a role returning under ~5 fresh rows, and record the widened window in the shortlist header.

   Done when: every role × region × platform combination has either returned rows or been recorded as a failed source.

3. **Dedup.** Key = lowercase `job_url` stripped of query params, falling back to a `company|title|location` slug for cross-board duplicates of one posting. Drop keys already in `.agents/cache/seen-jobs.json`, then append every survivor (`key`, `company`, `title`, `url`, `first_seen`). Done when: the cache holds a key for every row that reaches the shortlist.

4. **Filter.** Apply the `goals/search-filters.md` constraints. A clean pass lands in **Apply now**; a judgment call lands in **Watch** with the constraint it strains named; a row the filters cut goes into the Watch cut line with the filter that cut it. Done when: every deduped row appears in one of those three places.

5. **Comp.** For every row with no posted comp, run `salary_lookup.py` for the DOL base-pay **floor** (`source: dol_lca_base`). On `n=0` — and only in an interactive session — fall back to the Levels.fyi total-comp browser lookup (`source: levels_fyi_tc`); in a cron run write "no DOL match; Levels pending (interactive)". Flags and procedure: [references/salary-lookup.md](references/salary-lookup.md). Done when: every comp-less row carries a DOL floor, a Levels figure, or that pending note.

6. **Write.** Write the shortlist below, then set the `search` stage in `.agents/state.md` to today's date. Done when: the shortlist file exists with continuous numbering *and* `.agents/state.md`'s `search` stage reads today's date — `apply`, `inbox`, and `track` read that stage for the last run.

## Output — `shortlists/<YYYY-MM-DD>.md`

Numbering runs continuously across sections: **Apply now** takes 1..n, **Watch** resumes at n+1 (the `7.` below assumes Apply now ended at 6). The numbers are how `apply` addresses rows: assign them at write time and keep them stable. One `Cut:` line per filter that cut rows.

```
# Shortlist — YYYY-MM-DD
Sources: <sites/boards run; failed sources named>. Window: <hours_old>.
Filters: `goals/search-filters.md`; targets: `goals/role-preferences.md`.

## Apply now

1. **<Company> — <Role>** — <location> — posted <date> — <comp or "not listed">
   <url>
   Fit: <one line against the role targets and filters>

## Watch

7. **<Company> — <Role>** — ... — Strains <constraint>: <why it is a judgment call>

Cut: <filter> — <company (figure)>, <company (figure)>
```

## Unattended runs

Runs headless on cron with no user present. Apply the filters as written, park every judgment call in **Watch**, and finish by writing the shortlist for the user to review later. A source that fails (rate limit, network, adapter error) is named in the header and skipped; the run completes on the remaining sources.

## File contracts

| File | Mode | Notes |
|---|---|---|
| `goals/search-filters.md`, `goals/role-preferences.md` | read | run inputs |
| `<skill-dir>/scripts/search_jobs.py` | execute | JobSpy pass, one per role × region |
| `<skill-dir>/scripts/adapter_ats.py`, `adapter_remote.py` | execute | ATS + remote-board pulls |
| `.agents/config/sources.json` | read | board registries the adapters fetch (rows marked `live`) plus the profession + region scope filters |
| `<skill-dir>/scripts/us/salary_lookup.py`, `salary_index.py` | execute | US DOL LCA comp lookup; DB path via `SALARY_DB` |
| `.agents/scripts/adapter_<board>.py` | execute | custom adapters `sources` wrote for this user, if any |
| `.agents/cache/seen-jobs.json` | read + append | dedup cache, gitignored |
| `shortlists/<YYYY-MM-DD>.md` | write | daily output, gitignored |
| `.agents/state.md` | update | `search` stage: last run date |

A source that returns nothing, a registry row gone stale, a region with no board: name it in the header and hand it to `sources`.
