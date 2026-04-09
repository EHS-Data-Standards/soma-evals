# Ablation Levels

The core of this evaluation is a **schema ablation study** with four cumulative levels.
Each level adds more SOMA schema information to the LLM prompt, letting us measure
the marginal impact of each type of schema context on extraction quality.

## Overview

| Level | Schema Context | What's Added | Approx. Tokens |
|-------|---------------|--------------|----------------|
| [`baseline`](#level-1-baseline) | None | No schema — LLM uses only training knowledge | ~18,700 |
| [`class_names`](#level-2-class_names) | Class headers | Class names, descriptions, parent classes, URIs, mappings | ~19,500 |
| [`full_classes`](#level-3-full_classes) | + Slot definitions | All induced slots with ranges, cardinality, and constraints | ~20,500 |
| [`with_enums`](#level-4-with_enums) | + Enumerations | All enum definitions with permissible values and ontology meanings | ~21,700 |

Each level is **cumulative** — it includes everything from the previous level plus new context.

---

## Level 1: `baseline`

**Schema context injected:** *None*

The prompt contains only the extraction instructions and the paper text. This is the
control condition — it measures what each model can do purely from its pre-training
knowledge of scientific data structures.

??? note "Prompt sent to the LLM"
    **System:**
    ```
    You are a scientific data extraction assistant specializing in biological
    assays and measurements. Your task is to extract structured data from
    scientific text, identifying assays, measurements, protocols, study
    subjects, and experimental conditions.
    ```

    **User:**
    ```
    Extract structured assay and measurement data from the following scientific text.
    Identify all assays, their measurements, study subjects, protocols, and
    experimental conditions. Use ontology identifiers where possible (e.g.,
    OBI, CHEBI, CL, UBERON, NCBITaxon, UO). Provide the extracted data in
    a structured format (e.g., YAML).

    [paper text follows]
    ```

**What to expect:** Output structure is entirely model-dependent. Field naming is inconsistent
across models. Ontology IDs appear sporadically. Controlled vocabulary terms are free text.

| | Baseline |
|---|----------|
| Output structure | Model-dependent |
| Field naming | Inconsistent |
| Ontology IDs | Sporadic |
| Controlled vocab | Free text |
| Output consistency | Low |

**Results:** `results/baseline/<model>/<paper>.yaml`
([browse on GitHub](https://github.com/sierra-moxon/soma-evals/tree/main/results/baseline))

**Next level:** [class_names](#level-2-class_names) adds class names, descriptions, and ontology mappings.

---

## Level 2: `class_names`

**Schema context injected:** Class names, descriptions, parent classes, URIs, and mappings.

??? note "Schema context prepended to prompt"
    ```
    # SOMA Schema Classes

    ## Assay
      An experimental procedure to test a hypothesis or measure something.
      Parent: NamedThing
      URI: soma:Assay
      Mappings: OBI:0000070

    ## Protocol
      A detailed description of how an assay is performed.
      Parent: NamedThing
      URI: soma:Protocol

    ## Measurement
      A quantitative or qualitative result from an assay.
      Parent: NamedThing
      URI: soma:Measurement

    ## Subject
      An entity that is the focus of an investigation.
      Parent: NamedThing
      URI: soma:Subject

    [... all SOMA classes listed ...]
    ```

**What changed from baseline:**
This gives the LLM the vocabulary and hierarchy of the target data model. It knows *what
categories* of information to extract (Assay, Protocol, Measurement, Subject, etc.) and
has ontology URIs to anchor them.

| | Baseline | + Class Names |
|---|----------|---------------|
| Output structure | Model-dependent | **Aligned categories** |
| Field naming | Inconsistent | **Improved** |
| Ontology IDs | Sporadic | **Improved** |
| Controlled vocab | Free text | Free text |
| Output consistency | Low | **Medium** |

**Results:** `results/class_names/<model>/<paper>.yaml`
([browse on GitHub](https://github.com/sierra-moxon/soma-evals/tree/main/results/class_names))

**Previous level:** [baseline](#level-1-baseline) — no schema context at all.
**Next level:** [full_classes](#level-3-full_classes) adds slot definitions with types and cardinality.

---

## Level 3: `full_classes`

**Schema context injected:** Everything from `class_names`, plus all slot (field) definitions
for each class.

??? note "Schema context prepended to prompt"
    ```
    # SOMA Schema Classes and Slots

    ## Assay
      An experimental procedure to test a hypothesis or measure something.
      Parent: NamedThing
      URI: soma:Assay
      Mappings: OBI:0000070
      Slots:
        - name (string) [required, identifier]
        - description (string)
        - has_protocol (Protocol) [multivalued, inlined_as_list]
        - has_measurement (Measurement) [multivalued, inlined_as_list]
        - study_subjects (Subject) [multivalued]
        - assay_type (AssayTypeEnum)
        - gene_expression_method (GeneExpressionMethodEnum)

    ## Protocol
      A detailed description of how an assay is performed.
      Parent: NamedThing
      URI: soma:Protocol
      Slots:
        - name (string) [required, identifier]
        - description (string)
        - protocol_type (ProtocolTypeEnum)

    [... all classes with full slot definitions ...]
    ```

**What changed from class_names:**
The LLM now knows the exact fields to extract for each class — their names, types, whether
they're required, and whether they accept single or multiple values. This should produce
output that is structurally conformant with the SOMA schema.

| | Baseline | + Class Names | + Full Classes |
|---|----------|---------------|----------------|
| Output structure | Model-dependent | Aligned categories | **Schema-conformant fields** |
| Field naming | Inconsistent | Improved | **Matching schema** |
| Ontology IDs | Sporadic | Improved | **Good** |
| Controlled vocab | Free text | Free text | Free text |
| Output consistency | Low | Medium | **High** |

**Results:** `results/full_classes/<model>/<paper>.yaml`
([browse on GitHub](https://github.com/sierra-moxon/soma-evals/tree/main/results/full_classes))

**Previous level:** [class_names](#level-2-class_names) — class headers only, no slot details.
**Next level:** [with_enums](#level-4-with_enums) adds enumeration values with ontology meanings.

---

## Level 4: `with_enums`

**Schema context injected:** Everything from `full_classes`, plus all enumeration definitions
with permissible values and ontology term mappings.

??? note "Schema context prepended to prompt"
    ```
    # SOMA Schema Classes and Slots

    [... all classes with full slot definitions as in Level 3 ...]

    # Enumerations

    ## AssayTypeEnum
      Values:
        - RNA_sequencing: Whole-transcriptome RNA-seq (meaning: OBI:0001271)
        - chemical_analysis: Analytical chemistry assay (meaning: OBI:0000070)
        - microscopy: Imaging assay (meaning: OBI:0000185)
        - qRT_PCR: Quantitative RT-PCR (meaning: OBI:0002631)
        - western_blot: Protein immunoblot (meaning: OBI:0000920)

    ## GeneExpressionMethodEnum
      Values:
        - qRT_PCR: Quantitative reverse-transcription PCR
        - RNA_seq: RNA sequencing
        - microarray: Gene expression microarray

    [... all enumerations with permissible values and ontology meanings ...]
    ```

**What changed from full_classes:**
The LLM now has controlled vocabularies with exact permitted values and their ontology
term mappings. Instead of guessing "RNA-seq" vs "RNA sequencing" vs "RNAseq", it can use
the canonical `RNA_sequencing` value from the enum. This is the most complete level of
schema guidance.

| | Baseline | + Class Names | + Full Classes | + Enums |
|---|----------|---------------|----------------|---------|
| Output structure | Model-dependent | Aligned categories | Schema-conformant fields | Schema-conformant fields |
| Field naming | Inconsistent | Improved | Matching schema | Matching schema |
| Ontology IDs | Sporadic | Improved | Good | **Best** |
| Controlled vocab | Free text | Free text | Free text | **Enum-aligned** |
| Output consistency | Low | Medium | High | **Highest** |

**Results:** `results/with_enums/<model>/<paper>.yaml`
([browse on GitHub](https://github.com/sierra-moxon/soma-evals/tree/main/results/with_enums))

**Previous level:** [full_classes](#level-3-full_classes) — classes and slots, but no enum values.

---

## How schema context is generated

The schema context for each level is generated programmatically by `schema_context.py`,
which uses LinkML's `SchemaView` to introspect the SOMA schema and produce the text
blocks shown above.

```
┌─────────────────────────────────────────┐
│  ## Schema Context      (if not baseline)│
│  [generated by schema_context.py]       │
│                                         │
│  [extraction instructions from template]│
│                                         │
│  ## Source Text                          │
│  [full text extracted from PDF]         │
└─────────────────────────────────────────┘
```

For **baseline** runs, the schema context section is omitted entirely.

To inspect the actual generated context at each level:

```bash
just show-context
```
