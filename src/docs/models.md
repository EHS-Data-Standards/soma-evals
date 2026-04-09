# Models

## Configured Models

Models are defined in `models.yaml`. Names must match what's registered with
the [`llm` library](https://llm.datasette.io/).

| Model | Provider | Access |
|-------|----------|--------|
| `gpt-4o` | OpenAI | Direct API |
| `gpt-4o-mini` | OpenAI | Direct API |
| `cborg/claude-opus-4-6` | Anthropic (via CBORG) | CBORG proxy |
| `cborg/claude-sonnet-4-6` | Anthropic (via CBORG) | CBORG proxy |
| `cborg/gemini-2.5-flash` | Google (via CBORG) | CBORG proxy |

!!! note "CBORG"
    CBORG is Lawrence Berkeley National Lab's internal LLM gateway. Models
    prefixed with `cborg/` are accessed through this proxy, which is free
    for LBL staff. Pricing in the config is kept for comparison with direct
    API costs.

## Model Tiers

Tiers allow selecting subsets of models for different run budgets:

### Cheap

Fastest and lowest cost, good for iteration:

- `gpt-4o-mini`
- `cborg/gemini-2.5-flash`

### Standard

Balanced coverage across providers:

- `gpt-4o-mini`
- `gpt-4o`
- `cborg/gemini-2.5-flash`
- `cborg/claude-sonnet-4-6`

### Full

All available models including the most capable:

- `gpt-4o-mini`
- `gpt-4o`
- `cborg/claude-opus-4-6`
- `cborg/claude-sonnet-4-6`
- `cborg/gemini-2.5-flash`
- `cborg/gemini-2.5-pro`
- `cborg/gemini-3-flash`

## Pricing

Approximate cost per 1M tokens (for reference):

| Model | Input ($/1M) | Output ($/1M) |
|-------|-------------|---------------|
| gpt-4o-mini | $0.15 | $0.60 |
| gemini-2.5-flash | $0.30 | $2.50 |
| gemini-2.5-pro | $1.25 | $10.00 |
| gpt-4o | $2.50 | $10.00 |
| claude-sonnet-4-6 | $3.00 | $15.00 |
| claude-opus-4-6 | $15.00 | $75.00 |

!!! tip
    Use `just list-models` to see models and tiers configured on your system.
