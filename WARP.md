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
- **Brand System**: KnowB color palette and gradients (see BRAND_GUIDELINES.md)

### File Structure
```
.
├── index.html              # Single-page application
├── public/
│   └── favicon.svg         # KnowB brand favicon (3 vertical bars)
├── BRAND_GUIDELINES.md     # KnowB brand color system documentation
├── WARP.md                 # This file
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

1. **Static Content**: All content is hardcoded in HTML. To add/edit projects, modify the project cards directly in the HTML (lines 186-210).

2. **Section-Based Navigation**: Uses anchor links (`<a href="#section-id">`) with CSS smooth scrolling (`scroll-behavior: smooth`).

3. **Brand Color System**: Strict adherence to KnowB brand colors defined in BRAND_GUIDELINES.md:
   - **Entropy Black** (#0A0A0C) - primary background
   - **Deep Void Purple** (#160028) - depth sections
   - **Knowledge Ember** (#FF5F2E) - accents, CTAs, highlights
   - **Signal White** (#F5F5F7) - typography
   - Signature gradients for hero sections
   - Ember glows for interactive elements

4. **Tailwind-First Styling**: All styles use Tailwind utility classes with extended custom colors and gradients.

5. **CDN Dependencies**: Tailwind CSS loaded from CDN, with custom config inline (lines 11-40) including brand color tokens, gradient backgrounds, and shadow utilities.

## Editing Content

All content is in `index.html`. Common edits:
- **Projects gallery** (lines 186-210): Edit project titles and descriptions directly
- **Hero text** (lines 64-68): Main headline and tagline
- **Section content**: Edit text directly in the respective section

### Brand Color Usage
When editing, strictly follow BRAND_GUIDELINES.md. Each project card follows this structure:
```html
<div class="bg-void/50 border border-void rounded-xl p-8 hover:border-ember hover:shadow-ember-glow transition-all">
    <h3 class="text-2xl font-semibold mb-4 text-ember">Project Title</h3>
    <p class="text-signal/70 leading-relaxed">Project description</p>
</div>
```

### Favicon
The favicon (`public/favicon.svg`) uses three vertical bars [▮▮▮] in Knowledge Ember (#FF5F2E) on Entropy Black background. Do not modify without brand approval.
