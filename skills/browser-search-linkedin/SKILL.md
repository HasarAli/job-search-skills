---
name: browser-search-linkedin
description: Inspect LinkedIn job search results in the signed-in browser and produce a timestamped, salary-only shortlist using the shared seen ledger. Use for "search LinkedIn", "scrape LinkedIn jobs", or "/browser-search-linkedin". Does not apply to jobs or edit the user's profile.
---

# Browser search LinkedIn

Read `candidate/profile.md`, `candidate/role-preferences.md`, and
`candidate/search-filters.md` for fit. Read the shared
[shortlist format](../../search/shortlist-format.md) for naming and layout. Do not run
`search.py`, guest APIs, direct HTTP requests, or external salary lookups.

## Scope and browser boundary

Use only the LinkedIn search-results tab through the available browser tools.
If none is available, ask the user to open one. Do not open job, company, apply,
or external links, including in another tab. Read only rendered accessibility
or DOM state, not hidden application state or network responses.

Honor the requested page range; if unspecified, inspect only the current page
and state that scope. Scrolling the results list and using its pagination within
that range are allowed. Stop at the requested end, exhausted results, login,
CAPTCHA, rate-limit notice, or inaccessible details; report partial coverage
without bypassing the restriction or repeatedly reloading.

Use the newest shortlist that actually covered LinkedIn and a comparable query
to choose a Date posted filter. Prefer the smallest available window covering
the elapsed interval, with overlap for coarse dates; otherwise use the configured
`posted_since_hours` in `.agents/search/config.yaml`. Do not override an explicit
user window. Record the actual filter, query, page range, and any incomplete
prior coverage; a shortlist timestamp is not proof that all older results were seen.

## Collect cards, then inspect details sequentially

1. Collect all currently rendered cards in one compact DOM/accessibility read:
   job ID from an observed URL or card attribute, title, company, location,
   posted date, benefits, and visible salary. Use “not shown” for absent fields.
   Keep this page inventory in memory. When scrolling reveals more cards in a
   virtualized list, collect only newly rendered IDs; one read does not prove
   the whole page was covered. Rebuild the inventory after pagination/filter changes.
2. Before opening any details, batch-check the collected identities against
   `.agents/search/seen.db`: `source = linkedin`,
   `source_id = urn:li:jobPosting:<id>`. Use the shared ledger procedure below
   and dedup within this run too. Queue only unseen/expired records or justified
   early refreshes. If no stable ID is available, do not fabricate one;
   report the card as uninspected/unidentified and omit it from the shortlist.
3. Click the card's non-link selection area to load the in-page details pane.
   Never click the title anchor as a substitute. Wait for the rendered pane's
   job ID to match the queued card and its content to finish loading before
   extracting text; an updated URL alone is not proof the pane is ready.
   If the pane exposes no ID, verify its title and company instead; ambiguous
   identity is incomplete inspection. Expand inline sections without navigation.
   If no safe selection target exists, report the coverage gap.
4. Read **About the job** for salary, responsibilities, technologies, eligibility,
   and freshness. Read **About the company** for employee count, industry, and
   description. Employee count is not engineering-team size. The pane may have
   salary even when the card has none. Missing or failed details are not proof
   of no salary: report incomplete inspection, not `filtered:no_salary`.
5. Include only roles with explicit numeric salary/pay information on the card
   or pane and acceptable fit. Preserve salary verbatim, including currency,
   pay period, multiple geographic bands, and apparent formatting errors.
   “Competitive salary,” benefits, and third-party estimates do not qualify.
   Do not repair figures, assume a currency for `$`, or equate total comp with
   base. Explain ambiguity separately in fit notes.
6. Reject explicit US-only residence/work eligibility requirements; “remote”
   alone does not establish Canadian eligibility. Unclear eligibility belongs
   in Watch with the uncertainty named, provided salary is explicit. Apply the
   candidate's other hard constraints; salary alone does not make a fit.

Pause roughly 0.5–1 second between card clicks. Inspect sequentially, with no
parallel scraping or delegated browser workers, and no unnecessary reloads.
Prefer compact reads scoped to the active pane's required sections over repeated
full accessibility snapshots. Do not truncate salary bands or eligibility text.
Keep browser calls short enough to finish within tool timeouts; after a timeout,
check the current card/pane and completed results before resuming, rather than
replaying a whole batch. A pane that remains unavailable ends partial coverage
under the stopping rule above.

## Shared ledger

Read [ledger.py](../../search/lib/search_shared/ledger.py) before operating on the
database. Add `.agents/search/lib` to the Python import path and import
`Ledger` from `search_shared.ledger` and `Posting` from `search_shared.model`.
Use `Ledger.unseen_identities(set_of_source_id_pairs)` for each collected batch;
it checks identities in one connection and prunes expired records.
`Ledger.is_seen(source, source_id)` is the single-record equivalent. Inspect
existing outcomes/reasons only for potential early refreshes, preserving the
terminal-record rules below. `record` and `record_sightings` are
**insert-if-absent**, not updates.

- `applied` and `dismissed` are terminal: skip, never automatically refresh or
  replace. Check `search/applications/index.csv` too so an application not yet
  reflected in the ledger is not recommended again.
- `shortlisted` and `filtered:*` normally expire after 60 days. Skip active
  duplicates; re-inspect expired records. An early refresh of a filtered record
  is appropriate only on explicit user request or visible evidence that its
  exclusion changed (for example, a no-salary card now shows salary).
- For an early refresh, inspect the exact existing sighting first. Update only
  that `(source, source_id)` with a parameterized, transactional SQL update,
  guarded by its previous outcome and expiry; preserve `first_seen`, replace
  observed context/reason, and set a new 60-day expiry. Never delete the database
  or overwrite terminal outcomes. Verify the updated row; calling `record`
  again would silently leave the old result unchanged.

Record every inspected posting with observed company/title, canonical
`https://www.linkedin.com/jobs/view/<id>/` (constructed, not opened), and an
evidence-based reason:

- `shortlisted`: explicit salary and fit; both Apply now and Watch qualify.
- `filtered:no_salary`: neither card nor successfully read details has salary.
- `filtered:eligibility` or `filtered:<constraint>`: a hard exclusion, even
  when salary is present. Include all material exclusions in the reason.
- `incomplete`: attempted inspection could not finish; use an immediate expiry
  so it can be retried, and explain the missing evidence.

Put exact salary text and decision evidence in `reason` where relevant. Save
the shortlist before recording its included rows as `shortlisted`, so a failed
file write cannot suppress roles never delivered. Persist exclusions as work
progresses. Verify the recorded identities/outcomes and report any write failure.

## Deliver

Use the shared shortlist format for every run, including empty or interrupted runs.

Every included row has verbatim salary, location, posted date, canonical URL,
fit notes, benefits, and relevant company/technology evidence. Unknown facts
stay unknown. The Cut line summarizes no-salary exclusions and other reasons
with counts; separately report duplicate skips and incomplete/unidentified
cards. State pages actually covered and whether the run completed. Return the
file link and counts; applying is a separate user selection handled by `apply`.
