# knowb.run

The home of Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context.

## What Are Knowledge Agents?

Knowledge Agents are intelligent systems that combine three layers of knowledge:

1. **General Knowledge** — Foundation models (GPT-4o, Claude, Gemini) + web search
2. **Specialized Knowledge** — Curated KnowledgeBases with expert, domain-specific information
3. **Context & Use-Case Knowledge** — Personalization, local settings, and task-specific parameters

## Tech Stack

- **Vite** — Fast build tool and dev server
- **React** — UI framework
- **Tailwind CSS** — Utility-first styling
- **Inter** — Typography

## Installation

```bash
cd knowb-run
npm install
```

## Run Development Server

```bash
npm run dev
```

Visit `http://localhost:5173`

## Build for Production

```bash
npm run build
```

Output will be in `dist/`

## Project Structure

```
knowb-run/
├── src/
│   ├── App.jsx          # Main application component
│   ├── main.jsx         # React entry point
│   └── index.css        # Tailwind CSS imports
├── public/              # Static assets
├── index.html           # HTML template
└── README.md            # You are here
```

## Editing Content

All content is in `src/App.jsx`. The `projects` array (starting at line 14) contains the project gallery data — edit titles and descriptions there.

## License

MIT
