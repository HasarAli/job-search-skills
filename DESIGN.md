# Design — Job-Search Skills

Thirteen skills a job seeker installs into their agent harness. They run a whole job
search — background, targets, resume, profile, daily shortlist, applications,
inbox, tracking, interviews, retros — against a data repo the skills scaffold themselves.

- **This repo** — the engine. Skills under `skills/`, installed with `npx skills add <repo>`. No user data ever lives here.
- **The user's data repo** — everything about one job seeker. Created by `init` on first run; nothing to clone or fork. Git history is the tracking and error-tolerance layer: everything durable is committed, daily and derived artifacts are gitignored.

## Skills ship standalone and regenerate per-user artifacts

A `npx skills` update overwrites a skill directory, so nothing that encodes **who the
user is** may ship as data. The user's own repo is git-tracked, so anything of theirs
that a skill writes is recoverable.

Anything per-user ships instead as a documented schema or skeleton in the owning skill's
`references/`, filled with `<placeholder>` tokens, carrying the banner

> A **seed**: copied once into `<path>`, which is where every later change lives. A skill update overwrites this file.

The skill materializes it into the user's repo at `.agents/` on first use, and every run
after that reads and edits the user's copy, never its own reference.

| Seed | Materializes to | Owner |
|---|---|---|
| `create-resume/references/yaml-template.md` | `.agents/templates/resume.yaml` | `create-resume` |
| `init/references/scaffold.md` | the whole tree, incl. `.agents/state.md` | `init` |

### The one exception: shipped scripts

`search/search.py` and the `search/pipeline/` package are real code, not a seed: the
fetch/dedup/filter/price engine (`sources/`, `comp/`, `store/`), its `defaults/` seeds,
`requirements.txt`, and `tests/`. It ships because it is engine, never user-edited — the
profession and region gates it applies are external config (`.agents/search/config.yaml`
and `filters.py`), so retargeting it takes no code edit. Skills locate it relative to the
installed skill directory and run it from the user's repo root, so relative cache paths
resolve.

Two deliberate consequences:

- `pipeline/comp/visa_wages.py` is a US/Canada-specific module (DOL LCA salary index)
  shipped by default, against the "generic always" rule below. US/Canada is the expected
  majority of users and the data has no equivalent elsewhere; every other market falls
  back to posted comp. Calling it an exception is the honest framing — it is not a
  template for adding more.
- Sources are added by block in `config.yaml` (a tenant slug, a feed URL, a JSON path)
  up to what the shipped adapters cover — `ats`, `feed`, `jobspy`, `jsonfile`. A board
type none of them handles needs a new adapter: a change to the user's `.agents/search/`
config and filters, never an edit to the shipped package, because an update would
overwrite the edit.

## Skill-authoring philosophy

- **Concise and high-level.** A `SKILL.md` is ~50–90 lines: trigger, flow, file contracts, human-in-the-loop points. Anything detailed, long, or occasionally needed goes in that skill's `references/`, loaded only when needed.
- **One seam per skill.** The "X belongs to `y`" clauses in every description are load-bearing: they are how a skill hands off at its edges instead of reaching across them.
- **Orchestrator pattern.** The main session interfaces with the user and delegates; skills explicitly instruct spawning subagents for heavy work (parsing documents, scoring and rewriting content, crawling, running search passes, synthesizing reports) so the main context stays small over long conversations. Each subagent gets one focused task and returns conclusions only.
- **Interviews run in the main session** — subagents cannot talk to the user. Ask one question at a time. Facts from `career/` and `goals/` travel inline in a subagent's prompt; those docs stay open in the main session only.
- **Generic always.** No industry, country, company-tier, or platform assumption in skill prose. Anything culture- or market-specific lives in the user's own docs — `.agents/config/conventions/` for market norms, `.agents/search/config.yaml` for boards and sources per region.
- **Trust the user's numbers.** When the user supplies a metric or fact about themselves, write it in immediately; never demand justification.
- **Never fabricate.** Every resume, profile, or outreach claim traces to a line in `career/profile.md` or `career/career-diary.md`.
- **No standing todo lists.** Anything outstanding is either the `next_action` pair on an `applications.csv` row or a line in a skill's closing report. A checklist nobody sweeps rots within a week.
- **Record decisions and actions only** — no deliberation, scope notes, meta commentary, or rejected options. If a decision needs justification, one short reason line.

## Harness independence

Nothing here targets one agent runtime.

Skills that must not fire on their own carry three layers, kept in step, because different
harnesses read different ones:

1. `disable-model-invocation: true` in the frontmatter
2. `agents/openai.yaml` with `policy.allow_implicit_invocation: false`
3. description wording — "Use only when the user explicitly asks…" — for harnesses that honour neither

Five skills are explicit-invocation only: `init`, `goals`, `optimize-linkedin`,
`retro`, `teach`. The first four carry all three layers; `teach` carries 1 and 2 only —
its description is upstream's, left unmodified. The rest trigger on conditions they can
detect.

**Never name a specific tool, model, or vendor in a skill.** Say "the browser tools this
harness provides", not a tool id; "this harness's MCP client", not an install command.

## The thirteen skills

Each owns one seam. Five run only on the user's explicit request (**bold**).

| Skill | Seam it owns |
|---|---|
| **`init`** | scaffolds the data repo — tree, `.gitignore`, `README.md`, `.agents/state.md`, market conventions, first commit. Asks nothing about the user |
| `intake` | raw material → recorded facts. Sweeps `drop/`, reads the public URLs, interviews for the gaps, writes `career/profile.md` and appends to `career/career-diary.md` |
| **`goals`** | what the user is searching for. Targets and positioning → `goals/role-preferences.md`; comp, location, logistics, cadences → `goals/search-filters.md`. The two never mix |
| `highlights` | achievement bullets and their quality. XYZ format, a number or a visible placeholder on each, scored on a rubric → `career/highlights.md` |
| `create-resume` | selection, assembly, render. User picks bullets from `career/highlights.md`, one YAML per target region, RenderCV → PDF in `resumes/<date>/` |
| **`optimize-linkedin`** | the live profile page. Dated crawl snapshot, section-by-section scoring, each approved rewrite applied in the browser one confirmed edit at a time. An optional branch, never a prerequisite |
| `search` | the daily shortlist. Newest-first passes, dedup against the cache, filter, comp figure on every row → `shortlists/<timestamp>.md`, numbered. Cron-able |
| `apply` | form → submit → record. Autofill, Q&A bank, explicit user yes before every submit, then the `applications.csv` row and the JD snapshot |
| `inbox` | inbound recruiter threads on every configured channel. Reads, scores, recommends; the user sends every reply |
| `track` | one application event onto its row, then the stale-application sweep |
| **`retro`** | the funnel over all applications so far — where it leaks, and which skill owns each fix |
| `interview` | one scheduled round: format, research, question set matched to the user's stories, rehearsal, then the debrief |
| **`teach`** | multi-session teaching on one topic, in `teach/<topic-slug>/`. Vendored from `mattpocock/skills` (MIT) with one repo-local scoping edit |

## Data repo layout

The contract every skill shares. Top level is what the user reads or edits; everything the
agent maintains for itself is under `.agents/`.

```
drop/               raw material the user dumps at the start; gitignored but for its README
career/             profile.md (single source of truth), career-diary.md, highlights.md
goals/              role-preferences.md, search-filters.md
shortlists/         one file per search day (GITIGNORED — regenerated)
resumes/<date>/     one folder per render day; YAML + PDF committed, proofs are not
applications.csv    one row per application, and the only record of one
job-descriptions/   each posting as it appeared when applied to
interviews/         prep and debrief, one file per application
linkedin/           profile snapshots and the outstanding optimization plan
teach/<topic>/      one folder per topic being learned
.agents/
  state.md          the stage machine — what has happened, never what should happen next
  config/           channels.md, conventions/, qa-bank.md, autofill-config.json
  search/           config.yaml, filters.py (search sources + filters)
  templates/        resume.yaml and theme overrides
  cache/            dedup keys and scrape output (GITIGNORED)
```

Everything belonging to one application shares one stem — `<id>-<company>-<role>` — so the
CSV row, the posting, and the interview notes line up on sight.

`.agents/state.md` stages: `init`, `intake`, `goals`, `highlights`, `create-resume`,
`optimize-linkedin`, `apply`, `inbox`, `track`. Skills check prerequisites and,
if one is missing, hand off to the skill that owns it instead of failing obscurely.
