---
name: script-search
description: Run the job search into a numbered shortlist — pull fresh postings for the user's role targets from every configured source, dedup against everything already seen, and rank newest-first with a comp figure on every row. Use when the user says "find jobs", "run the search", or wants today's shortlist, and for unattended cron runs that leave the shortlist for later review.
---

# Script search

The script fetches, dedups, filters, and prices postings; you turn its JSON into the shortlist.

## Run

```bash
python .agents/skills/script-search/search.py                  # prints JSON to stdout
python .agents/skills/script-search/search.py --json path.json # hand in agent-collected postings
```

Exit codes: `0` shortlist produced · `1` nothing collected · `2` config error (JSON on stderr).

Collection uses one shared, polite `curl_cffi` transport for the complete run.
Requests are paced and retried within cooperative stage deadlines; blocked hosts
and hosts whose rate-limit retries are exhausted stop for the rest of the run. Source adapters must
report tenant-level failures while returning healthy postings, and new source
adapters should use the shared `http` passed by `build_adapters` rather than
creating their own session. Fetch and enrichment failures are reported on
stderr and do not discard healthy postings.

Defaults: at most three attempts, 0.5–1s host spacing (3–8s for LinkedIn), and
exponential retry backoff. `Retry-After` supports seconds and dates; waits over
30s or beyond the remaining budget defer the host instead of retrying early.
Only explicitly read-only search POSTs are retried. Check each source's access
rules and robots instructions before enabling it; this transport does not
automate those checks or bypass login/CAPTCHA restrictions.

## Render the shortlist

Read the JSON on stdout and follow the shared
[shortlist format](../../search/shortlist-format.md) for naming, metadata,
layout, numbering, and selection.

- Comp: if `stated_comp` carries a range, write `$min–$max (stated)`; else if `comp.floor_value`, write `$<floor_value> (<provenance>)`; else "not listed".
- A row that strains a filter but is otherwise a fit goes in **Watch**, naming the constraint; a row a filter cut goes in the **Cut** line.

## Add a source

Append a block to `.agents/search/config.yaml` → `sources:`. Not listed = not run.

```yaml
  - name: greenhouse            # ATS tenant: company slug
    tenants: [stripe, databricks]
  - name: ashby
    tenants: [ramp]
  - name: workday
    tenants: [nvidia.wd5.NVIDIAExternalCareerSite]   # slug.wdN.siteId
  - name: agent-json            # postings collected elsewhere, by path
    path: path/to/collected.json   # rows: source, source_id, title, company, url
```

Adding a source *type* (a board the adapters don't cover) means one adapter class that declares `name` and `keys`, registered in `pipeline/sources/registry.py` — that single entry is what config validation and the runner both read. The YAML block above is for adding a *tenant* to an existing type.

## Add a filter

Define a custom predicate in `.agents/search/filters.py`, then name it in `config.yaml`:

```python
def min_comp(posting): return posting.comp is None or (posting.comp.floor_value or 0) >= 200000
```

```yaml
filters: [discipline, remote_only]      # run early (cheap)
post_enrichment_filters: [min_comp]      # run after comp; may read posting.comp
```

A plain comp floor is the built-in `comp_floor` config key (runs post-enrich, reads `posting.comp`) — use that instead of a custom predicate. Write a `filters.py` predicate only for logic the built-ins don't cover; the example above is a custom predicate, not the way to enforce a floor.

## Comp

Cascade: stated salary → Levels.fyi → visa wages → "unknown" (still shown). `comp_floor` cuts only what's known to be below it.

## State

`.agents/search/` holds configuration, `seen.db`, `visa-wages/`, the shared
shortlist format, and `lib/search_shared/` (`Posting` and `Ledger`). The pipeline
package adds this shared library to the Python import path. Neither search skill
depends on the other skill's code or instructions.
