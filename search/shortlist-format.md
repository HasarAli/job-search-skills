# Shared shortlist format

Both `script-search` and `browser-search-linkedin` write
`search/shortlists/YYYY-MM-DD-HHMMSS.md`, using run start time in
America/Toronto. Never overwrite: append `-01`, `-02`, etc. on collision.
One file per run, including empty/partial runs; never append to an older run.

```markdown
# Shortlist — YYYY-MM-DD HH:MM:SS America/Toronto

Sources: <sources and failures>. Window: <actual filter or hours>.
Coverage: <query/pages or pipeline scope>; <complete or partial with reason>.

## Apply now

1. **<company> — <title>** — <location> — posted <date or —> — <comp>
   <url>
   Fit: <evidence against targets and filters; uncertainties stated>

## Watch

2. **<company> — <title>** — <location> — posted <date or —> — <comp>
   <url>
   Fit: <fit evidence>. Strains <constraint>: <why>.

Cut: <reason — count and companies/evidence; no-salary exclusions when applicable>.
Skipped: <duplicate count>. Incomplete: <count and reasons, or none>.
```

Number continuously across sections. Sort newest first within each section,
unknown dates last; distinguish repost dates where shown. Omit empty sections
or state none. Include benefits and company/technology evidence where observed.
Do not invent missing metadata. The collecting skill determines salary admission
and compensation provenance; both use this same layout and filename convention.

Select latest by filename timestamp then numeric collision suffix, not mtime.
Explicit conversation selection wins. A date matching multiple files needs a
full filename/timestamp before applying by row number.

For migrating legacy files, prefer recorded timestamp and timezone; otherwise
use filesystem creation metadata in America/Toronto and note that provenance
in the file. Do not infer a timezone from an ambiguous old filename or invent a
run start time. Preserve job content and numbering during a filename migration.
