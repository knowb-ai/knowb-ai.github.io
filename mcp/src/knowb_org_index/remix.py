"""Socratic, canon-aware brand and product visual-system remixing."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


AUTUMN = {
    "fire": "#FF4A1A",
    "rust": "#8E2F2A",
    "ember": "#F59A52",
    "ivory": "#FCF6F3",
    "saber": "#86E8FF",
    "bark": "#7A2217",
    "wood": "#77584F",
    "border": "#E9C2B3",
}
KENOBI = {
    "gold": "#FFD500",
    "firewatch": "#FFB300",
    "kodak": "#F7C700",
    "playmate": "#FFC61A",
    "date": "#F2C14E",
    "midnight": "#15163D",
    "indigo": "#1E2259",
    "purple": "#2D1F5B",
    "plum": "#221338",
}
INTERFACE_MODES = {"public-facing", "internal", "hybrid"}
DENSITIES = {"editorial", "balanced", "operational"}
SOURCE_PROVENANCE = [
    {
        "path": "knowledgeHQ/Knowledge Ecosystem Codex.md",
        "contract": "two canonical visual systems and place-specific usage",
    },
    {
        "path": "ORGBRAND_GUIDELINES.md",
        "contract": "KnowB Autumn palette, gradients, copy, and WCAG 2.2 AA rules",
    },
    {
        "path": "knowledgeHQ/Kenobi Product Book.md",
        "contract": "gold/yellow signal over indigo-purple depth for product interfaces",
    },
    {
        "path": "../kenobi/config.json",
        "contract": "configuration-driven light/dark semantic brand tokens",
    },
    {
        "path": "../kenobi/templates/index.html",
        "contract": "token-injected cockpit shell and explicit theme behavior",
    },
]


class RemixError(ValueError):
    """Raised when a remix brief or digest is invalid."""


def _clean(value: str) -> str:
    return " ".join(value.strip().split())


def _digest(brief: dict[str, Any]) -> str:
    canonical = json.dumps(brief, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_design_remix(
    *,
    project_name: str,
    purpose: str = "",
    audience: str = "",
    personality: str = "",
    desired_feeling: str = "",
    visual_metaphor: str = "",
    content_priority: str = "",
    interface_mode: str = "",
    density: str = "balanced",
    surfaces: list[str] | None = None,
    avoid: list[str] | None = None,
    require_complete: bool = False,
) -> dict[str, Any]:
    """Run the Socratic remix and render its governed design deliverables."""

    name = _clean(project_name)
    if not name:
        raise RemixError("project_name is required")
    if interface_mode and interface_mode not in INTERFACE_MODES:
        raise RemixError(f"interface_mode must be one of {sorted(INTERFACE_MODES)}")
    if density not in DENSITIES:
        raise RemixError(f"density must be one of {sorted(DENSITIES)}")

    normalized_surfaces = _items(surfaces)
    normalized_avoid = _items(avoid)
    brief = {
        "project_name": name,
        "purpose": _clean(purpose),
        "audience": _clean(audience),
        "personality": _clean(personality),
        "desired_feeling": _clean(desired_feeling),
        "visual_metaphor": _clean(visual_metaphor),
        "content_priority": _clean(content_priority),
        "interface_mode": interface_mode,
        "density": density,
        "surfaces": normalized_surfaces,
        "avoid": normalized_avoid,
    }
    prompts = {
        "purpose": "What useful change should this project create in the user's world?",
        "audience": "Who must recognize themselves in this product, and what do they already understand?",
        "personality": "Choose 3-5 traits that should remain true in copy, composition, and interaction.",
        "desired_feeling": "What should a person feel within the first ten seconds, and after sustained use?",
        "visual_metaphor": "What project-specific visual metaphor can carry the idea without becoming decoration?",
        "content_priority": "What information or action must dominate every important surface?",
        "interface_mode": "Is this an org/public narrative surface, an internal product interface, or a scoped hybrid?",
        "surfaces": "Which real surfaces must the six-panel gallery prove (for example landing, library, detail, mobile, campaign, tokens)?",
    }
    questions = [
        {"field": field, "question": question}
        for field, question in prompts.items()
        if not brief[field]
    ]
    if require_complete and questions:
        missing = ", ".join(item["field"] for item in questions)
        raise RemixError(f"Design remix is incomplete; answer: {missing}")

    response: dict[str, Any] = {
        "ready": not questions,
        "brief": brief,
        "questions": questions,
        "canon": _canon_summary(interface_mode),
        "source_provenance": SOURCE_PROVENANCE,
        "socratic_loop": [
            "Answer the open questions in the user's language.",
            "Review the narrative, place selection, token roles, and six proof surfaces.",
            "Change the brief, not the rendered output, when direction is wrong.",
            "Accept the digest only after the user recognizes the project in the remix.",
        ],
    }
    if questions:
        return response

    narrative = render_brand_narrative(brief)
    visual_system = render_visual_system(brief)
    gallery = build_gallery_spec(brief)
    response.update(
        {
            "remix_digest": _digest(brief),
            "brand_narrative": narrative,
            "visual_design_system": visual_system,
            "gallery": gallery,
            "compliance": _compliance(brief),
            "harness_action": {
                "type": "generate_image",
                "count": 1,
                "use_case": "ui-mockup",
                "presentation": "Return the generated image inline as the visual conclusion of /remix.",
                "prompt": gallery["image_prompt"],
            },
        }
    )
    return response


def validate_remix_digest(brief: dict[str, Any], digest: str) -> None:
    if not digest or not hmac.compare_digest(_digest(brief), digest):
        raise RemixError("remix_digest does not match the reviewed remix brief; run /remix again")
    build_design_remix(**brief, require_complete=True)


def render_remix_documents(brief: dict[str, Any], digest: str) -> tuple[str, str]:
    validate_remix_digest(brief, digest)
    return render_brand_narrative(brief), render_visual_system(brief)


def render_brand_narrative(brief: dict[str, Any]) -> str:
    place = _place_label(brief["interface_mode"])
    return f"""# Brand narrative and strategic direction

## Project truth

**{brief['project_name']} exists to {brief['purpose'].rstrip('.')}**

It is built for {brief['audience']}. The experience should feel {brief['desired_feeling']},
and its behavior and language should remain {brief['personality']}.

## Narrative spine

- **Tension:** The audience needs the outcome above without losing orientation or trust.
- **Promise:** Make `{brief['content_priority']}` unmistakably clear and actionable.
- **Proof:** Show evidence, system state, and consequences close to every important claim.
- **Memory:** Use **{brief['visual_metaphor']}** as a repeatable idea, not decorative wallpaper.

## Place in the KnowB system

{place}

This is a remix, not a new unconstrained parent brand. Project character comes from hierarchy,
rhythm, density, imagery, language, and the chosen metaphor. Canonical color roles and
accessibility constraints remain governed by KnowB AI Systems.

## Strategic direction

1. Establish a recognizable product grammar around {brief['visual_metaphor']}.
2. Prove that grammar across {', '.join(brief['surfaces'])}.
3. Keep the dominant user outcome visible: {brief['content_priority']}.
4. Measure whether the intended audience reaches useful understanding and action faster.

## Voice rules

- Lead with capability, reliability, and observable outcomes.
- Keep sentences direct and scannable; do not use hype or internal hierarchy in public copy.
- Explain what the product does before explaining its technology.
- Repeat the personality through word choice, not slogans alone: {brief['personality']}.
- Avoid these project-specific failure modes: {', '.join(brief['avoid']) or 'generic AI imagery and ornamental complexity'}.
"""


def render_visual_system(brief: dict[str, Any]) -> str:
    mode = brief["interface_mode"]
    sections = []
    if mode in {"public-facing", "hybrid"}:
        sections.append(_autumn_tokens(brief))
    if mode in {"internal", "hybrid"}:
        sections.append(_kenobi_tokens(brief))
    separation = (
        "\n## Hybrid separation rule\n\nUse the Autumn tokens on org, editorial, campaign, and public narrative surfaces. "
        "Use the Kenobi tokens inside authenticated runtime, dashboard, workflow, and product interaction surfaces. "
        "Do not blend both palettes inside one component or invent an intermediate palette.\n"
        if mode == "hybrid"
        else ""
    )
    return f"""# Visual design system

## Remix thesis

Translate **{brief['visual_metaphor']}** into a {brief['density']} system that feels
{brief['desired_feeling']}. The primary visual job is to make **{brief['content_priority']}**
easy to find, understand, and act on.

{''.join(sections)}{separation}
## Project-specific composition grammar

- **Shape:** derive frames, masks, and dividers from {brief['visual_metaphor']}; keep controls conventional.
- **Hierarchy:** one dominant idea or action per viewport; evidence and state sit immediately below it.
- **Density:** {_density_rule(brief['density'])}
- **Imagery:** use the metaphor through subject, crop, material, or lighting, never as a repeated clip-art icon.
- **Rhythm:** alternate one high-signal moment with quieter evidence-rich surfaces.
- **Type:** display type carries character; body and control type prioritize sustained readability.

## Component baseline

1. **Primary action:** one high-signal action per decision region, explicit verb, visible focus.
2. **Knowledge card:** title, provenance/state, one useful excerpt, and one clear continuation.
3. **Evidence rail:** source, confidence, recency, and status remain scannable without hover.
4. **Navigation shell:** current location and system state are always explicit.
5. **Campaign tile:** one claim, one proof, one project-specific image treatment.
6. **Token specimen:** show color roles, type hierarchy, spacing, radius, and interaction states together.

## Accessibility and governance

- Meet WCAG 2.2 AA: 4.5:1 normal text, 3:1 large text and component boundaries.
- Preserve keyboard access, visible focus, semantic landmarks, zoom/reflow, and reduced motion.
- Never encode state using color alone.
- Keep canonical hues and exact approved gradients; remix their proportion and role, not their values.
- Update the remix brief and digest when audience, metaphor, place, or product priority changes.

## Design provenance

- `knowledgeHQ/Knowledge Ecosystem Codex.md`: two-place system and place-specific usage.
- `ORGBRAND_GUIDELINES.md`: current Autumn palette, copy, gradient, and accessibility rules.
- `knowledgeHQ/Kenobi Product Book.md`: gold/yellow signal over indigo-purple product depth.
- `../kenobi/config.json` and `../kenobi/templates/index.html`: semantic token injection and explicit theme behavior.
"""


def build_gallery_spec(brief: dict[str, Any]) -> dict[str, Any]:
    requested = brief["surfaces"]
    defaults = [
        "landing page hero",
        "project library or dashboard",
        "knowledge detail and evidence view",
        "mobile workflow",
        "campaign or marketing material",
        "token and component specimen",
    ]
    panels = []
    for index in range(6):
        surface = requested[index] if index < len(requested) else defaults[index]
        panels.append(
            {
                "position": index + 1,
                "surface": surface,
                "proof": _panel_proof(surface, brief),
            }
        )
    palette = _palette_prompt(brief["interface_mode"])
    avoid = ", ".join(brief["avoid"]) or "generic AI symbolism, illegible microcopy, decorative clutter"
    panel_lines = "\n".join(
        f"Panel {panel['position']}: {panel['surface']}; {panel['proof']}"
        for panel in panels
    )
    prompt = f"""Use case: ui-mockup
Asset type: single six-panel brand gallery/contact sheet
Primary request: create one polished landscape image that distills the visual system for {brief['project_name']}
Project purpose: {brief['purpose']}
Audience: {brief['audience']}
Brand character: {brief['personality']}; should feel {brief['desired_feeling']}
Visual metaphor: {brief['visual_metaphor']}
Composition/framing: one 3-by-2 grid of six distinct, equal, carousel-like cards with consistent margins and a coherent progression; each card must read as a credible real design artifact
{panel_lines}
Color palette: {palette}
Typography: strong display hierarchy with clean readable product typography; use only the project name as prominent exact text; keep all other copy abstract or minimal to avoid garbled microtext
Lighting/mood: polished design-studio presentation, intentional material texture, high contrast, no glossy generic SaaS look
Constraints: exactly six panels in one image; preserve the correct public/internal palette scope; practical layouts; visible hierarchy; consistent tokens; no third palette; no logos except a simple text treatment of the project name; no watermark
Avoid: {avoid}
"""
    return {
        "format": "one landscape raster image",
        "layout": "3x2 six-panel carousel/contact sheet",
        "panels": panels,
        "image_prompt": prompt,
    }


def _items(values: list[str] | None) -> list[str]:
    return [item for item in dict.fromkeys(_clean(value) for value in (values or [])) if item]


def _canon_summary(mode: str) -> dict[str, Any]:
    return {
        "model": "two-place KnowB system",
        "selected_place": mode or "undecided",
        "public_org": {"name": "KnowB Autumn", "palette": AUTUMN},
        "internal_product": {"name": "Kenobi Digital Surface Canon", "palette": KENOBI},
        "remix_boundary": (
            "Remix narrative, metaphor, typography emphasis, density, composition, and imagery. "
            "Do not invent hues or collapse the two places into an ungoverned palette."
        ),
    }


def _compliance(brief: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "constrained remix",
        "interface_mode": brief["interface_mode"],
        "canonical_hues_only": True,
        "hybrid_palettes_scoped_by_surface": brief["interface_mode"] == "hybrid",
        "wcag_2_2_aa_required": True,
        "reduced_motion_required": True,
        "public_copy_rules_required": brief["interface_mode"] in {"public-facing", "hybrid"},
    }


def _place_label(mode: str) -> str:
    if mode == "public-facing":
        return "This project lives on the **KnowB Autumn public/org place** for narrative, ecosystem, and collateral surfaces."
    if mode == "internal":
        return "This project lives on the **Kenobi product place** for runtime, dashboard, workflow, and interaction surfaces."
    return (
        "This is a **scoped hybrid**: KnowB Autumn owns public narrative and collateral; "
        "Kenobi owns authenticated product and workflow surfaces."
    )


def _autumn_tokens(brief: dict[str, Any]) -> str:
    return f"""## Public/org place: KnowB Autumn

~~~css
:root, [data-kb-place="public"] {{
  --kb-bg: {AUTUMN['ivory']};
  --kb-surface: {AUTUMN['ivory']};
  --kb-text: {AUTUMN['bark']};
  --kb-muted: {AUTUMN['wood']};
  --kb-primary: {AUTUMN['rust']};
  --kb-accent: {AUTUMN['ember']};
  --kb-signal: {AUTUMN['saber']};
  --kb-border: {AUTUMN['border']};
  --kb-display: "Audiowide", sans-serif;
  --kb-heading: "Space Grotesk", system-ui, sans-serif;
  --kb-body: Inter, system-ui, sans-serif;
  --kb-mono: "JetBrains Mono", ui-monospace, monospace;
}}
~~~

Use Autumn Fire `{AUTUMN['fire']}` for display-scale energy, not normal body text.
Saber Blue is the only cool signal and should remain rare. The selected metaphor,
**{brief['visual_metaphor']}**, changes image direction and composition, not the palette.

"""


def _kenobi_tokens(brief: dict[str, Any]) -> str:
    return f"""## Internal/product place: Kenobi Digital Surface

~~~css
[data-kb-place="product"] {{
  --kb-bg: {KENOBI['midnight']};
  --kb-surface: {KENOBI['indigo']};
  --kb-surface-depth: {KENOBI['plum']};
  --kb-text: {KENOBI['gold']};
  --kb-muted: {KENOBI['date']};
  --kb-primary: {KENOBI['gold']};
  --kb-accent: {KENOBI['firewatch']};
  --kb-border: {KENOBI['purple']};
  --kb-heading: "DM Sans", system-ui, sans-serif;
  --kb-body: "DM Sans", system-ui, sans-serif;
  --kb-mono: "JetBrains Mono", ui-monospace, monospace;
}}
~~~

Yellow/gold communicates action and live signal. Indigo-midnight-purple establishes
shell, navigation, workflow, and depth. For **{brief['visual_metaphor']}**, remix panel
geometry and evidence presentation while keeping state immediate and explicit.

"""


def _density_rule(density: str) -> str:
    return {
        "editorial": "generous whitespace, paced narrative, and one proof point at a time.",
        "balanced": "clear breathing room around a compact core of evidence and action.",
        "operational": "high signal density, tight grouping, explicit state, and no hidden controls.",
    }[density]


def _palette_prompt(mode: str) -> str:
    if mode == "public-facing":
        return "KnowB Autumn only: paper ivory, deep rust, soft ember, autumn fire, bark and wood neutrals, terracotta borders, rare saber-blue signal"
    if mode == "internal":
        return "Kenobi product canon only: gold and yellow interaction signals over heavy midnight indigo, deep indigo, night purple, and dark plum depth"
    return "scoped hybrid: public/campaign cards use KnowB Autumn; authenticated product cards use Kenobi gold-on-indigo; never blend both palettes inside one card"


def _panel_proof(surface: str, brief: dict[str, Any]) -> str:
    folded = surface.casefold()
    if "landing" in folded or "hero" in folded:
        return f"prove the narrative and {brief['visual_metaphor']} with one dominant outcome"
    if "library" in folded or "dashboard" in folded:
        return f"show a usable project library with {brief['content_priority']} as the strongest hierarchy"
    if "detail" in folded or "evidence" in folded:
        return "show source, confidence, state, and a clear next action"
    if "mobile" in folded:
        return "show the same system at phone scale with obvious navigation and focus"
    if "campaign" in folded or "marketing" in folded or "poster" in folded:
        return "turn one concrete capability and one proof point into memorable collateral"
    if "token" in folded or "component" in folded:
        return "show semantic colors, type hierarchy, buttons, cards, status, and focus states"
    return f"prove this surface using the {brief['visual_metaphor']} metaphor and governed token roles"
