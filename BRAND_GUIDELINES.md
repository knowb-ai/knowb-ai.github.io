# KnowB Brand Color & Gradient System — Agent Instruction Document

(Agentic Workflow Specification)

## Purpose

This document defines the brand color palette, gradient palette, and usage guidelines for the KnowB identity system.
Agents using this document must generate UI code, components, styles, or visual assets strictly aligned to these specifications.

---

## 1. Brand Color Palette (Canonical Source of Truth)

The agent must use these four base colors as the foundation for all brand styling, interface elements, gradients, and compositional rules.

### PRIMARY BRAND COLORS (CORE)

- **Entropy Black**      — `#0A0A0C`
- **Deep Void Purple**   — `#160028`
- **Knowledge Ember**    — `#FF5F2E`
- **Signal White**       — `#F5F5F7`

These colors should never be altered, approximated, or replaced.

---

## 2. Gradient Palette (Generated from Core Colors)

All gradient usage must use the exact formulas below.

### 2.1 Dark Gradients (Backgrounds, Hero Sections)

#### A. Entropy → Void

```css
linear-gradient(135deg, #0A0A0C 0%, #160028 100%)
```

#### B. Deep Void → Entropy Black

```css
linear-gradient(180deg, #160028 0%, #0A0A0C 100%)
```

---

### 2.2 Ember Gradients (Accents, CTAs, Highlights)

#### A. Ember → Deep Void

```css
linear-gradient(145deg, #FF5F2E 0%, #160028 100%)
```

#### B. Ember Glow (Atmospheric)

```css
linear-gradient(135deg, rgba(255,95,46,0.9) 0%, rgba(255,95,46,0.55) 50%, rgba(22,0,40,0.8) 100%)
```

#### C. Ember → White (Mixed Mode)

```css
linear-gradient(135deg, #FF5F2E 0%, #F5F5F7 100%)
```

---

### 2.3 Light Gradients (Clean / Neutral)

#### A. Signal White → Void Tint

```css
linear-gradient(135deg, #F5F5F7 0%, #160028 6%, #F5F5F7 100%)
```

#### B. Signal White → Ember

```css
linear-gradient(90deg, #F5F5F7 0%, #FF5F2E 100%)
```

---

### 2.4 Multi-Stop KnowB Signature Gradients

#### A. KnowB Signature (Dark Mode)

```css
linear-gradient(135deg,
  #0A0A0C 0%,
  #160028 40%,
  #FF5F2E 100%
)
```

#### B. KnowB Vertical Spectrum

```css
linear-gradient(180deg,
  #160028 0%,
  #0A0A0C 35%,
  #FF5F2E 100%
)
```

#### C. KnowB Noise-to-Signal

```css
linear-gradient(120deg,
  #0A0A0C 0%,
  #160028 30%,
  #FF5F2E 70%,
  #F5F5F7 100%
)
```

---

## 3. Shadows & Glows

Design agents must use these glow definitions when creating effects:

### Ember Glow

```css
0 0 30px rgba(255,95,46,0.35)
```

### Void Glow

```css
0 0 25px rgba(22,0,40,0.25)
```

### Signal White Glow

```css
0 0 25px rgba(245,245,247,0.15)
```

---

## 4. Usage Rules

Agents must follow these rules at all times:

### 4.1 Backgrounds
- Use dark gradients or Entropy Black (`#0A0A0C`) as base.
- Deep Void (`#160028`) allowed for depth sections.

### 4.2 CTAs & Interactive Elements
- Must use Ember (`#FF5F2E`) or Ember-to-Void gradients.
- Primary hover states may use softened Ember variants (lighter tints).

### 4.3 Contrast
- Ember (`#FF5F2E`) must be used against dark backgrounds.
- Void (`#160028`) must never be used against Entropy Black without gradient or spacing.

### 4.4 White Usage
- Signal White (`#F5F5F7`) reserved for:
  - typography
  - highlights
  - separators in dark mode
  - light mode backgrounds

### 4.5 Gradient Usage Intensity
- Signature gradients used only for:
  - hero sections
  - core storytelling panels
  - brand identity pages
- Ember gradients for CTAs, highlights, active states.
- Light gradients for info sections or neutral spaces.

---

## 5. Deliverables Expected From Any Agent Using This Document

Any agent using this input must output assets/code/styles that include:

### A. Tailwind / CSS variables
- Color tokens
- Gradient tokens
- Shadow tokens

### B. UI Elements
- Buttons
- Cards
- Navigation
- Hero sections
- Backgrounds
- States (hover, active, focus)

### C. Asset Exports
- SVG backgrounds
- Gradient overlays
- Shadows for modals

### D. Style Documentation
- All elements must reference this palette as final truth source.

---

## 6. Constraints

Agents must NOT:
- invent new colors
- adjust luminosity outside gradient definitions
- mix unrelated hues
- generate neon samples
- use blue or green hues (legacy palette colors)
- create gradients that deviate from the formulas above

This is a strict brand system, not a suggestion.

---

## 7. Success Criteria

A generated result is acceptable when:
1. Every color used appears in the palette or gradients above.
2. Gradients match the formulas exactly.
3. All UI elements harmonize with the KnowB brand identity.
4. Dark UI follows Entropy Black / Deep Void foundations.
5. All accents use Knowledge Ember.
6. All typography remains legible with enforced contrast rules.
