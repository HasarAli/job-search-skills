# Browser search LinkedIn

Read `candidate/profile.md`, `candidate/role-preferences.md`, and
`candidate/search-filters.md` for fit. Read the shared
[shortlist format](../shared/shortlist-format.md) for naming and layout. Do not run
a `search.py` search, guest APIs, direct HTTP requests, or external salary
lookups. The `search.py` company commands in [Company check](#company-check)
are the one exception.

## Scope and browser boundary

Use only the LinkedIn search-results tab through the available browser tools.
If none is available, ask the user to open one. Do not open job, company, apply,
or external links, including in another tab, outside the
[Company check](#company-check) steps, which may open an apply link and a
company's People page in a new tab. Read only rendered accessibility or DOM
state, not hidden application state or network responses.

Honor the requested page range; if unspecified, inspect only the current page
and state that scope. Scrolling the results list and using its pagination within
that range are allowed. Stop at the requested end, exhausted results, login,
CAPTCHA, rate-limit notice, or inaccessible details; report partial coverage
without bypassing the restriction or repeatedly reloading.

Signed-out pages count as login: if the page shows "Sign in to create job alert"
or the guest header, stop and ask the user to sign in. The guest page silently
drops the remote, experience, and salary filters, so its results are not usable.

Get the current America/Toronto time with Python `zoneinfo` or PowerShell
`Get-Date`, not `TZ=... date` in Git Bash, which silently prints UTC.

## Search URL

Use the newest shortlist that actually covered LinkedIn and a comparable query
to choose the window. LinkedIn accepts a custom `f_TPR=r<seconds>`: use the
elapsed time since that run plus about 5h overlap rather than jumping to Past
week. With no comparable run, use the configured `posted_since_hours` in
`.agents/search/config.yaml`. Do not override an explicit user window. Record the
actual filter, query, page range, and any incomplete prior coverage; a shortlist
timestamp is not proof that all older results were seen.

Add the URL filters the candidate's search filters support: `f_JT=F` for
full-time only. US geo has a salary filter, `f_SB2` (`6` = $140k+); pick the
bucket at or below the user's floor. It also removes no-salary postings. Canada
geo has no salary filter.

Use plain keywords from `candidate/role-preferences.md`. Closely related titles
("frontend engineer", "full stack engineer") return largely the same page, while
the generic seniority title ("senior software engineer") returns a different
one: run the generic title first and treat the specialized ones as an optional
second pass, deduped by the ledger. Boolean keywords match loosely (description
text too), and `NOT` does not keep unwanted titles out.

## Collect cards, then inspect details sequentially

1. Collect all currently rendered cards in one compact DOM/accessibility read:
   job ID from an observed URL or card attribute, title, company, location,
   posted date, benefits, visible salary, and LinkedIn's **Viewed** label.
   Use “not shown” for absent fields, not an inference.
   Keep this page inventory in memory. When scrolling reveals more cards in a
   virtualized list, collect only newly rendered IDs; one read does not prove
   the whole page was covered. Rebuild the inventory after pagination/filter changes.
   Cards carrying **Viewed** are already reviewed by the user: skip them without
   opening, do not count them as inspected or cut, and note the skipped count in
   the Skipped line. With `company_check` on, every card whose location names
   the home country is company evidence, Viewed or not (see
   [Company check](#company-check)).
2. Triage each unviewed card on its own text, before the ledger check or pane.
   Do not open a card that shows a clear miss against the candidate's files:
   - Off-target title: a discipline, level, or track that
     `candidate/role-preferences.md` excludes or does not target.
   - Low pay: hourly when the user wants salaried, or an explicitly labelled
     range topping below the floor in `candidate/search-filters.md` for its
     currency and arrangement. `$`-only or unlabelled ranges go through the
     pane; do not assume a currency.
   - Staffing or recruiting agency poster.
   - An arrangement or location the search filters exclude (for example,
     hybrid outside the user's commuting area).
   Record these as `filtered:card_triage`, with reason starting "Card only:"
   and the card text that triggered it (no ID: report unidentified). Count
   them separately in the Cut line. Never triage on a guess; a borderline card
   goes through the pane.
3. Before opening any details, batch-check the remaining identities against
   `.agents/search/seen.db`: `source = linkedin`,
   `source_id = urn:li:jobPosting:<id>`. Use the shared ledger procedure below
   and dedup within this run too. Queue only unseen/expired records or justified
   early refreshes. If no stable ID is available, do not fabricate one;
   report the card as uninspected/unidentified and omit it from the shortlist.
4. Click the card's non-link selection area to load the in-page details pane.
   Never click the title anchor as a substitute. Wait for the rendered pane's
   job ID to match the queued card and its content to finish loading before
   extracting text; an updated URL alone is not proof the pane is ready.
   If the pane exposes no ID, verify its title and company instead; ambiguous
   identity is incomplete inspection. Expand inline sections without navigation.
   If no safe selection target exists, report the coverage gap.
5. Read **About the job** for salary, responsibilities, technologies, eligibility,
   and freshness. Read **About the company** for employee count, industry, and
   description. Employee count is not engineering-team size. The pane may have
   salary even when the card has none. Missing or failed details are not proof
   of no salary: report incomplete inspection, not `filtered:no_salary`.
6. Include only roles with explicit numeric salary/pay information on the card
   or pane and acceptable fit. Preserve salary verbatim, including currency,
   pay period, multiple geographic bands, and apparent formatting errors.
   “Competitive salary,” benefits, and third-party estimates do not qualify.
   Do not repair figures, assume a currency for `$`, or equate total comp with
   base. Explain ambiguity separately in fit notes.
7. Reject explicit US-only residence/work eligibility requirements; “remote”
   alone does not establish Canadian eligibility. Unclear eligibility belongs
   in Watch with the uncertainty named, provided salary is explicit. Apply the
   candidate's other hard constraints; salary alone does not make a fit.
   With `company_check` on, run the [Company check](#company-check) on each
   included row located outside the home country, and place it by the label.

Pause roughly 0.5–1 second between card clicks. Inspect sequentially, with no
parallel scraping or delegated browser workers, and no unnecessary reloads.
Prefer compact reads scoped to the active pane's required sections over repeated
full accessibility snapshots. Do not truncate salary bands or eligibility text.
Keep browser calls short enough to finish within tool timeouts; after a timeout,
check the current card/pane and completed results before resuming, rather than
replaying a whole batch. A pane that remains unavailable ends partial coverage
under the stopping rule above.

## Company check

Only when `.agents/search/config.yaml` has a `company_check:` block. Read it
for `home`, `home_terms`, `linkedin_geo_id`, and `people_check_cap`. Labels and
the evidence behind them are in the search skill's Company check section. Run
each command from the project root as
`python .agents/skills/search/search.py <command>`; each prints the company's
JSON, including its `label` and whether a check is `due`.

For each included row located outside the home country:

1. Look up the company with `--company "<company>"`. If it is `confirmed`, or
   not `due`, use its label and skip to step 4.
2. Apply link. If the pane's apply control is "Apply on company website" (not
   Easy Apply), read its link without clicking it. LinkedIn wraps the
   company's address as `/safety/go/?url=<address>`, so decode the `url`
   parameter, for example
   `new URL(new URL(a.href).searchParams.get("url"))`. Only if that fails,
   open the link in a new tab, read the address it lands on, and close the tab
   without filling in anything; if LinkedIn then asks whether you applied,
   dismiss the question unanswered. Run
   `--check-company "<company>" --title "<title>" --url "<that address>"
   --company-url "https://www.linkedin.com/company/<handle>"`, taking
   `<handle>` from the pane's company link. For Easy Apply, run it without
   `--url`: the script guesses the company's job board and accepts a guess
   only when it lists the same title. Either way, if the board doesn't confirm
   the company, the script also searches LinkedIn for its jobs in the home
   country.
3. People tab. If the label is still `unknown` and fewer than
   `people_check_cap` People pages have been opened this run, open
   `https://www.linkedin.com/company/<handle>/people/?facetGeoRegion=<linkedin_geo_id>`
   in a new tab. With the filter applied, "Where they live" shows the home
   country and the page reads "<N> associated members"; read N and the largest
   country's count beside it, then close the tab. Record N above zero with
   `--record-evidence "<company>" --kind people --detail "<N> employees in
   <home> on LinkedIn (<M> in <largest country>)" --url "<that address>"`, and
   zero with `--mark-checked "<company>"`. A handful against hundreds elsewhere
   is weak; the detail keeps both numbers so the shortlist shows that. Stop
   opening People pages at the cap, or at any login, CAPTCHA, or rate-limit
   notice.
4. Place the row. `confirmed` goes in Apply now when it otherwise fits.
   `likely` and `unknown` go in Watch, with the label named as the strain.
   `no` is cut as `filtered:company_check`, with the evidence in the reason.
   A posting whose own text limits it to another country is
   `filtered:eligibility` as before; also record that sentence with
   `--record-evidence "<company>" --kind away_only --detail "<sentence>"`.

Rows located in the home country need no check: their location is the
evidence. Record every card whose location names the home country (including
triage cuts and Viewed cards) as soon as the page inventory is collected,
before any lookup, so a company's home-located card settles its other cards:
`Ledger.record_evidence_many([(company, "home_role", "<title> — <location>",
canonical_url, None), ...])`.

## Shared ledger

Read [ledger.py](../shared/lib/search_shared/ledger.py) before operating on the
database. Add `.agents/skills/search/shared/lib` to the Python import path and import
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
- `filtered:card_triage`: excluded from card text alone, never opened;
  reason starts "Card only:".
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
fit notes, benefits, and relevant company/technology evidence, plus its
company-check line when the check is on. Unknown facts stay unknown. The Cut line summarizes no-salary exclusions and other reasons
with counts, card-triage cuts counted on their own; separately report Viewed
skips, duplicate skips, and incomplete/unidentified cards. State pages actually covered and whether the run completed. Return the
file link and counts; applying is a separate user selection handled by `apply`.
