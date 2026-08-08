---
name: sources
disable-model-invocation: true
description: >-
  Use only when the user explicitly asks to add, fix, or verify a place the
  system looks — a job board, an ATS company, a remote feed, a regional
  platform, a job-board MCP server, an inbox channel, or the US salary index.
  Owns the plumbing between the system and the outside world: installs the
  search engine, probes career sites, writes adapters, and maintains the
  registries under `.agents/config/`. Running the daily search belongs to
  `search`; deciding what the user is looking for belongs to `goals`.
---

Plumbing only. What the user is looking for is already settled in `goals/`; this decides where to look, and no source is called live until it has returned rows.

**Prerequisites** — `goals/search-filters.md` for region, industry, and dominant platform; a missing one hands off to `goals`.

Run only the steps the request touches. Step 7 closes every run.

## 1. Scope

Read `goals/search-filters.md` for country/region, industry, dominant platform, and the platforms already configured, and `goals/role-preferences.md` for the roles a new source has to cover. The boards a market actually uses come from the country row in `.agents/config/conventions/country-conventions.md`, the industry row in `.agents/config/conventions/industry-conventions.md`, and the regional-board table in [references/boards.md](references/boards.md) for the dominant local board JobSpy misses.

Done when: every region × role in the targets names the board, feed, or ATS that covers it, each marked already-configured or to-add.

## 2. Install the search engine

The search scripts ship with the `search` skill under its `scripts/` directory — read-only engine code, run from the repo root, never copied into the user's repo. Install their pinned dependencies from `scripts/requirements.txt` and run one pass to confirm the environment: [references/jobspy-guide.md](references/jobspy-guide.md).

Done when: one `search_jobs.py` pass prints JSON-lines rows.

## 3. Register a source

Every registry lives in `.agents/config/sources.json`, one top-level key per concern — **seed** it from [references/sources-schema.md](references/sources-schema.md) on a first run, filling each placeholder from `goals/`. Field list and maintenance rules: [references/boards.md](references/boards.md).

| Source | Where it goes |
|---|---|
| Company serving public ATS JSON | a row in `ats` (company, region, ats, slug, extra, status) |
| Fully-remote board feed | a row in `remote_feeds` (kind the adapter handles, feed URL, status) |
| Official job-board MCP server | a row in `mcp`, registered with this harness's MCP client |
| JobSpy site, regional board, or new adapter | target platforms in `goals/search-filters.md`, so the search subagent runs it |

Profession and region scope are data, not code: token lists in `filters.discipline`, state/province/city allowlists and remote rules in `filters.geo`. Both adapters read them, so swapping the two token sets retargets profession or region with no code edit.

Done when: every new row carries its kind, address, and status, and the two filter sets cover the profession and region just scoped.

## 4. Probe a career site, write an adapter

Identify the ATS behind an unknown site, then register it under step 3 where a shipped adapter already handles that kind. Where none does, write a new adapter to `.agents/scripts/adapter_<board>.py` in the user's repo — the shipped `adapter_ats.py` and `adapter_remote.py` are read-only and a skill update overwrites them. Endpoint per ATS, detection regexes, the open-source-library and browser-network-trace probes, and the adapter contract: [references/boards.md](references/boards.md).

Done when: the endpoint returns a non-empty jobs array and the adapter emits its rows in the JobSpy field shape — `site`, `title`, `company`, `location`, `date_posted`, `min_amount`, `max_amount`, `currency`, `job_url`.

## 5. Onboard an inbox channel

One `##` section per channel in `.agents/config/channels.md` is the channel list `inbox` sweeps; the file is **seeded** from [references/channels-schema.md](references/channels-schema.md), which is also the section's heading contract. Procedure: [references/boards.md](references/boards.md#onboarding-an-inbox-channel).

Done when: the channel's section states its entry URL, how to open a thread, how to extract a body, and what to skip — each step confirmed in the user's own browser.

## 6. Salary index (US)

`python <search-skill-dir>/scripts/us/salary_index.py --quarters 4` builds the DOL LCA index from the newest quarterly files; requires `curl_cffi`. The DB path comes from `SALARY_DB`, default `.agents/cache/salary/salary_index.sqlite`, resolved against the CWD — run from the repo root. Refresh quarterly, roughly one quarter behind the current date.

Done when: `salary_lookup.py` returns base-pay stats for a company known to sponsor.

## 7. Verify and report

Run every source touched this session end to end — the JobSpy pass, the adapter against `.agents/config/sources.json`, the MCP call, the channel section's three steps — and mark a registry row `live` only once it returns rows. A row that answers nothing stays `probe` or `custom`.

Done when: each configured source has returned rows, and the closing report names what is live, what is still `probe`, and which registries changed.
