# sources.json — schema and seed

> A **seed**: copied once into `.agents/config/sources.json`, which is where every later
> registry edit lives. A skill update overwrites this file.

Every value below written as `<...>` is a placeholder this skill fills from the user's
profession, region, and market — nothing here presumes a field of work. Key-by-key
maintenance rules and the endpoint tables: [boards.md](boards.md).

## Seed

```json
{
  "_comment": "Registries and scope filters for the board adapters. Maintained by the `sources` skill; read by the `search` skill's scripts/adapter_ats.py and adapter_remote.py via --config. Only rows with status 'live' are fetched. How to maintain each registry: the `sources` skill's references/boards.md.",

  "filters": {
    "discipline": {
      "_comment": "Profession scope for the board adapters. Keep a role if its dept/title contains an 'include' token and no 'exclude' token. Empty 'include' => keep every role. Swap these lists to target a different profession; the adapter scripts read this file and are otherwise profession-agnostic. Coarse by design — exact role + seniority stay at the role-targeting layer (goals/role-preferences.md + per-role search-term).",
      "include": ["<profession token>", "<profession token>", "<job-family token>"],
      "exclude": ["<adjacent field that shares the vocabulary>", "<wrong job family>"]
    },

    "geo": {
      "_comment": "Region scope for the board adapters. ATS adapter (is_us_ca) keeps US/CA worksites via country_hints, us/ca cities, us_states/ca_provinces (UPPERCASE 2-letter), and a remote allowance minus remote_exclude_hint. Remote adapter (remote_geo_ok) keeps a role unless it's pinned outside North America: na_hint => keep, non_na => drop. Edit these lists to change target regions.",
      "country_hints": ["<target country>", "<alternate spelling>"],
      "us_states": ["<UPPERCASE 2-letter state codes, if the US is in scope>"],
      "ca_provinces": ["<UPPERCASE 2-letter province codes, if Canada is in scope>"],
      "us_cities": ["<city>", "<city>", "remote - us", "remote (us)"],
      "ca_cities": ["<city>", "<city>"],
      "remote_exclude_hint": ["<region a remote role may be pinned to and must be dropped>"],
      "na_hint": ["<phrase a listing uses for the target region>", "<region> only", "<region>-based"],
      "non_na": ["<country outside the target region>", "<region outside the target region>"]
    }
  },

  "ats": [
    {"company": "<Company>", "region": "<region>", "ats": "greenhouse", "slug": "<board slug>", "extra": null, "status": "probe"},
    {"company": "<Company>", "region": "<region>", "ats": "workday", "slug": "<tenant slug>", "extra": "<wdN> / <SitePath>", "status": "probe"},
    {"company": "<Company>", "region": "<region>", "ats": "custom", "slug": null, "extra": null, "status": "probe",
     "note": "<why this row is not live yet, or what a custom site needs>"}
  ],

  "remote_feeds": [
    {"source": "Himalayas", "kind": "himalayas", "url": "https://himalayas.app/jobs/api/search", "status": "probe",
     "note": "Carries structured salary (minSalary/maxSalary/currency) and locationRestrictions[] — richest source; prefer it."},
    {"source": "Remote OK", "kind": "remoteok", "url": "https://remoteok.com/remote-<category>-jobs.rss", "status": "probe",
     "note": "RSS, capped at ~100 latest and category-scoped — add sibling feeds for more coverage."},
    {"source": "We Work Remotely", "kind": "wwr", "url": "https://weworkremotely.com/categories/remote-<category>-jobs.rss", "status": "probe",
     "note": "RSS, capped at ~25 latest and category-scoped — add sibling feeds for more coverage."}
  ],

  "mcp": [
    {"board": "Dice", "endpoint": "https://mcp.dice.com/mcp", "auth": "none", "official": true,
     "transport": "http", "note": null},
    {"board": "ZipRecruiter", "endpoint": "https://api.ziprecruiter.com/mcp", "auth": "none mentioned", "official": true,
     "transport": "http", "note": null},
    {"board": "Indeed", "endpoint": null, "auth": "OAuth sign-in with an Indeed account, beta", "official": true, "transport": null,
     "note": "Graphical connector UI in some harnesses only — no plain endpoint, not addable from a terminal session."},
    {"board": "Glassdoor", "endpoint": null, "auth": null, "official": false, "transport": null, "note": "Third-party scraper MCPs only."},
    {"board": "Monster", "endpoint": null, "auth": null, "official": false, "transport": null, "note": "Third-party scraper MCPs only."},
    {"board": "CareerBuilder", "endpoint": null, "auth": null, "official": false, "transport": null, "note": "Third-party scraper MCPs only."},
    {"board": "Wellfound/AngelList", "endpoint": null, "auth": null, "official": false, "transport": null, "note": "Third-party scraper MCPs only."},
    {"board": "Naukri", "endpoint": null, "auth": null, "official": false, "transport": null, "note": "Third-party scraper MCPs only."}
  ]
}
```

## Filling it

`filters.discipline` decides what the adapters call a job in the user's field. Take the
`include` tokens from the job families in `goals/role-preferences.md` — the words that
appear in the *title or department* of a posting the user would take, not the exact role.
Take `exclude` from adjacent fields that borrow the same vocabulary and would otherwise
flood the shortlist; a token only earns its place after a pass shows it cutting real
noise. An empty `include` keeps every role, which is the right start for a field whose
titles have no shared stem.

`filters.geo` is written from the regions in `goals/search-filters.md`. The two adapters
read it differently: the ATS adapter allows a worksite it recognizes, and the remote-feed
adapter allows anything not pinned to an excluded region — so a market absent from both
lists is kept by one adapter and dropped by the other.

Every seeded row lands at `"status": "probe"`. A row becomes `live` only in step 7, after
it has returned rows.
