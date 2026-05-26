# KnowB Autumn Brand + Accessibility System (WCAG 2.2 AA)
## Purpose
This document is the canonical style and accessibility source of truth for KnowB Autumn interfaces.
All UI implementations must satisfy both:
- Brand consistency (palette, gradients, tone)
- WCAG 2.2 AA accessibility requirements

## 1) Canonical Base Palette
Only these seven base colors are allowed for UI color tokens:
- **Autumn Fire**: `#FF4A1A`
- **Deep Rust**: `#8E2F2A`
- **Soft Ember**: `#F59A52`
- **Paper Ivory**: `#FCF6F3`
- **Charcoal Bark**: `#7A2217` (burnt rust base)
- **Muted Wood**: `#77584F`
- **Light Terracotta Border**: `#E9C2B3`

Notes:
- Opacity variants of the seven colors are allowed.
- New hues are not allowed.
- No blues, greens, purples, or neon colors.

## 2) Canonical Gradients
All gradient usage must match these formulas exactly.

### 2.1 Dark / Depth
```css
linear-gradient(135deg, #FF4A1A 0%, #8E2F2A 100%)
linear-gradient(180deg, #8E2F2A 0%, #7A2217 100%)
```

### 2.2 Warm Accent
```css
linear-gradient(145deg, #F59A52 0%, #FF4A1A 100%)
linear-gradient(135deg, rgba(255,74,26,0.88) 0%, rgba(245,154,82,0.58) 34%, rgba(142,47,42,0.84) 100%)
```

### 2.3 Light / Neutral
```css
linear-gradient(135deg, #FCF6F3 0%, #F59A52 100%)
linear-gradient(90deg, #FCF6F3 0%, #8E2F2A 6%, #FCF6F3 100%)
```

### 2.4 Signature
```css
linear-gradient(135deg, #FF4A1A 0%, #8E2F2A 40%, #7A2217 100%)
linear-gradient(180deg, #8E2F2A 0%, #7A2217 35%, #FF4A1A 100%)
linear-gradient(120deg, #FCF6F3 0%, #F59A52 30%, #8E2F2A 70%, #E9C2B3 100%)
```

## 3) Canonical Shadow / Glow Tokens
```css
0 0 30px rgba(245,154,82,0.35) /* ember glow */
0 0 25px rgba(255,74,26,0.30)  /* fire glow */
0 0 20px rgba(252,246,243,0.15) /* paper shadow */
```

## 4) Accessibility Requirements (Mandatory)
All pages and components must meet WCAG 2.2 AA:
- Normal text contrast: **>= 4.5:1**
- Large text contrast (24px regular or 18.66px bold+): **>= 3:1**
- UI component boundaries/focus indicators: **>= 3:1** where applicable
- Full keyboard accessibility for controls
- Visible focus style for all interactive elements
- Respect reduced motion via `prefers-reduced-motion`

## 5) Approved Contrast Pairings
Use these as defaults for body text and controls:
- `#7A2217` on `#FCF6F3`
- `#77584F` on `#FCF6F3`
- `#FCF6F3` on `#8E2F2A`
- `#FCF6F3` on `#7A2217`
- `#7A2217` on `#F59A52`
- `#E9C2B3` on `#7A2217`

## 6) Prohibited / Restricted Pairings
Do not use for normal body text:
- `#FF4A1A` on `#FCF6F3`
- `#FCF6F3` on `#FF4A1A`
- `#7A2217` on `#FF4A1A`

Allowed exception:
- `#FF4A1A` may be used for **large display text** that still meets the 3:1 large-text requirement.

## 7) Component Rules
### 7.1 Surfaces
- Default light surface: `#FCF6F3`
- Default dark surface: `#7A2217`
- Borders/separators: `#E9C2B3` (or opacity variants with preserved perceptibility)

### 7.2 Typography
- Primary body text: `#7A2217` on light surfaces
- Secondary text: `#77584F` on light surfaces
- On dark surfaces, use `#FCF6F3` (primary) and `#E9C2B3` (secondary)

### 7.3 Buttons and Interactive Controls
- Prefer high-contrast combinations from Section 5
- Avoid Autumn Fire as a small-text button background unless contrast is verified
- Every interactive element must have a clear focus-visible state

### 7.4 Links
- Must be visually identifiable and keyboard focusable
- Placeholder `href="#"` links are not allowed in production templates

## 8) Motion and Navigation Rules
- Include a skip-to-content link on long pages with persistent nav/toolbars
- Use semantic landmarks (`<main>`, properly structured headings)
- Disable/soften motion under `prefers-reduced-motion`

## 9) Implementation Constraints
Agents must not:
- invent extra palette colors
- deviate from canonical gradients
- ship UI that fails AA contrast on normal body text
- remove keyboard/focus accessibility behavior

## 10) Acceptance Checklist
A change is compliant only if:
1. All colors are from the seven-token palette (or opacity variants).
2. Gradients are exact canonical formulas.
3. All normal text and controls meet WCAG 2.2 AA contrast.
4. Focus-visible, keyboard navigation, and reduced-motion support are present.
5. Brand tone remains warm, structured, and signal-forward.

## 11) Agentic Brand Work Guidelines
All public-facing agentic product copy must follow these rules:
- Position work around capabilities, reliability, and measurable outcomes.
- Use subtle ecosystem amplification language. Do not directly name sister brands or external partner brands in core landing-page messaging.
- Avoid internal hierarchy labels in public copy.
- Keep claims concrete and operational. Prefer specifics over hype.
- Use privacy-safe language when describing data collection, crawling, or reporting features.

### 11.1 Writing Style Rules
- Do not use em dash characters (U+2014) in copy.
- Use commas, semicolons, colons, or short sentences instead.
- Keep sentence structure direct and scannable.
- Maintain consistent product naming, capitalization, and punctuation across pages and docs.
