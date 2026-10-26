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
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 10


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


def _read_pdf(source: FileSource) -> tuple[str, bool, int, int, bool]:
    """Read at most MAX_PDF_PAGES and report whether the document was capped."""
    _rewind(source)
    with pdfplumber.open(source) as pdf:
        parts = []
        total_pages = len(pdf.pages)
        pages = pdf.pages[:MAX_PDF_PAGES]
        image_only = bool(pages)
        for page in pages:
            parts.append(page.extract_text() or "")
            image_only = image_only and bool(page.images) and not page.chars
        return _normalize_text(parts), image_only, len(pages), total_pages, total_pages > len(pages)


def extract_text_from_pdf(pdf_source: FileSource) -> str:
    """Trích xuất văn bản từ PDF; trả chuỗi rỗng nếu không đọc được."""
    try:
        if (_source_size(pdf_source) or 0) > MAX_UPLOAD_BYTES:
            logger.warning("PDF exceeds the configured upload limit.")
            return ""
        return _read_pdf(pdf_source)[0]
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
        if (_source_size(docx_source) or 0) > MAX_UPLOAD_BYTES:
            logger.warning("DOCX exceeds the configured upload limit.")
            return ""
        return _read_docx(docx_source)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to extract text from DOCX: %s", exc)
        return ""


def _read_docx(source: FileSource) -> str:
    """Share ordered paragraph/table traversal without swallowing read errors."""
    _rewind(source)
    return _normalize_text(list(_iter_docx_content(docx.Document(source))))


def _suffix(source: FileSource | None, filename: str | None) -> str:
    name = filename or getattr(source, "name", None)
    if name is None and isinstance(source, (str, Path)):
        name = str(source)
    return Path(name).suffix.lower() if name else ""


def extract_text(source: FileSource, filename: str | None = None) -> str:
    """Legacy API: unsupported suffix raises, read failure returns empty text."""
    suffix = _suffix(source, filename)
    if suffix == ".pdf":
        return extract_text_from_pdf(source)
    if suffix == ".docx":
        return extract_text_from_docx(source)

    raise ValueError(
        "Định dạng tệp không được hỗ trợ. Vui lòng tải lên PDF hoặc DOCX."
    )


_MESSAGES = {
    "NO_FILE": "Chưa có tệp CV. Hãy tải lên PDF hoặc DOCX.",
    "UNREADABLE": "Không đọc được tệp CV. Tệp có thể bị hỏng hoặc được bảo vệ.",
    "EMPTY": "Tệp CV không có văn bản trích xuất được. Hãy dùng tệp có nội dung văn bản.",
    "UNSUPPORTED_FORMAT": "Định dạng tệp không được hỗ trợ. Vui lòng tải lên PDF hoặc DOCX.",
    "SCANNED_PDF": "PDF chứa các trang ảnh không có lớp văn bản; ứng dụng chưa hỗ trợ OCR.",
    "FILE_TOO_LARGE": "Tệp CV vượt giới hạn 10 MB. Hãy chọn tệp nhỏ hơn.",
    "INVALID_SIGNATURE": "Nội dung tệp không khớp phần mở rộng PDF hoặc DOCX. Hãy chọn đúng định dạng CV.",
}


def _source_size(source: FileSource) -> int | None:
    """Read a byte size without consuming an upload stream."""
    if isinstance(source, (str, Path)):
        return Path(source).stat().st_size
    size = getattr(source, "size", None)
    if isinstance(size, int) and not isinstance(size, bool) and size >= 0:
        return size
    getbuffer = getattr(source, "getbuffer", None)
    if callable(getbuffer):
        try:
            return getbuffer().nbytes
        except (BufferError, OSError, ValueError):
            pass
    tell, seek = getattr(source, "tell", None), getattr(source, "seek", None)
    if callable(tell) and callable(seek):
        try:
            position = tell()
            seek(0, 2)
            size = tell()
            seek(position)
            return size if isinstance(size, int) and size >= 0 else None
        except (OSError, ValueError):
            try:
                seek(0)
            except (OSError, ValueError):
                pass
    return None


def _has_expected_signature(source: FileSource, suffix: str) -> bool:
    """Check the leading signature before passing an upload to a document parser."""
    expected = {".pdf": b"%PDF", ".docx": b"PK\x03\x04"}[suffix]
    if isinstance(source, (str, Path)):
        with Path(source).open("rb") as handle:
            prefix = handle.read(4)
    else:
        _rewind(source)
        prefix = source.read(4)
        _rewind(source)
    return prefix == expected


def parse_document(source: FileSource | None, filename: str | None = None) -> dict:
    """Return text/error_code/message, classifying errors from the actual read.

    Missing source/path is NO_FILE. Zero bytes or a readable document without
    text is EMPTY. SCANNED_PDF requires raster images and no text characters
    on every page, not merely an empty extraction. No OCR is attempted.
    The caller owns file-like streams; consumed streams are rewound.
    """
    def failure(code: str, **metadata) -> dict:
        return {"text": "", "error_code": code, "message": _MESSAGES[code],
                "page_truncated": False, "pages_read": 0, "total_pages": None, **metadata}

    if source is None or isinstance(source, (str, Path)) and not str(source):
        return failure("NO_FILE")
    try:
        if isinstance(source, (str, Path)) and not Path(source).exists():
            return failure("NO_FILE")
        suffix = _suffix(source, filename)
        if suffix not in {".pdf", ".docx"}:
            return failure("UNSUPPORTED_FORMAT")
        size = _source_size(source)
        if size is not None and size > MAX_UPLOAD_BYTES:
            return failure("FILE_TOO_LARGE", size_bytes=size, max_bytes=MAX_UPLOAD_BYTES)
        if isinstance(source, (str, Path)):
            empty = Path(source).stat().st_size == 0
        else:
            _rewind(source)
            empty = source.read(1) == b""
            _rewind(source)
        if empty:
            return failure("EMPTY")
        if not _has_expected_signature(source, suffix):
            return failure("INVALID_SIGNATURE")
        if suffix == ".pdf":
            text, image_only, pages_read, total_pages, page_truncated = _read_pdf(source)
        else:
            text, image_only = _read_docx(source), False
            pages_read, total_pages, page_truncated = 0, None, False
    except Exception as exc:  # noqa: BLE001 - malformed user uploads must be reported
        logger.error("Failed to parse CV: %s", exc)
        return failure("UNREADABLE")
    if not text.strip():
        return failure(
            "SCANNED_PDF" if image_only else "EMPTY",
            page_truncated=page_truncated,
            pages_read=pages_read,
            total_pages=total_pages,
        )
    return {"text": text, "error_code": None, "message": "",
            "page_truncated": page_truncated, "pages_read": pages_read,
            "total_pages": total_pages}
