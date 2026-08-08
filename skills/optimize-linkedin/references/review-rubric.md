# Review rubric — the three lenses on a profile snapshot

Every section of the snapshot report is scored against this file. The snapshot is the source for what the profile says today; the live profile is read again only to confirm a save.

- [The standard](#the-standard) — what a shippable section looks like
- [The three lenses](#the-three-lenses) — findability, conversion, consistency, with score anchors
- [Section coverage](#section-coverage) — what each section is scored for
- [Scoring and rewriting](#scoring-and-rewriting) — how the pass is reported

## The standard

> **A forward-looking landing page for one target role, written in the user's own voice.**

A resume lists what happened; a profile sells what comes next. It is aimed at one reader — the recruiter searching for the target role in `goals/role-preferences.md` — and every section decision follows from what that reader should think and do.

Voice:

- First person, active, specific: "I rebuilt checkout for 2M daily users".
- Name the work plainly — "I owned the migration" where "helped with", "just did some", "was lucky to" say nothing.
- Short paragraphs and white space; a wall of text loses the reader before the pitch lands.
- Numbers as proof, each one traceable to `career/profile.md` or `career/career-diary.md`.

Headline:

- ✗ "Senior Software Engineer at Acme" (the platform default — a search result row with no keywords and no hook)
- ✗ "Results-oriented professional passionate about excellence" (third-person resume-speak, zero searchable terms)
- ✓ "Senior Frontend Engineer | React, TypeScript, design systems | scaled checkout to 2M users/day"

## The three lenses

Score every section 1–5 on each lens. Each lens anchors 1, 3, and 5; a section sitting between two anchors takes the 2 or 4 between them.

### Findability — the queries a recruiter types

Write the searches a recruiter hiring for the target role would actually run (target titles from `goals/role-preferences.md`, location and work type from `goals/search-filters.md`), then judge the profile against them. Recruiter filters are literal: they match the exact terms typed, and a synonym the user "obviously" has does not count. Which fields feed the index on this platform: [platform-notes.md](platform-notes.md).

- **5** — the target title and its 3–5 top keywords appear verbatim in the indexed fields (headline, each experience title line, the skills list), the skills list is filled toward the platform cap with searchable skills, and location plus work-type fields match the filters.
- **3** — the keywords live only in prose (About, experience descriptions) while the filterable fields carry a synonym or the official title alone.
- **1** — default `Title at Company` headline, an empty or off-target skills list, or a vague location that drops the profile out of filtered searches.

Placement beats repetition: the same term crammed through every field reads as desperate to the human who clicks in. A title field takes more than the official title — `Official Title | Keyword-Rich Descriptor` uses the space recruiters search.

### Conversion — the first screenful

The recruiter who clicks in gives it seconds, and screens out rather than in.

- **5** — name, headline, and the first two About lines answer what they do, at what level, and why care — with one number — before the "see more" truncation, and Featured shows proof (project, portfolio link, writing) rather than sitting empty.
- **3** — the answer is there but arrives below the fold, or the claims arrive with no number behind them.
- **1** — opens on duty language or a slogan, About is empty or a wall of resume-speak, nothing featured.

Truncation check: cut the About after line two — a 5 still lands the pitch.

### Consistency — the screen-out scan

A discrepancy between profile and resume is a screen-out, and an unbacked claim gets flagged, not polished.

`career/profile.md` is the anchor; the shipped resume matching the target role and region in `goals/role-preferences.md` is the secondary check.

- **5** — every title, employer, date, and metric matches `career/profile.md` and nothing contradicts that resume; each claim traces to a recorded line.
- **3** — cosmetic drift: a role worded differently across profile and resume, a metric rounded one way here and another there.
- **1** — a title, date, or number that contradicts `career/profile.md`, or a claim with no backing anywhere in `career/`.

## Section coverage

Every row gets scored. Dominant lens is where that section usually wins or loses, not the only one that applies.

| Section | Scored for | Dominant lens |
|---|---|---|
| Headline | Target keywords + value + hook, full character budget used | Findability |
| About | Hook in the first two lines, then story → proof with numbers → what they're looking for → contact | Conversion |
| Experience entries | Title field keywords, one scope-setting line per role, accomplishment statements with numbers, attached media as proof | Findability |
| Skills | Filled toward the cap with searchable skills, top/pinned skills matching the target role; a pinned skill with thin endorsements becomes an outreach task, seeded by endorsing others first | Findability |
| Featured | Best proof pinned first — an empty Featured is a cheap win | Conversion |
| Recommendations | One recent recommendation per key role, from managers and stakeholders; missing ones become an outreach task with a draft offered | Conversion |
| Photo / banner | Approachable headshot, banner reinforcing the target positioning — advise only, these ship as manual tasks | Conversion |
| URL, contact info, education, certifications | Custom URL, reachable contact details, complete sections; platform completeness feeds search ranking | Findability |
| Settings (open-to-work equivalent) | On or off, visibility scope, target titles, locations, work types, employment types — these are recruiter-side filters, so weight them like the headline | Findability |
| Activity recency | Whether the profile reads as active; a few substantive comments a week in the target field put the headline in front of hiring teams for free | Conversion |

Settings carry a confidentiality trade-off — a public job-seeking signal reaches more recruiters, a recruiters-only one keeps the search quieter while employed. Surface both sides with a recommendation; the choice is the user's.

## Scoring and rewriting

- Report each section as `section — findability/conversion/consistency`, plus one line naming its weakest lens.
- Any lens at 3 or below earns exactly one rewrite, aimed at that lens and leaving the rest of the section alone. One rewrite, not a menu.
- All three lenses at 4 or above: "ships as-is".
- Facts and numbers survive a rewrite unchanged. A rewrite that needs a fact nobody recorded becomes a question for the user.
- Keyword gaps get their own list: the recruiter queries the profile misses today, and the field each missing term belongs in.
- Order the recommendation list by expected effect on recruiter outreach, so the top three are the three that matter.
