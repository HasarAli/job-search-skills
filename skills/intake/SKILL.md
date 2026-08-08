---
name: intake
description: >-
  Turn raw material into recorded facts: sweep `drop/` for documents, read the
  public URLs listed in `drop/README.md`, extract each with its own subagent, then
  interview the user for what the documents left out — writing `career/profile.md`
  and appending the raw notes to `career/career-diary.md`. Use when the user has
  dropped documents to process, says their profile is out of date, or when
  another skill finds `career/profile.md` missing or thin. Resume-ready bullets
  belong to `highlights`; role targets and search filters belong to `goals`.
---

# Intake — documents and interview into facts

You are the user's **scribe**: every line you write traces to a document you read or an answer they gave, and their numbers go in as given. The interview happens in the main session — subagents cannot talk to the user.

**Prerequisites** — `drop/` and `career/` exist; without them, hand off to `init`. Read `career/profile.md` before anything else: it is what tells you which run this is.

**Two branches:**

- **First run** — `career/profile.md` holds headings and nothing else: every source is new and every question in the bank is live.
- **Refresh** — the profile has content: diff it against `drop/` and ask only about the delta. This is how the profile stays current, so a refresh is cheap and frequent.

## 1. Inventory the sources

List every file in `drop/` and every URL listed in `drop/README.md`. Mark each one new or already covered — a source is already covered when `career/career-diary.md` names it. On a refresh, drop the covered ones from the run.

Done when: every file and URL carries a new-or-covered mark, and the new ones are stated back to the user as the run's inputs.

## 2. Extract — one subagent per source

Spawn one subagent per new source. Its prompt names exactly one file path or one URL, and that is the only thing it opens; a URL is fetched with WebFetch. Any fact it needs to make sense of the source travels inline in the prompt — `career/` docs stay in the main session, opened by no subagent.

Each returns: employers, titles, dates, and locations; what the user was responsible for; achievements with any number attached; skills, tools, and credentials named; and direct quotes worth keeping verbatim (review lines, recommendations, customer feedback).

Done when: every new source has returned a fact list, and each list names its source file or URL.

## 3. Synthesize

Write the facts into `career/profile.md` under its headings — history, skills, interview stories, and each gap in the user's own framing. Append the returned raw notes to `career/career-diary.md` verbatim, each block headed by its source and the date read. Paraphrase in the profile; never in the diary.

A fact two sources disagree on goes to the user as a question, not to the file as a guess.

Done when: every returned fact is in `career/profile.md` or `career/career-diary.md`, and every diary block names its source.

## 4. Interview the holes

Work the question bank in [references/question-bank.md](references/question-bank.md): one question at a time, wait for the answer, probe once for depth, move on. What a document already answered you confirm instead of asking — "your 2021 resume says you led a team of 4 at Acme — still accurate?" Answers land in `career/profile.md` and append to `career/career-diary.md` as they arrive.

Done when: every heading in `career/profile.md` holds content or a recorded "none", and every gap the user named carries their own wording for it.

## 5. Empty `drop/`

`drop/` is staging, not storage: once a document's facts are in `career/`, the copy in `drop/` is done. Take the processed files one at a time — show what that file contributed, the facts and the diary block it produced, then ask whether to delete it. Delete on an explicit yes for that file; each yes covers the file it was asked about and no other. A file the user keeps stays untouched and goes on the keep list.

`drop/README.md` is the folder's own instructions and its link list: it survives every run.

Done when: every processed file has been deleted on the user's own yes or is on the keep list, and `drop/README.md` is still there.

## 6. Report and record

Report what each source contributed, what the user's answers added, and every file still sitting in `drop/`. Check off the `intake` stage in `.agents/state.md`, commit `career/`, and name `highlights` as the next run for turning this history into resume bullets.

Done when: the `intake` stage is checked off, `career/` is committed, and each kept file is named in the report.
