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

## Local Organization Index

This repository also contains a local-first MCP directory and GitHub work control
plane under `mcp/`. It is operationally separate from the Zola site: the current
public routes and build remain unchanged.

The server discovers explicitly allowlisted local `knowb-ai` clones, indexes only
their approved knowledge roots, and exposes project context through local stdio.
Brandbook/Org Book sources remain public web pages but are denied from this local
knowledge index. GitHub ticket and Projects operations use a separate boundary;
writes require a preview plus confirmation and are audited locally.

The same MCP can guide creation of new public or private `knowb-ai` repositories. It
requires a reviewed product/brand brief before confirmation, then initializes the repo
with contribution and agent guidance plus a project-owned knowledge wiki. Every new
wiki begins with brand narrative and strategic direction, a compact visual token and
component system adapted to public or internal use, and architecture, decision,
research, and operations sections. New repositories also receive a project passport,
portable MCP client example, and MCP-first validation guide so they can map approved
KnowledgeHQ decisions, boundaries, constraints, and direction into local work.

Registration remains explicit: the passport makes a repository a discovery candidate,
but an owner or operator must enable its local clone in the private KnowledgeHQ
registry before it is indexed. Private registry contents and proprietary documents are
never copied into the new repository.

The private [`knowledgeHQ` repository](https://github.com/knowb-ai/knowledgeHQ) is the canonical wiki for KnowB AI Systems. It contains the MCP Atlas design-asset vault decision, product and runtime strategy, operator architecture, and preservation research. Its contents are not part of this public site.

Clone the private wiki separately with GitHub access, for example:
`git clone https://github.com/knowb-ai/knowledgeHQ.git ../knowledgeHQ`. The MCP and
local knowledge index use that separate `knowledgeHQ/` checkout; this public
repository has no submodule or copy of the private files.

The `remix` MCP tool provides the preceding Socratic design loop. It keeps public/org
surfaces in the KnowB Autumn system and product/workflow surfaces in the Kenobi
gold-on-indigo system, then remixes narrative, metaphor, hierarchy, density, and imagery
for the specific project. Its accepted digest drives the generated project docs and its
gallery brief lets an image-capable host return one six-panel design contact sheet.

See [`mcp/README.md`](mcp/README.md) for setup, tools, privacy boundaries, and the
project manifest contract.

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
│   └── section.html         # Section listing (extends base.html)
├── static/
│   ├── css/
│   │   └── global.css       # Global stylesheet (all component styles)
│   ├── favicon.svg          # Brand favicon (▮▮▮, outer Autumn Fire, middle Saber Blue)
│   └── CNAME                # Custom domain config
├── mcp/                     # Local MCP org directory and ticket control plane
├── config/                  # Example local registry, client config, manifest schema
├── .knowb/project.yml       # Repo-owned knowledge policy (knowledgeHQ only)
├── DESIGN_SYSTEM.md        # Public cross-axis visual canon
├── ORGBRAND_GUIDELINES.md  # Autumn implementation and WCAG companion
├── WARP.md
└── README.md
```

## Template Architecture

All templates extend `base.html`, which provides:
- Shared `<head>` (meta, Google Fonts, Tailwind CDN config with all brand tokens, favicon)
- Link to `static/css/global.css` (all component styles in one place)
- Skip-to-content accessibility link
- Tera blocks: `title`, `head_extra`, `header`, `content`, `footer`

To change styles or layout globally, edit `base.html` or `static/css/global.css`. Page-specific content lives in each template's block overrides.

## Pages

- `/`: Main homepage (use cases, roadmap, contact)
- `/org-book/`: KnowB AI Visual Design System (palettes, channels, themes, styles, type, components, a11y)
- `/terms/`: Terms of service
- `/privacy/`: Privacy policy

## Editing Content

All page content lives in `templates/`. The content markdown files in `content/` are structural only (front matter, no body text). Edit the HTML templates directly.

## Favicon

Three vertical bars on Charcoal Bark (`#7A2217`): outer bars in Autumn Fire
(`#FF4A1A`), middle bar in Saber Blue (`#86E8FF`). Defined in `base.html` so
every page inherits it.

## License

MIT
