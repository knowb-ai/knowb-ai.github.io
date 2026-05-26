# knowb.run

The home of Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context.

## What Are Knowledge Agents?

Knowledge Agents are intelligent systems that combine three layers of knowledge:

1. **General Knowledge** — Foundation models (GPT-4o, Claude, Gemini) + web search
2. **Specialized Knowledge** — Curated KnowledgeBases with expert, domain-specific information
3. **Context & Use-Case Knowledge** — Personalization, local settings, and task-specific parameters

## Tech Stack

- **Zola** — Static site generator
- **Tailwind CSS** — Via CDN with inline config for brand color tokens
- **Typography** — Audiowide, Space Grotesk, Inter, Press Start 2P, JetBrains Mono (Google Fonts)

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
│   ├── org-book.md          # Org brandbook page
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
│   ├── favicon.svg          # Brand favicon (▮▮▮ — outer ember, middle saber blue)
│   ├── vite.svg
│   └── CNAME                # Custom domain config
├── knowledgeHQ/             # Reference docs (not part of site)
├── ORGBRAND_GUIDELINES.md
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

- `/` — Main homepage (use cases, roadmap, contact)
- `/org-book/` — KnowB AI Brandbook (colors, type, components, a11y)
- `/terms/` — Terms of service
- `/privacy/` — Privacy policy

## Editing Content

All page content lives in `templates/`. The content markdown files in `content/` are structural only (front matter, no body text). Edit the HTML templates directly.

## Favicon

Three vertical bars on Entropy Black (`#0A0A0C`): outer bars in Knowledge Ember (`#FF5F2E`), middle bar in Saber Blue (`#86E8FF`). Defined in `base.html` so every page inherits it.

## License

MIT
