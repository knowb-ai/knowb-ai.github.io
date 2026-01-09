# KnowB Autumn Brand Color & Gradient System — Agent Instruction Document

(Agentic Workflow Specification)

## Purpose

This document defines the brand color palette, gradient palette, and usage guidelines for the KnowB Autumn identity system.  
Agents using this document must generate UI code, components, styles, or visual assets strictly aligned to these specifications.

---

## 1. Brand Color Palette (Canonical Source of Truth)

The agent must use these seven base colors as the foundation for all brand styling, interface elements, gradients, and compositional rules.

### PRIMARY BRAND COLORS (CORE)

- **Autumn Fire**           — `#E14719`  
- **Deep Rust**             — `#8C2F14`  
- **Soft Ember**            — `#F7AD6A`  
- **Paper Ivory**           — `#FCF6F3`  
- **Charcoal Bark**         — `#2D140B`  
- **Muted Wood**            — `#77584F`  
- **Light Terracotta Border** — `#E9C2B3`  

These colors should never be altered, approximated, or replaced. They are the only allowed colors outside gradient definitions.

---

## 2. Gradient Palette (Generated from Core Colors)

All gradient usage must use the exact formulas below.

### 2.1 Dark / Depth Gradients

#### A. Autumn Fire → Deep Rust

```css
linear-gradient(135deg, #E14719 0%, #8C2F14 100%)
```

#### B. Deep Rust → Charcoal Bark

```css
linear-gradient(180deg, #8C2F14 0%, #2D140B 100%)
```

---

### 2.2 Warm Accent Gradients

#### A. Soft Ember → Autumn Fire

```css
linear-gradient(145deg, #F7AD6A 0%, #E14719 100%)
```

#### B. Soft Ember Glow (Atmospheric)

```css
linear-gradient(135deg, rgba(247,173,106,0.9) 0%, rgba(247,173,106,0.55) 50%, rgba(141,47,20,0.8) 100%)
```

---

### 2.3 Light / Neutral Gradients

#### A. Paper Ivory → Soft Ember

```css
linear-gradient(135deg, #FCF6F3 0%, #F7AD6A 100%)
```

#### B. Paper Ivory → Deep Rust (Subtle Edge Tint)

```css
linear-gradient(90deg, #FCF6F3 0%, #8C2F14 6%, #FCF6F3 100%)
```

---

### 2.4 Signature KnowB Autumn Gradients

#### A. KnowB Autumn Core (Warm → Deep)

```css
linear-gradient(135deg,
  #E14719 0%,
  #8C2F14 40%,
  #2D140B 100%
)
```

#### B. KnowB Autumn Vertical

```css
linear-gradient(180deg,
  #8C2F14 0%,
  #2D140B 35%,
  #E14719 100%
)
```

#### C. KnowB Autumn Memory Fade (Ivory → Ember → Rust)

```css
linear-gradient(120deg,
  #FCF6F3 0%,
  #F7AD6A 30%,
  #8C2F14 70%,
  #E9C2B3 100%
)
```

---

## 3. Shadows & Glows

Design agents must use these glow definitions when creating effects:

### Ember Glow

```css
0 0 30px rgba(247,173,106,0.35)
```

### Fire Glow

```css
0 0 25px rgba(225,71,25,0.25)
```

### Subtle Paper Shadow

```css
0 0 20px rgba(252,246,243,0.15)
```

---

## 4. Usage Rules

Agents must follow these rules at all times:

### 4.1 Backgrounds
- Use Paper Ivory (`#FCF6F3`) as the default light background.
- Charcoal Bark (`#2D140B`) allowed for dark text and depth sections.
- Dark gradients must use Autumn Fire and Deep Rust.

### 4.2 Text & Typography
- Charcoal Bark (`#2D140B`) is primary text color.
- Muted Wood (`#77584F`) may be used for secondary text or muted elements.
- Light Terracotta Border (`#E9C2B3`) used for borders and subtle accents.

### 4.3 CTAs & Interactive Elements
- Must use Autumn Fire (`#E14719`) or Soft Ember gradients.
- Hover and active states may use softened Soft Ember variants.

### 4.4 Contrast
- Ember tones must be used for emphasis only.
- Deep Rust must not be used against Charcoal Bark without gradient or spacing.

### 4.5 Color Restrictions
- No cold hues, neon colors, blues, greens, or purples allowed.
- Maintain warm, editorial, autumnal UI tone only.

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
- use blues, greens, or purples
- invent neon colors
- create high-saturation gradients outside formulas
- apply glassmorphism or cyberpunk effects
- deviate from the specified gradient formulas

This is a strict brand system, not a suggestion.

---

## 7. Success Criteria

A generated result is acceptable when:  
1. Every color used appears in the palette or gradients above.  
2. Gradients match the formulas exactly.  
3. All UI elements harmonize with the KnowB Autumn brand identity.  
4. Backgrounds and dark UI follow Charcoal Bark / Deep Rust foundations.  
5. All accents use Autumn Fire or Soft Ember.  
6. Typography remains legible with enforced contrast rules.
