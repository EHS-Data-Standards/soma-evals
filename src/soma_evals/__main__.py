"""CLI entry point: ``uv run python -m soma_evals``."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from soma_evals.runner import load_models, run_all_levels, run_level
from soma_evals.schema_context import ABLATION_LEVELS, AblationLevel, build_schema_context


def _resolve_models(model: tuple[str, ...], tier: str | None) -> list[str]:
    """Resolve model list from explicit flags, tier, or defaults."""
    if model:
        return list(model)
    return load_models(tier=tier)


@click.group()
def cli() -> None:
    """SOMA schema-ablation evaluation framework."""


@cli.command()
@click.option(
    "--level",
    "-l",
    type=click.Choice([lv.value for lv in AblationLevel], case_sensitive=False),
    required=True,
    help="Ablation level to run.",
)
@click.option("--tier", "-t", type=click.Choice(["cheap", "standard", "full"]), default=None)
@click.option("--model", "-m", multiple=True, help="Specific model(s). Repeatable.")
@click.option("--pdf", required=True, type=click.Path(exists=True), help="Path to source PDF.")
@click.option("--paper-slug", required=True, help="Short identifier for the paper.")
@click.option("--schema-path", default=None, help="Override path to SOMA schema.")
@click.option("--results-dir", default=None, help="Override results directory.")
def run(
    level: str,
    tier: str | None,
    model: tuple[str, ...],
    pdf: str,
    paper_slug: str,
    schema_path: str | None,
    results_dir: str | None,
) -> None:
    """Run extraction for a single ablation level."""
    models = _resolve_models(model, tier)
    click.echo(f"Models: {', '.join(models)}")
    run_level(
        AblationLevel(level),
        models,
        Path(pdf),
        paper_slug,
        schema_path=schema_path,
        results_dir=results_dir,
    )


@cli.command("run-all")
@click.option("--tier", "-t", type=click.Choice(["cheap", "standard", "full"]), default=None)
@click.option("--model", "-m", multiple=True, help="Specific model(s). Repeatable.")
@click.option("--pdf", required=True, type=click.Path(exists=True), help="Path to source PDF.")
@click.option("--paper-slug", required=True, help="Short identifier for the paper.")
@click.option("--schema-path", default=None, help="Override path to SOMA schema.")
@click.option("--results-dir", default=None, help="Override results directory.")
def run_all(
    tier: str | None,
    model: tuple[str, ...],
    pdf: str,
    paper_slug: str,
    schema_path: str | None,
    results_dir: str | None,
) -> None:
    """Run extraction for ALL ablation levels."""
    models = _resolve_models(model, tier)
    click.echo(f"Models: {', '.join(models)}")
    run_all_levels(
        models,
        Path(pdf),
        paper_slug,
        schema_path=schema_path,
        results_dir=results_dir,
    )


@cli.command("list-models")
def list_models() -> None:
    """List configured models and tiers."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    models_path = repo_root / "models.yaml"
    with models_path.open() as f:
        data = yaml.safe_load(f)

    click.echo("Default models:")
    for m in data.get("models", []):
        click.echo(f"  - {m}")

    click.echo("\nTiers:")
    for tier_name, tier_models in data.get("tiers", {}).items():
        click.echo(f"  {tier_name}:")
        for m in tier_models:
            click.echo(f"    - {m}")


@cli.command("show-context")
@click.option("--schema-path", default=None, help="Override path to SOMA schema.")
def show_context(schema_path: str | None) -> None:
    """Print schema context at each ablation level (debugging)."""
    for level in ABLATION_LEVELS:
        ctx = build_schema_context(level, schema_path)
        click.echo(f"\n{'=' * 60}")
        click.echo(f"Level: {level.value}")
        click.echo(f"{'=' * 60}")
        if ctx is None:
            click.echo("(no schema context)")
        else:
            click.echo(f"Length: {len(ctx)} chars")
            click.echo(f"\n{ctx[:2000]}")
            if len(ctx) > 2000:
                click.echo(f"\n... ({len(ctx) - 2000} more chars)")


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
