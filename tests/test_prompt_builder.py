"""Tests for prompt builder."""

from soma_evals.prompt_builder import build_prompt, condition_label


class TestConditionLabel:
    def test_baseline(self) -> None:
        assert condition_label(schema=False, fmt=False) == "baseline"

    def test_schema_only(self) -> None:
        assert condition_label(schema=True, fmt=False) == "schema_only"

    def test_format_only(self) -> None:
        assert condition_label(schema=False, fmt=True) == "format_only"

    def test_schema_and_format(self) -> None:
        assert condition_label(schema=True, fmt=True) == "schema_and_format"


class TestBuildPrompt:
    def test_baseline_no_context(self) -> None:
        result = build_prompt("Some scientific text here.")
        assert "system" in result
        assert "prompt" in result
        assert "Some scientific text here." in result["prompt"]

    def test_with_schema_context(self) -> None:
        result = build_prompt(
            "Some text.",
            schema_context="## CiliaryFunctionAssay\n  A planned process...",
        )
        assert "CiliaryFunctionAssay" in result["prompt"]
        assert "schema" in result["prompt"].lower()

    def test_with_format_instructions(self) -> None:
        result = build_prompt(
            "Some text.",
            format_instructions="## Sheet: CiliaryFunctionAssay\n  Columns: id, name",
        )
        assert "CiliaryFunctionAssay" in result["prompt"]
        assert "Sheet" in result["prompt"]

    def test_with_both(self) -> None:
        result = build_prompt(
            "Some text.",
            schema_context="## Schema\nclass info",
            format_instructions="## Format\nsheet info",
        )
        assert "Schema" in result["prompt"]
        assert "Format" in result["prompt"]
        assert "Some text." in result["prompt"]
