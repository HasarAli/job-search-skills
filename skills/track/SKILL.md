---
name: track
description: Track application outcomes and pipeline health. Use when the user wants to log a response, rejection, interview, or offer, update their applications, ask "how is my search going", or check follow-ups. Handles outcome logging, follow-up flagging, and periodic retros.
---

# Track — outcomes, follow-ups, retro

Prerequisite: `applications/applications.csv` exists (created by the `apply` skill). If missing, point the user at `apply` — nothing to track yet.

## File contract

- `applications/applications.csv` — one row per application; `status` column holds the current stage.
- `applications/<id>.md` — per-application record; outcome events are appended here as dated notes.
- `search/search-config.md` — optional settings: `follow-up-days` (default 14), `retro-every` (default 50).
- `state.md` — retro learnings become prep tasks here.

Stage taxonomy: `applied → screen → interview-N → offer | rejected | ghosted`. Definitions, valid transitions, and event→stage mapping: `references/stages.md`.

## 1. Log an outcome event

When the user reports an event (recruiter reply, rejection, interview invite, offer, learning):

1. Identify the application — match by company/role against the CSV; confirm if ambiguous.
2. Update the row: set `status` to the new stage per `references/stages.md`; add a short note.
3. Append to `applications/<id>.md`: `## YYYY-MM-DD — <event>` plus what the user said (who reached out, format, scheduling, learnings). Verbatim over paraphrase.
4. If the event carries a learning (e.g. failed a system-design round), also record a prep task in `state.md`.

## 2. Follow-up flagging (every invocation)

On every invocation of this skill, after handling the user's request:

1. Scan the CSV for applications whose `last_activity` column is older than `follow-up-days` (default 14) and whose stage is not terminal (`offer`, `rejected`, `ghosted`).
2. List them: company, role, stage, days since last activity.
3. Offer actions per item: draft a follow-up message (user sends it), mark `ghosted` (per criteria in `references/stages.md`), or snooze.
4. Log any action taken as an event (step 1 flow).

## 3. Retro (every `retro-every` applications)

When total applications crosses a multiple of `retro-every` (default 50) — or the user asks "how is my search going":

1. Spawn a subagent to analyze `applications/applications.csv` and the applied JDs in `applications/<id>.md` files. It returns numbers only: response rate, stage-conversion funnel (applied→screen→interview→offer), and patterns in applied JDs (common titles, keywords, seniority). Procedure: `references/retro-guide.md`.
2. Present the funnel to the user with the interpretation guidance from `references/retro-guide.md` — which stage is leaking and what adjustment fits that leak.
3. If response rate is below ~1/50, strongly recommend reviewing the resume, role targets, or search filters. This is a review trigger, not a hard rule — benchmarks differ per industry and market; discuss before changing anything.
4. Learnings become prep tasks in `state.md`; agreed adjustments route to the owning skill (`resume`, `onboard` targets/filters).

## Commit reminder

Tracker updates are meant to be committed — git history is the audit trail. After writing, remind the user to commit `applications/` and `state.md` (or offer to).
