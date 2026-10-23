"""Streamlit entry point for the AI Career Coach sample application."""

from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from modules import (
    build_profile,
    calculate_match_score,
    extract_text,
    generate_interview_questions,
    get_course_recommendations,
)

# Cấu hình đường dẫn thư mục Data
PROJECT_DIR = Path(__file__).resolve().parent
CAREERS_PATH = PROJECT_DIR / "Data" / "roles.json"

def load_positions() -> list[dict]:
    """Load the role list from the bundled sample careers file."""
    try:
        with CAREERS_PATH.open(encoding="utf-8") as data_file:
            return json.load(data_file).get("positions", [])
    except FileNotFoundError:
        return []

def main():
    st.set_page_config(page_title="AI Career Coach", page_icon="🎯", layout="wide")
    st.title("🎯 AI Career Coach")
    st.markdown("Hệ thống phân tích CV và đối chiếu Yêu cầu tuyển dụng (JD).")

    # Đọc danh sách vị trí
    positions = load_positions()
    position_titles = [p.get("title", "Unknown") for p in positions] if positions else ["Chưa có dữ liệu"]
    
    with st.form("cv_analysis_form"):
        st.subheader("Thông tin đầu vào")
        
        selected_role = st.selectbox("Chọn vị trí mục tiêu", options=position_titles)
        
        job_description = st.text_area(
            "Nhập mô tả công việc (JD - Job Description)",
            height=150
        )

        # Giao diện tải CV đã cập nhật chuẩn DOCX/PDF
        uploaded_cv = st.file_uploader(
            "Tải CV định dạng PDF hoặc DOCX (không bắt buộc)",
            type=["pdf", "docx"],
        )

        submitted = st.form_submit_button("Phân tích")

    # Xử lý logic khi bấm submit
    if submitted:
        if uploaded_cv or job_description.strip():
            with st.spinner("Đang xử lý dữ liệu..."):
                try:
                    # Gọi hàm đọc CV mới (hỗ trợ cả file PDF và Word)
                    cv_text = (
                        extract_text(uploaded_cv, filename=uploaded_cv.name)
                        if uploaded_cv
                        else ""
                    )

                    # Kiểm tra lỗi file scan hoặc rỗng
                    if uploaded_cv and not cv_text.strip():
                        st.session_state["match_error"] = (
                            "Không đọc được nội dung CV (có thể là file scan hoặc file hỏng)."
                        )
                    else:
                        st.session_state["match_score"] = calculate_match_score(
                            cv_text,
                            job_description,
                        )
                        # Xóa lỗi cũ nếu phân tích thành công
                        if "match_error" in st.session_state:
                            del st.session_state["match_error"]
                            
                except ValueError as exc:
                    st.session_state["match_error"] = str(exc)
        else:
            st.warning("Vui lòng tải lên CV hoặc nhập Mô tả công việc (JD).")

    # Hiển thị kết quả ra màn hình
    if "match_error" in st.session_state:
        st.error(st.session_state["match_error"])
    elif "match_score" in st.session_state:
        st.success("✅ Trích xuất và phân tích thành công!")
        st.write(st.session_state["match_score"])

if __name__ == "__main__":
    main()