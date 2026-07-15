---
name: onboard
description: Staged onboarding interview that sets up a job search from scratch. Use when the user says "set up my job search", "onboard me", "start my job search", "interview me about my career", or wants to build their profile, role targets, search filters, and advisor agents for the first time. Resumable — picks up at the last incomplete stage recorded in state.md.
---

# Onboard — staged interview → context docs + advisor agents

Five stages, one sitting each, checkpointed in `state.md`. Produces the context docs and advisor agents every other skill depends on.

## Prerequisites & resume behavior

1. Verify the data-repo skeleton exists (`context/`, `search/`, `applications/`, `state.md`). If missing, tell the user to clone `job-search-template` first — do not improvise a layout.
2. Read `state.md`. Stages: `onboard:setup` → `onboard:context` → `onboard:targets` → `onboard:filters` → `onboard:advisors`. Resume at the first incomplete stage; confirm with the user before redoing a completed one.
3. On completing each stage: write its output files, mark the stage done in `state.md`, offer to stop or continue.

## Orchestrator rules (binding)

- **Interviews run in the main session.** Subagents cannot talk to the user. Ask **one question at a time**; wait for the answer before the next.
- **Delegate heavy work to subagents**: parsing uploaded resumes/reviews/project docs (PDF/DOCX), synthesizing many notes into draft bullets. Each subagent gets one focused task and returns extracted facts or drafts only.
- **Never grant subagents direct access to personal docs** (`context/*`, uploaded files with personal data beyond the one file they parse). Relay facts into the prompt instead.
- **Trust the user's numbers.** Write supplied metrics in immediately; never demand justification.
- **Never fabricate.** Everything written must trace to the user's answers or parsed documents.

Question banks for every stage: `references/interview-guide.md`.

## Stage 1 — setup → `search/search-config.md`

Capture: country/region, industry, working language, target platforms/boards. Use answers to load the right rows from `references/country-conventions.md` and `references/industry-conventions.md` — these drive later resume and profile conventions; never assume them. Also confirm or adjust the tracking defaults (`follow-up-days: 14`, `retro-every: 50`).

## Stage 2 — context → `context/profile.md`, `context/highlights.md`, `context/career-diary.md`

1. Ask for existing material (old resumes, performance reviews, project docs, portfolio). Spawn one subagent per document to parse it and return facts (roles, dates, metrics, tech/skills, achievements) — facts only, no file writes.
2. Interview the user through their timeline (interview-guide has the question bank): role by role, mining achievements toward XYZ bullets — "Accomplished [X] as measured by [Y] by doing [Z]".
3. Write `profile.md` (history, skills, stories, gaps — facts only), seed `highlights.md` with XYZ bullets, initialize `career-diary.md` as an append-only archive.

## Stage 3 — targets → `context/role-preferences.md`

Interview: target role list, one positioning anchor per role, and an explicit "Do not pursue" list. Positioning only — no search logistics here.

## Stage 4 — filters → `search/job-search-filters.md`

Interview: compensation floor/target, location/remote, company type/size, logistics (hours, travel, start date), visa/work authorization. Search logistics only — no role positioning here. Targets and filters never mix.

## Stage 5 — advisors → data repo `.claude/agents/`

1. Read `search-config.md` + `role-preferences.md` for `{{industry}}`, `{{country}}`, `{{role}}` values.
2. For each of 3–5 advisors, copy a template from `references/advisor-archetypes/` (recruiter-reviewer, hiring-manager, industry-insider, profile-platform-expert), fill the placeholders, write to the data repo's `.claude/agents/<name>.md`.
3. Archetypes, not real people. The user may optionally name real experts as "inspired by" flavor in the persona body.
4. Advisors review, score, and rewrite **in their replies only** — they never edit files. This constraint is baked into each template; do not remove it.

## File contracts

| File | Owner stage | Consumers |
|---|---|---|
| `search/search-config.md` | setup | all skills |
| `context/profile.md`, `highlights.md`, `career-diary.md` | context | resume (appends metrics), apply |
| `context/role-preferences.md` | targets | resume, search |
| `search/job-search-filters.md` | filters | search |
| `.claude/agents/*.md` | advisors | resume, profile |
