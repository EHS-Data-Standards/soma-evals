"""Orchestrate schema-ablation eval runs across models and levels."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import yaml

from soma_evals.llm_adapter import LLMLibraryAdapter
from soma_evals.pdf_utils import extract_pdf_text
from soma_evals.prompt_builder import build_prompt
from soma_evals.schema_context import ABLATION_LEVELS, AblationLevel

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RESULTS_DIR = _REPO_ROOT / "results"
_MODELS_YAML = _REPO_ROOT / "models.yaml"


def sanitize_model_name(model: str) -> str:
    """Convert model name to filesystem-safe directory name.

    ``cborg/claude-sonnet-4-6`` becomes ``cborg--claude-sonnet-4-6``.
    """
    return model.replace("/", "--")


def load_models(
    tier: str | None = None,
    models_path: str | Path | None = None,
) -> list[str]:
    """Load model list from models.yaml.

    If *tier* is given, load from ``tiers.<tier>``; otherwise from ``models``.
    """
    path = Path(models_path) if models_path else _MODELS_YAML
    with path.open() as f:
        data = yaml.safe_load(f)

    if tier:
        models: list[str] = data["tiers"][tier]
    else:
        models = data["models"]
    return models


def parse_llm_output(raw: str) -> str:
    """Strip markdown fences from LLM output, return cleaned text."""
    stripped = raw.strip()
    stripped = re.sub(r"^```(?:ya?ml)?\s*\n", "", stripped)
    stripped = re.sub(r"\n```\s*$", "", stripped)
    return stripped.strip()


def run_single(
    model: str,
    level: AblationLevel,
    pdf_path: str | Path,
    paper_slug: str,
    *,
    pdf_text: str | None = None,
    schema_path: str | Path | None = None,
    template_path: str | Path | None = None,
    results_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run a single extraction: one model, one level, one paper.

    Returns metadata dict with model, level, status, tokens, timing.
    """
    out_dir = Path(results_dir) if results_dir else _RESULTS_DIR
    model_dir = sanitize_model_name(model)
    output_path = out_dir / level.value / model_dir / f"{paper_slug}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    meta: dict[str, Any] = {
        "model": model,
        "model_dir": model_dir,
        "output_file": f"{model_dir}/{paper_slug}.yaml",
        "timestamp": timestamp,
    }

    try:
        if pdf_text is None:
            pdf_text = extract_pdf_text(str(pdf_path))

        prompt = build_prompt(
            pdf_text,
            level,
            schema_path=schema_path,
            template_path=template_path,
        )

        click.echo(f"  [{model}] sending prompt ({len(prompt['prompt'])} chars)...")
        adapter = LLMLibraryAdapter(model_name=model, system_prompt=prompt["system"])
        adapter.add_message(prompt["prompt"])

        t0 = time.monotonic()
        raw = adapter.generate()
        duration_ms = int((time.monotonic() - t0) * 1000)

        cleaned = parse_llm_output(raw)
        output_path.write_text(cleaned + "\n")

        tokens = adapter.get_token_usage()
        meta.update(
            {
                "status": "success",
                "input_tokens": tokens.get("input_tokens"),
                "output_tokens": tokens.get("output_tokens"),
                "duration_ms": duration_ms,
            }
        )
        click.echo(
            f"  [{model}] done in {duration_ms}ms "
            f"(in={tokens.get('input_tokens')}, out={tokens.get('output_tokens')})"
        )
    except Exception as exc:  # noqa: BLE001
        meta.update({"status": "error", "error_message": str(exc)})
        click.echo(f"  [{model}] ERROR: {exc}")

    return meta


def run_level(
    level: AblationLevel,
    models: list[str],
    pdf_path: str | Path,
    paper_slug: str,
    *,
    schema_path: str | Path | None = None,
    template_path: str | Path | None = None,
    results_dir: str | Path | None = None,
) -> None:
    """Run all models for a single ablation level and write run_metadata.yaml."""
    out_dir = Path(results_dir) if results_dir else _RESULTS_DIR

    click.echo(f"\n=== Level: {level.value} ===")

    # Extract PDF once for all models
    pdf_text = extract_pdf_text(str(pdf_path))

    runs: list[dict[str, Any]] = []
    for model in models:
        meta = run_single(
            model,
            level,
            pdf_path,
            paper_slug,
            pdf_text=pdf_text,
            schema_path=schema_path,
            template_path=template_path,
            results_dir=results_dir,
        )
        runs.append(meta)

    # Write run metadata
    metadata = {
        "level": level.value,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "paper_slug": paper_slug,
        "pdf_path": str(pdf_path),
        "runs": runs,
    }
    meta_path = out_dir / level.value / "run_metadata.yaml"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    click.echo(f"  Metadata written to {meta_path}")


def run_all_levels(
    models: list[str],
    pdf_path: str | Path,
    paper_slug: str,
    *,
    schema_path: str | Path | None = None,
    template_path: str | Path | None = None,
    results_dir: str | Path | None = None,
) -> None:
    """Run all ablation levels for all models."""
    for level in ABLATION_LEVELS:
        run_level(
            level,
            models,
            pdf_path,
            paper_slug,
            schema_path=schema_path,
            template_path=template_path,
            results_dir=results_dir,
        )
