# List all commands
_default:
    @just --list

# --- QC (no evals, no API calls) ---

# Fix and check everything
all: fix check

# Auto-fix lint and format issues
fix:
    uv run ruff check --fix src/ tests/ datasets/
    uv run ruff format src/ tests/ datasets/

# Run all checks via pre-commit (single source of truth)
check:
    uv run pre-commit run --all-files

# Run tests (excludes API tests)
test:
    uv run pytest -v -m "not api"

# Run tests with coverage report
coverage:
    uv run pytest -m "not api" --cov=soma_evals --cov-report=term-missing

# --- Setup ---

# Install dependencies and pre-commit hooks
setup:
    uv sync
    uv run pre-commit install
    @echo ""
    @echo "Set API keys as env vars or via llm key store:"
    @echo "  uv run llm keys set openai"
    @echo "  uv run llm keys set anthropic"
    @echo "  uv run llm keys set gemini"

# Verify API auth works for all providers (1 cheap call each)
verify-auth:
    uv run python -m soma_evals.runner --verify-auth

# --- Eval Runs (require API keys) ---

# Run a single eval case
run case model="gpt-4o-mini" condition="all":
    uv run python -m soma_evals.runner --case {{ case }} --model {{ model }} --condition {{ condition }}

# Run full eval matrix (models x conditions x cases)
full-eval *args="":
    uv run python -m soma_evals.runner --full {{ args }}

# Compare results across models and conditions
compare *args="":
    uv run python -m soma_evals.compare {{ args }}

# --- Cleanup ---

clean-cache:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache .mypy_cache

clean-results:
    rm -rf datasets/results/*.yaml datasets/results/*.tsv

clean-all: clean-cache clean-results
