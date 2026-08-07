"""Deterministic, user-briefed scaffolding for new KnowB repositories."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .remix import RemixError, render_remix_documents, validate_remix_digest


_REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_VISIBILITIES = {"private", "public"}
_INTERFACE_MODES = {"internal", "public-facing", "hybrid"}
_LICENSES = {"MIT", "Proprietary"}


class ScaffoldError(ValueError):
    """Raised when a repository brief or scaffold target is invalid."""


def _clean(value: str) -> str:
    return " ".join(value.strip().split())


def _yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _brief_digest(brief: dict[str, Any]) -> str:
    canonical = json.dumps(brief, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_repository_blueprint(
    *,
    name: str,
    purpose: str = "",
    audience: str = "",
    primary_users: str = "",
    strategic_direction: str = "",
    success_criteria: str = "",
    brand_tone: str = "",
    visibility: str = "private",
    interface_mode: str = "internal",
    tech_stack: list[str] | None = None,
    license_name: str = "MIT",
    design_remix: dict[str, Any] | None = None,
    remix_digest: str = "",
    require_complete: bool = False,
) -> dict[str, Any]:
    """Create the reviewable blueprint that must precede repository creation."""

    repository_name = name.strip()
    if not _REPOSITORY_NAME.fullmatch(repository_name):
        raise ScaffoldError(
            "Repository name may contain only letters, numbers, dots, underscores, and hyphens"
        )
    if repository_name in {".", ".."} or len(repository_name) > 100:
        raise ScaffoldError("Repository name must be 1-100 characters and cannot be . or ..")
    if visibility not in _VISIBILITIES:
        raise ScaffoldError(f"visibility must be one of {sorted(_VISIBILITIES)}")
    if interface_mode not in _INTERFACE_MODES:
        raise ScaffoldError(f"interface_mode must be one of {sorted(_INTERFACE_MODES)}")
    if license_name not in _LICENSES:
        raise ScaffoldError(f"license_name must be one of {sorted(_LICENSES)}")

    normalized_stack = sorted(
        {_clean(item) for item in (tech_stack or []) if isinstance(item, str) and _clean(item)},
        key=str.casefold,
    )
    brief = {
        "name": repository_name,
        "purpose": _clean(purpose),
        "audience": _clean(audience),
        "primary_users": _clean(primary_users),
        "strategic_direction": _clean(strategic_direction),
        "success_criteria": _clean(success_criteria),
        "brand_tone": _clean(brand_tone),
        "visibility": visibility,
        "interface_mode": interface_mode,
        "tech_stack": normalized_stack,
        "license": license_name,
        "design_remix": design_remix or {},
        "remix_digest": remix_digest.strip(),
    }
    questions = []
    prompts = {
        "purpose": "What concrete problem does this repository solve?",
        "audience": "Is the output for the public, partners, builders, or the internal organization?",
        "primary_users": "Who uses or maintains the result day to day?",
        "strategic_direction": "What should this project become over the next 6-12 months?",
        "success_criteria": "What observable outcome proves the project is working?",
        "brand_tone": "Which 3-5 words should describe how this project feels and communicates?",
        "tech_stack": "Which implementation stack or documentation mode should the scaffold support?",
        "design_remix": "Run /remix with the user, review its gallery direction, then pass its brief and remix_digest.",
        "remix_digest": "Confirm the reviewed /remix result by passing its remix_digest unchanged.",
    }
    for field, prompt in prompts.items():
        if not brief[field]:
            questions.append({"field": field, "question": prompt})
    if require_complete and questions:
        missing = ", ".join(item["field"] for item in questions)
        raise ScaffoldError(f"Repository ideation is incomplete; answer: {missing}")
    if brief["design_remix"] and brief["remix_digest"]:
        try:
            validate_remix_digest(brief["design_remix"], brief["remix_digest"])
        except RemixError as exc:
            raise ScaffoldError(str(exc)) from exc
        remix = brief["design_remix"]
        linked_fields = {
            "project_name": brief["name"],
            "purpose": brief["purpose"],
            "audience": brief["audience"],
            "interface_mode": brief["interface_mode"],
        }
        mismatched = [
            field for field, expected in linked_fields.items() if remix.get(field) != expected
        ]
        if mismatched:
            raise ScaffoldError(
                "The /remix brief must match the repository brief for: "
                + ", ".join(mismatched)
            )

    result: dict[str, Any] = {
        "ready": not questions,
        "brief": brief,
        "questions": questions,
        "required_review": [
            "Confirm the brand narrative and 6-12 month strategic direction.",
            "Confirm public-facing vs internal organization interface mode.",
            "Confirm the /remix narrative, visual metaphor, gallery direction, and digest.",
            "Confirm visual tokens, accessibility stance, and component baseline.",
            "Confirm visibility, stack, license, and measurable success criteria.",
        ],
    }
    if not questions:
        files = render_repository_files(brief)
        result.update(
            {
                "blueprint_digest": _brief_digest(brief),
                "files": sorted(files),
                "brand_narrative_preview": files[
                    "docs/brand-narrative-and-strategic-direction.md"
                ],
                "visual_design_preview": files["docs/visual-design-system.md"],
            }
        )
    return result


def validate_blueprint_digest(brief: dict[str, Any], digest: str) -> None:
    expected = _brief_digest(brief)
    if not digest or not secrets_compare(expected, digest):
        raise ScaffoldError(
            "blueprint_digest does not match the completed brief; draft and review it again"
        )


def secrets_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def render_repository_files(brief: dict[str, Any]) -> dict[str, str]:
    """Render a complete initial repository from an already validated brief."""

    name = brief["name"]
    purpose = brief["purpose"]
    docs_visibility = "public" if brief["visibility"] == "public" else "local"
    try:
        narrative, visual_system = render_remix_documents(
            brief["design_remix"], brief["remix_digest"]
        )
    except (KeyError, RemixError) as exc:
        raise ScaffoldError("A complete, reviewed /remix result is required") from exc
    files = {
        "README.md": _readme(brief),
        ".gitignore": _gitignore(brief["tech_stack"]),
        "LICENSE": _license(brief["license"]),
        "CONTRIBUTING.md": _contributing(name),
        "AGENTS.md": _agents(name),
        ".knowb/project.yml": (
            "version: 1\n"
            f"id: {_yaml(name)}\n"
            f"name: {_yaml(name)}\n"
            "owner: knowb-ai\n"
            "lifecycle: incubating\n"
            "knowledge:\n"
            "  roots:\n"
            "    - path: docs\n"
            "      include: [\"**/*.md\"]\n"
            "      exclude: [\"private/**\", \"drafts/**\"]\n"
            "    - path: .\n"
            "      include: [\"README.md\", \"CONTRIBUTING.md\", \"AGENTS.md\"]\n"
            "directory:\n"
            f"  visibility: {docs_visibility}\n"
        ),
        "docs/README.md": _docs_index(brief),
        "docs/brand-narrative-and-strategic-direction.md": narrative,
        "docs/visual-design-system.md": visual_system,
        "docs/architecture/README.md": _section(
            "Architecture",
            "Record the system boundaries, primary data flows, trust boundaries, and deployment shape.",
        ),
        "docs/decisions/README.md": _section(
            "Decisions",
            "Record durable decisions as small ADR-style files: context, choice, alternatives, consequences, and date.",
        ),
        "docs/decisions/0000-decision-template.md": _decision_template(),
        "docs/research/README.md": _section(
            "Research",
            "Keep evidence, experiments, unknowns, references, and rejected approaches close to the project.",
        ),
        "docs/operations/README.md": _section(
            "Operations",
            "Document how to run, observe, recover, release, and safely retire the system.",
        ),
    }
    if not purpose:
        raise ScaffoldError("Cannot render a repository without a purpose")
    return {path: content.rstrip() + "\n" for path, content in files.items()}


def write_repository_scaffold(target: Path, files: dict[str, str]) -> None:
    """Create a brand-new local tree; never overwrite an existing path."""

    resolved_target = target.resolve()
    if resolved_target.exists():
        raise ScaffoldError(f"Local target already exists: {resolved_target}")
    resolved_target.mkdir(parents=False)
    for relative_path, content in files.items():
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ScaffoldError(f"Unsafe scaffold path: {relative_path}")
        destination = (resolved_target / relative).resolve()
        try:
            destination.relative_to(resolved_target)
        except ValueError as exc:
            raise ScaffoldError(f"Scaffold path escapes target: {relative_path}") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def _readme(brief: dict[str, Any]) -> str:
    stack = ", ".join(brief["tech_stack"])
    return f"""# {brief['name']}

{brief['purpose']}

## Direction

{brief['strategic_direction']}

## Audience

- Primary users: {brief['primary_users']}
- Audience: {brief['audience']}
- Interface mode: {brief['interface_mode']}
- Visibility: {brief['visibility']}

## Success

{brief['success_criteria']}

## Stack

{stack}

## Knowledge map

- [Brand narrative and strategic direction](docs/brand-narrative-and-strategic-direction.md)
- [Visual design system](docs/visual-design-system.md)
- [Architecture](docs/architecture/README.md)
- [Decisions](docs/decisions/README.md)
- [Research](docs/research/README.md)
- [Operations](docs/operations/README.md)

## Status

Incubating. Replace assumptions with evidence and keep the docs aligned with implementation.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before changing the project.
"""


def _docs_index(brief: dict[str, Any]) -> str:
    return f"""# {brief['name']} knowledge wiki

This is the project-owned, OKF-style living knowledge space: small Markdown files,
clear entry points, explicit decisions, and context that stays useful to humans and agents.

## Start here

1. [Brand narrative and strategic direction](brand-narrative-and-strategic-direction.md)
2. [Visual design system](visual-design-system.md)
3. [Architecture](architecture/README.md)
4. [Decisions](decisions/README.md)
5. [Research](research/README.md)
6. [Operations](operations/README.md)

## Knowledge contract

- Keep claims concise and source important assertions.
- Prefer several focused files over one unbounded document.
- Record decisions when they change constraints, APIs, data, security, or product direction.
- Update the narrative and visual system when the product direction changes.
- Never place credentials, personal data, or private scratch material in indexed docs.

Current purpose: {brief['purpose']}
"""


def _brand_strategy(brief: dict[str, Any]) -> str:
    surface = (
        "Public trust, clarity, and recognizability are product requirements."
        if brief["interface_mode"] == "public-facing"
        else "Operational clarity, scan speed, and trustworthy system state are product requirements."
    )
    return f"""# Brand narrative and strategic direction

## Core narrative

**{brief['name']} exists to {brief['purpose'].rstrip('.')} for {brief['primary_users']}.**

It belongs to KnowB AI Systems: local-first knowledge infrastructure that turns durable,
well-scoped context into useful work for people and agents. {surface}

## Audience

{brief['audience']}

## Brand promise

Deliver the value described above with a tone that is {brief['brand_tone']}.
Every claim should be legible, grounded, and proportional to what the project actually does.

## Strategic direction: next 6-12 months

{brief['strategic_direction']}

## Definition of success

{brief['success_criteria']}

## Product principles

1. **Context before automation.** Understand the user, source, constraints, and desired outcome.
2. **Local-first knowledge.** Keep project truth close to the work and explicitly scoped.
3. **Traceable outputs.** Important results should explain their source and confidence.
4. **Small coherent surfaces.** Prefer focused workflows over sprawling feature collections.
5. **Human authority.** Irreversible or external actions stay visible and confirmable.

## Narrative guardrails

- Do not overstate autonomy, certainty, privacy, or intelligence.
- Explain what the project does before explaining its technology.
- Use KnowB AI Systems as the organizational endorsement, not as visual noise.
- Revisit this document when audience, strategy, or success criteria materially change.
"""


def _visual_system(brief: dict[str, Any]) -> str:
    public = brief["interface_mode"] == "public-facing"
    if public:
        mode = "Public-facing KnowB surface"
        background = "#FCF6F3"
        surface = "#FFFFFF"
        text = "#1D1514"
        muted = "#77584F"
        primary = "#8E2F2A"
        accent = "#FF4A1A"
        signal = "#16758A"
        direction = (
            "Use warm paper-like surfaces, restrained ember emphasis, generous whitespace, "
            "and direct human language. Saber-derived blue is a rare informational signal."
        )
    else:
        mode = "Internal KnowB mission-control surface"
        background = "#0A0A0C"
        surface = "#1D1514"
        text = "#FCF6F3"
        muted = "#C9AAA0"
        primary = "#86E8FF"
        accent = "#F59A52"
        signal = "#FF5F2E"
        direction = (
            "Use dark operational surfaces, high scan speed, compact density, and explicit state. "
            "Saber Blue communicates system signal; ember communicates attention and action."
        )
    return f"""# Visual design system

## Mode

**{mode}.** {direction}

The intended tone is {brief['brand_tone']}. Visual choices must support the product purpose:
{brief['purpose']}

## Compact token system

~~~css
:root {{
  --kb-color-bg: {background};
  --kb-color-surface: {surface};
  --kb-color-text: {text};
  --kb-color-muted: {muted};
  --kb-color-primary: {primary};
  --kb-color-accent: {accent};
  --kb-color-signal: {signal};
  --kb-color-danger: #B42318;
  --kb-color-success: #18794E;

  --kb-font-display: "Space Grotesk", system-ui, sans-serif;
  --kb-font-body: Inter, system-ui, sans-serif;
  --kb-font-mono: "JetBrains Mono", ui-monospace, monospace;

  --kb-space-1: 0.25rem;
  --kb-space-2: 0.5rem;
  --kb-space-3: 0.75rem;
  --kb-space-4: 1rem;
  --kb-space-6: 1.5rem;
  --kb-space-8: 2rem;

  --kb-radius-sm: 0.25rem;
  --kb-radius-md: 0.5rem;
  --kb-shadow-focus: 0 0 0 3px color-mix(in srgb, var(--kb-color-primary) 35%, transparent);
  --kb-motion-fast: 120ms;
  --kb-motion-base: 180ms;
}}
~~~

## Component baseline

### Button

- Primary uses `--kb-color-primary`; secondary is a bordered surface action.
- Labels are verbs. Disabled state must remain readable and never rely on opacity alone.
- Focus uses `--kb-shadow-focus`; target size is at least 44×44 CSS pixels.

### Card

- One clear purpose per card: summary, action, or system state.
- Use `--kb-color-surface`, a quiet border, `--kb-radius-md`, and spacing tokens only.
- Do not stack decorative shadows or gradients without a semantic reason.

### Status badge

- Pair color with a text label and optional icon.
- Reserve success/danger for actual outcomes; use signal/accent for informational state.

### Navigation

- Current location is explicit in text and focus order.
- Public navigation prioritizes orientation; internal navigation prioritizes task switching and state.

### Form control

- Every control has a persistent label, help/error region, and visible keyboard focus.
- Validation explains recovery. Never encode failure using color alone.

## Typography

- Display: Space Grotesk, concise headings, sentence case.
- Body: Inter, 16px minimum default, 1.5 line height for prose.
- Mono: JetBrains Mono for identifiers, commands, evidence, and system state.
- Keep line length near 65-75 characters for knowledge documents and primary reading surfaces.

## Accessibility and motion

- Meet WCAG 2.2 AA contrast and interaction expectations.
- Honor `prefers-reduced-motion`; motion explains state change and is never required for comprehension.
- Test keyboard order, focus visibility, zoom/reflow, error recovery, and non-color state cues.

## Governance

Tokens are the contract. Add a token only when an existing semantic role cannot express the need.
Document intentional exceptions here and keep components visually aligned with the selected mode.
"""


def _gitignore(stack: list[str]) -> str:
    lines = [
        ".DS_Store",
        ".env",
        ".env.*",
        "!.env.example",
        ".idea/",
        ".vscode/",
        "*.log",
        "dist/",
        "build/",
        ".claude/",
        ".codex/",
    ]
    normalized = " ".join(stack).casefold()
    if any(token in normalized for token in ("python", "django", "flask", "fastapi")):
        lines.extend(["__pycache__/", "*.py[cod]", ".venv/", ".pytest_cache/", ".ruff_cache/"])
    if any(token in normalized for token in ("node", "javascript", "typescript", "react", "next", "vite")):
        lines.extend(["node_modules/", ".next/", ".nuxt/", ".turbo/", "coverage/"])
    if "rust" in normalized:
        lines.append("target/")
    if any(token in normalized for token in ("go", "golang")):
        lines.extend(["vendor/", "*.test", "coverage.out"])
    if any(token in normalized for token in ("terraform", "opentofu")):
        lines.extend([".terraform/", "*.tfstate", "*.tfstate.*"])
    return "\n".join(dict.fromkeys(lines))


def _license(license_name: str) -> str:
    year = datetime.now(UTC).year
    if license_name == "Proprietary":
        return f"""Copyright (c) {year} KnowB AI Systems. All rights reserved.

This repository and its contents are proprietary and confidential. No permission is
granted to use, copy, modify, distribute, or disclose the material without prior
written authorization from KnowB AI Systems.
"""
    return f"""MIT License

Copyright (c) {year} KnowB AI Systems

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _contributing(name: str) -> str:
    return f"""# Contributing to {name}

## Before changing code

1. Read `README.md`, `AGENTS.md`, and `docs/README.md`.
2. Link the work to a GitHub issue and state the intended outcome.
3. Create a focused branch from the default branch.
4. Keep secrets, personal data, generated state, and private scratch files out of git.

## Change discipline

- Prefer small coherent commits with meaningful messages.
- Update architecture, decisions, operations, brand, or visual docs when their contract changes.
- Validate in proportion to risk; always run the mandatory build or smoke path.
- Explain user impact and evidence in the pull request.

## Review

A change is ready when its behavior, documentation, and operational consequences agree.
"""


def _agents(name: str) -> str:
    return f"""# AGENTS.md — {name}

These instructions apply to the entire repository unless a deeper `AGENTS.md` narrows them.

## Required context

- Read `README.md` and `docs/README.md` before acting.
- Read the brand narrative, strategic direction, and visual design system before changing UI or copy.
- Check current branch, worktree state, and the linked GitHub issue.

## Working rules

- Preserve user changes and keep unrelated files out of commits.
- Keep project knowledge in `docs/`; record durable decisions in `docs/decisions/`.
- Do not add secrets, credentials, personal data, local indexes, or assistant state.
- Prefer reversible operations. Confirm external, destructive, or irreversible actions.
- Use the repository's semantic tokens and documented components for interface work.
- Update docs with code when a governed contract changes.

## Completion

- Run the mandatory build/smoke path for the changed surface.
- Review the final diff for scope, security, and documentation alignment.
- Report what changed, what was validated, and any remaining operational step.
"""


def _section(title: str, purpose: str) -> str:
    return f"""# {title}

{purpose}

Keep this index short. Add focused files and link them here as the project evolves.
"""


def _decision_template() -> str:
    return """# Decision: <short title>

- Status: proposed
- Date: YYYY-MM-DD
- Owners: <names or team>

## Context

What changed or required a durable choice?

## Decision

What are we choosing?

## Alternatives

What credible options were considered?

## Consequences

What becomes easier, harder, constrained, or intentionally deferred?
"""
