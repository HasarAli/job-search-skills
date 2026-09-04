---
name: search
description: >-
  Search for jobs in one of two modes: run the configured scripted sources into
  a numbered shortlist, or inspect the signed-in LinkedIn results tab into a
  salary-only shortlist. Use when the user says "find jobs", "run the search",
  "search LinkedIn", or asks for a shortlist. Does not apply to jobs.
---

# Search

Choose the mode from the user's request. `search script` (or an ordinary
"find jobs" request) uses configured sources. `search browser linkedin` uses
only the current signed-in LinkedIn results tab. Both modes write the same
timestamped shortlist format and share `.agents/search/seen.db`.

## Script mode

Run:

```bash
python .agents/skills/search/search.py                  # prints JSON to stdout
python .agents/skills/search/search.py --json path.json # agent-collected postings
```

Exit codes: `0` shortlist produced · `1` nothing collected · `2` config error.
Read [shared/shortlist-format.md](shared/shortlist-format.md) for naming,
metadata, layout, numbering, and selection.

The script fetches, dedups, filters, and prices postings; turn its JSON into
the shortlist. Collection uses a shared, polite transport: requests are paced
and retried within cooperative stage deadlines; blocked or exhausted-rate-limit
hosts stop for the run. Fetch and enrichment failures go to stderr without
discarding healthy postings. Check each source's access rules and robots
instructions before enabling it; never bypass login or CAPTCHA restrictions.

Add a tenant by appending a block to `.agents/search/config.yaml` → `sources:`.
Adding a source type means one adapter declaring `name` and `keys`, registered
in `pipeline/sources/registry.py`. Define candidate-specific predicates in
`.agents/search/filters.py`; use `comp_floor` for a plain compensation floor.

## Browser LinkedIn mode

Read and follow [references/browser-linkedin.md](references/browser-linkedin.md).
It is browser-only: do not run the script, guest APIs, direct HTTP requests, or
external salary lookups for this mode.

## Shared state

`.agents/search/` holds user configuration, filters, `seen.db`, and
`visa-wages/`. This skill's `shared/` directory holds the shipped shortlist
format and `search_shared` types/ledger; it is never copied or edited per user.
