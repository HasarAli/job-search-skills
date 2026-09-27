---
name: create-resume
description: >-
  Build, tailor, edit, or render the user's resume/CV: the user picks bullets
  from `candidate/highlights.md`, you assemble one YAML per target region, and
  RenderCV turns each into a PDF. Use when the user says "write my resume",
  "tailor my resume for this role", "update my CV", "re-render my resume", or
  wants a resume PDF. Writing, scoring, and rewriting the bullets themselves
  belongs to `highlights`; LinkedIn and other profile pages belong to
  `optimize-linkedin`; filling in and submitting applications belongs to `apply`.
---

Selection, assembly, render. Bullet quality is already settled by `highlights` — this run picks the right bullets for the target and puts them on a page. The user picks; apply exactly what they select.

**Prerequisites** — read `.agents/state.md`, `candidate/highlights.md`, and `candidate/role-preferences.md`. A missing doc hands off to `intake` (facts) or `goals` (targets); a `candidate/highlights.md` too thin for the target hands off to `highlights`.

**Three branches:**

- **Create base** — no base resume fits the target role and region: steps 1–6.
- **Edit/re-render base** — a base YAML exists: edit it in place (content edits leave the `design` block alone), then render (step 5) and report (step 6).
- **Tailor for an application** — copy the closest base YAML into the application's directory, tailor it against that application's `job-description.md`, then render and report. Never edit the base as a side effect of tailoring.

Field syntax: [references/rendercv-guide.md](references/rendercv-guide.md). Design fields: [references/themes.md](references/themes.md).

Content sources are the candidate documents and `.agents/templates/resume.yaml` — a previously rendered resume is an output, not a source.

## 1. Inputs

Resolve the target role from the user's argument, else the first entry under "Targets — apply now" in `candidate/role-preferences.md`; its positioning drives the Summary and the Skills ordering. Summary facts come from `candidate/profile.md`. Regions come from `candidate/search-filters.md` unless the user names them.

Done when: target role, regions, and the positioning line are stated back to the user.

## 2. The user picks the highlights

Present the `candidate/highlights.md` bullets as plain text, grouped by role and section, each with its `section.entry` id. Ask for 3–6 per experience entry and suggest a thematic spread (impact, leadership, cross-functional, technical depth).

Done when: every experience entry carries 3–6 user-chosen ids.

## 3. Fill open placeholders

For each `{{METRIC: …}}` placeholder among the picks, ask the user once for the number. Take it as given and write it into the working bullet, `candidate/highlights.md`, and `candidate/career-diary.md`. A number the user doesn't have stays a placeholder and travels through to the final report. A picked bullet that reads badly for the target hands back to `highlights` — scoring and rewriting are not this skill's job.

Done when: every picked bullet holds a number or a placeholder, and every new number appears in both docs.

## 4. Build the YAML

**Seed** `.agents/templates/resume.yaml` if it doesn't exist yet: copy [references/yaml-template.md](references/yaml-template.md), fill in the target regions' conventions (photo, personal details, paper size, date format, work-authorization line) from `.agents/config/conventions/country-conventions.md`, and pick a theme from [references/themes.md](references/themes.md). Every build after that reads `.agents/templates/resume.yaml`; design changes live there, or in a single region file for a one-off.

For a base resume, build one file per region at a stable role-and-region path:

```
search/resumes/<role-slug>/<region>/<First>_<Last>_<Target_Role>_Resume.yaml
```

Example: `search/resumes/senior_frontend_engineer/ca/First_Last_Senior_Frontend_Engineer_Resume.yaml`. The stable path always names the current base for that role and region.

For application tailoring, copy the closest base into:

```
search/applications/<stem>/<First>_<Last>_<Posted_Role>_Resume.yaml
```

The application directory and its `draft` index row must already be provisioned by `apply`, and its `job-description.md` drives the tailoring. The matching PDF is what `apply` reviews and attaches; it becomes the immutable submitted copy only after submission. The filename contains normal title words joined by `_`; company, date, region, version numbers, and words such as `final` stay out because the containing directory supplies that context.

Line 2, under the `# yaml-language-server` comment, carries `# generated: <ISO8601-UTC>` (e.g. `# generated: 2026-07-21T18:30:04Z`).

Fill headline, Summary, Experience highlights (the user's picks, in `candidate/highlights.md` order), and Skills ordered by target-role relevance.

Done when: each requested base YAML exists at its stable role-and-region path, or the tailored YAML exists in the named application directory. A diff between regional base files shows region conventions and nothing else.

## 5. Render

Commands, the remaining stamp carriers, Windows encoding, and the flag that silently kills the PDF: [references/rendercv-guide.md](references/rendercv-guide.md). Renders land in the source YAML's directory under its basename. Inspect the PNGs.

Done when: each region file has a PDF and exactly one PNG — a second PNG means the page overflowed, so trim and re-render — unless the region's conventions call for a multi-page CV.

## 6. Report and record

Report each base role-and-region path or application-local path and every placeholder still open. Update the `create-resume` stage in `.agents/state.md`. Keep every PDF, Markdown render, HTML render, and PNG preview beside its YAML as local, regenerable output, including the exact application-local PDF that was submitted. Every submitted application keeps that local PDF beside its YAML so later base edits do not obscure what was sent.

Done when: every region's paths and open placeholders are reported, and the `create-resume` stage is updated in `.agents/state.md`.
