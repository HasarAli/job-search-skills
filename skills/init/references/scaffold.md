# Scaffold — what `init` creates

Every path is relative to the repo root. Create directories with `mkdir -p`; write a file only when it is absent.

## Tree

```
drop/                     raw material the user dumps; gitignored except the README
  README.md               what to put here, and the public URLs for `intake`
career/                   profile.md, career-diary.md, highlights.md
goals/                    role-preferences.md, search-filters.md
.agents/config/           conventions (written here); sources.json and channels.md, written by `sources`
.agents/scripts/          custom board adapters, if `sources` ever writes one
.agents/templates/        resume template + theme overrides, written by `resume`
.agents/cache/            dedup keys and scrape output; gitignored
.agents/state.md          stage machine
```

`applications.csv`, `job-descriptions/`, `interviews/`, `shortlists/`, `resumes/`, and `linkedin/` are created by the skills that write into them.

## `.agents/config/conventions/`

Copy [conventions/country-conventions.md](conventions/country-conventions.md) and [conventions/industry-conventions.md](conventions/industry-conventions.md) verbatim. They are market lookup tables every later skill reads from `.agents/config/conventions/`, and the user's copy is the one that gets corrected when a **verify locally** row turns out to be wrong for their market.

## `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/

# Env / secrets
.env
.env.*
*.key

# OS cruft
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/

# Resume renders. The YAML is the source and the PDF is what an employer actually
# received — both are the record and both are committed. Everything else regenerates.
resumes/**/*.png
resumes/**/*.md
resumes/**/*.typ
resumes/**/*.html

# Daily shortlists (regenerated per run)
shortlists/

# Raw documents you dropped for intake — originals stay on your machine, not in git
drop/*
!drop/README.md

# Agent caches: dedup keys, raw scrape output, DOL salary index
.agents/cache/

# LinkedIn raw review output (historical, not synthesized context)
linkedin/*-reviews/
```

## `README.md`

Do not write a second copy here. This repository ships its own `README.md` at the root —
it is the template. Copy it verbatim into the new project, then correct only what is
project-specific (the user's name in the title, if the title carries one).

It must end up covering, in this order: the three stages (set up, optional LinkedIn,
then the apply/prepare/track loop), a "Where things are" tree, the per-application
filename convention, the skills glossary, and how history is saved. Written for someone
who does not know what git is.

## `drop/README.md`

Instructions and link list in one file — the folder holds no other tracked file.

```markdown
# drop/

Put everything about your working life in here, then say **"process my drop folder"**.
This is a one-time setup step. Once it is done, this folder goes back to empty.

## Files to drop in

- old resumes and CVs, any format
- performance reviews, promotion packets, 360 feedback
- project docs, design docs, post-mortems you wrote
- offer letters, and job descriptions from roles you have held
- anything with a number in it you might want on a resume

## Links to add below

Anything about your work that is public. Add a line under the right heading — a word or
two of context helps if the URL is not self-explanatory.

### Profiles

- LinkedIn:
- GitHub:
- Portfolio / personal site:

### Work

<!-- Published writing, conference talks, open-source contributions, shipped products,
     press coverage, anything with your name on it. -->

---

Nothing in here is saved to version history — the originals stay on your machine. What
gets extracted from them lands in `career/`. When processing finishes you will be asked,
file by file, whether to delete what has been read; nothing is removed without your yes.
```

## `.agents/state.md`

```markdown
# Pipeline State

Skills read this first and update their stage on completion. Stages only — no todo list.

## Stages

- [ ] init — repo scaffolded
- [ ] intake — `career/profile.md`, `career/career-diary.md` populated
- [ ] goals — targets → `goals/role-preferences.md`, filters → `goals/search-filters.md`
- [ ] sources — boards, feeds, and channels configured under `.agents/config/`
- [ ] highlights — XYZ bullets → `career/highlights.md`
- [ ] resume — rendered → `resumes/`
- [ ] optimize-linkedin — audited and optimized → `linkedin/`
- [ ] search — shortlist running → `shortlists/`
- [ ] apply — applications submitted and logged
- [ ] inbox — channels swept
- [ ] track — outcomes logged
```

## Seed docs — headings only

```markdown
# career/profile.md
# <Name> — Job Search Profile
## Identity
## Current Role
## Career Timeline
## Skills & Tools
## Education & Credentials
## Interview Stories
## Gaps & Explanations
```

```markdown
# career/career-diary.md
# Career Diary
Raw, append-only. Notes land here verbatim; `career/profile.md` holds the synthesis.
```

```markdown
# career/highlights.md
# Highlights
Resume-ready XYZ bullets grouped by the role held when the work shipped. Sections number continuously, so every bullet is addressable as `section.entry`.
```

```markdown
# goals/role-preferences.md
# Role Preferences
## Preferences
## Targets — apply now
## Stretch
## Do not pursue
```

```markdown
# goals/search-filters.md
# Search Filters
## Identity & logistics
## Constraints & preferences
## Comp
```
