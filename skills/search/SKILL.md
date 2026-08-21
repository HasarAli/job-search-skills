---
name: search
description: Run the job search into a numbered shortlist — pull fresh postings for the user's role targets from every configured source, dedup against everything already seen, and rank newest-first with a comp figure on every row. Use when the user says "find jobs", "run the search", or wants today's shortlist, and for unattended cron runs that leave the shortlist for later review.
---

# search

The script fetches, dedups, filters, and prices postings; you turn its JSON into the shortlist.

## Run

```bash
python .agents/skills/search/search.py                  # prints JSON to stdout
python .agents/skills/search/search.py --json path.json # hand in agent-collected postings
```

Exit codes: `0` shortlist produced · `1` nothing collected · `2` config error (JSON on stderr).

## Render the shortlist

Read the JSON on stdout, write `shortlists/<YYYY-MM-DD-HHMMSS>.md`:

```markdown
# Shortlist — YYYY-MM-DD
Sources: <which sources ran; name any that failed>. Window: <posted_since_hours or "—">.

## Apply now

1. **<company> — <title>** — <location> — posted <date or "—"> — <comp>
   <url>
   Fit: <one line against role targets and filters>

## Watch

7. **<company> — <title>** — … — Strains <constraint>: <why>

Cut: <filter> — <company (figure)>, …
```

- Number rows continuously, newest first (the script already sorts them).
- Comp: if `stated_comp` carries a range, write `$min–$max (stated)`; else if `comp.floor_value`, write `$<floor_value> (<provenance>)`; else "not listed".
- A row that strains a filter but is otherwise a fit goes in **Watch**, naming the constraint; a row a filter cut goes in the **Cut** line.

## Add a source

Append a block to `.agents/search/config.yaml` → `sources:`. Not listed = not run.

```yaml
  - name: greenhouse            # ATS tenant: company slug
    tenants: [acme, globex]
  - name: ashby
    tenants: [beta]
  - name: workday
    tenants: [gamma.wd5.GammaExternalCareerSite]   # slug.wdN.siteId
  - name: agent-json            # postings collected elsewhere, by path
    path: path/to/collected.json   # rows: source, source_id, title, company, url
```

## Add a filter

Define it in `.agents/search/filters.py`, then name it in `config.yaml`:

```python
def min_comp(posting): return posting.comp is None or (posting.comp.floor_value or 0) >= 200000
```

```yaml
filters: [discipline, us_ca_remote]      # run early (cheap)
post_enrichment_filters: [min_comp]      # run after comp; may read posting.comp
```

## Comp

Cascade: stated salary → Levels.fyi → visa wages → "unknown" (still shown). `comp_floor` cuts only what's known to be below it.

## State

`.agents/search/` holds `config.yaml` and `filters.py` (yours) plus `seen.db` and `visa-wages/` (the pipeline's). Shortlists live in `shortlists/` — the newest file is the latest run.
