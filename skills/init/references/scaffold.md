# Scaffold — what `init` creates

Every path is relative to the repo root. Create directories with `mkdir -p`; write a file only when it is absent.

## Tree

```
candidate/                    profile, diary, highlights, role preferences, search filters
search/
  resumes/                   current base resumes, grouped by role and region
  shortlists/                timestamped search results
  applications/             index.csv plus one directory per application, draft onward
development/                 one teaching workspace per topic
info-drop-zone/              raw material; gitignored except README.md
.agents/config/              channels, autofill, Q&A bank, conventions
.agents/search/              search source configuration and regenerable state
.agents/templates/           canonical resume template and theme assets
.agents/cache/               regenerable agent data; gitignored
.agents/state.md             stage machine
```

`search/applications/index.csv`, application directories, base-role resume directories, shortlists, `candidate/<platform>/`, and topic directories under `development/` are created by the skills that write into them.

## `.gitignore`

```gitignore
# Python
__pycache__/
.pytest_cache/
*.py[cod]
.venv/

# Env / secrets
.env
.env.*
!.env.example
*.key

# OS cruft
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/

# Resume YAML is tracked; all rendered resume artifacts stay local and regenerate.
search/resumes/**/*.png
search/resumes/**/*.md
search/resumes/**/*.typ
search/resumes/**/*.html
search/resumes/**/*.pdf
search/resumes/.render-cache/

# Application resume YAML is tracked; rendered artifacts stay local.
search/applications/**/*_Resume.pdf
search/applications/**/*_Resume*.png
search/applications/**/*_Resume.md
search/applications/**/*_Resume.html
search/applications/**/*.typ

# Daily shortlists regenerate on each run
search/shortlists/

# Pipeline state that regenerates
.agents/search/seen.db
.agents/search/visa-wages/

# Raw documents you dropped for intake — originals stay on your machine, not in git
info-drop-zone/*
!info-drop-zone/README.md

# Agent caches: dedup keys, raw scrape output, DOL salary index
.agents/cache/

# Platform raw review output (historical, not synthesized context)
candidate/*/*-reviews/
```

## `.gitattributes`

```gitattributes
*.pdf binary
```

## `README.md`

Do not write a second copy here. This repository ships its own `README.md` at the root —
it is the template. Copy it verbatim into the new project, then correct only what is
project-specific (the user's name in the title, if the title carries one).

It must explain the workflow, the user-facing project tree, the per-application directory
and resume conventions, and the skills glossary.

## `info-drop-zone/README.md`

Instructions and link list in one file — the folder holds no other tracked file.

```markdown
# info-drop-zone/

Put everything about your working life in here, then say **"process my info drop zone"**.
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
gets extracted from them lands in `candidate/`. When processing finishes you will be asked,
file by file, whether to delete what has been read; nothing is removed without your yes.
```

## `.agents/state.md`

```markdown
# Pipeline State

Skills read this first and update their stage on completion. Stages only — no todo list.

## Stages

- [ ] init — repo scaffolded
- [ ] intake — `candidate/profile.md`, `candidate/career-diary.md` populated
- [ ] goals — targets → `candidate/role-preferences.md`, filters → `candidate/search-filters.md`
- [ ] highlights — XYZ bullets → `candidate/highlights.md`
- [ ] create-resume — base resumes rendered → `search/resumes/`
- [ ] optimize-linkedin — audited and optimized → `candidate/linkedin/`
- [ ] apply — applications submitted and logged
- [ ] inbox — channels swept
- [ ] track — outcomes logged
```

## Seed docs — headings only

```markdown
# candidate/profile.md
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
# candidate/career-diary.md
# Career Diary
Raw, append-only. Notes land here verbatim; `candidate/profile.md` holds the synthesis.
```

```markdown
# candidate/highlights.md
# Highlights
Resume-ready XYZ bullets grouped by the role held when the work shipped. Sections number continuously, so every bullet is addressable as `section.entry`.
```

```markdown
# candidate/role-preferences.md
# Role Preferences
## Preferences
## Targets — apply now
## Stretch
## Do not pursue
```

```markdown
# candidate/search-filters.md
# Search Filters
## Identity & logistics
## Constraints & preferences
## Comp
```
