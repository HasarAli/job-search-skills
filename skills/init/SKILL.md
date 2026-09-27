---
name: init
disable-model-invocation: true
description: >-
  Use only when the user explicitly asks to set up, scaffold, or initialize a
  new job-search workspace — create the directory tree, seed the empty context docs,
  and write `README.md`.
---

# Init — scaffold the workspace

You scaffold and stop. Every question about the user's history, targets, or filters belongs to `intake` and `goals`; this run asks nothing and invents nothing.

**Prerequisites** — a working directory the user picked. Empty or already holding files, both are fine: you create what is absent and leave every existing file untouched.

Paths, file contents, and seed headings: [references/scaffold.md](references/scaffold.md).

## 1. Build the tree

Create every directory in the scaffold's tree, then write each file it lists that does not already exist: `README.md`, `info-drop-zone/README.md`, `.agents/state.md`. A file already on disk keeps its current contents — report it as skipped.

Done when: every path in the scaffold's tree exists, and every file that was already there is byte-identical to before.

## 2. Seed the empty docs

Write `candidate/profile.md`, `candidate/career-diary.md`, `candidate/highlights.md`, `candidate/role-preferences.md`, and `candidate/search-filters.md` with the headings the scaffold lists and nothing under them. `intake` fills the `candidate/` docs, `goals` fills `candidate/`, `highlights` fills `candidate/highlights.md`.

Done when: all five files exist with their headings and no content beneath any heading.

## 3. Hand off

Tell the user to put their raw material in `info-drop-zone/` — old resumes, performance reviews, project docs, anything describing work they have done — and paste their LinkedIn, portfolio, and published-work URLs into `info-drop-zone/README.md`. Name `intake` as the next run: it reads that folder, then interviews them for what the documents left out.

Done when: the user has the `info-drop-zone/` instruction and knows `intake` runs next.
