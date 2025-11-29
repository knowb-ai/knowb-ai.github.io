# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**knowb.run** is a landing page showcasing Knowledge Agents — systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context. This is a single-page React application built with Vite, Tailwind CSS, and React 19.

## Development Commands

### Setup
```bash
npm install
```

### Development Server
```bash
npm run dev
```
Runs the Vite dev server at `http://localhost:5173` with hot module reloading.

### Build
```bash
npm run build
```
Builds production assets to the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```
Serves the production build locally for testing.

### Linting
```bash
npm run lint
```
Runs ESLint to check for code quality issues. The project uses the recommended ESLint configs for React hooks and React Refresh.

## Architecture

### Technology Stack
- **Build Tool**: Vite 7 with React plugin
- **UI Framework**: React 19 (with StrictMode enabled)
- **Styling**: Tailwind CSS 4 with Inter font family
- **Linting**: ESLint 9 with React-specific plugins

### File Structure
```
src/
├── App.jsx          # Main single-page application component
├── main.jsx         # React entry point with StrictMode wrapper
└── index.css        # Tailwind imports and Google Fonts (Inter)
```

### Component Architecture

**App.jsx** is a self-contained single-page application with:
- **State Management**: Single `activeSection` state for navigation tracking
- **Navigation**: Smooth-scroll implementation using `scrollToSection` function
- **Content Structure**: 
  - Fixed header with navigation
  - Hero section
  - "What Are Knowledge Agents" explanatory section (3-layer knowledge model)
  - "How Knowledge Agents Work" process section
  - Projects gallery (data-driven from `projects` array starting at line 14)
  - Footer with contact info

### Key Design Patterns

1. **Content-Driven Gallery**: The projects showcase is rendered from the `projects` array. To add/edit projects, modify this array in `App.jsx` (line 14).

2. **Section-Based Navigation**: Uses smooth scrolling and element IDs for single-page navigation without routing libraries.

3. **Tailwind-First Styling**: All styles are utility classes with a dark theme (gray-950 background, gray-100 text).

4. **No External Routing**: Navigation is handled via scroll behavior, not React Router or similar.

## Editing Content

All visible content lives in `src/App.jsx`. The most commonly edited section is the `projects` array (line 14), which controls the project gallery cards. Each project has:
- `title`: Project name
- `description`: Short description text

## Configuration Files

- **eslint.config.js**: ESLint 9 flat config with React Hooks and React Refresh plugins. Ignores the `dist/` folder and allows unused vars matching `^[A-Z_]`.
- **tailwind.config.js**: Tailwind configuration extending the default theme with Inter font family.
- **vite.config.js**: Minimal Vite setup with React plugin only.
- **postcss.config.js**: PostCSS setup for Tailwind CSS processing.

## Build Output

Production builds output to `dist/` and are ignored by git (via `.gitignore`).
