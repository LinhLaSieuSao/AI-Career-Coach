"""Streamlit entry point for the AI Career Coach sample application."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import streamlit as st

from modules import (
    build_profile,
    calculate_match_score,
    extract_text_from_pdf,
    generate_interview_questions,
    get_course_recommendations,
)


PROJECT_DIR = Path(__file__).resolve().parent
CAREERS_PATH = PROJECT_DIR / "Data" / "roles.json"


def load_positions() -> list[dict]:
    """Load the role list from the bundled sample careers file."""
    with CAREERS_PATH.open(encoding="utf-8") as data_file:
        return json.load(data_file).get("positions", [])


def run_app() -> None:
    st.set_page_config(page_title="AI Career Coach", page_icon="🧭")
    st.title("AI Career Coach")
    st.write("Tạo hồ sơ kỹ năng và kinh nghiệm để nhận gợi ý học tập.")

    with st.form("profile_form"):
        skills_text = st.text_area(
            "Kỹ năng",
            placeholder="Python, SQL\ninteresting: play games",
            help="Có thể phân tách bằng dấu phẩy, dấu chấm phẩy hoặc xuống dòng.",
        )
        interests_text = st.text_area("Sở thích", placeholder="Phân tích dữ liệu, đọc sách")
        experience_text = st.text_area(
            "Kinh nghiệm",
            placeholder="Công Ty A, Data Intern, 2024",
            help="Nội dung được giữ như văn bản tự do; dấu phẩy không dùng để tách mục.",
        )
        positions = load_positions()
        role_titles = [position["title"] for position in positions]
        selected_role = st.selectbox("Vị trí quan tâm", role_titles)
        uploaded_cv = st.file_uploader("CV dạng PDF (tùy chọn)", type=["pdf"])
        job_description = st.text_area("Mô tả công việc để so khớp (tùy chọn)")
        submitted = st.form_submit_button("Tạo hồ sơ")

    if submitted:
        st.session_state["profile_result"] = build_profile(
            {"skills": skills_text, "interests": interests_text, "experience": experience_text}
        )
        st.session_state["match_score"] = None
        st.session_state["match_error"] = None
        if uploaded_cv or job_description.strip():
            cv_text = (
                extract_text_from_pdf(BytesIO(uploaded_cv.getvalue()))
                if uploaded_cv
                else ""
            )
            try:
                st.session_state["match_score"] = calculate_match_score(cv_text, job_description)
            except ValueError as exc:
                st.session_state["match_error"] = str(exc)

    profile = st.session_state.get("profile_result")
    if not profile:
        return

    if st.session_state.get("match_error"):
        st.error(f"Không thể tính điểm so khớp CV: {st.session_state['match_error']}")
    elif st.session_state.get("match_score") is not None:
        st.metric("Mức độ tương đồng giữa CV và mô tả công việc", f"{st.session_state['match_score']}%")

    for index, item in enumerate(profile["moved"]):
        left, right = st.columns([4, 1])
        left.info(f"Đã chuyển ‘{item['item']}’ từ {item['from']} sang {item['to']}.")
        if right.button("Hoàn tác", key=f"undo_move_{index}"):
            profile["interests"] = [
                interest for interest in profile["interests"]
                if interest.casefold() != item["item"].casefold()
            ]
            profile["skills"].append(item["item"])
            profile["moved"].pop(index)
            profile["skills"] = sorted(set(profile["skills"]), key=str.casefold)
            st.session_state["profile_result"] = profile
            st.success(f"Đã hoàn tác: ‘{item['item']}’ được chuyển lại sang Kỹ năng.")

    retained_unknowns: list[str] = []
    if profile["unrecognized_skills"]:
        st.subheader("Kỹ năng chưa nhận diện")
        st.caption("Bạn có muốn giữ các mục này trong hồ sơ không?")
        for index, skill in enumerate(profile["unrecognized_skills"]):
            if st.checkbox(f"Giữ ‘{skill}’ trong hồ sơ", value=True, key=f"keep_unknown_{index}_{skill}"):
                retained_unknowns.append(skill)

    effective_skills = [
        skill for skill in profile["skills"]
        if skill not in profile["unrecognized_skills"] or skill in retained_unknowns
    ]

    st.subheader("Hồ sơ của bạn")
    st.write("**Kỹ năng:**", ", ".join(effective_skills) or "Chưa có")
    st.write("**Sở thích:**", ", ".join(profile["interests"]) or "Chưa có")
    st.write("**Kinh nghiệm:**", profile["experience"] or "Chưa có")

    position = next((entry for entry in positions if entry["title"] == selected_role), None)
    required = position.get("required_skills", []) if position else []
    known_skill_keys = {skill.casefold() for skill in effective_skills}
    missing_skills = [skill for skill in required if skill.casefold() not in known_skill_keys]

    st.subheader(f"Gợi ý cho vị trí {selected_role}")
    st.write("**Kỹ năng cần bổ sung:**", ", ".join(missing_skills) or "Không có")
    courses = get_course_recommendations(missing_skills)
    if courses:
        st.write("**Khóa học gợi ý:**")
        for course in courses:
            st.markdown(f"- [{course['course_name']}]({course['link']})")
    questions = generate_interview_questions(missing_skills, role=selected_role)
    if questions:
        st.write("**Câu hỏi phỏng vấn luyện tập:**")
        for question in questions:
            st.markdown(f"- {question}")


if __name__ == "__main__":
    run_app()
