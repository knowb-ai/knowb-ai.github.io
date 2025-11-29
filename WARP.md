# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**knowb.run** is a static landing page showcasing Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context. This is a single-page static HTML site with Tailwind CSS via CDN.

## Running the Site

### Open Directly
```bash
open index.html
```

### Local Server
```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

No build step or dependencies required.

## Architecture

### Technology Stack
- **HTML**: Static single-page site
- **Styling**: Tailwind CSS 4 via CDN with Inter font family (Google Fonts)
- **JavaScript**: CSS-based smooth scrolling (no framework)

### File Structure
```
.
├── index.html       # Single-page application
├── public/          # Static assets
└── README.md
```

### Page Structure

**index.html** contains:
- **Navigation**: Smooth-scroll anchor links to page sections
- **Content Sections**: 
  - Fixed header with navigation (lines 30-40)
  - Hero section (lines 43-60)
  - "What Are Knowledge Agents" explanatory section with 3-layer knowledge model (lines 63-103)
  - "Why This Matters" section (lines 106-114)
  - "How Knowledge Agents Work" process section (lines 117-159)
  - Projects gallery with 5 hardcoded projects (lines 162-194)
  - Footer with contact info (lines 197-208)

### Key Design Patterns

1. **Static Content**: All content is hardcoded in HTML. To add/edit projects, modify the project cards directly in the HTML (lines 167-193).

2. **Section-Based Navigation**: Uses anchor links (`<a href="#section-id">`) with CSS smooth scrolling (`scroll-behavior: smooth`).

3. **Tailwind-First Styling**: All styles use Tailwind utility classes with a dark theme (gray-950 background, gray-100 text).

4. **CDN Dependencies**: Tailwind CSS loaded from CDN, with custom config inline (lines 10-21).

## Editing Content

All content is in `index.html`. Common edits:
- **Projects gallery** (lines 167-193): Edit project titles and descriptions directly
- **Hero text** (lines 45-49): Main headline and tagline
- **Section content**: Edit text directly in the respective section

Each project card follows this structure:
```html
<div class="bg-gray-900 border border-gray-800 rounded-xl p-8 hover:border-gray-600 transition-all hover:shadow-xl hover:shadow-gray-900/50">
    <h3 class="text-2xl font-semibold mb-4">Project Title</h3>
    <p class="text-gray-400 leading-relaxed">Project description</p>
</div>
```
