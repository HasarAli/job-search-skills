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
It is browser-only: do not run a script search, guest APIs, direct HTTP
requests, or external salary lookups for this mode. The company commands below
are the one exception.

## Company check

For remote roles at companies based in another country: can this company
employ the user where they live? On when `.agents/search/config.yaml` has a
`company_check:` block (example in [defaults/config.yaml](defaults/config.yaml));
both modes use it, and its memory is in `seen.db`.

Each company gets a label from its evidence
([companies.py](shared/lib/search_shared/companies.py)):

- `confirmed` — a role located in the home country, pay in its currency, a
  posting open to a region that includes it ("US or Canada", "North America"),
  or an employer-of-record mention.
- `no` — only evidence against: a posting limited to another country, or a
  rejection citing work authorization there.
- `likely` — only circumstantial evidence: employees living in the home country
  (LinkedIn People tab).
- `unknown` — nothing recorded in the last 90 days.

Evidence counts for 90 days. A `confirmed` company is not checked again until
its evidence ages out; others are checked when never checked, then at most
every 30 days.

Script mode does the check itself. Every collected posting and every row of
every configured board is free evidence. For each posting that survives the
filters, a company that is due gets an active check: its job board is found
(the posting's own board, one on record, else guessed board names, accepted
only when that board lists the same role title) and read. If that doesn't
confirm it, a LinkedIn search for the company's jobs in the home country,
matched by its LinkedIn company page, covers companies whose careers site the
script can't read. Each row carries
`company_check`: `label`, `posting_in_home`, `board`, `evidence`, and
`people_check` (still `unknown`; worth the browser People-tab step). The run
cuts, as `filtered:company_check`, a posting whose own text limits it to
another country and every posting from a `no` company.

With `manage_tenants: true`, the run also keeps the board lists in
`config.yaml` in step: it adds `confirmed` companies whose board it can read
(Greenhouse, Ashby, Lever, Workday) and removes configured boards it read this
run whose company is no longer `confirmed`. The envelope's `companies` section
reports `added`, `removed`, `applied`, any `problem`, and `reader_needed`:
platforms the script can't read that two or more confirmed companies use. When
`reader_needed` names a platform, say so in the shortlist and offer to build
its adapter. A company's own careers site (`custom:`) never gets one.

Company commands, run from the project root; each prints JSON and exits:

```bash
python .agents/skills/search/search.py --companies [--label confirmed]
python .agents/skills/search/search.py --company "Acme"
python .agents/skills/search/search.py --check-company "Acme" --title "<role>" [--url "<apply link>"] [--company-url "<LinkedIn company page>"] [--location "<location>"] [--text "<posting text>"] [--force]
python .agents/skills/search/search.py --record-evidence "Acme" --kind people --detail "<what was seen>" [--url "<where>"]
python .agents/skills/search/search.py --mark-checked "Acme"
python .agents/skills/search/search.py --link-company "Acme" "Acme Labs"
```

`--link-company` joins two names for one company (a brand and its parent, or a
board slug that doesn't match the name). Other skills record evidence too:
`track` records `rejected` when a rejection cites work authorization.

## Shared state

`.agents/search/` holds user configuration, filters, `seen.db` (sightings,
comp cache, and the company check's memory), and `visa-wages/`. This skill's `shared/` directory holds the shipped shortlist
format and `search_shared` types/ledger; it is never copied or edited per user.
