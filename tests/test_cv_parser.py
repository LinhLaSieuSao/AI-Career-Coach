import pytest
import os
from modules.cv_parser import extract_text

def test_extract_text_invalid_format():
    """Kiểm tra xem hàm có ném ra ValueError khi truyền định dạng sai không"""
    fake_file = "dummy_resume.txt"
    with open(fake_file, "w", encoding="utf-8") as f:
        f.write("Nội dung test")

    try:
        with pytest.raises(ValueError, match="Định dạng tệp không được hỗ trợ"):
            extract_text(fake_file)
    finally:
        if os.path.exists(fake_file):
            os.remove(fake_file)

def test_file_not_found():
    """Kiểm tra xem hàm có báo lỗi FileNotFoundError khi đường dẫn không tồn tại không"""
    with pytest.raises(FileNotFoundError):
        extract_text("duong_dan_ao_khong_ton_tai.pdf")