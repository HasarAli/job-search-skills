// Custom Header override for this project.
//
// Purpose: expose the vertical gap between wrapped connection lines
// (e.g. "<city>, <region> | ... | LinkedIn" and the "Authorized to work" line),
// which the stock theme hardcodes as `line_spacing * 1.7` inside the package
// `connections()` function and does NOT expose via any design field.
//
// This shadows the package `connections()` with an identical copy whose only
// change is the paragraph `leading` below. Edit CONNECTIONS-LINE-LEADING to tune.

// >>> EDITABLE: gap between wrapped connection lines <<<
#let connections-line-leading = 0.7em

// >>> EDITABLE: color of custom connections (e.g. the work-authorization note) <<<
// Custom connections render muted so they recede into the page. Assumes
// `custom_connections` is the last key under `cv:` (so they sort last).
#let custom-connection-color = luma(150)

#let connections(..connections) = {
  metadata("skip-content-area")

  context {
    let config = rendercv-config.get()
    let typography-line-spacing = config.at("typography-line-spacing")
    let header-connections-space-between-connections = config.at("header-connections-space-between-connections")
    let header-connections-separator = config.at("header-connections-separator")
    let page-left-margin = config.at("page-left-margin")
    let page-right-margin = config.at("page-right-margin")
    let header-space-below-connections = config.at("header-space-below-connections")
    let section-titles-space-above = config.at("section-titles-space-above")
    let colors-connections = config.at("colors-connections")
    let typography-font-family-connections = config.at("typography-font-family-connections")
    let typography-font-size-connections = config.at("typography-font-size-connections")
    let typography-small-caps-connections = config.at("typography-small-caps-connections")
    let typography-bold-connections = config.at("typography-bold-connections")
    let header-alignment = config.at("header-alignment")

    set par(spacing: 0pt, leading: connections-line-leading, justify: false)
    set text(
      fill: colors-connections,
      font: typography-font-family-connections,
      size: typography-font-size-connections,
      weight: if typography-bold-connections { 700 } else { 400 },
    )

    let separator = (
      h(header-connections-space-between-connections / 2, weak: true)
        + header-connections-separator
        + h(header-connections-space-between-connections / 2, weak: true)
    )
    let separator-width = (
      measure(header-connections-separator).width + header-connections-space-between-connections
    )
    if connections.pos().len() > 0 {
      set align(header-alignment)
      box(
        {
          layout(size => {
            let line-width = 0cm
            for (i, connection) in connections.pos().enumerate() {
              let connection-body = if typography-small-caps-connections { smallcaps(connection) } else { connection }
              let connection-width = measure(connection-body).width
              let is-last = i == connections.pos().len() - 1

              // Check if adding this connection + separator would exceed the line
              if (
                line-width + connection-width + separator-width > size.width and line-width > 0cm
              ) {
                linebreak()
                line-width = 0cm
              }

              // Add separator only if we're not at the start of a line
              if line-width > 0cm {
                separator
              }

              box(connection-body, width: auto)
              line-width = line-width + connection-width + (if line-width > 0cm { separator-width } else { 0cm })
            }
          })
        },
        width: 100%,
        height: auto,
      )
    }
    v(header-space-below-connections - section-titles-space-above)
  }
}

{% if cv.name %}
= {{ cv.name }}
{% endif %}

{% if cv.headline %}
  #headline([{{ cv.headline }}])

{% endif %}
{% set n_custom = (cv.custom_connections or []) | length %}
{% set n_total = cv._connections | length %}
#connections(
{% for connection in cv._connections %}
{% if loop.index0 >= n_total - n_custom %}
  [#text(fill: custom-connection-color)[{{ connection }}]],
{% else %}
  [{{ connection }}],
{% endif %}
{% endfor %}
)
