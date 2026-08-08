# Platform notes — mechanics per platform

Which fields feed recruiter search, how the job-seeking settings behave, and how edits are saved. **Every claim here is perishable**: platforms redesign UIs, rename settings, and retune search without notice. Re-verify anything load-bearing against the live UI (or one quick web search), and append what you learn.

Scoring lives in [review-rubric.md](review-rubric.md); this file only says which fields the lenses land on.

## LinkedIn (default)

### Fields recruiter search indexes

LinkedIn Recruiter searches structured fields. Weight the review accordingly:

- **Headline** — highest-visibility keyword field, shown in every search result row and beside every comment the user leaves.
- **Current and past job titles** — filterable per experience entry, independent of the headline.
- **Skills** — filterable, and a skill mentioned only in prose misses skill-filtered searches. ~50 slots; top/pinned skills carry display weight, and skills added to an experience entry link the term to its proof.
- **About and experience descriptions** — keyword-indexed free text.
- **Location** — a hard filter in most searches; a vague or wrong location silently drops the profile from results.

### Open to Work

Settings > "Open to work", also reachable from the profile top card:

- **Visibility**: "Recruiters only" (hidden from the current employer's recruiters, best-effort) or "All LinkedIn members" (adds the green #OpenToWork photo frame, and recruiters filter for it).
- Configurable and recruiter-filterable: target job titles, location types (on-site/hybrid/remote), locations, start-date urgency, employment types.

### Featured

A manually curated showcase (posts, articles, links, documents) directly under About. Order is user-controlled and the first items get the visibility.

### Editing mechanics

- Each section has its own pencil affordance opening a modal; each modal saves on its own.
- Headline ~220 chars, About ~2,600 chars — read the modal's live counter rather than trusting these numbers.
- After saving, re-read the section to confirm the change persisted.
- Photo and cover uploads open a file picker, which is one reason images ship as manual tasks.

## Xing (DACH region)

- Structure maps closely: headline, work experience, skills ("Fähigkeiten und Kenntnisse"), and a wants/offers pair ("Ich suche" / "Ich biete") that recruiters filter on — treat those two lists as LinkedIn's skills plus open-to-work targets combined.
- Job-seeking status has its own recruiter-visibility toggle.
- Profile language matters: recruiters search in the local working language, so align the profile with the working language in `goals/search-filters.md`.
- UI labels shift with the account language — navigate by section semantics.

## Other platforms

When `goals/search-filters.md` names a platform not covered above:

1. Crawl by section semantics from [crawl-guide.md](crawl-guide.md) — headline-equivalent, summary, experience, skills, job-seeking settings — and record the platform's own names for them in the snapshot.
2. Spend one web search on "how do recruiters search on <platform>" to learn which fields are filterable; those fields get headline-level attention in the findability lens.
3. Append what the search turned up to this file, as a new section above.
