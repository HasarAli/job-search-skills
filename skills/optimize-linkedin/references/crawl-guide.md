# Crawl guide — the profile snapshot

How the crawl subagent captures the user's profile and structures the snapshot report.

## Crawl conduct

- **The user's own profile, and nothing else.** Other people's profiles, search results, and company pages are out of scope for this crawl.
- **Navigate like a human**: one page or section at a time, waiting for each to load. If the platform shows friction — an unusual challenge, a warning, a rate message — stop and report it back.
- Work on the user's existing logged-in session. A logged-out session ends the crawl: return and ask the user to log in.
- Prefer the platform's own "view profile" and edit screens over the public view — they show the unabridged text and the settings.

## Sections to capture

Verbatim text wherever text exists, never a paraphrase. An empty or missing section is a finding: record it as missing.

| Section | Capture |
|---|---|
| Identity | Display name, pronouns if shown, location, current title line under the name |
| Headline | Full text, character count |
| About / summary | Full text, expanding any "see more" truncation |
| Experience | Every entry: title, company, employment type, dates, location, full description text, attached media |
| Education | School, degree, field, dates |
| Skills | Full list in displayed order; which are pinned/top; endorsement counts if shown |
| Recommendations | Count received/given; for each received: the recommender's role relationship (e.g. "managed the user directly") and full text |
| Featured / media | What is featured (posts, links, documents), titles, order |
| Certifications / licenses | Name, issuer, date |
| Projects / publications / volunteering | Whatever the platform offers and the profile has |
| Profile photo / cover image | Present or absent, plus a rough description — describe, don't download |
| URL | Custom/vanity profile URL, or the default one |
| Settings | Open-to-work (or equivalent): on/off, visibility scope, target titles/locations if visible; creator mode or similar toggles; profile visibility settings reachable without leaving profile context |
| Activity signal | Rough recency of the last post or comment (recent / months ago / none) — recency only, no content mining |

Also capture platform-surfaced meta where visible: profile completeness meter, "suggested for you" prompts, section order.

## Snapshot report structure

Write to `<platform>/<YYYY-MM-DD>-snapshot.md`, e.g. `linkedin/2026-07-09-snapshot.md`:

```markdown
# Profile snapshot — <platform> — YYYY-MM-DD

Profile URL: ...
Crawled: <datetime>

## Headline
<verbatim text> (NN chars)

## About
<verbatim text>

## Experience
### <Title> — <Company> (<dates>)
<verbatim description>
...

## Skills
1. <skill> (pinned, N endorsements)
...

## Recommendations
...

## Featured
...

## Settings
- Open to work: on, recruiters-only, titles: ...
...

## Gaps observed
- <empty or missing sections, truncations that could not be expanded>
```

One `##` per section, in the order of the table above, verbatim text in place. The report stands alone: the scoring pass in step 2 reads this file and never the live profile.

Return to the main session: the report path plus a 3–5 line summary (sections present, notable gaps). The full text stays in the file.
