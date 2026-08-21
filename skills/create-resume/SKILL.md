---
name: create-resume
description: >-
  Build, tailor, edit, or render the user's resume/CV: the user picks bullets
  from `career/highlights.md`, you assemble one YAML per target region, and
  RenderCV turns each into a PDF. Use when the user says "write my resume",
  "tailor my resume for this role", "update my CV", "re-render my resume", or
  wants a resume PDF. Writing, scoring, and rewriting the bullets themselves
  belongs to `highlights`; LinkedIn and other profile pages belong to
  `optimize-linkedin`; filling in and submitting applications belongs to `apply`.
---

Selection, assembly, render. Bullet quality is already settled by `highlights` — this run picks the right bullets for the target and puts them on a page. The user picks; apply exactly what they select.

**Prerequisites** — read `.agents/state.md`, `career/highlights.md`, and `goals/role-preferences.md`. A missing doc hands off to `intake` (facts) or `goals` (targets); a `career/highlights.md` too thin for the target hands off to `highlights`.

**Two branches:**

- **Create** — no resume YAML fits the target: steps 1–6.
- **Edit/re-render** — a resume YAML exists: edit it in place (content edits leave the `design` block alone), then render (step 5) and report (step 6). Field syntax: [references/rendercv-guide.md](references/rendercv-guide.md). Design fields: [references/themes.md](references/themes.md).

Content sources are `career/`, `goals/`, and `.agents/templates/resume.yaml` — a previously rendered resume is an output, not a source.

## 1. Inputs

Resolve the target role from the user's argument, else the first entry under "Targets — apply now" in `goals/role-preferences.md`; its positioning drives the Summary and the Skills ordering. Summary facts come from `career/profile.md`. Regions come from `goals/search-filters.md` unless the user names them.

Done when: target role, regions, and the positioning line are stated back to the user.

## 2. The user picks the highlights

Present the `career/highlights.md` bullets as plain text, grouped by role and section, each with its `section.entry` id. Ask for 3–6 per experience entry and suggest a thematic spread (impact, leadership, cross-functional, technical depth).

Done when: every experience entry carries 3–6 user-chosen ids.

## 3. Fill open placeholders

For each `{{METRIC: …}}` placeholder among the picks, ask the user once for the number. Take it as given and write it into the working bullet, `career/highlights.md`, and `career/career-diary.md`. A number the user doesn't have stays a placeholder and travels through to the final report. A picked bullet that reads badly for the target hands back to `highlights` — scoring and rewriting are not this skill's job.

Done when: every picked bullet holds a number or a placeholder, and every new number appears in both docs.

## 4. Build one YAML per region

**Seed** `.agents/templates/resume.yaml` if it doesn't exist yet: copy [references/yaml-template.md](references/yaml-template.md), fill in the target regions' conventions (photo, personal details, paper size, date format, work-authorization line) from `.agents/config/conventions/country-conventions.md`, and pick a theme from [references/themes.md](references/themes.md). Every build after that reads `.agents/templates/resume.yaml`; design changes live there, or in a single region file for a one-off.

Build each region file from `.agents/templates/resume.yaml` into today's output directory:

```
resumes/<YYYY-MM-DD>/<Name>-<role-slug>-<region>.yaml
```

- `<YYYY-MM-DD>` is today's local date. `-` separates sections, `_` joins words inside one: `Jane_Doe-senior_data_analyst-de.yaml`. Re-rendering the same target the same day overwrites in place — autofill setups reference this stable path.
- Line 2, under the `# yaml-language-server` comment, carries `# generated: <ISO8601-UTC>` (e.g. `# generated: 2026-07-21T18:30:04Z`). The readable date is the directory; the exact render time hides inside the file.

Fill headline, Summary, Experience highlights (the user's picks, in `career/highlights.md` order), and Skills ordered by target-role relevance.

Done when: one YAML per region exists, and a diff between any two of them shows region conventions and nothing else.

## 5. Render

Commands, the remaining stamp carriers, Windows encoding, and the flag that silently kills the PDF: [references/rendercv-guide.md](references/rendercv-guide.md). Renders land in the source YAML's directory under its basename. Inspect the PNGs.

Done when: each region file has a PDF and exactly one PNG — a second PNG means the page overflowed, so trim and re-render — unless the region's conventions call for a multi-page CV.

## 6. Report and record

Report each region's `resumes/<YYYY-MM-DD>/` paths and every placeholder still open. Update the `create-resume` stage in `.agents/state.md`, then offer to commit the run: the YAML and the PDF are tracked, the PNG proofs and markdown intermediates are not. A resume named in an `applications.csv` row has to still exist to be worth naming — that is why the PDF is committed and not just regenerated.

Done when: every region's paths and open placeholders are reported, and the `create-resume` stage is updated in `.agents/state.md`.
