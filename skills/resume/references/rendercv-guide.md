# RenderCV guide — install, render, edit, troubleshoot

RenderCV turns one YAML file per base resume into a PDF: **YAML → Typst source → PDF** (plus PNG previews and Markdown). Typst ships bundled — no separate LaTeX/Typst install.

## Install

```bash
pip install "rendercv[full]"
rendercv --version   # sanity check; this guide assumes v2.x
```

Pin it in the data repo's root `requirements.txt` as `rendercv[full]` so renders are reproducible.

## Render command

`-pdf`/`-png`/`-md`/`-typ` resolve **relative to the input YAML**, so bare basenames land beside it — one directory and one basename (`<base>` = `<Name>-<role-slug>-<region>`) for the source and all its renders:

```bash
DIR="resumes/$(date +%F)"                 # local date → directory
BASE="<Name>-<role-slug>-<region>"
PYTHONIOENCODING=utf-8 rendercv render "$DIR/$BASE.yaml" \
  -pdf "$BASE.pdf" -png "$BASE.png" -md "$BASE.md" \
  -typ discard.typ -nohtml
```

- **Always pass `-pdf`/`-png` explicitly with the YAML's basename.** The default output name is built from `cv.name` (e.g. `Jane_Doe_CV.pdf`), which collides across every base resume for the same person.
- The Typst source is disposable — point `-typ` at a scratch name and forget it.

### Invisible provenance stamp

The render time rides inside each output — it survives a copy and stays invisible to a reader. The YAML carries its own `# generated:` line from build time; the render adds two more:

```bash
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"       # UTC ISO8601 — machine-readable
# MD: an HTML comment, invisible when rendered
printf '\n<!-- generated: %s | source: %s.yaml -->\n' "$TS" "$BASE" >> "$DIR/$BASE.md"
# PDF: Typst writes the render time into the PDF's own CreationDate metadata — no extra step.
```

### Windows

- **`PYTHONIOENCODING=utf-8` is required.** RenderCV prints checkmark glyphs (✓) that crash on the default cp1252 Windows console. Run via a bash shell (Git Bash) for the env-var prefix, or set `$env:PYTHONIOENCODING = 'utf-8'` first in PowerShell.
- **`-nohtml` is the only safe skip flag.** PDF renders *from* the Typst file, so `-notyp` / any other `--dont-generate-*` silently takes PDF and PNG down with it, exit code 0 and no error.
- Leave PNG generation on: it is the fastest way to inspect output, and RenderCV writes **one PNG per page**, so the file count is the page check.

## Themes

Built-in themes: `classic` (default), `harvard`, `engineeringresumes`, `engineeringclassic`, `sb2nov`, `moderncv`. All share the same `design` field structure and differ only in defaults — switch by setting `design.theme` and overriding fields. Which theme suits which industry and region, the full field reference, every theme's default design block, and a worked override example: [themes.md](themes.md).

Region conventions (paper size `us-letter` vs `a4`, photo, page count) come from `.agents/config/conventions/country-conventions.md`, applied via `design.page.size`, `cv.photo`, and theme choice.

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
- Phone must be E.164 (`"+15551234567"`), copied from `career/profile.md`.
- Nested highlights: indent a sub-item two spaces under its parent line within the same string.
- Editor autocompletion: put this on line 1 of every YAML:
  `# yaml-language-server: $schema=https://raw.githubusercontent.com/rendercv/rendercv/refs/tags/v2.8/schema.json`

## Locales

`--locale LOCALE` on `rendercv new`, or set `locale.language` in the YAML. ~20 built-ins (french, german, spanish, japanese, ...); override individual `locale` fields for custom month names/phrases. Pick per `goals/search-filters.md` working language.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `UnicodeEncodeError` mid-render on Windows | Missing `PYTHONIOENCODING=utf-8` |
| PDF/PNG missing but no error | A `--dont-generate-*` flag (usually `-notyp`) suppressed the chain — remove it |
| Two+ PNGs produced | Resume overflowed one page — trim bullets or tighten `design` spacing |
| Field ignored with no error | Misspelled key silently accepted — check against the schema |
| Invalid YAML at a specific line | Unquoted colon in a string value |
| Output overwrote another resume's PDF | Default `cv.name`-based filename — pass `-pdf`/`-png` explicitly |
