# soma-evals

Evaluation framework for schema-guided text extraction using the [SOMA LinkML model](https://github.com/EHS-Data-Standards/soma).

Measures whether providing the SOMA schema to an LLM improves its ability to extract structured assay/measurement data from scientific papers.

## Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| [uv](https://docs.astral.sh/uv/) | 0.6+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [just](https://just.systems/) | 1.0+ | `brew install just` or [other methods](https://just.systems/man/en/packages.html) |
| Python | 3.12+ | Managed by uv (`uv python install 3.12`) |

## Quickstart

```bash
just setup

# Set API keys
uv run llm keys set openai
uv run llm keys set anthropic
uv run llm keys set gemini
```

## Usage

```bash
just --list              # see all available commands
just all                 # fix + check everything (no API calls)
just test                # run tests (no API calls)

# Eval runs (require API keys)
just run ciliary_function                          # single case, default model
just run ciliary_function gpt-4o schema_only       # specific model + condition
just full-eval --cheap                             # matrix: cheap models x 4 conditions
just compare --latest                              # comparison table
```

## Eval Matrix

Each eval run crosses **models x conditions x cases**:

| Condition | Schema | Format | Description |
|-----------|--------|--------|-------------|
| `baseline` | No | No | Freeform extraction |
| `schema_only` | Yes | No | SOMA LinkML class/slot definitions as context |
| `format_only` | No | Yes | Excel sheet/column structure as output format |
| `schema_and_format` | Yes | Yes | Both schema + format |

The key metric is the **schema delta**: how much does providing the SOMA schema improve extraction quality (precision/recall/F1) compared to baseline.

## Adding eval cases

See [`datasets/cases/README.md`](datasets/cases/README.md).

## Model configuration

Edit [`datasets/models.yaml`](datasets/models.yaml) to add models, update tiers, or change pricing.
