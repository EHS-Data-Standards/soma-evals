# Architecture

## Project Structure

```
soma-evals/
├── src/soma_evals/          # Python package
│   ├── __main__.py          # CLI entry point (Click)
│   ├── runner.py            # Orchestrates eval runs
│   ├── llm_adapter.py       # Wraps llm library
│   ├── pdf_utils.py         # PDF text extraction (PyMuPDF)
│   ├── prompt_builder.py    # Assembles prompts from parts
│   └── schema_context.py    # Generates schema context per ablation level
├── results/                 # Output directory (per-level, per-model)
│   └── baseline/
│       ├── run_metadata.yaml
│       └── <model>/paper.yaml
├── extract.yaml             # Prompt template
├── models.yaml              # Model config and pricing
├── mkdocs.yml               # Documentation config
└── justfile                 # Build automation
```

## Data Flow

```
                    ┌─────────────────┐
                    │   extract.yaml  │  prompt template
                    └────────┬────────┘
                             │
┌──────────┐    ┌────────────▼────────────┐    ┌──────────────┐
│  PDF      │───▶│   prompt_builder.py     │───▶│  LLM API     │
│  (paper)  │    │  + schema_context.py    │    │  (via llm)   │
└──────────┘    └─────────────────────────┘    └──────┬───────┘
                                                      │
                    ┌─────────────────┐               │
                    │  runner.py      │◀──────────────┘
                    │  orchestration  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  results/       │
                    │  level/model/   │
                    │    paper.yaml   │
                    └─────────────────┘
```

## Key Modules

### `__main__.py` -- CLI

Click-based interface with four commands:

| Command | Description |
|---------|-------------|
| `run --level <LEVEL>` | Run a single ablation level |
| `run-all` | Run all four levels sequentially |
| `list-models` | Display configured models and tiers |
| `show-context` | Debug: print schema context at each level |

### `runner.py` -- Orchestration

Manages the eval workflow:

- **`run_single()`** -- one model, one level, one paper
- **`run_level()`** -- all models for a single level; writes `run_metadata.yaml`
- **`run_all_levels()`** -- all levels for all models

The runner extracts PDF text once per level and reuses it across models.

### `schema_context.py` -- Ablation Levels

Uses `linkml-runtime`'s `SchemaView` to programmatically generate schema context
at four cumulative levels. See the [Ablation Levels](../ablation-levels.md) page for details.

### `prompt_builder.py` -- Prompt Assembly

Combines three parts into the final prompt:

1. **Schema context** (if level > baseline) as `## Schema Context`
2. **Template prompt** from `extract.yaml`
3. **PDF text** as `## Source Text`

### `llm_adapter.py` -- LLM Integration

Thin wrapper around [Simon Willison's `llm` library](https://llm.datasette.io/).
This supports any model plugin (`llm-claude-3`, `llm-gemini`, OpenAI built-in)
with a uniform interface. Temperature defaults to `0.0` for deterministic output.

### `pdf_utils.py` -- PDF Extraction

Simple PyMuPDF wrapper that extracts all text from a PDF, concatenating pages
with double-newline separators.

## Output Format

Each model run produces a YAML file with the LLM's structured extraction.
Metadata is captured in `run_metadata.yaml` per level:

```yaml
level: baseline
timestamp: '2026-04-09T00:05:30.216735+00:00'
paper_slug: montgomery2020-pm25-mucociliary
pdf_path: rcmb.2019-0454OC.pdf
runs:
  - model: gpt-4o
    status: success
    input_tokens: 18707
    output_tokens: 937
    duration_ms: 16264
```
