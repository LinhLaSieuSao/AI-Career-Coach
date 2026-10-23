"""Trích xuất văn bản từ CV (PDF hoặc DOCX)."""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path
from typing import BinaryIO

import docx
import pdfplumber
from docx.table import Table
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)

FileSource = str | Path | BinaryIO


def _rewind(source: FileSource) -> None:
    """Đưa file-like object về đầu trước khi đọc."""
    if isinstance(source, (str, Path)):
        return
    seek = getattr(source, "seek", None)
    if callable(seek):
        seek(0)


def _normalize_text(parts: list[str]) -> str:
    """Ghép nội dung và chuẩn hóa dấu Unicode về NFC."""
    return unicodedata.normalize("NFC", "\n".join(parts))


def extract_text_from_pdf(pdf_source: FileSource) -> str:
    """Trích xuất văn bản từ PDF; trả chuỗi rỗng nếu không đọc được."""
    try:
        _rewind(pdf_source)
        with pdfplumber.open(pdf_source) as pdf:
            page_texts = [page.extract_text() or "" for page in pdf.pages]
        return _normalize_text(page_texts)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to extract text from PDF: %s", exc)
        return ""


def _iter_docx_content(container):
    """Duyệt paragraph và table theo thứ tự; hỗ trợ table lồng nhau."""
    for block in container.iter_inner_content():
        if isinstance(block, Paragraph):
            yield block.text
        elif isinstance(block, Table):
            yield from _iter_table_content(block)


def _iter_table_content(table: Table):
    """Duyệt nội dung bảng; chỉ đọc một lần mỗi ô gộp trong bảng."""
    seen_cells = set()
    for row in table.rows:
        for cell in row.cells:
            xml_cell = cell._tc
            if xml_cell in seen_cells:
                continue
            seen_cells.add(xml_cell)
            yield from _iter_docx_content(cell)


def extract_text_from_docx(docx_source: FileSource) -> str:
    """Trích xuất nội dung DOCX theo thứ tự, gồm bảng và bảng lồng nhau."""
    try:
        _rewind(docx_source)
        document = docx.Document(docx_source)
        parts = list(_iter_docx_content(document))
        return _normalize_text(parts)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to extract text from DOCX: %s", exc)
        return ""


def extract_text(source: FileSource, filename: str | None = None) -> str:
    """Chọn parser theo đuôi tệp."""
    name = filename or getattr(source, "name", None)
    if name is None and isinstance(source, (str, Path)):
        name = str(source)

    suffix = Path(name).suffix.lower() if name else ""
    if suffix == ".pdf":
        return extract_text_from_pdf(source)
    if suffix == ".docx":
        return extract_text_from_docx(source)

    raise ValueError(
        "Định dạng tệp không được hỗ trợ. Vui lòng tải lên PDF hoặc DOCX."
    )
