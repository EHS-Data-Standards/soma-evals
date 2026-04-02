"""Scoring functions for text extraction evaluation.

Compares LLM-extracted structured data against hand-curated ground truth.
"""

from __future__ import annotations

import re
from typing import Any


def score_sets(
    predicted: set[str],
    expected: set[str],
) -> dict[str, Any]:
    """Precision, recall, F1 on two sets of strings.

    Returns dict with precision, recall, f1, true_positives, false_positives,
    false_negatives.
    """
    if not predicted and not expected:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "true_positives": [],
            "false_positives": [],
            "false_negatives": [],
        }

    tp = predicted & expected
    fp = predicted - expected
    fn = expected - predicted

    precision = len(tp) / len(predicted) if predicted else 0.0
    recall = len(tp) / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": sorted(tp),
        "false_positives": sorted(fp),
        "false_negatives": sorted(fn),
    }


def score_slots(
    predicted: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Score slot-level extraction: did the LLM extract the right field names?

    Args:
        predicted: dict of slot_name -> value (from LLM output)
        expected: dict of slot_name -> value (from ground truth)

    Returns:
        Set-based scores on the slot names.
    """
    return score_sets(set(predicted.keys()), set(expected.keys()))


def _normalize_value(v: Any) -> str:
    """Normalize a value for comparison."""
    s = str(v).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def score_values(
    predicted: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Score value-level extraction for matched slots.

    Only scores slots that appear in both predicted and expected.

    Returns:
        dict with exact_matches, total_compared, accuracy, and per-slot details.
    """
    common_slots = set(predicted.keys()) & set(expected.keys())
    if not common_slots:
        return {
            "exact_matches": 0,
            "total_compared": 0,
            "accuracy": 0.0,
            "details": [],
        }

    exact = 0
    details: list[dict[str, Any]] = []
    for slot in sorted(common_slots):
        pred_norm = _normalize_value(predicted[slot])
        exp_norm = _normalize_value(expected[slot])
        match = pred_norm == exp_norm
        if match:
            exact += 1
        details.append(
            {
                "slot": slot,
                "predicted": str(predicted[slot]),
                "expected": str(expected[slot]),
                "exact_match": match,
            }
        )

    return {
        "exact_matches": exact,
        "total_compared": len(common_slots),
        "accuracy": round(exact / len(common_slots), 4),
        "details": details,
    }


def flatten_yaml_to_slots(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested YAML/dict structure into dot-separated slot paths.

    Example:
        {"study_subject": {"name": "foo", "species": {"id": "NCBITaxon:9606"}}}
        -> {"study_subject.name": "foo", "study_subject.species.id": "NCBITaxon:9606"}
    """
    flat: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_yaml_to_slots(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flat.update(flatten_yaml_to_slots(item, f"{full_key}[{i}]"))
                else:
                    flat[f"{full_key}[{i}]"] = item
        else:
            flat[full_key] = value
    return flat
