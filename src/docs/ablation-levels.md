# Ablation Levels

The core of this evaluation is a **schema ablation study** with four cumulative levels.
Each level adds more SOMA schema information to the LLM prompt, letting us measure
the marginal impact of each type of schema context on extraction quality.

## The Four Levels

| Level | Schema Context | What's Added |
|-------|---------------|--------------|
| `baseline` | None | No schema context -- the LLM uses only its training knowledge |
| `class_names` | Class headers | Class names, descriptions, parent classes, URIs, mappings |
| `full_classes` | + Slot definitions | All induced slots with ranges, cardinality, and constraints |
| `with_enums` | + Enumerations | All enum definitions with permissible values and ontology meanings |

## Level Details

### Baseline

No schema context is provided. The prompt contains only the extraction instructions
and the paper text. This is the control condition -- it measures what each model can
do purely from its pre-training knowledge of scientific data structures.

### Class Names

Adds a structured listing of all SOMA classes:

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
```

This gives the LLM the vocabulary and hierarchy of the target data model without
the detailed field structure.

### Full Classes

Adds all slot (field) definitions for each class:

```
## Assay
  ...
  Slots:
    - name (string) [required]
    - description (string)
    - has_protocol (Protocol) [multivalued, inlined_as_list]
    - has_measurement (Measurement) [multivalued, inlined_as_list]
    - study_subjects (Subject) [multivalued]
```

This tells the LLM exactly what fields to extract, their types, and whether
they accept single or multiple values.

### With Enums

Adds all enumeration definitions with their permissible values:

```
# Enumerations

## AssayTypeEnum
  Values:
    - RNA_sequencing: Whole-transcriptome RNA-seq (meaning: OBI:0001271)
    - chemical_analysis: Analytical chemistry assay (meaning: OBI:0000070)
    - microscopy: Imaging assay (meaning: OBI:0000185)
```

This provides controlled vocabularies so the LLM can use exact permitted values
and ontology terms rather than free text.

## Expected Impact

| Aspect | Baseline | + Class Names | + Full Classes | + Enums |
|--------|----------|---------------|----------------|---------|
| Output structure | Model-dependent | Aligned categories | Schema-conformant fields | Schema-conformant fields |
| Field naming | Inconsistent | Improved | Matching schema | Matching schema |
| Ontology IDs | Sporadic | Improved | Good | Best |
| Controlled vocab | Free text | Free text | Free text | Enum-aligned |
| Output consistency | Low | Medium | High | Highest |
