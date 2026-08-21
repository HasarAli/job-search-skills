---
name: init
disable-model-invocation: true
description: >-
  Use only when the user explicitly asks to set up, scaffold, or initialize a
  new job-search repo — create the directory tree, seed the empty context docs,
  write `.gitignore` and `README.md`, and make the first commit.
---

# Init — scaffold the repo

You scaffold and stop. Every question about the user's history, targets, or filters belongs to `intake` and `goals`; this run asks nothing and invents nothing.

**Prerequisites** — a working directory the user picked. Empty or already holding files, both are fine: you create what is absent and leave every existing file untouched.

Paths, file contents, and seed headings: [references/scaffold.md](references/scaffold.md).

## 1. Git

Run `git --version`. Missing means the user installs it themselves — tell them to run `! sudo apt install git` (or their platform's equivalent) and stop the run there; installing system packages is theirs to do, not yours.

Present, but `git rev-parse --git-dir` fails: run `git init`.

Done when: `git rev-parse --git-dir` succeeds, or the run has stopped on the install instruction.

## 2. Build the tree

Create every directory in the scaffold's tree, then write each file it lists that does not already exist: `.gitignore`, `README.md`, `drop/README.md`, `.agents/state.md`. A file already on disk keeps its current contents — report it as skipped.

Done when: every path in the scaffold's tree exists, and every file that was already there is byte-identical to before.

## 3. Seed the empty docs

Write `career/profile.md`, `career/career-diary.md`, `career/highlights.md`, `goals/role-preferences.md`, and `goals/search-filters.md` with the headings the scaffold lists and nothing under them. `intake` fills the `career/` docs, `goals` fills `goals/`, `highlights` fills `career/highlights.md`.

Done when: all five files exist with their headings and no content beneath any heading.

## 4. First commit

`git add -A` then commit. `drop/*` is gitignored, so the documents the user drops stay on their machine and never enter history — only `drop/README.md` is tracked.

Done when: `git log` shows the commit, and `git status` reports a clean tree.

## 5. Hand off

Tell the user to put their raw material in `drop/` — old resumes, performance reviews, project docs, anything describing work they have done — and paste their LinkedIn, GitHub, portfolio, and published-work URLs into `drop/README.md`. Name `intake` as the next run: it reads that folder, then interviews them for what the documents left out.

Done when: the user has the `drop/` instruction and knows `intake` runs next.
