"""Model pricing for cost estimation.

Loads pricing from the ``pricing:`` section of datasets/models.yaml.
Edit that file to add models or update prices — no code changes needed.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_MODELS_YAML = Path(__file__).parent.parent.parent / "datasets" / "models.yaml"


def _load_pricing() -> dict[str, tuple[float, float]]:
    """Load pricing table from models.yaml."""
    if not _MODELS_YAML.exists():
        return {}
    with open(_MODELS_YAML) as f:
        data = yaml.safe_load(f) or {}
    raw = data.get("pricing", {})
    return {str(k): (float(v[0]), float(v[1])) for k, v in raw.items() if isinstance(v, list) and len(v) == 2}


_PRICING: dict[str, tuple[float, float]] = _load_pricing()


def _normalize_model_name(model: str) -> str:
    """Strip provider prefixes (e.g. 'anthropic/', 'gemini/')."""
    for prefix in ("anthropic/", "gemini/", "openai/"):
        if model.startswith(prefix):
            return model[len(prefix) :]
    return model


def get_pricing(model: str) -> tuple[float, float] | None:
    """Look up (input_cost, output_cost) per 1M tokens for a model."""
    normalized = _normalize_model_name(model)
    if normalized in _PRICING:
        return _PRICING[normalized]
    for key in sorted(_PRICING, key=len, reverse=True):
        if normalized.startswith(key):
            return _PRICING[key]
    return None


def estimate_cost(
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    """Estimate cost in USD for a single LLM call."""
    if input_tokens is None or output_tokens is None:
        return None
    pricing = get_pricing(model)
    if pricing is None:
        return None
    input_cost, output_cost = pricing
    return (input_tokens * input_cost + output_tokens * output_cost) / 1_000_000
