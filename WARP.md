# knowb.run Repository Guide

This repository contains the public KnowB AI website, its rendered visual
design Org Book, and the public local MCP directory implementation.

## Running the site

```bash
zola serve
# Visit http://127.0.0.1:1111
```

Build for production:

```bash
zola build
# Output in public/
```

The `public/` directory is generated and ignored by Git. GitHub Pages builds
it from the repository source through `.github/workflows/deploy.yml`.

## Design system source of truth

- [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) defines the public cross-axis canon:
  Autumn and Gold palettes, Internal, External, and Artistic channels, six
  themes, five styles, fixed typography, asset rules, and configuration.
- [`ORGBRAND_GUIDELINES.md`](ORGBRAND_GUIDELINES.md) defines the Autumn
  implementation, WCAG 2.2 AA, gradient, CRT, motion, and copy rules.
- `/org-book/` is the rendered visual design system reference generated from
  `content/org-book.md` and `templates/orgbook.html`.
- The shared Pop-out Player is a persistent side surface for media, curated
  agent status, or contextual assistant UI; its visual contract belongs in the
  design-system companion and the rendered Org Book.

Use the design axes explicitly when adding a page or asset:

```text
surface or asset = channel + palette + theme + style + product vocabulary
```

Brand and product text is restricted to Audiowide, Space Grotesk, Inter, and
JetBrains Mono. Art-directed lettering is allowed inside an illustration but
cannot replace functional UI text or accessibility labels.

## Architecture

- `config.toml` configures the Zola site.
- `content/` contains page front matter and route structure.
- `templates/base.html` owns shared head metadata, fixed font loading, palette
  tokens, Tailwind extensions, and accessibility scaffolding.
- `templates/index.html` is the public home page.
- `templates/orgbook.html` renders the complete visual design reference.
- `templates/page.html` renders policy and content pages.
- `static/css/global.css` contains shared component and motion styles.
- `static/favicon.svg` uses canonical Autumn and Saber tokens.
- `mcp/` is the separate local-first organization directory and GitHub work
  control plane. See [`mcp/README.md`](mcp/README.md).

## Editing rules

Keep the site static-first and preserve the existing Zola architecture. Use
shared semantic tokens and the fixed font roles. Product vocabulary may vary,
but new palettes, channels, themes, styles, or functional fonts require a
dated design-system decision and synchronized documentation.

All interactive controls need keyboard access and visible focus. Long pages
need skip navigation and semantic landmarks. Motion and CRT treatments must
respect `prefers-reduced-motion` and never reduce legibility.

Before handoff, run `zola build` and inspect `git diff --check`. Do not commit
generated `public/` output.
