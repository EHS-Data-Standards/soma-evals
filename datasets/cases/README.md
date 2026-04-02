# Eval Cases

Each YAML file in this directory defines one evaluation case — a source text
paired with expected structured output (ground truth).

## Adding a new case

Create a YAML file with this structure:

```yaml
name: my_case
description: What this case tests

# Which soma classes to include when schema context is enabled
relevant_classes:
  - ClassName1
  - ClassName2

# Which Excel sheets to include when format context is enabled
relevant_sheets:
  - SheetName1

# Path to ground truth YAML (relative to datasets/)
ground_truth: ground_truth/Container-my_case.yaml

# The text the LLM will extract from
source_text: |
  Your source text here...
```

## Ground truth

Ground truth files live in `datasets/ground_truth/` and follow the soma
YAML format (same as `soma/examples/output/`). Copy or adapt from the
soma project's example outputs.
