# KnowB Autumn Diagram Style Guide

**The single source of truth for KnowB diagram colors, typography, and tokens.** Every new diagram uses semantic roles from this document, not inline hexadecimal values. These rules inherit the Diagram Design grammar while remaining subordinate to [`ORGBRAND_GUIDELINES.md`](../../../ORGBRAND_GUIDELINES.md).

The style is intentionally editorial and restrained: one focal color, thin borders, no shadows, and a maximum of two focal nodes. The current site may use a more arcade-forward treatment; diagrams use this quieter sibling system so relationships remain legible at small sizes.

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, not `#f7591f`.

| Role | Purpose | KnowB light | KnowB dark |
|---|---|---|---|
| `paper` | Page background, default node fill | `#FCF6F3` Paper Ivory | `#7A2217` Charcoal Bark |
| `paper-2` | Diagram container bg, secondary fill | `#FCF6F3` Paper Ivory | `#8E2F2A` Deep Rust |
| `ink` | Primary text, primary stroke | `#7A2217` Charcoal Bark | `#FCF6F3` Paper Ivory |
| `muted` | Secondary text, default arrow stroke | `#77584F` Muted Wood | `#E9C2B3` Terracotta Border |
| `soft` | Sublabels, boundary labels | `#77584F` Muted Wood | `#F59A52` Soft Ember |
| `rule` | Hairline borders | `rgba(122,34,23,0.16)` | `rgba(252,246,243,0.18)` |
| `rule-solid` | Stronger borders, baselines | `#E9C2B3` Terracotta Border | `#E9C2B3` Terracotta Border |
| `accent` | Focal / 1–2 max per diagram | `#8E2F2A` Deep Rust | `#F59A52` Soft Ember |
| `accent-tint` | Fill for accent-bordered boxes | `rgba(142,47,42,0.08)` | `rgba(245,154,82,0.12)` |
| `link` | HTTP/API calls, external arrows | `#7A2217` Charcoal Bark | `#86E8FF` Saber Blue |

> **Brand palette source:** all values map directly to the eight approved KnowB Autumn colors, with opacity variants used only for soft fills and rules. Saber Blue is reserved for external or secure signal paths on dark diagrams. It is not body text on light paper.

> **Note:** Upstream example HTML files are retained as grammar references and may show the inherited neutral skin. New KnowB diagrams must use the tokens above or start from `static/diagrams/knowb-diagram-template.html`.

### Inversion rule (light → dark)

Any light `ink` opacity becomes a Paper Ivory opacity on dark. Keep the same opacity. The focal color changes from Deep Rust to Soft Ember to preserve separation on Charcoal Bark.

### Series palette (multi-series chart types only)

A small set of desaturated, editorial-tone colors for chart types that genuinely need to distinguish multiple overlapping entities (currently: **radar**). The "1-focal" rule still holds — `accent` is reserved for the focal series; the palette below covers the rest.

| Token | Light | Dark | Notes |
|---|---|---|---|
| `series-1` | `#77584F` Muted Wood | `#E9C2B3` Terracotta Border | Non-focal series |
| `series-2` | `#8E2F2A` Deep Rust | `#F59A52` Soft Ember | Non-focal series |
| `series-3` | `#7A2217` Charcoal Bark | `#FCF6F3` Paper Ivory | Non-focal series |
| `series-4` | `#F59A52` Soft Ember | `#86E8FF` Saber Blue | Non-focal series |
| `series-5` | `#E9C2B3` Terracotta Border | `#77584F` Muted Wood | Non-focal series |

Fills sit at `0.18` opacity light, `0.22` dark; strokes use the full color. **Don't backfill these tokens to non-chart types** — architecture, swimlane, etc. continue to use muted-ink variants. The series palette is opt-in for diagrams where overlapping shapes demand distinguishable color, not a license to add color elsewhere.

### Terminal skin (opt-in alternate)

A self-contained palette for the terminal-window primitive (see [primitive-terminal.md](primitive-terminal.md)) — a CLI-chrome register for dev-tool posts and technical social cards. It does not replace the default skin above and isn't affected by onboarding; it's a second, fixed skin you opt into per-diagram.

| Token | Hex | Purpose |
|---|---|---|
| `terminal-page` | `#7A2217` | Page background behind the window |
| `terminal-paper` | `#8E2F2A` | Window body, node fill |
| `terminal-bar` | `#7A2217` | Titlebar strip |
| `terminal-border` | `#E9C2B3` | Window border, hairlines |
| `terminal-ink` | `#FCF6F3` | Primary text, primary stroke |
| `terminal-muted` | `#E9C2B3` | Secondary text, sublabels, ring stroke |
| `terminal-soft` | `#77584F` | Tertiary — inactive dots, spokes |
| `terminal-accent` | `#86E8FF` | The one signal accent — focal station, prompt sign, active dot |
| `terminal-accent-tint` | `rgba(134,232,255,0.12)` | Fill for accent-bordered boxes |

**1-accent rule still holds.** Everything that isn't `terminal-ink` or `terminal-muted`/`terminal-soft` should be `terminal-accent` — never introduce a second hue.

---

## Typography

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | Space Grotesk | 1.75rem | 600 | Page H1 |
| `node-name` | Inter | 12px | 600 | Human-readable labels |
| `sublabel` | JetBrains Mono | 9px | 400 | Port, protocol, URL, field type |
| `eyebrow` | JetBrains Mono | 7–8px | 500, tracked 0.18em, uppercase | Type tags, axis labels |
| `arrow-label` | JetBrains Mono | 8px | 400, tracked 0.06em | Arrow annotations |
| `callout` | Space Grotesk *italic* | 14px | 500 | Editorial asides only |

### Font stack

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
```

**Load-bearing rule:** Mono is for *technical* content (ports, commands, URLs, field types). Names go in Inter. Page titles and editorial callouts use Space Grotesk. Never use mono as the blanket body or node-name font.

---

## Stroke, radius, spacing

| Token | Value | Use |
|---|---|---|
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes |
| `stroke-default` | `1` | Most strokes |
| `stroke-strong` | `1.2` | Emphasis strokes |
| `radius-sm` | `4` | Small tags |
| `radius-md` | `6` | Node boxes |
| `radius-lg` | `8` | Containers, rings |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) |

---

## Node type → treatment

Semantic role combinations — reference these by name in type specs.

| Type | Fill | Stroke |
|---|---|---|
| `focal` (1–2 max) | `accent-tint` | `accent` |
| `backend` | `#ffffff` (white) | `ink` |
| `store` | `ink @ 0.05` | `muted` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.10` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| `security` | `accent @ 0.05` | `accent @ 0.50` dashed `4,4` |

---

## Customizing the skin

Three options:

1. **Run onboarding** — see [`onboarding.md`](onboarding.md). Drop a URL; the skill extracts the palette + fonts and rewrites this file.
2. **Edit by hand** — change the hex values in the tables above. Run the pre-output taste gate afterward to verify the accent still reads as "focal" against the new paper color.
3. **Brand handoff** — paste your existing design-token JSON into a new section here and map its tokens to the semantic roles above.

### Constraints (don't break these)

- **Contrast**: `ink` must hit WCAG AA on `paper`. `muted` must hit AA on `paper` for 11px+ text.
- **One accent**: pick one color for `accent`. Two accents erases the focal signal.
- **No rainbow palette**: if your brand ships 8 colors, pick 3 (paper, ink, accent). The rest become `muted` variants.
- **Display + sans + mono**: Space Grotesk is for titles and callouts, Inter is for names and body copy, JetBrains Mono is for technical labels. Do not introduce another font family.
- **Paper is warm-neutral, not pure white**: pure white turns the design sterile. Pick a cream, bone, or light grey with a hint of warmth.
- **Dot pattern is optional, not default**: the 22×22 dot pattern is an opt-in "dotted paper" variant (good for long-form editorial hero diagrams). The default background is a clean `paper` fill, no pattern. When the pattern is enabled, it should sit at ~10% opacity of `ink` on `paper` — visible but quiet.
- **Container is clean by default**: the diagram sits directly on the page paper, no secondary container background or border. A framed variant (`paper-2` bg + `rule` border + 8px radius + padding) is available as an opt-in for card-heavy layouts, but don't reach for it by default — the extra chrome fights the figure.
