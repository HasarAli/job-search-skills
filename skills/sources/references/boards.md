# Boards Beyond JobSpy — sources, adapters, probing

Reached when coverage needs extending: a region JobSpy misses, a company whose reqs never surface on the aggregators, or a new adapter.

- [The registry file](#the-registry-file) — the one config the adapters read, and how to maintain it
- [Adapter contract](#adapter-contract) — how any source is made to look like a JobSpy pass
- [ATS public JSON](#ats-public-json) — the highest-value source; endpoint per ATS
- [Probing an unknown career site](#probing-an-unknown-career-site) — finding the slug or the hidden endpoint
- [Remote-board feeds](#remote-board-feeds)
- [Regional boards](#regional-boards) — dominant local board per market
- [Official MCP endpoints](#official-mcp-endpoints)
- [Onboarding an inbox channel](#onboarding-an-inbox-channel)

Every coverage claim on this page drifts — boards add and remove APIs, JobSpy adds sites, MCP endpoints appear and vanish. Confirm a row before relying on it, and correct the row when it has moved.

## The registry file

`.agents/config/sources.json` holds every registry and both scope filters, one top-level key per concern. Seed the file from [sources-schema.md](sources-schema.md) when it does not exist yet.

| Key | Holds | Row fields |
|---|---|---|
| `filters.discipline` | profession scope | `include` / `exclude` token lists |
| `filters.geo` | region scope | country hints, state/province/city allowlists, remote rules |
| `ats` | ATS target registry | `company`, `region`, `ats`, `slug`, `extra`, `status` |
| `remote_feeds` | remote-board feeds | `source`, `kind`, `url`, `status` |
| `mcp` | job-board MCP servers | `board`, `endpoint`, `auth`, `official`, `install` |

Maintenance rules:

- The `sources` skill produces and updates the file; the adapters only read it.
- Only rows with `"status": "live"` are fetched. `probe` and `custom` rows stay in the file and are skipped until resolved.
- Slugs drift and companies migrate ATS, so re-probe live rows periodically.
- `kind` and `ats` select the per-source parser (field shapes differ), so only add a row whose kind a shipped adapter already handles, or extend the adapter first.
- A caveat that belongs to one row — why it is `probe`, what a feed is missing — goes in that row's `note` field, not in prose here.

## Adapter contract

An adapter makes one board's results look exactly like a JobSpy pass:

1. `.agents/scripts/adapter_<board>.py` in the user's repo, taking `search_jobs.py`'s CLI (`--search-term`, `--location`, `--hours-old`, `--results`, `--out`) plus `--config` (default `.agents/config/sources.json`).
2. Fetch through the board's official API where one exists (ATS JSON, Reed, Arbeitsagentur, Platsbanken, MCF); otherwise fetch the public search page politely — robots.txt respected, no login, low volume.
3. Emit JSON lines with JobSpy's fields: `site`, `title`, `company`, `location`, `date_posted` (ISO or null), `min_amount`, `max_amount`, `currency`, `job_url`.
4. Add the adapter to `goals/search-filters.md` under target platforms, so the search subagent runs it alongside the JobSpy passes.

**Discipline and geo gates are external config, not code.** Both shipped adapters share the `search` skill's `scripts/adapter_common.py` and read the `filters` key of the config:

- `discipline` — `include`/`exclude` token lists gating department (captured per source; Greenhouse needs `?content=true`) plus title. Empty `include` keeps every role, which is where an unfilled config starts.
- `geo` — state, province, and city allowlists for the target regions plus remote rules.

Both gates are coarse on purpose: exact role and seniority stay at the role-targeting layer (`goals/role-preferences.md` plus the per-role search term). Swap the two token sets to retarget profession or region — the adapters are generic engines and need no edits.

## ATS public JSON

Most top tech companies publish their live req list as public JSON from their ATS — stable, comp-transparent where law requires, no login, no browser, no ban risk. The maintained target list is the `ats` array in `.agents/config/sources.json`; the `search` skill's `scripts/adapter_ats.py` reads it, fetches every row marked `live`, normalizes to the JobSpy field shape, and applies the discipline + geo gates.

| ATS | Method | Endpoint | Date field | Notes |
|---|---|---|---|---|
| Greenhouse | GET | `boards-api.greenhouse.io/v1/boards/<slug>/jobs` | `updated_at` (ISO) | full dump, filter client-side; `?content=true` adds department |
| Ashby | GET | `api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true` | `publishedAt` (ISO) | filter client-side; `includeCompensation=true` adds salary; `secondaryLocations[].address.postalAddress.addressCountry` gives clean geo |
| Lever | GET | `api.lever.co/v0/postings/<slug>?mode=json` | `createdAt` (ms epoch) | `?location=`/`team=`/`level=` are exact-match and case-sensitive — filter client-side instead |
| Workday | POST | `<slug>.<wdN>.myworkdayjobs.com/wday/cxs/<slug>/<Site>/jobs` | none — `postedOn` is human text ("Posted Today") | **`searchText` filters server-side** (pass the role query); body `{limit≤20,offset,searchText}`; paginate by offset; `hours-old` cannot trim it |
| Eightfold | GET | `<board-host>/api/apply/v2/jobs?domain=<microsite>&query=&location=&start=&num=50` | `t_create` (epoch) | **`query` and `location` filter server-side**; needs `Referer: <host>/careers`; registry `slug`=microsite (`netflix.com`), `extra`=board host (`explore.jobs.netflix.net`); paginate by `start` until `count` |
| SmartRecruiters | GET | `api.smartrecruiters.com/v1/companies/<slug>/postings?limit=100&offset=N` | — | filter client-side |

Filtering the client-side sources in one place keeps geo, comp floor, and dedup consistent across every source.

## Probing an unknown career site

**Known-ATS probe:** try each GET above with the company name as slug; a `200` carrying a non-empty jobs array means live. Set a row's status to `live` only once the endpoint answers; otherwise mark it `probe` or `custom`. Slugs drift and companies migrate ATS (Netflix left Lever; Vercel moved Ashby → Greenhouse), so re-probe periodically.

**Detection regexes:** `boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, `jobs.ashbyhq.com/<slug>`, `careers.smartrecruiters.com/<slug>`, `<slug>.<wdN>.myworkdayjobs.com/<site>`.

**Custom site, two methods** (both used to add Netflix):

1. **Open-source ATS libraries** — repos like [jobhive-py / ats-scrapers](https://github.com/kalil0321/ats-scrapers) carry endpoint patterns and detection regexes for Eightfold, SmartRecruiters, iCIMS, Workable, Ashby. Read the per-ATS scraper source for the exact URL and params.
2. **Browser network trace** — open the careers page, apply a filter in the UI, and read the XHR it fires: JSON endpoint, exact params, required headers. This is the method that corrected Netflix's path (the UI calls `/api/apply/v2/jobs`, not the library's `/api/pcsx/search`) and revealed the `Referer` requirement. Reach for it whenever a library's pattern 403s or returns empty.

## Remote-board feeds

Fully-remote boards publish public feeds — a good supplement when the filters say fully-remote, and a natural fit for newest-first since all three carry real dates. The maintained feed list is the `remote_feeds` array in `.agents/config/sources.json`; the `search` skill's `scripts/adapter_remote.py` reads it and normalizes to the JobSpy field shape.

Geo works differently here from the ATS registry: these are remote-first boards, so a **Worldwide / Anywhere** role is eligible from anywhere the user sits. The adapter **includes** worldwide plus the `geo.na_hint` regions and **excludes** only roles explicitly restricted to a region on `geo.non_na`.

RSS feeds are capped and category-scoped, so add sibling category/tag feeds (WWR and Remote OK publish several) as new rows for more coverage. HN "Who is hiring" is deliberately not a feed row — it skews early-stage startups; revisit if the targeting shifts.

| Source | Kind | Feed | Structure |
|---|---|---|---|
| Himalayas | himalayas | `himalayas.app/jobs/api/search?q=<kw>&country=<name>&worldwide=true&sort=recent` (JSON) | richest — structured company, `locationRestrictions[]`, salary, `pubDate` (epoch). The **search** endpoint filters server-side by `q`/`country`/`worldwide`; the plain `/jobs/api` browse endpoint ignores them. Adapter unions the target countries with worldwide |
| Remote OK | remoteok | `remoteok.com/remote-<category>-jobs.rss` | structured `company` + `location` + `tags` + ISO `pubDate`; send a browser UA |
| We Work Remotely | wwr | `weworkremotely.com/categories/remote-<category>-jobs.rss` | weak — company is the title prefix (`Company: Role`), `region` mostly "Anywhere", RFC822 `pubDate` |

## Regional boards

Most markets have a dominant local board JobSpy does not reach. Pick by the country/region in `goals/search-filters.md`.

| Region | Board | Access route | Notes |
|---|---|---|---|
| AU / NZ | Seek | scrape or unofficial API | dominant board for AU/NZ |
| DE / AT / CH | StepStone | scrape | also Xing Jobs for DACH |
| DE | Arbeitsagentur Jobsuche | official public API | government board, free API |
| UK | Reed | official API (free key) | also CV-Library, Totaljobs |
| IN | Naukri | JobSpy covers it | confirm in installed version |
| Gulf / MENA | Bayt | JobSpy covers it | GulfTalent as secondary |
| BR | Catho | scrape | also Vagas.com; LinkedIn strong in BR |
| LATAM | Computrabajo | scrape | country-specific subdomains |
| FR | Welcome to the Jungle, APEC | scrape / partial API | WTTJ strong for tech and startups |
| NL | Indeed NL, Nationale Vacaturebank | JobSpy (`country_indeed`) / scrape | |
| JP | Rikunabi, Doda, Japan Dev | scrape | Japan Dev has clean listings for English-speaking tech |
| SE / Nordics | Arbetsförmedlingen Platsbanken | official public API | government board, free API |
| SG / SEA | JobStreet, MyCareersFuture (SG) | scrape / official API (MCF) | JobStreet is Seek-owned |
| ZA | Careers24, PNet | scrape | |
| Tech (global) | Hacker News "Who is hiring" (monthly) | HN Algolia API | early-stage skew |

## Official MCP endpoints

Some boards run official MCP servers callable straight from the harness — the lowest-risk route of all, since there is no scraping and no login. The maintained endpoint list, with transport and auth notes per board, is the `mcp` array in `.agents/config/sources.json`; register a row with whatever MCP client this harness exposes; Dice and ZipRecruiter are addable there today.

- Dice and ZipRecruiter require no login, so there is no personal-account ban risk — add them directly.
- Indeed's beta connector is available only through a graphical connector UI in some harnesses, not as a plain endpoint. It has no config URL, ties usage to the user's real Indeed account over OAuth, and cannot be added from a terminal session — its row therefore carries no transport.
- A board with `"official": false` has only third-party scraper MCPs (Apify-hosted and similar). Those carry the same ToS exposure as scraping while logged in — take one only when the user has explicitly accepted that risk.
- Re-check periodically; more boards ship official MCP servers over time.

Sources: [Indeed MCP docs](https://docs.indeed.com/mcp/), [Dice MCP announcement](https://www.dice.com/career-advice/dice-launches-mcp-server-for-ai-powered-job-search), [Dice MCP setup](https://www.dice.com/career-advice/how-to-connect-the-dice-mcp-server-to-your-ai-assistant), [ZipRecruiter MCP docs](https://api.ziprecruiter.com/mcp/docs)

## Onboarding an inbox channel

1. Get the entry URL from the user and confirm they are signed in there.
2. Explore in their browser: open the message list, open one thread, extract one body.
3. Add a `## <Platform>` section to `.agents/config/channels.md` under the headings in [channels-schema.md](channels-schema.md) — Entry, Open a thread, Extract — plus whatever else that platform needs: reading the list, finding an old thread, what to skip, high-value content, guardrails. Seed the file from that schema when it does not exist yet.
4. Hand the channel to `inbox` for its first triage once the section exists.

Record what surprised you: which element accepts the click and which one silently does nothing, whether text extraction returns the open thread or only the list, whether the body needs a screenshot, how threads collapse, how to filter the list down to recruiter mail.
