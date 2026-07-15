# RenderCV theme & design reference

> Seed/default only — customize `resumes/template.yaml` in your data repo, not this file; skill updates overwrite it.

Load this only when tuning a design field or switching themes. For basic YAML editing, [yaml-template.md](yaml-template.md) is enough.

All 6 built-in themes (`classic`, `harvard`, `engineeringresumes`, `engineeringclassic`, `sb2nov`, `moderncv`) share the same `design` field structure — they only differ in default values. To use one, set `design.theme` and override any field below. Theme choice should follow the target industry/region's conventions — see the onboard skill's `references/industry-conventions.md` (document norms by field) and `references/country-conventions.md` (paper size, photo, length by country) — not personal preference.

## Complete field reference (classic theme defaults)

```yaml
design:
  theme: classic
  page:
    size: us-letter
    top_margin: 0.7in
    bottom_margin: 0.7in
    left_margin: 0.7in
    right_margin: 0.7in
    show_footer: true
    show_top_note: true
  colors:
    body: rgb(0, 0, 0)
    name: rgb(0, 79, 144)
    headline: rgb(0, 79, 144)
    connections: rgb(0, 79, 144)
    section_titles: rgb(0, 79, 144)
    links: rgb(0, 79, 144)
    footer: rgb(128, 128, 128)
    top_note: rgb(128, 128, 128)
  typography:
    line_spacing: 0.6em
    alignment: justified
    date_and_location_column_alignment: right
    font_family:
      body: Source Sans 3
      name: Source Sans 3
      headline: Source Sans 3
      connections: Source Sans 3
      section_titles: Source Sans 3
    font_size:
      body: 10pt
      name: 30pt
      headline: 10pt
      connections: 10pt
      section_titles: 1.4em
    small_caps:
      name: false
      headline: false
      connections: false
      section_titles: false
    bold:
      name: true
      headline: false
      connections: false
      section_titles: true
  links:
    underline: false
    show_external_link_icon: false
  header:
    alignment: center
    photo_width: 3.5cm
    photo_position: left
    photo_space_left: 0.4cm
    photo_space_right: 0.4cm
    space_below_name: 0.7cm
    space_below_headline: 0.7cm
    space_below_connections: 0.7cm
    connections:
      phone_number_format: national
      hyperlink: true
      show_icons: true
      display_urls_instead_of_usernames: false
      separator: ''
      space_between_connections: 0.5cm
  section_titles:
    type: with_partial_line
    line_thickness: 0.5pt
    space_above: 0.5cm
    space_below: 0.3cm
  sections:
    allow_page_break: true
    space_between_regular_entries: 1.2em
    space_between_text_based_entries: 0.3em
    show_time_spans_in:
      - experience
  entries:
    date_and_location_width: 4.15cm
    side_space: 0.2cm
    space_between_columns: 0.1cm
    allow_page_break: false
    short_second_row: true
    degree_width: 1cm
    summary:
      space_above: 0cm
      space_left: 0cm
    highlights:
      bullet: •
      nested_bullet: •
      space_left: 0.15cm
      space_above: 0cm
      space_between_items: 0cm
      space_between_bullet_and_text: 0.5em
  templates:
    footer: '*NAME -- PAGE_NUMBER/TOTAL_PAGES*'
    top_note: '*LAST_UPDATED CURRENT_DATE*'
    single_date: MONTH_ABBREVIATION YEAR
    date_range: START_DATE – END_DATE
    time_span: HOW_MANY_YEARS YEARS HOW_MANY_MONTHS MONTHS
    one_line_entry:
      main_column: '**LABEL:** DETAILS'
    education_entry:
      main_column: |-
        **INSTITUTION**, AREA
        SUMMARY
        HIGHLIGHTS
      degree_column: '**DEGREE**'
      date_and_location_column: |-
        LOCATION
        DATE
    normal_entry:
      main_column: |-
        **NAME**
        SUMMARY
        HIGHLIGHTS
      date_and_location_column: |-
        LOCATION
        DATE
    experience_entry:
      main_column: |-
        **COMPANY**, POSITION
        SUMMARY
        HIGHLIGHTS
      date_and_location_column: |-
        LOCATION
        DATE
    publication_entry:
      main_column: |-
        **TITLE**
        SUMMARY
        AUTHORS
        URL (JOURNAL)
      date_and_location_column: DATE
```

## Theme defaults

Each block below shows only the fields that differ from the `classic` defaults above.

### classic

Full defaults are the field reference above — colored accents, footer and top-note on, serif-adjacent sans body.

**When to use:** general-purpose default; fine for most industries unless the target's conventions call for something more conservative or more minimal (check `industry-conventions.md`).

### engineeringresumes

```yaml
design:
  theme: engineeringresumes
  page:
    show_footer: false
  typography:
    font_family:
      body: XCharter
      name: XCharter
      headline: XCharter
      connections: XCharter
      section_titles: XCharter
    font_size:
      name: 25pt
      section_titles: 1.2em
    bold:
      name: false
  header:
    connections:
      separator: '|'
      show_icons: false
      display_urls_instead_of_usernames: true
  colors:
    name: rgb(0,0,0)
    connections: rgb(0,0,0)
    headline: rgb(0,0,0)
    section_titles: rgb(0,0,0)
    links: rgb(0,0,0)
  links:
    underline: true
    show_external_link_icon: false
  section_titles:
    type: with_full_line
    space_above: 0.5cm
    space_below: 0.3cm
  sections:
    space_between_regular_entries: 0.42cm
    space_between_text_based_entries: 0.15cm
    show_time_spans_in: []
  entries:
    short_second_row: false
    summary:
      space_above: 0.08cm
    side_space: 0cm
    highlights:
      bullet: ●
      nested_bullet: ●
      space_left: 0cm
      space_above: 0.08cm
      space_between_items: 0.08cm
      space_between_bullet_and_text: 0.3em
```

**When to use:** black-and-white, no icons, tight single-page layout — tech/engineering resumes per `industry-conventions.md`, where skim time is seconds and density beats decoration.

### harvard

```yaml
design:
  theme: harvard
  page:
    top_margin: 0.5in
    bottom_margin: 0.5in
    left_margin: 0.5in
    right_margin: 0.5in
    show_top_note: false
  colors:
    name: rgb(0,0,0)
    headline: rgb(0,0,0)
    connections: rgb(0,0,0)
    section_titles: rgb(0,0,0)
    links: rgb(0,0,0)
  typography:
    font_family:
      body: XCharter
      name: XCharter
      headline: XCharter
      connections: XCharter
      section_titles: XCharter
    font_size:
      name: 25pt
      connections: 9pt
      section_titles: 1.3em
  header:
    space_below_name: 0.5cm
    space_below_headline: 0.5cm
    space_below_connections: 0.5cm
    connections:
      show_icons: false
      separator: •
      space_between_connections: 0.4cm
  section_titles:
    type: centered_with_centered_partial_line
    space_below: 0.2cm
  sections:
    space_between_regular_entries: 1em
    show_time_spans_in: []
  entries:
    short_second_row: false
```

**When to use:** dense, centered section titles, serif, black-and-white — conservative fields (finance, government, academia) per `industry-conventions.md`.

### engineeringclassic

```yaml
design:
  theme: engineeringclassic
  typography:
    font_family:
      body: Raleway
      name: Raleway
      headline: Raleway
      connections: Raleway
      section_titles: Raleway
    bold:
      name: false
      section_titles: false
  header:
    alignment: left
  links:
    show_external_link_icon: false
  section_titles:
    type: with_full_line
  sections:
    show_time_spans_in: []
  entries:
    short_second_row: false
    summary:
      space_above: 0.12cm
    highlights:
      space_left: 0cm
      space_above: 0.12cm
      space_between_items: 0.12cm
```

**When to use:** left-aligned header, sans-serif — same tech/engineering fit as `engineeringresumes` with a softer, less dense look.

### sb2nov

```yaml
design:
  theme: sb2nov
  typography:
    font_family:
      body: New Computer Modern
      name: New Computer Modern
      headline: New Computer Modern
      connections: New Computer Modern
      section_titles: New Computer Modern
  colors:
    name: rgb(0,0,0)
    connections: rgb(0,0,0)
    section_titles: rgb(0,0,0)
    headline: rgb(0,0,0)
    links: rgb(0,0,0)
  links:
    underline: true
    show_external_link_icon: false
  section_titles:
    type: with_full_line
  sections:
    show_time_spans_in: []
  header:
    connections:
      hyperlink: true
      show_icons: false
      display_urls_instead_of_usernames: true
      separator: •
  entries:
    short_second_row: false
    highlights:
      bullet: ◦
      nested_bullet: ◦
```

**When to use:** Computer Modern (academic look) — academia/research per `industry-conventions.md`, or any field where a LaTeX-native aesthetic reads as credible.

### moderncv

```yaml
design:
  theme: moderncv
  typography:
    line_spacing: 0.6em
    font_family:
      body: Fontin
      name: Fontin
      headline: Fontin
      connections: Fontin
      section_titles: Fontin
    font_size:
      name: 25pt
      section_titles: 1.4em
    bold:
      name: false
      section_titles: false
  header:
    alignment: left
    photo_width: 4.15cm
    photo_space_left: 0cm
    photo_space_right: 0.3cm
  links:
    underline: true
    show_external_link_icon: false
  section_titles:
    type: moderncv
    space_above: 0.55cm
    space_below: 0.3cm
    line_thickness: 0.15cm
  sections:
    show_time_spans_in: []
  entries:
    short_second_row: false
    side_space: 0cm
    space_between_columns: 0.3cm
    summary:
      space_above: 0.1cm
    highlights:
      space_left: 0cm
      space_above: 0.15cm
      space_between_items: 0.1cm
      space_between_bullet_and_text: 0.3em
```

**When to use:** photo-friendly header — regions where a photo is customary or expected per `country-conventions.md` (e.g. DACH, Japan, Gulf states).

## Worked example: customizing a theme

Overrides are applied on top of a theme's defaults, not instead of them — only list the fields you're changing. Example: `engineeringresumes` tightened for a denser single-page fit and switched to a different font/link color:

```yaml
design:
  theme: engineeringresumes
  page:
    top_margin: 6mm
    bottom_margin: 6mm
    left_margin: 15mm
    right_margin: 15mm
    show_top_note: false
  typography:
    line_spacing: 0.55em
    font_family:
      body: Arial
      name: Arial
      headline: Arial
      connections: Arial
      section_titles: Arial
    font_size:
      body: 10.5pt
      name: 14pt
      section_titles: 12pt
  colors:
    name: rgb(0,0,0)
    connections: rgb(0,0,0)
    headline: rgb(0,0,0)
    section_titles: rgb(0,0,0)
    links: rgb(26,63,168)
  header:
    space_below_name: 0.4em
    space_below_headline: 0.8em
    space_below_connections: 0.4em
  section_titles:
    space_above: 1.2em
    space_below: 0.4em
  sections:
    space_between_regular_entries: 0.8em
    space_between_text_based_entries: 0.4em
  entries:
    summary:
      space_above: 0.2em
    highlights:
      space_above: 0.2em
      space_between_items: 0.2em
```

Reach for overrides only when the render overflows a page or a theme default clashes with region/industry convention — theme defaults are fine to start.
