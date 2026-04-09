# soma-evals

Schema-ablation evals for [SOMA](https://github.com/EHS-Data-Standards/soma) — measures how progressively richer LinkML schema context improves LLM-based structured extraction from scientific literature.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [just](https://github.com/casey/just) (task runner)
- Python 3.12+

## Setup

```bash
git clone https://github.com/EHS-Data-Standards/soma-evals.git
cd soma-evals
just setup
```

### API keys

Set keys via the `llm` key store **or** environment variables. Use whichever method you prefer — you only need keys for the providers whose models you plan to run.

**Option A — key store (recommended):**

```bash
uv run llm keys set openai       # paste your OpenAI key
uv run llm keys set anthropic    # paste your Anthropic key
uv run llm keys set gemini       # paste your Gemini key
```

**Option B — `.env` file:**

```bash
cp .env.example .env
```

Then edit `.env`:

```ini
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=AIyour-key-here
```

> **CBORG users (LBNL staff):** Models prefixed with `cborg/` route through the CBORG proxy and are free for lab staff. Authentication is handled by CBORG — no extra API key is needed beyond your CBORG access.

## Running evals

```bash
just list-models        # show available models & tiers
just run-all            # run all four ablation levels (standard tier)
just run-baseline       # run a single level
```

Run a specific tier or override the default paper:

```bash
just run-all cheap
EVAL_PDF=my-paper.pdf EVAL_SLUG=my-slug just run-all
```

### Ablation levels

| Level | Schema context provided |
|-------|------------------------|
| `baseline` | None — LLM relies on training knowledge only |
| `class_names` | Class names, descriptions, and mappings |
| `full_classes` | + slot definitions with ranges & cardinality |
| `with_enums` | + enumeration values and ontology meanings |

See the [Ablation Levels](ablation-levels.md) page for full details on each level, the prompt context it injects, and links to example result YAML.

Results are written to `results/<level>/<model>/<paper>.yaml`.

## Tests & QC

```bash
just test       # run tests (no API calls)
just coverage   # tests with coverage report
just fix        # auto-fix lint/format (ruff)
```

## License

MIT
