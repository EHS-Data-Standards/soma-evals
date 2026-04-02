"""Main eval orchestrator: run extraction tasks across the eval matrix.

Usage:
    # Single case
    uv run python -m soma_evals.runner --case ciliary_function --model gpt-4o-mini

    # Full matrix
    uv run python -m soma_evals.runner --full --cheap

    # Verify auth
    uv run python -m soma_evals.runner --verify-auth
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from typing import Any

import click
import yaml

from soma_evals.llm_adapter import LLMLibraryAdapter
from soma_evals.pricing import estimate_cost
from soma_evals.prompt_builder import build_prompt, condition_label
from soma_evals.schema_loader import excel_to_format_string, schema_to_context_string
from soma_evals.scoring import flatten_yaml_to_slots, score_slots, score_values

HERE = Path(__file__).parent
CASES_DIR = HERE.parent.parent / "datasets" / "cases"
RESULTS_DIR = HERE.parent.parent / "datasets" / "results"
MODELS_YAML = HERE.parent.parent / "datasets" / "models.yaml"


def _load_models_yaml() -> dict[str, Any]:
    with open(MODELS_YAML) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return data


def _load_tier(tier_name: str) -> list[str]:
    data = _load_models_yaml()
    tiers = data.get("tiers", {})
    return list(tiers.get(tier_name, []))


def load_case(case_name: str) -> dict[str, Any]:
    """Load an eval case YAML from datasets/cases/."""
    path = CASES_DIR / f"{case_name}.yaml"
    if not path.exists():
        msg = f"Case not found: {path}"
        raise FileNotFoundError(msg)
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return data


def _parse_llm_output(raw: str) -> dict[str, Any]:
    """Parse LLM output as YAML (stripping markdown fences if present)."""
    cleaned = re.sub(r"^```(?:yaml|json)?\s*\n?|\n?```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = yaml.safe_load(cleaned) or {}
        if not isinstance(parsed, dict):
            return {"_raw": cleaned, "_parse_error": True}
        return parsed
    except yaml.YAMLError:
        return {"_raw": cleaned, "_parse_error": True}


def run_one(
    case_name: str,
    model: str,
    *,
    use_schema: bool,
    use_format: bool,
    schema_classes: list[str] | None = None,
    excel_sheets: list[str] | None = None,
) -> dict[str, Any]:
    """Run a single extraction eval.

    Returns a result dict with scores, tokens, timing, cost.
    """
    case = load_case(case_name)
    source_text = case.get("source_text", "")
    source_pdf = case.get("source_pdf")
    ground_truth_path = CASES_DIR.parent / case["ground_truth"]
    relevant_classes = case.get("relevant_classes", schema_classes)
    relevant_sheets = case.get("relevant_sheets", excel_sheets)

    # Resolve PDF path relative to datasets/ directory
    pdf_paths: list[str] = []
    if source_pdf:
        pdf_path = CASES_DIR.parent / source_pdf
        if not pdf_path.exists():
            pdf_path = Path(source_pdf)  # try as absolute path
        if not pdf_path.exists():
            msg = f"PDF not found: {source_pdf}"
            raise FileNotFoundError(msg)
        pdf_paths.append(str(pdf_path.resolve()))
        if not source_text:
            source_text = f"[See attached PDF: {pdf_path.name}]"

    # Load ground truth
    with open(ground_truth_path) as f:
        ground_truth: dict[str, Any] = yaml.safe_load(f) or {}

    # Build context
    schema_context = schema_to_context_string(classes=relevant_classes) if use_schema else None
    format_instructions = excel_to_format_string(sheets=relevant_sheets) if use_format else None

    prompt_data = build_prompt(
        source_text=source_text,
        schema_context=schema_context,
        format_instructions=format_instructions,
    )

    # Run LLM
    adapter = LLMLibraryAdapter(model_name=model, system_prompt=prompt_data["system"])
    adapter.add_message(prompt_data["prompt"], pdf_files=pdf_paths if pdf_paths else None)

    t0 = time.time()
    raw_response = adapter.generate()
    elapsed = round(time.time() - t0, 2)

    usage = adapter.get_token_usage()
    est_cost = estimate_cost(model, usage["input_tokens"], usage["output_tokens"])

    # Parse and score
    parsed = _parse_llm_output(raw_response)
    condition = condition_label(use_schema, use_format)

    flat_predicted = flatten_yaml_to_slots(parsed) if not parsed.get("_parse_error") else {}
    flat_expected = flatten_yaml_to_slots(ground_truth)

    slot_scores = score_slots(flat_predicted, flat_expected)
    value_scores = score_values(flat_predicted, flat_expected)

    return {
        "case": case_name,
        "model": model,
        "condition": condition,
        "use_schema": use_schema,
        "use_format": use_format,
        "elapsed_seconds": elapsed,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "est_cost_usd": round(est_cost, 6) if est_cost is not None else None,
        "slot_scores": slot_scores,
        "value_scores": {k: v for k, v in value_scores.items() if k != "details"},
        "parse_error": parsed.get("_parse_error", False),
        "raw_response_preview": raw_response[:500],
    }


def run_matrix(
    cases: list[str],
    models: list[str],
    conditions: list[tuple[bool, bool]] | None = None,
) -> list[dict[str, Any]]:
    """Run the full eval matrix: cases x models x conditions.

    Args:
        cases: list of case names
        models: list of model names
        conditions: list of (use_schema, use_format) tuples.
                    Default: all 4 combinations.
    """
    if conditions is None:
        conditions = [
            (False, False),  # baseline
            (True, False),  # schema_only
            (False, True),  # format_only
            (True, True),  # schema_and_format
        ]

    total = len(cases) * len(models) * len(conditions)
    click.echo(f"Running {len(cases)} cases x {len(models)} models x {len(conditions)} conditions = {total} calls")

    results: list[dict[str, Any]] = []
    for i, (case, model, (use_schema, use_format)) in enumerate(
        ((c, m, cond) for c in cases for m in models for cond in conditions),
        1,
    ):
        cond_label = condition_label(use_schema, use_format)
        model_short = model.split("/")[-1][:20]
        click.echo(f"  [{i:>3d}/{total}] {case} | {model_short:<20s} | {cond_label}")

        try:
            result = run_one(
                case,
                model,
                use_schema=use_schema,
                use_format=use_format,
            )
            s = result["slot_scores"]
            cost_str = f"${result['est_cost_usd']:.4f}" if result["est_cost_usd"] else "n/a"
            click.echo(
                f"           P={s['precision']:.3f} R={s['recall']:.3f} F1={s['f1']:.3f}"
                f"  {result['elapsed_seconds']}s  {cost_str}"
            )
            results.append(result)
        except Exception as e:
            click.echo(f"           ERROR: {e}", err=True)
            results.append(
                {
                    "case": case,
                    "model": model,
                    "condition": cond_label,
                    "status": "error",
                    "error": str(e),
                }
            )

    return results


def save_results(results: list[dict[str, Any]], label: str = "") -> Path:
    """Save results to a timestamped YAML file in datasets/results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    slug = f"_{label}" if label else ""
    path = RESULTS_DIR / f"eval{slug}_{timestamp}.yaml"
    with open(path, "w") as f:
        yaml.dump(
            {"timestamp": timestamp, "results": results},
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
    click.echo(f"\nResults saved to {path}")
    return path


def _list_cases() -> list[str]:
    """List available eval case names."""
    return [p.stem for p in sorted(CASES_DIR.glob("*.yaml"))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SOMA text extraction evaluation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", help="Run a single case")
    group.add_argument("--full", action="store_true", help="Run full eval matrix")
    group.add_argument("--verify-auth", action="store_true", help="Test API credentials")
    group.add_argument("--list-cases", action="store_true", help="List available eval cases")

    parser.add_argument("--model", default=None, help="Model name (for --case)")
    parser.add_argument(
        "--condition",
        default="all",
        choices=["all", "baseline", "schema_only", "format_only", "schema_and_format"],
        help="Which condition(s) to run",
    )
    parser.add_argument("--cheap", action="store_true", help="Use cheap tier models only")
    parser.add_argument("--models", nargs="+", help="Specific models to run")
    args = parser.parse_args()

    if args.list_cases:
        for name in _list_cases():
            click.echo(f"  {name}")
        return

    if args.verify_auth:
        import llm as llm_lib

        data = _load_models_yaml()
        for name in data.get("models", []):
            try:
                llm_lib.get_model(name)
                click.echo(f"  OK  {name}")
            except llm_lib.UnknownModelError:
                click.echo(f"  FAIL  {name} (unknown model / missing plugin)")
        return

    # Determine conditions
    condition_map: dict[str, list[tuple[bool, bool]]] = {
        "all": [(False, False), (True, False), (False, True), (True, True)],
        "baseline": [(False, False)],
        "schema_only": [(True, False)],
        "format_only": [(False, True)],
        "schema_and_format": [(True, True)],
    }
    conditions = condition_map[args.condition]

    if args.case:
        models = [args.model or "gpt-4o-mini"]
        results = run_matrix([args.case], models, conditions)
        save_results(results, label=args.case)
    elif args.full:
        cases = _list_cases()
        if not cases:
            click.echo("No eval cases found in datasets/cases/", err=True)
            raise SystemExit(1)

        if args.models:
            models = args.models
        elif args.cheap:
            models = _load_tier("cheap")
        else:
            models = _load_tier("standard")

        if not models:
            click.echo("No models configured. Check datasets/models.yaml", err=True)
            raise SystemExit(1)

        results = run_matrix(cases, models, conditions)
        save_results(results)


if __name__ == "__main__":
    main()
