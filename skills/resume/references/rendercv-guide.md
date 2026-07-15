# RenderCV guide — install, render, edit, troubleshoot

RenderCV turns one YAML file per base resume into a PDF: **YAML → Typst source → PDF** (plus PNG previews and Markdown). Typst ships bundled — no separate LaTeX/Typst install.

## Install

```bash
pip install "rendercv[full]"
rendercv --version   # sanity check; this guide assumes v2.x
```

Pin it in the data repo's root `requirements.txt` as `rendercv[full]` so renders are reproducible.

## Render command

```bash
PYTHONIOENCODING=utf-8 rendercv render resumes/<name>.yaml \
  -pdf resumes/<name>.pdf -png rendercv_output/<name>.png -md rendercv_output/<name>.md \
  -typ rendercv_output/discard.typ -nohtml
```

- `-pdf`/`-png`/`-md`/`-typ` resolve **relative to the input YAML**, and RenderCV creates destination dirs as needed — point `-pdf` at `resumes/` (no subdir) so the PDF lands next to its YAML and gets committed alongside it. Point `-png`/`-md`/`-typ` at `rendercv_output/`, which lands in `resumes/rendercv_output/` — gitignored, so intermediates never get committed.
- **Always pass `-pdf`/`-png` explicitly with the YAML's basename.** The default output name is built from `cv.name` (e.g. `Jane_Doe_CV.pdf`), which collides across every base resume for the same person.
- The Typst source is disposable — point `-typ` at a scratch path and forget it.

### Windows gotchas (do not skip)

- **`PYTHONIOENCODING=utf-8` is required.** RenderCV prints checkmark glyphs (✓) that crash on the default cp1252 Windows console. Run via a bash shell (Git Bash) for the env-var prefix, or set `$env:PYTHONIOENCODING = 'utf-8'` first in PowerShell.
- **Never pass `-notyp` / `--dont-generate-typst`.** PDF renders *from* the Typst file, so skipping Typst silently disables PDF (and PNG) too. Treat every `--dont-generate-*` flag as suspect; the only safe skip is `-nohtml`.
- `-nohtml` is safe: PDF, PNG, and Markdown still generate.
- Keep PNG generation on (no `-nopng`) — PNGs are the fastest way to inspect output, and **one PNG per page** doubles as the page-count check: a second PNG means the resume overflowed one page.

## Themes

Built-in themes: `classic` (default), `harvard`, `engineeringresumes`, `engineeringclassic`, `sb2nov`, `moderncv`. All share the same `design` field structure and differ only in defaults — switch by setting `design.theme` and overriding fields. Full field reference, every theme's default design block, and a worked override example: [themes.md](themes.md).

Picking one:

| Theme | Character |
|---|---|
| `classic` | Traditional, colored accents, footer/top-note on |
| `harvard` | Dense, centered section titles, serif — conservative industries |
| `engineeringresumes` | Black-and-white, no icons, single page focus — tech/engineering |
| `engineeringclassic` | Left-aligned header, sans-serif |
| `sb2nov` | Computer Modern (academic look) |
| `moderncv` | Photo-friendly header, colored rule titles — regions where photos are customary |

Region conventions (paper size `us-letter` vs `a4`, photo, page count) come from the onboard skill's `references/country-conventions.md`; apply them via `design.page.size`, `cv.photo`, and theme choice — never hardcode.

## Editing YAML

`cv.sections` is a dict: keys are section titles, values are entry lists. Each section holds a single entry type, auto-detected from fields present. **Extra or misspelled keys are accepted silently — a typo will NOT error**, so double-check field names.

| Entry type | Required | Common optional |
|---|---|---|
| ExperienceEntry | `company`, `position` | `location`, `start_date`+`end_date` or `date`, `summary`, `highlights` |
| EducationEntry | `institution`, `area` | `degree` + the shared fields |
| OneLineEntry | `label`, `details` | — |
| TextEntry | *(plain string)* | — |

- **Quote any string containing a colon** — the most common invalid-YAML cause: `title: "Results: A Study"`.
- Inline Markdown only (`**bold**`, `*italic*`, `[text](url)`); no headers/lists inside values.
- `date` and `start_date`/`end_date` are mutually exclusive. `start_date`/`end_date` need strict `YYYY-MM-DD`/`YYYY-MM`/`YYYY`; `end_date` omitted = `present`. `date` is free-form (`"Fall 2023"`).
- Phone must be E.164 (`"+15551234567"`). Never invent one.
- Nested highlights: indent a sub-item two spaces under its parent line within the same string.
- Editor autocompletion: put this on line 1 of every YAML:
  `# yaml-language-server: $schema=https://raw.githubusercontent.com/rendercv/rendercv/refs/tags/v2.8/schema.json`

## Locales

`--locale LOCALE` on `rendercv new`, or set `locale.language` in the YAML. ~20 built-ins (french, german, spanish, japanese, ...); override individual `locale` fields for custom month names/phrases. Pick per `search/search-config.md` working language.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `UnicodeEncodeError` mid-render on Windows | Missing `PYTHONIOENCODING=utf-8` |
| PDF/PNG missing but no error | A `--dont-generate-*` flag (usually `-notyp`) suppressed the chain — remove it |
| Two+ PNGs produced | Resume overflowed one page — trim bullets or tighten `design` spacing |
| Field ignored with no error | Misspelled key silently accepted — check against the schema |
| Invalid YAML at a specific line | Unquoted colon in a string value |
| Output overwrote another resume's PDF | Default `cv.name`-based filename — pass `-pdf`/`-png` explicitly |
