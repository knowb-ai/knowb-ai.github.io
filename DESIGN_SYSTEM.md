# KnowB Visual Design System

**Status:** Locked foundational canon
**Scope:** KnowB AI public surfaces, product interfaces, internal operating
assets, and the shared artistic asset system

This public document is the implementation companion to the canonical visual
design decision held in the private KnowledgeHQ repository. It defines how a
KnowB asset, page, product surface, or brand expression receives a distinct,
compliant design configuration without forcing every product into one look.

## 1. Composition model

KnowB uses four independent design axes:

| Axis | Variants | Controls |
| --- | --- | --- |
| Palette | Autumn, Gold | Color family, signal hierarchy, surface depth, and contrast |
| Channel | Internal, External, Artistic | Role and destination of the surface or asset |
| Theme | Space-race, Psychedelic, Retrowave, Editorial, Arcade, Comic | World, mood, motifs, subject matter, and behavioral energy |
| Style | 60s, 70s, 80s, 90s, 2000s | Historical and formal visual grammar used to render the theme |

Typography is fixed brand infrastructure, not another selectable axis. Product
teams may select a primary and optional secondary theme or style, but must
declare the channel and primary palette.

```text
surface or asset = channel + palette + theme + style + product vocabulary
```

The axes compose without owning one another. Gold is not Internal, Autumn is
not External, and a theme or style cannot introduce new colors or substitute
new functional text fonts.

## 2. Palette options

### KnowB Autumn

Autumn is the warm, editorial, graphic, and narrative palette. It is the
default for public and outward-facing work.

| Token | Hex | Semantic use |
| --- | --- | --- |
| Autumn Fire | `#FF4A1A` | Primary action, focal accent, display emphasis |
| Deep Rust | `#8E2F2A` | Dark signal field, strong accent, depth |
| Soft Ember | `#F59A52` | Warm highlight, secondary action, soft emphasis |
| Paper Ivory | `#FCF6F3` | Default light canvas and paper field |
| Charcoal Bark | `#7A2217` | Dark canvas, primary text, primary stroke |
| Muted Wood | `#77584F` | Secondary text, quiet rules, inactive detail |
| Light Terracotta | `#E9C2B3` | Borders, separators, and quiet framing |
| Saber Blue | `#86E8FF` | Optional shared cool signal for secure or special state |

Autumn uses Paper Ivory, Charcoal Bark, and Deep Rust to create paper-and-ink
contrast. It does not add greens, purples, or unrelated neon hues.

### KnowB Gold

Gold is the high-signal, technical, and operational palette. It is the default
for internal product interfaces and command-oriented surfaces.

| Token | Hex | Semantic use |
| --- | --- | --- |
| Gold Primary | `#FFD500` | Primary action, active state, focal signal |
| Gold Attention | `#FFB300` | Attention, pending action, elevated emphasis |
| Gold Secondary | `#F7C700` | Secondary action and supporting highlight |
| Gold Highlight | `#FFC61A` | Selected detail and local emphasis |
| Gold Muted | `#F2C14E` | Inactive, historical, or low-priority signal |
| Gold Midnight | `#15163D` | Default dark field |
| Gold Indigo | `#1E2259` | Primary panel and workspace surface |
| Gold Purple | `#2D1F5B` | Raised panel and grouped controls |
| Gold Plum | `#221338` | Deep cockpit layer and modal backdrop |

Gold creates information-rich depth through indigo, purple, and plum fields.
It should remain controlled rather than using every signal token at once.

Palette rules:

- Choose one primary palette for each surface.
- Paper Ivory and Saber Blue are shared options with deliberate use.
- Opacity variants are allowed for fills, glows, overlays, and dividers.
- Themes and styles may change composition, motif, geometry, and finish, but
  they do not add colors to either palette.
- All color usage must preserve WCAG 2.2 AA contrast and must not communicate
  state by color alone.

## 3. Channels

Channels identify what a thing is and where it is used. They are not palettes,
themes, or eras.

### Internal

Internal covers product interfaces, workspaces, hubs, control panels, command
decks, cockpits, run views, instrumentation, system maps, and operational
reference material.

Its shared grammar is internal-facing space age: launch, orbit, dock, relay,
command, archive, recovery, and related product vocabulary. Dials, radial
systems, control surfaces, instrumentation, restrained retro-futurist line art,
and minimalist industrial design may establish orientation and system state.
Each product still owns its own vocabulary.

Default:

```yaml
channel: internal
palette: gold
theme: space-race
style:
  primary: 60s
  secondary: 70s
```

### External

External covers marketing, narrative, promotional material, public websites,
publishing surfaces, product launches, and outward-facing product polish.

Its shared grammar is arcade-informed public clarity: memorable title cards,
strong silhouettes, readable color blocks, energetic framing, and editorial
polish. Space-age material may appear, but it should not dominate the public
voice.

Default:

```yaml
channel: external
palette: autumn
theme: arcade
style:
  primary: 80s
  secondary: 90s
```

### Artistic

Artistic is the asset channel for characters, avatars, mascots, illustration,
posters, editorial scenes, and other authored visual artifacts. It is
palette-independent. Autumn or Gold may be applied after the asset's
construction is defined.

Default:

```yaml
channel: artistic
palette: autumn  # or gold
theme: comic     # or arcade
style:
  primary: 90s
  secondary: 2000s
```

The Artistic channel owns construction. The destination channel controls how
much of the asset, motion, contrast, and narrative is appropriate on the final
surface.

## 4. Themes

Themes answer: what world or energy does this belong to? They provide subject
matter, motifs, emotional register, and interaction attitude. Themes are not
eras and do not dictate a palette or font.

| Theme | Core properties | Typical expression |
| --- | --- | --- |
| Space-race | Optimistic, exploratory, engineered, mission-oriented, progress-driven | Orbits, trajectories, launch states, docking, modular craft, technical diagrams, and purposeful progression |
| Psychedelic | Playful, fluid, surprising, surreal, pattern-led | Optical rhythm, warped geometry, repetition, unexpected scale, flowing transitions, and dreamlike juxtaposition |
| Retrowave | Synthetic, signal-driven, nocturnal, cinematic, nostalgic, energetic | Horizon lines, grids, scanlines, glow bands, signal traces, CRT atmosphere, perspective, and controlled gradients |
| Editorial | Authored, composed, contextual, image-led, confident, curated | Strong hierarchy, margins, captions, pull quotes, pacing, key-art composition, and considered negative space |
| Arcade | Immediate, playable, competitive, bold, responsive, readable | Title cards, marquees, score and state language, color blocking, silhouettes, fast feedback, and repeatable visual hooks |
| Comic | Expressive, sequential, dramatic, character-led, tactile, narrative | Panels, ink contours, action framing, expressive poses, ensemble hierarchy, visual sequencing, and impact moments |

Theme boundaries:

- Arcade supplies playable energy, not a requirement for neon, pixel art, or a
  literal game screen.
- Space-race supplies mission world-building, not generic science fiction or
  decorative starfields.
- Retrowave supplies synthetic atmosphere, not unstructured cyberpunk clutter.
- Editorial supplies curation and hierarchy, not a mandatory magazine grid.
- Comic supplies narrative framing and ink logic, not a requirement for human
  figures or multiple panels.
- Psychedelic supplies playful transformation, not uncontrolled distortion or
  visual confusion.

## 5. Styles

Styles answer: what formal visual grammar renders the chosen theme? They are
historical reference frames, not literal reproductions.

| Style | Properties |
| --- | --- |
| 60s | Space age, optimistic modernism, atomic and aerodynamic forms, clean line art, capsule and orbit geometry, confident reduction, forward motion |
| 70s | Instrumentation, dials, gauges, radial systems, analog marks, measured density, tactile control logic, and system feedback |
| 80s | Bold title cards, CRT logic, dramatic diagonals, high-impact framing, chunky display forms, hard transitions, and strong first read |
| 90s | Console interfaces, arcade-fighter energy, chunky digital forms, darker contrast, industrial futurism, status-heavy layouts, and assertive feedback |
| 2000s | Techno, controlled comic pop art, polished gradients, compact digital ornament, sleek interfaces, signal gloss, and restrained retro-futurism |

Style pairings are encouraged when they clarify the intended surface. The
default Internal pairing is 60s primary with 70s secondary. The default
External pairing is 80s primary with 90s secondary. The default Artistic
pairing is 90s primary with 2000s secondary.

### Theme versus style

Theme is the subject and emotional world. Style is the visual method.

```text
Space-race + 70s = orbital operations expressed through dials and radial systems.
Arcade + 80s = public clarity expressed through title cards and dramatic diagonals.
Comic + 90s = expressive characters expressed through ink contours and chunky digital forms.
```

An optional rendering treatment may record the medium or finish, for example
`pixel-art`, `line-art`, `inked-comic`, `editorial-key-art`, `graphic-poster`,
`synth-grid`, `flat-illustration`, `vector`, or `3d`. It is not a fifth locked
axis and cannot redefine the selected configuration.

## 6. Fixed typography

KnowB brand and product text fonts are fixed. Variants can change scale,
weight, tracking, casing, placement, and composition, but not the functional
font family.

| Role | Font | Use |
| --- | --- | --- |
| Logo and designated display | Audiowide | KnowB wordmark, logo lockups, and limited display moments |
| Headings and navigation | Space Grotesk | Page titles, section headings, navigation, labels, and interface hierarchy |
| Body and UI text | Inter | Paragraphs, descriptions, forms, controls, helper text, and readable copy |
| Code, logs, and telemetry | JetBrains Mono | Code, command output, identifiers, timestamps, metrics, and machine content |

Art-directed lettering may be drawn into an illustration or title-card asset,
but it cannot replace functional UI text, accessibility labels, or core brand
copy.

## 7. Shared asset rules

- Favor silhouette clarity, color blocking, and a strong first read.
- Shared components may recur across products, but composition and vocabulary
  remain product-defined.
- Line art, digital illustration, geometry, and ornament must communicate
  structure or character, not hide state or hierarchy.
- Motion, CRT effects, glow, density, and dramatic framing yield to legibility,
  keyboard access, focus visibility, reduced-motion support, and WCAG 2.2 AA.

The Saber avatar system belongs to the Artistic channel and is independent of
palette. Frost is a sleek, streamlined, aerodynamic flying drone for quick and
lightweight assistance. Ember is a more stable, expressive, and complex flying
drone for control and difficult work. They share a design language while using
different forms and flight signatures. Anthro cues come from orientation,
gesture, timing, voice, movement, and personality, while both remain visibly
non-humanoid flying systems.

## 8. Configuration contract

```yaml
surface:
  channel: internal | external | artistic
  palette: autumn | gold
  theme: space-race | psychedelic | retrowave | editorial | arcade | comic
  style:
    primary: 60s | 70s | 80s | 90s | 2000s
    secondary: 60s | 70s | 80s | 90s | 2000s  # optional
  rendering_treatment: optional
  vocabulary: product-defined
```

Any asset, page, or brand surface can use this contract to receive a distinct
KnowB-compliant configuration. The configuration is a design brief, not a
permission to invent a new palette or functional type system.

## 9. Accessibility and change control

All surfaces must provide WCAG 2.2 AA contrast, keyboard access, visible focus,
semantic structure, reduced-motion support, and non-color state communication.
Use the Autumn implementation companion in
[`ORGBRAND_GUIDELINES.md`](ORGBRAND_GUIDELINES.md) for the public site's
contrast, gradient, CRT, motion, and copy acceptance rules.

New or renamed palettes, channels, themes, styles, or brand font roles require
a dated design-system decision and synchronized updates to the canonical
KnowledgeHQ document, this public companion, and the public Org Book.
