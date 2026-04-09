# What & Why

## What is SOMA Evals?

SOMA Evals is an evaluation framework that measures how effectively LLMs extract structured
biological and experimental data from scientific papers. It specifically tests whether
providing the [SOMA LinkML schema](https://github.com/EHS-Data-Standards/soma) as prompt
context improves extraction quality.

The framework implements a **schema ablation study** -- systematically varying the amount of
schema information given to the LLM and comparing the resulting extractions.

## The Problem

Scientific papers contain rich experimental data -- assays, measurements, protocols, study
subjects, and experimental conditions -- but this data is locked in unstructured text and
tables. Manually extracting and structuring this data is labor-intensive and inconsistent.

LLMs can automate this extraction, but without guidance on the target data model, outputs
vary wildly in structure, field naming, and ontology usage across models.

## The Hypothesis

> Providing progressively more detailed schema context to an LLM will produce
> increasingly structured, consistent, and ontology-rich extractions.

Specifically, we expect that:

1. **Baseline** (no schema) produces varied, model-dependent output structures
2. **Class names** help the LLM organize output into the correct top-level categories
3. **Full class definitions** align field names and types with the schema
4. **Enumerations** improve use of controlled vocabularies and ontology terms

## How It Works

```
Scientific PDF  ──┐
                   ├──▶  LLM  ──▶  Structured YAML
Schema Context  ──┘
```

For each combination of **(model, ablation level, paper)**:

1. Extract raw text from the PDF
2. Build a prompt combining the extraction template, schema context, and paper text
3. Send to the LLM via [Simon Willison's `llm` library](https://llm.datasette.io/)
4. Parse the response and save as YAML
5. Record metadata: tokens, latency, status

## The SOMA Schema

[SOMA](https://github.com/EHS-Data-Standards/soma) (Schema for Omics and Multi-modal Assays)
is a LinkML data model for environmental health sciences. It defines classes for:

- **Container** -- top-level wrapper for a study
- **Investigation** -- study-level metadata
- **Assay** -- experimental procedures (RNA-seq, chemical analysis, etc.)
- **Protocol** -- detailed methods
- **Subject** -- study organisms/samples
- **Measurement** -- quantitative results
- **ExperimentalCondition** -- treatments and controls

The schema includes ontology mappings to OBI, CHEBI, CL, UBERON, NCBITaxon, and UO,
providing a rich target for structured extraction.
