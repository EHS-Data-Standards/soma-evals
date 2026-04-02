"""Assemble prompts from templates, optional schema context, and format instructions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "datasets" / "prompts"


def load_prompt_template(template_name: str = "extract") -> dict[str, Any]:
    """Load a prompt template YAML file from datasets/prompts/.

    Returns dict with keys: system, prompt, and optional schema_preamble / format_preamble.
    """
    path = _PROMPTS_DIR / f"{template_name}.yaml"
    if not path.exists():
        msg = f"Prompt template not found: {path}"
        raise FileNotFoundError(msg)
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return data


def build_prompt(
    source_text: str,
    *,
    template_name: str = "extract",
    schema_context: str | None = None,
    format_instructions: str | None = None,
) -> dict[str, str]:
    """Build a complete prompt from template + optional context.

    Args:
        source_text: the text to extract data from (paper abstract, TSV, etc.)
        template_name: which template to load from datasets/prompts/
        schema_context: schema description string (from schema_loader.schema_to_context_string)
        format_instructions: format description string (from schema_loader.excel_to_format_string)

    Returns:
        dict with 'system' and 'prompt' keys ready for the LLM adapter.
    """
    template = load_prompt_template(template_name)

    system = template.get("system", "You are a scientific data extraction assistant.")

    parts: list[str] = []

    if schema_context:
        preamble = template.get("schema_preamble", "Use the following schema to guide your extraction:")
        parts.append(preamble)
        parts.append(schema_context)
        parts.append("")

    if format_instructions:
        preamble = template.get("format_preamble", "Structure your output according to this format:")
        parts.append(preamble)
        parts.append(format_instructions)
        parts.append("")

    prompt_template = template.get("prompt", "Extract structured data from the following text:\n\n{source_text}")
    parts.append(prompt_template.format(source_text=source_text))

    return {
        "system": system,
        "prompt": "\n".join(parts),
    }


def condition_label(schema: bool, fmt: bool) -> str:
    """Return a human-readable condition label."""
    if schema and fmt:
        return "schema_and_format"
    if schema:
        return "schema_only"
    if fmt:
        return "format_only"
    return "baseline"
