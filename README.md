# knowb.run

The home of Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context.

## What Are Knowledge Agents?

Knowledge Agents are intelligent systems that combine three layers of knowledge:

1. **General Knowledge** — Foundation models (GPT-4o, Claude, Gemini) + web search
2. **Specialized Knowledge** — Curated KnowledgeBases with expert, domain-specific information
3. **Context & Use-Case Knowledge** — Personalization, local settings, and task-specific parameters

## Tech Stack

- **Zola** — Static site generator
- **Tailwind CSS** — Via CDN for styling
- **Inter** — Typography (Google Fonts)

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
│   ├── landing.md           # Landing page variant
│   └── org-book.md          # Org brandbook page
├── templates/
│   ├── index.html           # Homepage template
│   ├── landing.html         # Landing variant template
│   ├── orgbook.html         # Org brandbook template
│   ├── page.html            # Default page template
│   └── section.html         # Default section template
├── static/
│   ├── favicon.svg          # Brand favicon
│   ├── vite.svg
│   └── CNAME                # Custom domain config
├── knowledgeHQ/             # Reference docs (not part of site)
├── ORGBRAND_GUIDELINES.md
├── WARP.md
└── README.md
```

## Pages

- `/` — Main homepage (Knowledge Agents overview + projects gallery)
- `/landing/` — Alternate landing page with dark autumn palette
- `/org-book/` — KnowB AI Org Book / brandbook

## Editing Content

All page content lives in `templates/`. The content markdown files in `content/` are structural only (front matter, no body text). Edit the HTML templates directly.

## Migration Notes

This site was migrated from a plain static HTML repo to Zola. The visual design is unchanged — same CSS, same layout, same colors, same typography. Only the repo structure changed:

- `index.html` → `templates/index.html`
- `landing.html` → `templates/landing.html`
- `knowledgeHQ/orgbook.html` → `templates/orgbook.html`
- `public/` assets → `static/`
- `render.yaml` removed (replaced by Zola)
- `static/CNAME` added for `knowb.run` custom domain

## License

MIT
