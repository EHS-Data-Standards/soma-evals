set dotenv-load

# List all commands
_default:
    @just --list

# --- QC (no evals, no API calls) ---

# Fix and check everything
all: fix

# Auto-fix lint and format issues
fix:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Run tests (excludes API tests)
test:
    uv run pytest -v -m "not api"

# Run tests with coverage report
coverage:
    uv run pytest -m "not api" --cov=soma_evals --cov-report=term-missing

# --- Setup ---

# Install dependencies
setup:
    uv sync
    @echo ""
    @echo "Set API keys as env vars or via llm key store:"
    @echo "  uv run llm keys set openai"
    @echo "  uv run llm keys set anthropic"
    @echo "  uv run llm keys set gemini"

# List configured models and tiers
list-models:
    uv run python -m soma_evals list-models

# --- Schema Ablation Runs (require API keys) ---

# Default PDF and paper slug (override via env vars or CLI)
pdf := env("EVAL_PDF", "rcmb.2019-0454OC.pdf")
slug := env("EVAL_SLUG", "montgomery2020-pm25-mucociliary")

# Run baseline ablation level (no schema context)
run-baseline tier="standard":
    uv run python -m soma_evals run --level baseline --tier {{tier}} --pdf {{pdf}} --paper-slug {{slug}}

# Run class_names ablation level
run-class-names tier="standard":
    uv run python -m soma_evals run --level class_names --tier {{tier}} --pdf {{pdf}} --paper-slug {{slug}}

# Run full_classes ablation level
run-full-classes tier="standard":
    uv run python -m soma_evals run --level full_classes --tier {{tier}} --pdf {{pdf}} --paper-slug {{slug}}

# Run with_enums ablation level
run-with-enums tier="standard":
    uv run python -m soma_evals run --level with_enums --tier {{tier}} --pdf {{pdf}} --paper-slug {{slug}}

# Run ALL ablation levels
run-all tier="standard":
    uv run python -m soma_evals run-all --tier {{tier}} --pdf {{pdf}} --paper-slug {{slug}}

# Show schema context at each level (debugging)
show-context:
    uv run python -m soma_evals show-context

# --- Documentation ---

# Generate docs (copy src/docs to docs/) and serve locally
gen-doc:
    rm -rf docs
    cp -r src/docs docs

# Serve docs locally for preview
testdoc: gen-doc
    uv run mkdocs serve

# Deploy docs to GitHub Pages
deploy: gen-doc
    uv run mkdocs gh-deploy --force

# --- Cleanup ---

clean-cache:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache .mypy_cache

clean-results:
    rm -rf results/

clean-docs:
    rm -rf docs site

clean-all: clean-cache clean-results clean-docs
