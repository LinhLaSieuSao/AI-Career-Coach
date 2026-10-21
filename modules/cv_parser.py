import os
import pdfplumber
import docx

def extract_text(file_path: str) -> str:
    """
    Trích xuất văn bản thô từ tệp PDF hoặc DOCX.
    Đầu vào: Đường dẫn tệp (file_path)
    Đầu ra: Chuỗi văn bản thô (str)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp tại đường dẫn: {file_path}")
    
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if file_extension == '.pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            raise ValueError(f"Không thể đọc tệp PDF. Lỗi: {str(e)}")
            
    elif file_extension == '.docx':
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            raise ValueError(f"Không thể đọc tệp DOCX. Lỗi: {str(e)}")
    else:
        raise ValueError("Định dạng tệp không được hỗ trợ. Vui lòng tải lên PDF hoặc DOCX.")
        
    return text.strip()