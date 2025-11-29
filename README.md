# knowb.run

The home of Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context.

## What Are Knowledge Agents?

Knowledge Agents are intelligent systems that combine three layers of knowledge:

1. **General Knowledge** — Foundation models (GPT-4o, Claude, Gemini) + web search
2. **Specialized Knowledge** — Curated KnowledgeBases with expert, domain-specific information
3. **Context & Use-Case Knowledge** — Personalization, local settings, and task-specific parameters

## Tech Stack

- **HTML** — Static markup
- **Tailwind CSS** — Via CDN for styling
- **Inter** — Typography (Google Fonts)

## No Build Required

This is a static HTML site with no build step or dependencies.

## Run Locally

Just open `index.html` in your browser:

```bash
open index.html
```

Or use any static server:

```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Project Structure

```
knowb-run/
├── public/              # Static assets
├── index.html           # Main HTML file
└── README.md            # You are here
```

## Editing Content

All content is in `index.html`. The projects gallery is around line 167-193 — edit project titles and descriptions directly in the HTML.

## License

MIT
