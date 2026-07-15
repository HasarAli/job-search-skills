---
name: resume
description: >-
  Create, draft, edit, or render a resume/CV with RenderCV (YAML -> Typst PDF).
  Human-led: the user picks achievement bullets from context/highlights.md,
  advisor agents score and rewrite them, the user chooses the rewrites, then a
  YAML is built per target region and rendered to PDF. Also covers editing an
  existing resumes/*.yaml and re-rendering it. Use when asked to create, draft,
  update, edit, or render a resume or CV.
---

The user drives this skill. You gather picks and decisions, spawn advisor subagents, and assemble the YAML — never choose highlights or apply rewrites without the user's say-so.

**Prerequisites** — read `state.md` first. Needs `context/highlights.md` and `context/role-preferences.md` (written by the `onboard` skill). If either is missing, stop and point the user at `onboard` instead of improvising.

**Two paths:**
- **Create** — no suitable YAML exists for the target role: full flow below.
- **Edit/re-render** — a `resumes/*.yaml` already exists: edit it in place (content edits rarely touch the `design` block), then jump to step 6. Syntax rules: [references/rendercv-guide.md](references/rendercv-guide.md).

Orchestrator rules:

- Advisor scoring/rewriting runs in subagents; the main session only relays bullets inline and collects the user's choices. Never grant an advisor file access — picked bullets travel in the prompt.
- Never read old resumes in `resumes/` during a create; `context/` docs and the YAML template are the only content sources.

## Create flow

### 1. Inputs

Read `context/role-preferences.md` and `context/highlights.md`. Resolve the target role (argument, else the first active target) and use its positioning for the Summary and Skills ordering. Pull Summary facts from `context/profile.md`. Target regions come from `search/search-config.md` unless the user names them.

### 2. User picks the highlights (human-in-the-loop)

Present the `highlights.md` bullets grouped by role/section and ask the user to pick **3–6 per experience entry**. Suggest a thematic balance (e.g. impact, leadership, cross-functional, technical depth) but the picks are theirs. Plain-text question, not a widget — too many options.

### 3. Fill missing metrics (human-in-the-loop)

For each placeholder or weak metric in a picked bullet, ask the user for the number, one at a time. Write the answer into the working bullet, `context/highlights.md`, and `context/career-diary.md` (the trace source). Never invent a number; if the user has none, keep the placeholder and carry it through — flag it in the final report.

### 4. Advisor review (subagents)

Spawn the advisor agents from the data repo's `.claude/agents/` (default: recruiter-reviewer + hiring-manager; the user may name others) in parallel. Each prompt contains inline: the picked bullets with ids, the target role, and the writing rules from [references/bullet-writing.md](references/bullet-writing.md). Ask for: per-bullet score 1–5, verdict, and the one rewrite they'd ship (or "keep as-is"). Conclusions only, no file access.

### 5. User chooses rewrites (human-in-the-loop)

Show original vs. each advisor's rewrite side by side, per bullet. The user selects which rewrites to apply; "keep original" is always an option. Apply exactly what they select. If a rewrite needs a new fact, ask one question at a time and append the answer to `context/career-diary.md`.

### 6. Build YAML per region

One file per target region from [references/yaml-template.md](references/yaml-template.md):

```
resumes/<Name>-<role-slug>-<region>-<yyyyMMdd_HHmm>.yaml
```

`-` separates sections; `_` joins words within one (e.g. `Jane_Doe-senior_data_analyst-de-20260714_0930.yaml`). Full descriptive names matter — autofill setups reference one canonical file.

Fill headline, Summary, Experience highlights (the user's final bullets, in their `highlights.md` order), and role-ordered Skills. Apply the region's conventions (photo, personal details, paper size, length, work-authorization line) from the onboard skill's `references/country-conventions.md` — content differences between region files should be exactly the conventions, nothing else.

### 7. Render

Commands, theme selection, and the Windows gotchas (UTF-8 env, never pass `--dont-generate-*` flags): [references/rendercv-guide.md](references/rendercv-guide.md). A resume should be one page unless the region's conventions say otherwise — RenderCV writes one PNG per page, so a second PNG means it overflowed; trim and re-render. Inspect the PNGs, not the PDF.

### 8. Report and record

Report YAML + PDF paths per region and any metric placeholders left to fill. Update `state.md` (`resume` stage done). Commit the YAMLs and PDFs; only the typst/PNG/Markdown intermediates are gitignored.
