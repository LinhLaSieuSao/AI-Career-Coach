import logging
from io import BytesIO
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str | Path | BytesIO) -> str:
    """Extract all textual content from a PDF file using *pdfplumber*.

    Parameters
    ----------
    pdf_path: str | Path | BytesIO
        Path to a PDF file or an in-memory PDF byte stream.

    Returns
    -------
    str
        The concatenated text of all pages. Returns an empty string if the
        file cannot be opened or read.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # ``extract_text`` may return ``None`` for a page without text.
            page_texts = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(page_texts)
    except Exception as exc:  # noqa: BLE001 – broad capture for any PDF read error
        logger.error("Failed to extract text from %s: %s", pdf_path, exc)
        # Return an empty string so callers can handle the failure gracefully.
        return ""

