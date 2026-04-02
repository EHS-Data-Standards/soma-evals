"""Compare eval results across models and conditions.

The key output is the schema vs no-schema delta: how much does providing
the soma schema improve extraction quality?

Usage:
    uv run python -m soma_evals.compare --latest
    uv run python -m soma_evals.compare --detail
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import click
import yaml

RESULTS_DIR = Path(__file__).parent.parent.parent / "datasets" / "results"


def load_all_results() -> list[dict[str, Any]]:
    """Load all result YAML files, sorted by filename."""
    if not RESULTS_DIR.exists():
        return []
    all_results: list[dict[str, Any]] = []
    for path in sorted(RESULTS_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["_file"] = path.name
        all_results.append(data)
    return all_results


def _aggregate_by_model_condition(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Group results by (model, condition) and compute averages."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        if "slot_scores" not in r:
            continue
        key = f"{r['model']}|{r['condition']}"
        groups[key].append(r)

    summaries: dict[str, dict[str, Any]] = {}
    for key, items in groups.items():
        model, condition = key.split("|", 1)
        n = len(items)
        avg_p = sum(r["slot_scores"]["precision"] for r in items) / n
        avg_r = sum(r["slot_scores"]["recall"] for r in items) / n
        avg_f1 = sum(r["slot_scores"]["f1"] for r in items) / n
        total_cost = sum(r.get("est_cost_usd") or 0 for r in items)
        total_time = sum(r.get("elapsed_seconds", 0) for r in items)

        summaries[key] = {
            "model": model,
            "condition": condition,
            "n": n,
            "precision": avg_p,
            "recall": avg_r,
            "f1": avg_f1,
            "total_cost": total_cost,
            "total_time": total_time,
        }
    return summaries


def print_comparison(all_data: list[dict[str, Any]]) -> None:
    """Print a comparison table grouped by model, showing all conditions."""
    # Flatten all results from all files
    flat: list[dict[str, Any]] = []
    for data in all_data:
        flat.extend(data.get("results", []))

    summaries = _aggregate_by_model_condition(flat)
    if not summaries:
        click.echo("No scored results found.")
        return

    # Header
    click.echo(f"{'Model':<28s} {'Condition':<20s} {'P':>6s} {'R':>6s} {'F1':>6s} {'Cost':>8s} {'Time':>6s} {'N':>3s}")
    click.echo("-" * 95)

    for _key, s in sorted(summaries.items(), key=lambda x: (x[1]["model"], x[1]["condition"])):
        cost_str = f"${s['total_cost']:.4f}" if s["total_cost"] else f"{'--':>8s}"
        click.echo(
            f"{s['model']:<28s} {s['condition']:<20s}"
            f" {s['precision']:>6.3f} {s['recall']:>6.3f} {s['f1']:>6.3f}"
            f" {cost_str} {s['total_time']:>5.0f}s {s['n']:>3d}"
        )

    # Schema delta table
    click.echo(f"\n{'=' * 60}")
    click.echo("SCHEMA IMPACT (schema_and_format - baseline)")
    click.echo(f"{'=' * 60}")
    click.echo(f"{'Model':<28s} {'dP':>6s} {'dR':>6s} {'dF1':>6s}")
    click.echo("-" * 50)

    models = sorted({s["model"] for s in summaries.values()})
    for model in models:
        baseline_key = f"{model}|baseline"
        schema_key = f"{model}|schema_and_format"
        if baseline_key in summaries and schema_key in summaries:
            b = summaries[baseline_key]
            s = summaries[schema_key]
            dp = s["precision"] - b["precision"]
            dr = s["recall"] - b["recall"]
            df1 = s["f1"] - b["f1"]
            click.echo(f"{model:<28s} {dp:>+6.3f} {dr:>+6.3f} {df1:>+6.3f}")
        else:
            click.echo(f"{model:<28s} {'(incomplete data)':>20s}")


def save_summary_tsv(all_data: list[dict[str, Any]], output_path: Path) -> None:
    """Write comparison as TSV."""
    flat: list[dict[str, Any]] = []
    for data in all_data:
        flat.extend(data.get("results", []))

    summaries = _aggregate_by_model_condition(flat)
    cols = ["model", "condition", "n", "precision", "recall", "f1", "total_cost", "total_time"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for s in sorted(summaries.values(), key=lambda x: (x["model"], x["condition"])):
            row = []
            for c in cols:
                v = s.get(c)
                if v is None:
                    row.append("")
                elif isinstance(v, float):
                    row.append(f"{v:.6f}")
                else:
                    row.append(str(v))
            f.write("\t".join(row) + "\n")
    click.echo(f"Summary saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare SOMA extraction eval results")
    parser.add_argument("--latest", action="store_true", help="Show only the most recent result file")
    parser.add_argument("--save-tsv", type=Path, help="Write comparison to TSV file")
    args = parser.parse_args()

    all_data = load_all_results()

    if args.latest and all_data:
        all_data = [all_data[-1]]

    print_comparison(all_data)

    if args.save_tsv:
        save_summary_tsv(all_data, args.save_tsv)


if __name__ == "__main__":
    main()
