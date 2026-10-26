"""Synthetic documents containing no personal CV data."""

from io import BytesIO

import docx


def pdf_bytes(text="", *, image=False, vector=False, pages=1):
    if type(pages) is not int or pages < 1:
        raise ValueError("pages must be a positive integer")
    if pages != 1 and (image or vector):
        raise ValueError("image/vector fixtures support one page")
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    if image:
        content = b"q 600 0 0 780 0 0 cm /Im0 Do Q"
    if vector:
        content = b"0 0 m 100 100 l S"
    font_id = 3 + pages * 2
    image_id = font_id + 1
    kids = " ".join(f"{3 + page * 2} 0 R" for page in range(pages))
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {pages} >>".encode())
    for page in range(pages):
        page_id = 3 + page * 2
        resources = f"/Font << /F1 {font_id} 0 R >>"
        if image:
            resources += f" /XObject << /Im0 {image_id} 0 R >>"
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << {resources} >> /Contents {page_id + 1} 0 R >>".encode()
        )
        objects.append(
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    if image:
        objects.append(b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >>\nstream\n\xff\xff\xff\nendstream")
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(result)


def docx_bytes(text=""):
    document = docx.Document()
    if text:
        document.add_paragraph(text)
    result = BytesIO()
    document.save(result)
    return result.getvalue()
