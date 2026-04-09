"""PDF text extraction utilities."""

from __future__ import annotations

import pymupdf


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF using pymupdf.

    Args:
        pdf_path: absolute or relative path to a PDF file.

    Returns:
        Concatenated text from all pages, separated by double newlines.

    Raises:
        RuntimeError: if pymupdf cannot open/parse the file.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        msg = f"Failed to open PDF: {pdf_path}"
        raise RuntimeError(msg) from exc

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)
