"""Tests for schema loader.

These tests check that schema loading works with the actual soma schema
files at ../soma/. Tests are skipped if the soma directory is not present.
"""

from pathlib import Path

import pytest

SOMA_SCHEMA_PATH = Path(__file__).parent.parent.parent / "soma" / "src" / "soma" / "schema"
SOMA_EXCEL_PATH = Path(__file__).parent.parent.parent / "soma" / "project" / "excel" / "soma.xlsx"

skip_no_soma = pytest.mark.skipif(
    not SOMA_SCHEMA_PATH.exists(),
    reason="soma schema not found at ../soma/",
)
skip_no_excel = pytest.mark.skipif(
    not SOMA_EXCEL_PATH.exists(),
    reason="soma Excel not found at ../soma/",
)


@skip_no_soma
class TestSchemaLoader:
    def test_load_schema_yaml(self) -> None:
        from soma_evals.schema_loader import load_schema_yaml

        data = load_schema_yaml(SOMA_SCHEMA_PATH)
        assert "classes" in data or "imports" in data
        assert data.get("name") == "soma"

    def test_load_all_schema_yamls(self) -> None:
        from soma_evals.schema_loader import load_all_schema_yamls

        data = load_all_schema_yamls(SOMA_SCHEMA_PATH)
        assert "classes" in data
        assert "slots" in data
        assert len(data["classes"]) > 10

    def test_schema_to_context_string(self) -> None:
        from soma_evals.schema_loader import schema_to_context_string

        context = schema_to_context_string(SOMA_SCHEMA_PATH)
        assert "SOMA Schema" in context
        assert "CiliaryFunctionAssay" in context

    def test_schema_to_context_filtered(self) -> None:
        from soma_evals.schema_loader import schema_to_context_string

        context = schema_to_context_string(
            SOMA_SCHEMA_PATH,
            classes=["CiliaryFunctionAssay"],
        )
        assert "CiliaryFunctionAssay" in context
        # Should not include unrelated classes
        assert "OxidativeStressAssay" not in context


@skip_no_excel
class TestExcelLoader:
    def test_load_excel_headers(self) -> None:
        from soma_evals.schema_loader import load_excel_headers

        headers = load_excel_headers(SOMA_EXCEL_PATH)
        assert "CiliaryFunctionAssay" in headers
        assert len(headers) > 10
        assert "id" in headers["CiliaryFunctionAssay"]

    def test_excel_to_format_string(self) -> None:
        from soma_evals.schema_loader import excel_to_format_string

        fmt = excel_to_format_string(SOMA_EXCEL_PATH)
        assert "Sheet: CiliaryFunctionAssay" in fmt
        assert "Columns:" in fmt

    def test_excel_to_format_filtered(self) -> None:
        from soma_evals.schema_loader import excel_to_format_string

        fmt = excel_to_format_string(
            SOMA_EXCEL_PATH,
            sheets=["CiliaryFunctionAssay"],
        )
        assert "CiliaryFunctionAssay" in fmt
        assert "OxidativeStressAssay" not in fmt
