# Boards Beyond JobSpy — per-region sources and adapters

JobSpy covers LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, Naukri, and BDJobs (verify against the installed version's README). Many markets have a dominant local board it does not reach. Pick from this table using `search-config.md`'s country/region.

**Coverage and availability claims below are changeable** — boards add/remove APIs, JobSpy adds sites, MCP endpoints appear and disappear. Verify before relying on a row; update the row when it drifts.

## Regional boards

| Region | Board | Access route | Notes |
|---|---|---|---|
| AU / NZ | Seek | scrape or unofficial API | Dominant board for AU/NZ |
| DE / AT / CH | StepStone | scrape | Also Xing Jobs for DACH |
| DE | Arbeitsagentur Jobsuche | official public API | Government board, free API |
| UK | Reed | official API (free key) | Also CV-Library, Totaljobs |
| IN | Naukri | JobSpy covers it | Verify in installed version |
| Gulf / MENA | Bayt | JobSpy covers it | GulfTalent as secondary |
| BR | Catho | scrape | Also Vagas.com, LinkedIn strong in BR |
| LATAM | Computrabajo | scrape | Country-specific subdomains |
| FR | Welcome to the Jungle, APEC | scrape / partial API | WTTJ strong for tech/startups |
| NL | Indeed NL, Nationale Vacaturebank | JobSpy (`country_indeed`) / scrape | |
| JP | Rikunabi, Doda, Japan Dev | scrape | Japan Dev has clean listings for English-speaking tech |
| SE / Nordics | Arbetsförmedlingen Platsbanken | official public API | Government board, free API |
| SG / SEA | JobStreet, MyCareersFuture (SG) | scrape / official API (MCF) | JobStreet = Seek-owned |
| ZA | Careers24, PNet | scrape | |
| Remote-only (global) | Himalayas, We Work Remotely, Remote OK, RemoteRocketship | scrape / RSS (WWR, Remote OK) | Good supplement when filters say fully-remote |
| Tech (global) | Hacker News "Who is hiring" (monthly), company ATS boards (Greenhouse/Lever/Ashby public JSON APIs) | HN Algolia API / ATS JSON | ATS APIs are stable and comp-transparent where required by law |

## Official MCP endpoints (no login, no scrape risk)

Some boards run official MCP servers usable directly from the harness — prefer these over scraping when available:

| Board | Endpoint | Auth |
|---|---|---|
| Dice | `https://mcp.dice.com/mcp` | none |
| ZipRecruiter | `https://api.ziprecruiter.com/mcp` | none stated |

Add via `claude mcp add --transport http <name> <endpoint>`. Third-party scraper MCPs (Apify-hosted etc.) carry the same ToS risk as scraping while logged in — avoid unless the user explicitly accepts the risk. Re-check periodically; more boards keep shipping official servers.

## Adding a board adapter

An adapter is one small script in the data repo's `search/` that makes a board's results look exactly like a JobSpy pass:

1. Create `search/adapter_<board>.py` accepting the same CLI contract as the JobSpy template: `--search-term`, `--location`, `--hours-old`, `--results`, `--out`.
2. Fetch via the board's official API if one exists (Reed, Arbeitsagentur, Platsbanken, MCF, ATS JSON); otherwise scrape the public search page politely (respect robots.txt, no login, low volume).
3. Emit JSON lines with the same fields JobSpy produces: `site`, `title`, `company`, `location`, `date_posted` (ISO or null), `min_amount`, `max_amount`, `currency`, `job_url`.
4. List the adapter in `search-config.md` under target platforms; the search subagent runs it alongside the JobSpy passes and the orchestrator merges, dedups, and filters identically.

Same failure rule as JobSpy passes: an adapter that errors is noted in the shortlist header and skipped, never fatal to the run.
