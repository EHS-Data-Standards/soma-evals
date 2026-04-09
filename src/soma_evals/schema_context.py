"""Extract schema context at each ablation level using SchemaView.

Uses linkml-runtime's SchemaView for programmatic access to the SOMA
LinkML schema. Produces formatted text strings suitable for inclusion
in LLM prompts.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


class AblationLevel(str, Enum):
    """The four ablation levels, each cumulative."""

    BASELINE = "baseline"
    CLASS_NAMES = "class_names"
    FULL_CLASSES = "full_classes"
    WITH_ENUMS = "with_enums"


ABLATION_LEVELS: list[AblationLevel] = [
    AblationLevel.BASELINE,
    AblationLevel.CLASS_NAMES,
    AblationLevel.FULL_CLASSES,
    AblationLevel.WITH_ENUMS,
]

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SCHEMA_DIR = _REPO_ROOT.parent / "soma" / "src" / "soma" / "schema"

_cached_sv: SchemaView | None = None
_cached_sv_path: Path | None = None


def resolve_schema_path(schema_path: str | Path | None = None) -> Path:
    """Resolve the soma.yaml schema path.

    Priority: explicit arg > ``SOMA_SCHEMA_PATH`` env var > default sibling dir.
    """
    if schema_path is not None:
        p = Path(schema_path)
    elif env := os.environ.get("SOMA_SCHEMA_PATH"):
        p = Path(env)
    else:
        p = _DEFAULT_SCHEMA_DIR

    if p.is_dir():
        p = p / "soma.yaml"
    if not p.exists():
        msg = f"Schema not found: {p}"
        raise FileNotFoundError(msg)
    return p


def get_schema_view(schema_path: str | Path | None = None) -> SchemaView:
    """Load and return a SchemaView instance, caching across calls."""
    global _cached_sv, _cached_sv_path  # noqa: PLW0603
    resolved = resolve_schema_path(schema_path)
    if _cached_sv is not None and _cached_sv_path == resolved:
        return _cached_sv
    _cached_sv = SchemaView(str(resolved))
    _cached_sv_path = resolved
    return _cached_sv


def build_schema_context(
    level: AblationLevel,
    schema_path: str | Path | None = None,
) -> str | None:
    """Build the schema context string for the given ablation level.

    Returns ``None`` for baseline (no schema context).
    """
    if level == AblationLevel.BASELINE:
        return None

    sv = get_schema_view(schema_path)

    if level == AblationLevel.CLASS_NAMES:
        return _build_class_names_context(sv)
    if level == AblationLevel.FULL_CLASSES:
        return _build_full_classes_context(sv)
    if level == AblationLevel.WITH_ENUMS:
        return _build_with_enums_context(sv)

    msg = f"Unknown ablation level: {level}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Level builders
# ---------------------------------------------------------------------------


def _format_class_header(sv: SchemaView, class_name: str) -> str:
    """Format a single class header with name, description, URI, mappings."""
    cls = sv.get_class(class_name)
    parts: list[str] = []

    label = class_name
    if cls.abstract:
        label += " (abstract)"
    parts.append(f"## {label}")

    if cls.description:
        parts.append(f"  {cls.description}")
    if cls.is_a:
        parts.append(f"  Parent: {cls.is_a}")
    if cls.class_uri:
        parts.append(f"  URI: {cls.class_uri}")
    if cls.exact_mappings:
        parts.append(f"  Mappings: {', '.join(cls.exact_mappings)}")
    if cls.examples:
        examples_str = "; ".join(str(e.value) for e in cls.examples if e.value)
        if examples_str:
            parts.append(f"  Examples: {examples_str}")
    return "\n".join(parts)


def _format_slot(slot) -> str:  # noqa: ANN001
    """Format a single induced slot as an indented description."""
    parts: list[str] = []
    sig = f"    - {slot.name}"
    if slot.range:
        sig += f" ({slot.range})"
    flags: list[str] = []
    if slot.required:
        flags.append("required")
    if slot.identifier:
        flags.append("identifier")
    if slot.multivalued:
        flags.append("multivalued")
    if slot.inlined:
        flags.append("inlined")
    if slot.inlined_as_list:
        flags.append("inlined_as_list")
    if flags:
        sig += f" [{', '.join(flags)}]"
    parts.append(sig)
    if slot.description:
        parts.append(f"      {slot.description}")
    if slot.slot_uri:
        parts.append(f"      URI: {slot.slot_uri}")
    if slot.exact_mappings:
        parts.append(f"      Mappings: {', '.join(slot.exact_mappings)}")
    return "\n".join(parts)


def _build_class_names_context(sv: SchemaView) -> str:
    """Level 2: class names, descriptions, URIs, mappings."""
    sections: list[str] = ["# SOMA Schema Classes\n"]
    for class_name in sorted(sv.all_classes()):
        sections.append(_format_class_header(sv, class_name))
    return "\n\n".join(sections)


def _build_full_classes_context(sv: SchemaView) -> str:
    """Level 3: class headers + full slot definitions."""
    sections: list[str] = ["# SOMA Schema Classes and Slots\n"]
    for class_name in sorted(sv.all_classes()):
        header = _format_class_header(sv, class_name)
        slots = sv.class_induced_slots(class_name)
        if slots:
            slot_lines = "\n".join(_format_slot(s) for s in slots)
            header += f"\n  Slots:\n{slot_lines}"
        sections.append(header)
    return "\n\n".join(sections)


def _build_with_enums_context(sv: SchemaView) -> str:
    """Level 4: full classes + all enum definitions."""
    context = _build_full_classes_context(sv)

    enum_sections: list[str] = ["\n\n# Enumerations\n"]
    for enum_name in sorted(sv.all_enums()):
        enum_def = sv.get_enum(enum_name)
        parts: list[str] = [f"## {enum_name}"]
        if enum_def.description:
            parts.append(f"  {enum_def.description}")
        if enum_def.permissible_values:
            parts.append("  Values:")
            for pv_name, pv in enum_def.permissible_values.items():
                line = f"    - {pv_name}"
                if pv.description:
                    line += f": {pv.description}"
                if pv.meaning:
                    line += f" (meaning: {pv.meaning})"
                parts.append(line)
        enum_sections.append("\n".join(parts))

    return context + "\n\n".join(enum_sections)
