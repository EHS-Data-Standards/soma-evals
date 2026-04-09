# Running Evals

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [just](https://github.com/casey/just) command runner
- API keys for the models you want to use

## Setup

```bash
# Clone and install
git clone https://github.com/EHS-Data-Standards/soma-evals.git
cd soma-evals
just setup

# Set API keys
uv run llm keys set openai
uv run llm keys set anthropic
uv run llm keys set gemini

# Verify models are available
just list-models
```

!!! note "CBORG Models"
    Models prefixed with `cborg/` require access to Lawrence Berkeley National Lab's
    CBORG gateway. If you don't have CBORG access, use the OpenAI models directly
    or configure your own model aliases.

## Running Evaluations

### Single Ablation Level

```bash
# Run baseline (no schema context) with the standard tier
just run-baseline

# Run a specific level with a specific tier
just run-class-names tier=cheap
just run-full-classes tier=full
just run-with-enums tier=standard
```

### All Levels

```bash
# Run all four ablation levels sequentially
just run-all

# With a specific tier
just run-all tier=full
```

### Custom Paper

Override the default PDF and paper slug via environment variables:

```bash
EVAL_PDF=my-paper.pdf EVAL_SLUG=my-paper-slug just run-baseline
```

Or pass them directly to the CLI:

```bash
uv run python -m soma_evals run \
  --level baseline \
  --tier standard \
  --pdf my-paper.pdf \
  --paper-slug my-paper-slug
```

## Output

Results are written to `results/<level>/<model>/`:

```
results/
└── baseline/
    ├── run_metadata.yaml
    ├── gpt-4o/montgomery2020-pm25-mucociliary.yaml
    ├── gpt-4o-mini/montgomery2020-pm25-mucociliary.yaml
    ├── cborg--claude-sonnet-4-6/montgomery2020-pm25-mucociliary.yaml
    └── cborg--gemini-2.5-flash/montgomery2020-pm25-mucociliary.yaml
```

Each model produces a YAML file with its structured extraction.
The `run_metadata.yaml` file records token counts, latency, and status for each model.

## Debugging

```bash
# Show what schema context looks like at each level
just show-context

# Run QC checks (no API calls)
just fix     # lint + format
just test    # pytest (excludes API tests)
```

## Justfile Reference

| Command | Description |
|---------|-------------|
| `just setup` | Install dependencies |
| `just list-models` | Show configured models and tiers |
| `just run-baseline` | Run baseline ablation level |
| `just run-class-names` | Run class_names level |
| `just run-full-classes` | Run full_classes level |
| `just run-with-enums` | Run with_enums level |
| `just run-all` | Run all four levels |
| `just show-context` | Print schema context at each level |
| `just fix` | Auto-fix lint and format |
| `just test` | Run tests (no API calls) |
| `just clean-results` | Delete all results |
