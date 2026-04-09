---
hide:
  - navigation
  - toc
---

<div class="aop-hero" markdown>

# SOMA Evals

<p class="aop-subtitle">
Schema-ablation evaluation framework for measuring how SOMA LinkML schema context
improves LLM extraction of structured biological data from scientific papers.
</p>

</div>

<div class="aop-cards" markdown>

<div class="aop-card aop-card--green" markdown>

### Schema Ablation Study

Test four cumulative levels of schema context to isolate the impact on extraction quality.

- Baseline (no schema)
- Class names & descriptions
- Full class + slot definitions
- Complete with enumerations

[Learn more](ablation-levels.md){: .aop-btn .aop-btn--green }

</div>

<div class="aop-card aop-card--orange" markdown>

### Multi-Model Comparison

Compare extraction quality across frontier LLMs from OpenAI, Anthropic, and Google.

- GPT-4o & GPT-4o-mini
- Claude Opus 4 & Sonnet 4
- Gemini 2.5 Flash & Pro

[View models](models.md){: .aop-btn .aop-btn--outline }

</div>

<div class="aop-card aop-card--blue" markdown>

### Extraction Results

Browse structured YAML outputs showing how each model extracts assays, measurements, and protocols.

- Token usage & latency
- Ontology annotation quality
- Side-by-side comparisons

[See results](results/baseline.md){: .aop-btn .aop-btn--blue }

</div>

<div class="aop-card aop-card--purple" markdown>

### Run It Yourself

Reproduce evaluations or add your own papers and models with a simple CLI.

- `just run-baseline`
- `just run-all`
- Configurable tiers & models

[Get started](running-evals.md){: .aop-btn .aop-btn--outline }

</div>

</div>

## Quick Context

This framework evaluates how well LLMs extract structured experimental data from scientific
PDFs when given varying amounts of the [SOMA LinkML schema](https://github.com/EHS-Data-Standards/soma)
as prompt context. The goal is to quantify whether providing schema definitions (class names,
slot types, enumerations) measurably improves the quality, consistency, and ontology coverage
of LLM-generated structured output.

The test corpus currently uses [Montgomery et al. 2020](https://doi.org/10.1165/rcmb.2019-0454OC),
a study on PM2.5-induced mucociliary remodeling in nasal epithelial cells, as the reference
paper for extraction.
