# knowb.run

The home of Knowledge Agents: systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context.

## What Are Knowledge Agents?

Knowledge Agents are intelligent systems that combine three layers of knowledge:

1. **General Knowledge**: Foundation models (GPT-4o, Claude, Gemini) + web search
2. **Specialized Knowledge**: Curated KnowledgeBases with expert, domain-specific information
3. **Context & Use-Case Knowledge**: Personalization, local settings, and task-specific parameters

## Tech Stack

- **Zola**: Static site generator
- **Tailwind CSS**: Via CDN with inline config for brand color tokens
- **Typography**: Audiowide, Space Grotesk, Inter, and JetBrains Mono (fixed KnowB brand system)

## Design System

The cross-axis canon is documented in [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md):
Autumn and Gold palettes, Internal, External, and Artistic channels, six
themes, five styles, fixed typography, asset rules, and the configuration
contract. The rendered reference is the [`KnowB AI Visual Design System`](/org-book/).

[`ORGBRAND_GUIDELINES.md`](ORGBRAND_GUIDELINES.md) is the Autumn-specific
implementation and WCAG companion for this public site.

## KnowB MCP connector

The KnowB MCP connector, its project registry and its releases live in the
private [`knowledgeHQ` repository](https://github.com/knowb-ai/knowledgeHQ),
under `mcp/`. This repository is the public website only. Register new projects
in knowledgeHQ, not here.

The published `knowb-org-index` 0.2.0 release stays available on this
repository's [`mcp-v0.2.0` release](https://github.com/knowb-ai/knowb-ai.github.io/releases/tag/mcp-v0.2.0)
and its tag, as history.

## Run Locally

```bash
zola serve
# Visit http://127.0.0.1:1111
```

Build for production:

```bash
zola build
# Output in public/
```

## Project Structure

```
knowb-run/
├── config.toml              # Zola configuration
├── content/
│   ├── _index.md            # Homepage content
│   ├── org-book.md          # Visual design system page
│   ├── privacy.md           # Privacy policy
│   └── terms.md             # Terms of service
├── templates/
│   ├── base.html            # Shared base template (head, fonts, Tailwind config, favicon)
│   ├── index.html           # Homepage (extends base.html)
│   ├── orgbook.html         # Brandbook (extends base.html)
│   ├── page.html            # Policy/content pages (extends base.html)
│   ├── 404.html             # Not-found page (extends page.html)
│   ├── macros.html          # Wordmark, fin stairs, pixel icons, art
│   ├── concept/             # Generated Concept Book plates (do not edit)
│   └── section.html         # Section listing (extends base.html)
├── static/
│   ├── css/
│   │   ├── global.css       # Global stylesheet (editorial and arcade layers)
│   │   └── concept-book.css # Generated, scoped Concept Book plate styles
│   ├── favicon.svg          # Brand favicon (▮▮▮, outer Autumn Fire, middle Saber Blue)
│   └── CNAME                # Custom domain config
├── design/concept-book/     # Source boards for the Org Book Concept Book
├── scripts/build_concept_book.py  # Rebuilds templates/concept/ and concept-book.css
├── .knowb/project.yml       # Repo-owned knowledge policy (knowledgeHQ only)
├── DESIGN_SYSTEM.md        # Public cross-axis visual canon
├── ORGBRAND_GUIDELINES.md  # Autumn implementation and WCAG companion
├── WARP.md
└── README.md
```

## Template Architecture

All templates extend `base.html`, which provides:
- Shared `<head>` (meta, Google Fonts, Tailwind CDN config with all brand tokens, favicon)
- Link to `static/css/global.css`: the space-age editorial layer (surfaces, type, nav, horizon) and the tailfin arcade layer (buttons, chips, cabinets, alerts, art screens, CRT pass)
- Skip-to-content accessibility link
- Tera blocks: `title`, `head_extra`, `header`, `content`, `footer`

To change styles or layout globally, edit `base.html` or `static/css/global.css`. Page-specific content lives in each template's block overrides.

## Pages

- `/`: Main homepage (use cases, roadmap, contact)
- `/org-book/`: KnowB AI Visual Design System (palettes, channels, themes, styles, type, components, a11y, Concept Book)
- `/terms/`: Terms of service
- `/privacy/`: Privacy policy

## Editing Content

All page content lives in `templates/`. The content markdown files in `content/` are structural only (front matter, no body text). Edit the HTML templates directly.

## Favicon

Three vertical bars on the Ground surface (`#161211`): outer bars in Autumn Fire
(`#FF4A1A`), middle bar in Saber Blue (`#86E8FF`). Defined in `base.html` so
every page inherits it.

## License

MIT
