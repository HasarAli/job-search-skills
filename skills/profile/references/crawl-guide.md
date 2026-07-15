# Crawl Guide — profile snapshot

How the crawl subagent captures the user's profile and structures the snapshot report.

## Cautions

- **The user's own profile only.** Never crawl, snapshot, or scrape other people's
  profiles, search results, or company pages. This skill audits the user's page, nothing
  else.
- **Crawl gently.** Navigate like a human: one page/section at a time, let pages load,
  no rapid-fire navigation, no bulk requests. If the platform shows friction (unusual
  challenges, warnings), stop and report back rather than pushing through.
- **Logged-in session.** Work on the user's existing session. Never handle credentials;
  if logged out, return and ask the user to log in.
- Prefer the platform's own "view profile" / edit screens over public views — they show
  the full, unabridged content and the settings.

## Sections to capture

Capture verbatim text (not paraphrases) wherever text exists. Note anything empty or
missing — gaps are findings too.

| Section | Capture |
|---|---|
| Identity | Display name, pronouns if shown, location, current title line under the name |
| Headline | Full text, character count |
| About / summary | Full text; note if it is truncated behind a "see more" (expand it) |
| Experience | Every entry: title, company, employment type, dates, location, full description text, media attached |
| Education | School, degree, field, dates |
| Skills | Full list in displayed order; which are pinned/top; endorsement counts if shown |
| Recommendations | Count received/given; for each received: recommender's role relationship (e.g. "managed the user directly") and full text |
| Featured / media | What is featured (posts, links, documents), titles, order |
| Certifications / licenses | Name, issuer, date |
| Projects / publications / volunteering | Whatever the platform offers and the profile has |
| Profile photo / cover image | Present or absent; rough description (do not download) |
| URL | Custom/vanity profile URL or the default one |
| Settings | Open-to-work (or equivalent): on/off, visibility (recruiters-only vs public), target titles/locations if visible; creator mode or similar toggles; profile visibility settings reachable without leaving profile context |
| Activity signal | Rough recency of last post/comment activity (recent / months ago / none) — no content mining |

Also capture platform-surfaced meta where visible: profile completeness meter,
"suggested for you" prompts, section order.

## Snapshot report structure

Write to the data repo, e.g. `search/profile-snapshot-YYYY-MM-DD.md`:

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

One `##` per section, same order as the table above, verbatim text in place. The report
must stand alone: advisors read only this file, never the live profile.

Return to the orchestrator: the report path + a 3–5 line summary (sections present,
notable gaps). Do not return the full text.
