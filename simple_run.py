#!/usr/bin/env python3
"""Simple script: run a prompt + PDF through multiple models, print raw output.

Extracts text from the PDF and injects it into the prompt. If the prompt
contains {source_text}, the PDF text replaces that placeholder. Otherwise
the PDF text is appended to the prompt.

Usage:
    uv run python simple_run.py datasets/montgomery2020-pm25-mucociliary.pdf
    uv run python simple_run.py datasets/montgomery2020-pm25-mucociliary.pdf --models gpt-4o cborg/claude-opus-4-6
    uv run python simple_run.py datasets/montgomery2020-pm25-mucociliary.pdf --prompt "Summarize the key findings of: {source_text}"
    uv run python simple_run.py datasets/montgomery2020-pm25-mucociliary.pdf --prompt-file datasets/prompts/extract-no-schema.yaml
    uv run python simple_run.py datasets/montgomery2020-pm25-mucociliary.pdf --outdir results/
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pymupdf
import yaml

from soma_evals.llm_adapter import LLMLibraryAdapter

DEFAULT_MODELS = [
    "gpt-4o-mini",
    "cborg/claude-sonnet-4-6",
    "cborg/gemini-2.5-flash",
]

DEFAULT_SYSTEM = "You are a scientific data extraction assistant specializing in biological assays and measurements."

DEFAULT_PROMPT = (
    "Extract structured assay and measurement data from the following scientific text. "
    "Identify all assays, their measurements, study subjects, protocols, and "
    "experimental conditions. Output valid YAML.\n\n"
    "--- Source Text ---\n{source_text}"
)


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF using pymupdf."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)


def load_prompt_file(path: str) -> tuple[str | None, str]:
    """Load a prompt file. If it's YAML with system/prompt keys, parse those.
    Otherwise treat the whole file as the prompt text.

    Returns (system_prompt, user_prompt).
    """
    text = Path(path).read_text()
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and "prompt" in data:
            return data.get("system"), data["prompt"]
    except yaml.YAMLError:
        pass
    return None, text


def run_model(model: str, system: str | None, prompt: str) -> dict:
    adapter = LLMLibraryAdapter(model_name=model, system_prompt=system)
    adapter.add_message(prompt)

    t0 = time.time()
    try:
        text = adapter.generate(temperature=0.0)
    except Exception as e:
        return {"model": model, "error": str(e), "elapsed": 0}
    elapsed = time.time() - t0

    usage = adapter.get_token_usage()
    return {
        "model": model,
        "response": text,
        "elapsed": round(elapsed, 1),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def main():
    parser = argparse.ArgumentParser(description="Run a prompt + PDF through multiple models")
    parser.add_argument("pdf", nargs="?", help="Path to PDF file")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="Models to use")
    parser.add_argument("--prompt", default=None, help="Custom prompt text (use {source_text} for PDF)")
    parser.add_argument("--prompt-file", default=None, help="Read prompt from file (YAML or plain text)")
    parser.add_argument("--outdir", default=None, help="Save each response to a file in this dir")
    args = parser.parse_args()

    # Extract PDF text
    pdf_text = ""
    if args.pdf:
        pdf_path = Path(args.pdf).resolve()
        if not pdf_path.exists():
            print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Extracting text from {args.pdf} ...")
        pdf_text = extract_pdf_text(str(pdf_path))
        print(f"Extracted {len(pdf_text):,} characters from PDF\n")

    # Resolve prompt
    system = DEFAULT_SYSTEM
    if args.prompt_file:
        file_system, prompt = load_prompt_file(args.prompt_file)
        if file_system:
            system = file_system
    elif args.prompt:
        prompt = args.prompt
    else:
        prompt = DEFAULT_PROMPT

    # Inject PDF text into prompt
    if "{source_text}" in prompt:
        prompt = prompt.replace("{source_text}", pdf_text)
    elif pdf_text:
        prompt = prompt + "\n\n--- Source Text ---\n" + pdf_text

    outdir = Path(args.outdir) if args.outdir else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    for model in args.models:
        print(f"\n{'=' * 60}")
        print(f"Model: {model}")
        print(f"{'=' * 60}")

        result = run_model(model, system, prompt)

        if "error" in result:
            print(f"ERROR: {result['error']}")
            continue

        print(f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
        print(f"Time:   {result['elapsed']}s")
        print(f"{'-' * 60}")
        print(result["response"])

        if outdir:
            safe_name = model.replace("/", "_")
            (outdir / f"{safe_name}.txt").write_text(result["response"])
            print(f"\nSaved to {outdir / safe_name}.txt")


if __name__ == "__main__":
    main()
