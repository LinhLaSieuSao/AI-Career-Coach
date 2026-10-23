from io import BytesIO

import docx
import pytest

from modules.cv_parser import extract_text

def _minimal_pdf_bytes(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"),
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    )
    pdf.extend(trailer.encode("ascii"))
    return bytes(pdf)

def _docx_bytes(document: docx.Document) -> BytesIO:
    source = BytesIO()
    document.save(source)
    source.seek(0)
    return source

def test_unsupported_format_raises_value_error():
    with pytest.raises(ValueError, match="Định dạng tệp không được hỗ trợ"):
        extract_text("resume.txt")

def test_missing_pdf_path_returns_empty_string():
    assert extract_text("khong_ton_tai.pdf") == ""

def test_extract_valid_pdf_from_bytesio():
    source = BytesIO(_minimal_pdf_bytes("Python developer"))
    source.seek(0, 2)  # Parser must rewind an already-consumed upload.
    assert "Python developer" in extract_text(source, filename="resume.pdf")

def test_extract_docx_from_bytesio():
    document = docx.Document()
    document.add_paragraph("Python developer")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "SQL and data engineering"
    extracted = extract_text(_docx_bytes(document), filename="resume.docx")
    assert "Python developer" in extracted
    assert "SQL and data engineering" in extracted
