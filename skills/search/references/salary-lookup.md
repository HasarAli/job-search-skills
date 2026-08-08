# Comp lookup — DOL LCA floor, Levels.fyi total comp

Two sources for a shortlisted row that posted no salary. DOL is the deterministic first source and the **floor**; Levels.fyi is the preferred figure when it exists, sitting above that floor.

DOL data is the base salary employers commit to on H-1B/E-3 Labor Condition Applications, published quarterly by the DOL Office of Foreign Labor Certification. Present it as a conservative lower bound: it excludes equity and bonus, and skews to visa-sponsoring employers.

## DOL scripts

`<skill-dir>/scripts/us/` — deterministic, no LLM, no network at query time. `<skill-dir>` is the directory holding this skill's `SKILL.md`; the scripts ship with the skill and are never copied into the user's repo. The generated index lives in the cache: path from the `SALARY_DB` env var, default `.agents/cache/salary/salary_index.sqlite`, resolved against the CWD, so run every command from the repo root. Cache and DB are gitignored and regenerable.

| Script | Role |
| --- | --- |
| `salary_common.py` | employer normalization, wage annualization, `SALARY_DB` resolution |
| `salary_index.py` | build/refresh the SQLite index from DOL quarterly XLSX |
| `salary_lookup.py` | query base-pay stats for a company (+ optional role) |

### Refresh the index (quarterly)

```
python <skill-dir>/scripts/us/salary_index.py --quarters 4
```

Discovers the newest 4 quarter files from the OFLC performance page, downloads any not cached, and streams each into the SQLite index. Rerun when a new quarter posts (~one quarter behind the current date). Requires `curl_cffi` — DOL sits behind Akamai bot protection and plain urllib/requests get 403.

### Look up a company

```
python <skill-dir>/scripts/us/salary_lookup.py --company "<company>" --role "backend engineer"
python <skill-dir>/scripts/us/salary_lookup.py --company "<company>" --soc 15-1252 --json
```

- `--company` matches a suffix-insensitive normalized key (`Acme, Inc.` == `ACME`), falling back to substring when the exact key misses.
- `--role` is a substring on job title / SOC title; `--soc` is an exact SOC code and the most precise (`15-1252` = Software Developers).
- `--json` emits `{low, median, high, p25, p75, n, pw_level_mix, quarters, confidence, ...}`.
- `confidence`: `low` at n<5 or filings mostly at PW level 1–2 (entry prevailing wage, which understates real pay); `high` at n≥25.

## Levels.fyi total comp — interactive sessions only

Levels gives real total comp (base + stock + bonus by level). Every content page sits behind a Cloudflare JS challenge that only the in-app browser clears, so this runs in an interactive session and never in headless or cron search.

1. Build `https://www.levels.fyi/companies/<company-slug>/salaries/<role-slug>` — slugs lowercase, spaces to hyphens (`software-engineer`). On a 404, drop to `/companies/<company-slug>/salaries`.
2. Navigate there with the browser tools this harness provides (Cloudflare clears itself), then extract the "Average Compensation By Level" table with the harness's JavaScript-evaluation tool:

   ```js
   (()=>{const t=[...document.querySelectorAll('table')].find(t=>{const h=t.innerText.toLowerCase();return h.includes('total')&&h.includes('base')&&h.includes('stock')});
   if(!t)return{err:'no comp table'};
   const rows=[...t.querySelectorAll('tr')].map(r=>[...r.querySelectorAll('td,th')].map(c=>c.innerText.trim().replace(/\s+/g,' ')).filter(Boolean)).filter(r=>r.length);
   const med=(document.body.innerText.match(/median[^.]*?\$[\d.]+[KkMm]/i)||[])[0];
   return{currency:(t.innerText.match(/CA\$|US\$|\$/)||[])[0],median:med,rows};})()
   ```

3. Confirm the currency is USD (`$`, not `CA$`) — the site geolocates and can render CAD. Reload or flip the currency toggle until it reads USD.

Attach the result as `source: levels_fyi_tc` alongside the DOL row.
