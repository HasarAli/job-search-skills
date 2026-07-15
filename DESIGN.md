# Design — Generic Job-Search Skills

Two-repo architecture for a job-search assistant that works in any industry and country.

- **This repo (`job-search-skills`)** — the engine. Six skills under `skills/`, installed into a user's harness via `npx skills add <repo>`. No user data ever lives here.
- **`job-search-template`** — the data repo a job seeker clones/forks. Empty skeletons, `state.md`, `.gitignore`, README. Git history is the tracking and error-tolerance layer: everything durable is committed; daily/derived artifacts are gitignored.

## Skill-authoring philosophy

- **Concise and high-level.** A `SKILL.md` is ≤ ~80 lines: trigger, flow, file contracts, human-in-the-loop points. Anything detailed, long, or occasionally needed goes in that skill's `references/` directory, loaded only when needed.
- **Orchestrator pattern.** The main session interfaces with the user and delegates; skills must explicitly instruct spawning subagents for heavy work (parsing documents, scoring/rewriting content, crawling, synthesizing reports) so the main context stays small over long conversations. Each subagent gets one focused task and returns conclusions only.
- **Interviews run in the main session** — subagents cannot talk to the user. Ask one question at a time; relay facts to subagents rather than granting them file access to personal docs.
- **Generic always.** No industry, country, company-tier, or platform assumption in skill prose. Anything culture- or market-specific lives in `references/` lookup tables (`country-conventions.md`, `industry-conventions.md`, board lists) keyed by the user's `search-config.md`.
- **Trust the user's numbers.** When the user supplies a metric or fact about themselves, write it in immediately; never demand justification.
- **Never fabricate.** Every resume/outreach claim must trace to a line in `context/profile.md` or `context/career-diary.md`.

## Data repo layout (contract all skills share)

```
context/
  profile.md            facts about the user (history, stack, stories, gaps) — single source of truth
  career-diary.md       raw append-only archive of the user's notes
  highlights.md         resume-ready achievement bullets, XYZ format
  role-preferences.md   role targets, positioning, do-not-pursue
search/
  search-config.md      country, industry, language, platforms — written by onboard, read by everyone
  job-search-filters.md comp, location, company type, logistics
  shortlist-YYYY-MM-DD.md   daily output (GITIGNORED)
  seen-jobs.json        dedup cache (GITIGNORED)
resumes/                generated resume YAML + rendered PDFs
applications/
  applications.csv      one row per application
  qa-bank.md            reusable application answers (visa, salary, "why us" patterns)
  <id>.md               per-application record: JD snapshot, resume used, ad-hoc answers
state.md                pipeline checklist — every skill reads it first, updates its stage on completion
.claude/agents/         advisor agents GENERATED here by onboard (not shipped with skills)
```

`state.md` stages: `onboard:setup`, `onboard:context`, `onboard:targets`, `onboard:filters`, `onboard:advisors`, `resume`, `profile`, `search`, `apply`, ongoing `track`. Skills check prerequisites and, if missing, point the user at the earlier skill instead of failing obscurely.

## The six skills

### 1. `onboard` — staged interview → context docs + advisor agents
Resumable via `state.md`; each stage is one sitting.
- **setup**: capture country, industry, working language, target platforms → `search/search-config.md`. Verify data-repo skeleton exists.
- **context**: ingest existing resumes/reviews/project docs (subagents parse PDF/DOCX and return extracted facts); interview the user through their timeline; write `profile.md`; seed `highlights.md` with XYZ-format bullets (X = accomplishment, Y = measure, Z = method: "Accomplished [X] as measured by [Y] by doing [Z]"); initialize `career-diary.md` as append-only.
- **targets**: interview → `role-preferences.md` (role list + positioning anchor, incl. "do not pursue").
- **filters**: interview → `job-search-filters.md`. Targets and filters are separate docs — positioning vs. search logistics never mix.
- **advisors**: generate 3–5 agents into the data repo's `.claude/agents/` from `references/advisor-archetypes/` templates (recruiter-reviewer, hiring-manager, industry-insider, profile-platform-expert), with `{{industry}}`/`{{country}}`/`{{role}}` placeholders filled from `search-config.md` + `role-preferences.md`. Archetypes, not real people; the user may optionally name real experts as "inspired by" flavor. Advisors review and score; they never edit files directly.

References: `interview-guide.md` (question banks per stage), `country-conventions.md`, `industry-conventions.md`, `advisor-archetypes/*.md`.

### 2. `resume` — create / edit / render
- Read `role-preferences.md` + `highlights.md` → user picks 3–6 bullets per role → advisor agents (subagents) score and rewrite → user picks rewrites → build resume YAML per target region → render to PDF.
- Engine: RenderCV (YAML → Typst PDF). Region/industry customs (photo, personal details, A4 vs Letter, length, date formats, CV vs resume) come from `references/country-conventions.md` — applied to content and template choice, never hardcoded.
- Filenames: `<Name>-<role-slug>-<region>-<timestamp>` — full names matter because autofill setups reference one canonical file.
- Windows gotcha (must be in references): set UTF-8 env for rendercv; do not pass `--dont-generate-*` flags.

References: `rendercv-guide.md`, `yaml-template.md`, `bullet-writing.md` (XYZ + skim-test rules), `country-conventions.md` (shared copy or pointer).

### 3. `profile` — audit + optimize the user's professional profile
- Default adapter: LinkedIn via browser tools; other platforms (Xing etc.) chosen in `search-config.md`.
- Flow: crawl the user's profile (subagent) → detailed snapshot report → advisor agents review section-by-section → present recommendations → user picks → apply approved edits **one at a time, each confirmed** (browser automation on their logged-in session). Photo/cover changes are flagged for the user to do manually.

References: `crawl-guide.md` (sections to capture), `platform-notes.md`.

### 4. `search` — daily shortlist, newest-first
- Engine: JobSpy scripts (already proven) + optional per-country board adapters from `references/boards.md`.
- **Prioritize new postings**: default window = postings from the last 24–72h; sort newest-first; shortlist ordered by posted date. Window widens only if results are thin.
- Dedup against `seen-jobs.json`; every surfaced job is appended to the cache.
- Output `search/shortlist-YYYY-MM-DD.md` with numbered entries (numbers are the `apply` skill's default references). Shortlists and cache are gitignored.
- Cron-able: designed to run unattended and leave the shortlist for review.

References: `jobspy-guide.md` (env setup, script patterns), `boards.md` (per-country boards and notes).

### 5. `apply` — autofill → human-approved submit → record
- **First-run branch**: no autofill config found → offer to set up an autofill service (Simplify is the default adapter, optional). Upload ONE canonical resume (free tiers allow one), record its full filename and upload date in `applications/autofill-config.md`, fill the service's profile fields for deterministic autofill.
- Flow per job (args: shortlist numbers, default = today's shortlist; or a date): open posting → autofill (extension + browser tools) → fill gaps from `qa-bank.md` → ask the user for any genuinely new answers → **STOP: never submit; ask explicit permission per application** → on submit, write the record.
- Record = row in `applications.csv` (id, datetime, company, role, location, source, url, resume filename, status=applied, last_activity=submission date, notes) + `applications/<id>.md` (JD snapshot, resume used, all ad-hoc answers). New answers are appended to `qa-bank.md` — the bank compounds and halves application time over the first dozen applications.

References: `autofill-setup.md`, `record-format.md`, `qa-bank-format.md`.

### 6. `track` — outcomes, follow-ups, retro
- Log outcome events (recruiter reply, rejection, interview stage, offer, learnings) → update the CSV row + `<id>.md`. Stage taxonomy: applied → screen → interview-N → offer | rejected | ghosted.
- Flag applications with no response after N days (default 14) for follow-up.
- **Retro trigger**: every 50 applications (configurable), compute response rate and stage-conversion; if response rate < ~1/50, strongly consider changes to resume, targets, or filters — a review trigger, not a hard rule; thresholds differ per industry. Learnings (e.g. a failed interview type) become prep tasks in `state.md`.

References: `retro-guide.md`, `stages.md`.

## Out of scope (phase 3, not designed yet)
LinkedIn engagement mining, content creation, recruiter-reply drafting — one future `engage` skill.
