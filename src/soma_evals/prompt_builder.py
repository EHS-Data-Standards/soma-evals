"""Assemble prompts from the extract.yaml template, PDF text, and schema context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from soma_evals.schema_context import AblationLevel, build_schema_context

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_prompt_template(template_path: str | Path | None = None) -> dict[str, Any]:
    """Load the extract.yaml prompt template.

    Returns:
        dict with ``system`` and ``prompt`` keys.
    """
    path = Path(template_path) if template_path else _REPO_ROOT / "extract.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)
    return {"system": data["system"], "prompt": data["prompt"]}


def build_prompt(
    pdf_text: str,
    level: AblationLevel,
    *,
    schema_path: str | Path | None = None,
    template_path: str | Path | None = None,
) -> dict[str, str]:
    """Build the complete prompt for a given ablation level.

    Returns:
        dict with ``system`` (system message) and ``prompt`` (user message).
    """
    template = load_prompt_template(template_path)
    schema_context = build_schema_context(level, schema_path)

    parts: list[str] = []

    if schema_context:
        parts.append("## Schema Context\n")
        parts.append(schema_context)
        parts.append("")

    parts.append(template["prompt"].strip())
    parts.append("\n## Source Text\n")
    parts.append(pdf_text)

    return {
        "system": template["system"],
        "prompt": "\n".join(parts),
    }
