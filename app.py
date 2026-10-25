"""AI Career Coach community landing page and career planning toolkit."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from uuid import uuid4

import streamlit as st

from modules import (
    build_roadmap,
    match_role,
    get_question_feedback,
    get_questions,
    compute_gap,
    suggest_roles,
    build_timed_roadmap,
    score_answer,
)
from modules.catalog import DATA_DIR, load_roles
from modules.profile import undo_profile_move
from modules.submission import prepare_submission
from modules.export import export_report


PROJECT_DIR = Path(__file__).resolve().parent
CAREERS_PATH = DATA_DIR / "roles.json"
LOGO_PATH = PROJECT_DIR / "brand_assets" / "LogoAICC.jpg"
STYLE_PATH = PROJECT_DIR / "assets" / "style.css"
DEMO_PROFILES_PATH = DATA_DIR / "demo_profiles.json"
RESULT_TABS = ("Tóm tắt", "Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn")
SKILL_NAMES_VI = {
    "data visualization": "Trực quan hóa dữ liệu",
    "statistical analysis": "Phân tích thống kê",
    "rest api design": "Thiết kế REST API",
    "database management": "Quản lý cơ sở dữ liệu",
    "machine learning": "Học máy",
    "deep learning": "Học sâu",
    "data manipulation": "Thao tác dữ liệu",
    "query optimization": "Tối ưu truy vấn",
    "supervised learning": "Học có giám sát",
    "model evaluation": "Đánh giá mô hình",
    "report building": "Xây dựng báo cáo",
}


@st.cache_data(max_entries=1)
def load_positions() -> list[dict]:
    """Use the same catalog rules as Profile, Matcher, and Interview."""
    return sorted(load_roles(CAREERS_PATH), key=lambda role: role["name_vi"].casefold())


@st.cache_data(max_entries=1)
def load_resources() -> dict:
    with (DATA_DIR / "resources.json").open(encoding="utf-8") as source:
        return json.load(source)


@st.cache_data(max_entries=1)
def load_demo_profiles() -> list[dict]:
    with DEMO_PROFILES_PATH.open(encoding="utf-8") as source:
        demos = json.load(source)
    if not isinstance(demos, list) or any(not item.get("synthetic") for item in demos):
        raise ValueError("Data/demo_profiles.json must contain explicitly synthetic profiles.")
    return demos


def format_role(position: dict) -> str:
    """Show the Vietnamese role name and the source role title when useful."""
    name_vi = position.get("name_vi", position.get("title", ""))
    title = position.get("title", "")
    return name_vi if name_vi == title else f"{name_vi} · {title}"


def logo_data_uri() -> str:
    """Return the supplied logo, or a small built-in mark, as an image URI."""
    if LOGO_PATH.is_file():
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    fallback_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="72" '
        'viewBox="0 0 96 72"><rect width="96" height="72" rx="18" '
        'fill="#1556A8"/><text x="48" y="48" text-anchor="middle" '
        'font-family="Arial,sans-serif" font-size="34" font-weight="700" '
        'fill="#fff">AI</text></svg>'
    )
    encoded = base64.b64encode(fallback_svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def display_skill(skill: str) -> str:
    """Translate descriptive skill labels while preserving technology names."""
    return SKILL_NAMES_VI.get(skill.casefold(), skill)


def _level_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Level trùng khóa JSON: {key}.")
        result[key] = value
    return result


def inject_styles() -> None:
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_landing_page() -> None:
    logo = logo_data_uri()
    st.markdown(
        f"""
        <div class="hero-wrap" id="top">
          <div class="topbar">
            <a class="brand" href="#top"><img src="{logo}" alt="Biểu trưng AI Career Coach"><span class="brand-word">AI CAREER COACH<span>CÔNG CỤ ĐỊNH HƯỚNG</span></span></a>
            <nav class="nav-links"><a href="#why">Về công cụ</a><a href="#how">Cách hoạt động</a><a class="nav-cta" href="#career-toolkit">Bắt đầu ngay&nbsp; →</a></nav>
          </div>
          <div class="hero">
            <div>
              <div class="eyebrow">Công cụ định hướng nghề nghiệp</div>
              <h1>Tự tin chọn <em>con đường sự nghiệp</em> của bạn.</h1>
              <div class="hero-copy">Tổng hợp kỹ năng, đối chiếu với yêu cầu nghề nghiệp và biến mục tiêu thành các bước học tập có căn cứ.</div>
              <div class="hero-actions"><a class="button-primary" href="#career-toolkit">Khám phá hồ sơ nghề nghiệp&nbsp; →</a><a class="text-link" href="#why">Xem cách hoạt động <span>↓</span></a></div>
              <div class="social-proof"><span>Ứng dụng mã nguồn mở · xử lý bằng quy tắc có thể kiểm tra</span></div>
            </div>
            <div class="hero-art" aria-label="Minh họa hồ sơ nghề nghiệp">
              <div class="orbit"></div>
              <div class="career-card"><div class="card-kicker"><span>Minh họa tổng hợp</span><span class="live">DỮ LIỆU VÍ DỤ</span></div><div class="role-row"><div class="role-icon">✳</div><div><div class="role-title">Phân tích dữ liệu</div><div class="role-sub">Ví dụ kỹ năng, không phải kết quả người dùng</div></div></div><div class="skills"><span class="skill">Python</span><span class="skill">Phân tích dữ liệu</span><span class="skill">SQL</span></div></div>
              <div class="floating float-top"><strong><span class="spark">✦</span>Lộ trình của bạn</strong>Từng bước nhỏ, tiến xa hơn</div>
              <div class="floating float-bottom"><strong>Học tập có định hướng</strong>Kỹ năng · Tài liệu · Luyện tập</div>
            </div>
          </div>
        </div>
        <section class="section" id="why"><div class="section-heading"><div class="eyebrow">Biến mục tiêu thành hành động</div><h2>Rõ hướng đi, vững bước tiến</h2><p>Hành trình sự nghiệp sẽ dễ dàng hơn khi bạn hiểu mình đang ở đâu, nên tập trung vào điều gì tiếp theo và có thể tìm sự hỗ trợ ở đâu. Hãy bắt đầu từ những gì bạn đã có.</p></div>
          <div class="feature-grid">
            <article class="feature"><div class="feature-icon">⌕</div><h3>Nhận diện thế mạnh</h3><p>Tổng hợp kỹ năng, sở thích và kinh nghiệm để hiểu rõ những giá trị bạn có thể mang đến.</p></article>
            <article class="feature"><div class="feature-icon">◎</div><h3>Tìm công việc phù hợp</h3><p>Đối chiếu kỹ năng hiện tại với vị trí bạn quan tâm và khám phá những cơ hội phía trước.</p></article>
            <article class="feature"><div class="feature-icon">↗</div><h3>Bổ sung kỹ năng cần thiết</h3><p>Xác định năng lực nên trau dồi tiếp theo để việc học có mục tiêu và định hướng rõ ràng.</p></article>
            <article class="feature"><div class="feature-icon">▤</div><h3>Lập lộ trình học tập</h3><p>Tìm khóa học và tài liệu phù hợp để biến mục tiêu nghề nghiệp thành tiến bộ mỗi ngày.</p></article>
            <article class="feature"><div class="feature-icon">✧</div><h3>Luyện phỏng vấn tự tin</h3><p>Thực hành với các câu hỏi phỏng vấn gắn với vị trí bạn đang hướng đến.</p></article>
            <article class="feature"><div class="feature-icon">♡</div><h3>Tự học theo định hướng</h3><p>Tham khảo tài liệu, ghi nhận gap và luyện tập theo mục tiêu cá nhân.</p></article>
          </div>
        </section>
        <section class="path-section" id="how"><div class="path-inner"><div class="path-copy"><div class="eyebrow">Bắt đầu thật đơn giản</div><h2>Chủ động cho bước tiến tiếp theo.</h2><p>Bạn không cần phải có sẵn mọi câu trả lời. Một chút rõ ràng có thể biến câu hỏi lớn về nghề nghiệp thành vài việc cụ thể để bắt đầu.</p><div class="path-list"><div class="path-item"><span class="check">✓</span>Bắt đầu từ kỹ năng và kinh nghiệm bạn đang có</div><div class="path-item"><span class="check">✓</span>Chọn vị trí hoặc hướng đi bạn quan tâm</div><div class="path-item"><span class="check">✓</span>Nhận gợi ý học tập và luyện tập thiết thực</div></div></div>
          <div class="steps"><article class="step"><div class="step-num">01</div><div><h3>Tạo hồ sơ cá nhân</h3><p>Nhập kỹ năng, sở thích, kinh nghiệm hoặc tải CV để bắt đầu.</p></div></article><article class="step"><div class="step-num">02</div><div><h3>Khám phá mức độ phù hợp</h3><p>Tìm hiểu yêu cầu của vị trí mục tiêu và xác định kỹ năng cần phát triển.</p></div></article><article class="step"><div class="step-num">03</div><div><h3>Tự tin tiến thêm một bước</h3><p>Nhận gợi ý học tập và câu hỏi phỏng vấn phù hợp với định hướng của bạn.</p></div></article></div>
          </div></section>
        """,
        unsafe_allow_html=True,
    )


def render_closing_sections() -> None:
    st.markdown(
        """
        <section class="community"><div class="community-box"><div class="eyebrow">Bắt đầu với dữ liệu của bạn</div><h2>Mỗi gợi ý đều có thể xem lại.</h2><p>Điểm đối chiếu, khoảng cách và tài liệu tham khảo được trình bày riêng để bạn tự đánh giá và chọn bước tiếp theo.</p><a class="button-light" href="#career-toolkit">Tạo hồ sơ nghề nghiệp&nbsp; →</a></div></section>
        <div class="footer"><span><b>AI Career Coach</b> &nbsp;·&nbsp; Ứng dụng mã nguồn mở.</span><span>Điểm heuristic không phải xác suất tuyển dụng.</span></div>
        """,
        unsafe_allow_html=True,
    )


def render_toolkit() -> None:
    st.markdown(
        '<div class="tool-title" id="career-toolkit"><div class="eyebrow">Bắt đầu với bước tiếp theo</div><h2>Hồ sơ nghề nghiệp</h2><p>Chia sẻ một chút về bản thân để khám phá mức độ phù hợp với công việc, tài liệu học tập và nội dung luyện phỏng vấn.</p></div>',
        unsafe_allow_html=True,
    )
    positions = load_positions()
    role_by_id = {position["id"]: position for position in positions}
    if not role_by_id:
        st.error("Chưa có dữ liệu vị trí nghề nghiệp trong Data/roles.json.")
        return

    pending_demo = st.session_state.pop("pending_demo_profile_id", None)
    if pending_demo:
        demo = next((item for item in load_demo_profiles() if item["id"] == pending_demo), None)
        if demo and demo["role_id"] in role_by_id:
            values = demo["profile"]
            st.session_state["skills_input"] = "; ".join(values["skills"])
            st.session_state["levels_input"] = json.dumps(values["levels"], ensure_ascii=False)
            st.session_state["interests_input"] = "; ".join(values["interests"])
            st.session_state["experience_input"] = values["experience"]
            st.session_state["career_role_picker"] = demo["role_id"]
            st.session_state["job_description_input"] = ""
            st.session_state.pop("uploaded_cv_input", None)
            candidate = prepare_submission(values, None)
            if candidate["accepted"]:
                for key in list(st.session_state):
                    if key.startswith(("keep_unknown_", "undo_move_", "answer_", "interview_", "start_interview_")):
                        del st.session_state[key]
                st.session_state.update({
                    "career_role_id": demo["role_id"],
                    "profile_result": candidate["profile"],
                    "profile_original_interests": candidate["original_interests"],
                    "profile_revision": st.session_state.get("profile_revision", 0) + 1,
                    "cv_jd_result": None,
                    "cv_extraction": None,
                    "submission_errors": [],
                    "submission_rejected": False,
                    "submission_notice": f"Đã nạp hồ sơ tổng hợp “{demo['label']}”. {demo['notice']}",
                    "active_demo_profile_id": demo["id"],
                })

    pending_role = st.session_state.pop("pending_career_role", None)
    if pending_role in role_by_id:
        st.session_state["career_role_picker"] = pending_role

    with st.container(border=True):
        st.subheader("Dùng hồ sơ mẫu tổng hợp")
        st.caption("Ví dụ dùng role/skill thật trong catalog; không đại diện người thật, kinh nghiệm thật hay kết quả tuyển dụng.")
        cols = st.columns(3)
        for col, demo in zip(cols, load_demo_profiles()):
            col.button(
                f"Dùng hồ sơ mẫu · {demo['label']}",
                key=f"use_demo_{demo['id']}",
                on_click=lambda demo_id=demo["id"]: st.session_state.update({"pending_demo_profile_id": demo_id}),
            )

    with st.form("profile_form"):
        skills_text = st.text_area("Kỹ năng", placeholder="Python, SQL, phân tích dữ liệu", key="skills_input")
        st.caption("Ngăn cách các kỹ năng bằng dấu phẩy, dấu chấm phẩy hoặc xuống dòng.")
        levels_text = st.text_area(
            "Level tự khai báo (JSON, không bắt buộc)",
            placeholder='{"Python": 2, "SQL": 1}',
            help="0: chưa có; 1: cơ bản cần hướng dẫn; 2: độc lập tác vụ quen; 3: tác vụ phức tạp. Không suy level từ CV.",
            key="levels_input",
        )
        interests_text = st.text_area("Sở thích nghề nghiệp", placeholder="Phân tích dữ liệu, thiết kế sản phẩm", key="interests_input")
        experience_text = st.text_area("Kinh nghiệm", placeholder="Mô tả ngắn về kinh nghiệm của bạn", key="experience_input")
        selected_role_id = st.selectbox(
            "Vị trí công việc bạn quan tâm", list(role_by_id),
            format_func=lambda value: format_role(role_by_id[value]), index=None,
            placeholder="Chọn vị trí để xem gợi ý (không bắt buộc)", key="career_role_picker",
        )
        uploaded_cv = st.file_uploader(
            "Tải CV định dạng PDF hoặc DOCX (không bắt buộc)", type=["pdf", "docx"],
            help="PDF cần có lớp văn bản; PDF scan dạng ảnh chưa được OCR.", key="uploaded_cv_input",
        )
        job_description = st.text_area("Mô tả công việc cần đối chiếu (không bắt buộc)", key="job_description_input")
        submitted = st.form_submit_button("Tạo hồ sơ nghề nghiệp")
    if submitted:
        try:
            levels = json.loads(levels_text, object_pairs_hook=_level_json_object) if levels_text.strip() else {}
            candidate = prepare_submission(
                {"skills": skills_text, "interests": interests_text, "experience": experience_text, "levels": levels},
                uploaded_cv, jd_text=job_description,
            )
        except (ValueError, TypeError) as exc:
            candidate = {"accepted": False, "errors": [f"Level chưa hợp lệ: {exc}"]}
        st.session_state["submission_errors"] = candidate["errors"]
        st.session_state["submission_rejected"] = not candidate["accepted"]
        if candidate["accepted"]:
            for key in list(st.session_state):
                if key.startswith(("keep_unknown_", "undo_move_", "answer_", "interview_", "start_interview_")):
                    del st.session_state[key]
            st.session_state.update({
                "career_role_id": selected_role_id,
                "profile_result": candidate["profile"],
                "profile_original_interests": candidate["original_interests"],
                "profile_revision": st.session_state.get("profile_revision", 0) + 1,
                "cv_jd_result": candidate["cv_jd_result"],
                "cv_extraction": candidate["cv_extraction"],
                "submission_notice": "Hồ sơ đã được cập nhật. Kết quả bên dưới phản ánh lần gửi này.",
                "active_demo_profile_id": None,
            })
    for error in st.session_state.get("submission_errors", []):
        st.error(error)
    profile = st.session_state.get("profile_result")
    if not profile:
        return
    if st.session_state.get("submission_rejected"):
        st.warning("Lần gửi mới chưa hợp lệ. Đang giữ hồ sơ đã lưu trước đó.")
    if st.session_state.get("submission_notice"):
        st.success(st.session_state["submission_notice"])

    revision = st.session_state.get("profile_revision", 0)
    tabs = st.tabs(RESULT_TABS)
    cv_jd = st.session_state.get("cv_jd_result")
    cv_extraction = st.session_state.get("cv_extraction")
    effective_skills = [
        skill for skill in profile["skills"]
        if skill not in profile["unrecognized_skills"]
        or st.session_state.get(f"keep_unknown_{revision}_{skill}", True)
    ]

    with tabs[0]:
        saved_role = next((item for item in load_positions() if item["id"] == st.session_state.get("career_role_id")), None)
        if saved_role:
            st.caption(f"Kết quả đã lưu gắn với vị trí: {format_role(saved_role)}.")
        if st.session_state.get("active_demo_profile_id"):
            st.info("Hồ sơ tổng hợp minh họa · không phải hồ sơ của người thật.")
        if cv_jd:
            st.metric("Mức độ phù hợp giữa CV và mô tả công việc", f"{cv_jd['percent']}%")
            st.caption("Tỷ lệ kỹ năng nhận diện trong JD có trong CV; không đánh giá mức độ thành thạo.")
            st.write("**Kỹ năng CV khớp JD:**", ", ".join(display_skill(s) for s in cv_jd["matched"]) or "Chưa có")
            st.write("**Kỹ năng JD còn thiếu trong CV:**", ", ".join(display_skill(s) for s in cv_jd["missing"]) or "Không có")
        if cv_extraction:
            if not cv_jd:
                st.info("Đã gộp kỹ năng nhận diện từ CV vào hồ sơ. Thêm JD để đối chiếu.")
            with st.expander(f"Văn bản đã trích xuất · {cv_extraction['filename']}"):
                st.caption(f"{len(cv_extraction['text']):,} ký tự")
                st.text_area("Nội dung CV", value=cv_extraction["text"], height=260, disabled=True, label_visibility="collapsed")
        for index, item in enumerate(profile["moved"]):
            left, right = st.columns([4, 1])
            left.info(f"Đã chuyển ‘{item['item']}’ từ {item['from']} sang {item['to']}.")
            if right.button("Hoàn tác", key=f"undo_move_{revision}_{index}"):
                st.session_state["profile_result"] = undo_profile_move(
                    profile, index, original_interests=st.session_state.get("profile_original_interests", [])
                )
                st.rerun()
        retained = []
        if profile["unrecognized_skills"]:
            st.subheader("Kỹ năng chưa nhận diện được")
            st.caption("Chọn kỹ năng muốn giữ lại trong hồ sơ.")
            for skill in profile["unrecognized_skills"]:
                if st.checkbox(f"Giữ ‘{skill}’ trong hồ sơ", value=True, key=f"keep_unknown_{revision}_{skill}"):
                    retained.append(skill)
        effective_skills = [
            skill for skill in profile["skills"]
            if skill not in profile["unrecognized_skills"] or skill in retained
        ]
        st.subheader("Hồ sơ của bạn")
        st.write("**Kỹ năng:**", ", ".join(display_skill(s) for s in effective_skills) or "Chưa có thông tin")
        st.write("**Sở thích:**", ", ".join(profile["interests"]) or "Chưa có thông tin")
        st.write("**Kinh nghiệm:**", profile["experience"] or "Chưa có thông tin")
        st.write("**Level đã khai báo:**", profile.get("levels", {}) or "Chưa khai báo; không suy từ CV")
        st.subheader("Vị trí gợi ý từ hồ sơ")
        st.caption("Điểm heuristic theo kỹ năng/sở thích; không là xác suất tuyển dụng hay đánh giá level.")
        suggestions = suggest_roles({**profile, "skills": effective_skills})
        if not suggestions:
            st.caption("Chưa có tín hiệu khớp catalog để xếp hạng vị trí.")
        for item in suggestions:
            st.markdown(f"**{item['role_name']}** · điểm gợi ý {item['score']}/100")
            st.caption("; ".join(item["reasons"]))
            if st.button(f"Chọn {item['role_name']}", key=f"choose_role_{revision}_{item['role_id']}"):
                st.session_state["career_role_id"] = item["role_id"]
                st.session_state["pending_career_role"] = item["role_id"]
                st.session_state.pop("interview_session", None)
                st.rerun()

    position = role_by_id.get(st.session_state.get("career_role_id"))
    has_signal = bool(effective_skills or profile.get("levels"))
    if position is None or not has_signal:
        gap_message = "Hãy chọn vị trí để xem khoảng cách." if position is None else "Chưa có kỹ năng để đối chiếu. Hãy bổ sung kỹ năng vào form hoặc CV."
        for tab, label in zip(tabs[1:], ["Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn"]):
            with tab:
                st.info(gap_message if label == "Khoảng cách" or not effective_skills else "Chưa có dữ liệu cho mục này.")
        if position:
            with tabs[3]:
                exported_profile = {**profile, "role_id": position["id"]}
                st.download_button("Tải báo cáo Markdown", export_report(exported_profile, None, []), "bao-cao-ho-so.md", "text/markdown")
                st.download_button("Tải báo cáo CSV", export_report(exported_profile, None, [], "csv"), "bao-cao-ho-so.csv", "text/csv")
        return

    role = position
    mode_key = f"assessment_mode_{revision}"
    selected_mode = st.session_state.get(mode_key, "Theo kỹ năng đã có")
    if st.session_state.get("assessment_snapshot") != (revision, selected_mode, role["id"]):
        st.session_state.pop("interview_session", None)
        st.session_state["assessment_snapshot"] = (revision, selected_mode, role["id"])
    presence = match_role(effective_skills, role)
    gap_result = None
    timed_result = None
    weekly_roadmap = None

    with tabs[1]:
        st.subheader(f"Đánh giá cho {format_role(role)}")
        mode = st.radio("Loại đánh giá", ["Theo kỹ năng đã có", "Theo level tự khai báo"], key=mode_key)
        if mode != selected_mode:
            st.session_state.pop("interview_session", None)
            st.session_state["assessment_snapshot"] = (revision, mode, role["id"])
        if mode == "Theo level tự khai báo":
            st.info("Skill role chưa khai báo level được tính current=0 cho lần đánh giá này; đây không phải kết luận rằng bạn kém kỹ năng đó.")
            confirmed = st.checkbox("Tôi đồng ý tính level chưa khai báo là 0 cho lần đánh giá này", key=f"confirm_levels_{revision}")
            if confirmed:
                levels = {k: v for k, v in profile.get("levels", {}).items()
                          if k not in profile["unrecognized_skills"] or k in effective_skills}
                gap_result = compute_gap(levels, role)
                st.metric("Mức độ đáp ứng theo level", f"{gap_result['match_percent']}%")
                st.progress(gap_result["match_percent"] / 100, text="Điểm level gap · từ level đã khai báo và quy ước current=0")
                st.dataframe(gap_result["items"], hide_index=True)
        else:
            st.metric("Mức độ đáp ứng kỹ năng vị trí", f"{presence['percent']}%")
            st.progress(presence["percent"] / 100, text="Presence score · kỹ năng nhận diện theo trọng số role")
            st.caption("Không đánh giá level hoặc xác suất tuyển dụng.")
            st.write("**Kỹ năng khớp vị trí:**", ", ".join(display_skill(s) for s in presence["matched"]) or "Chưa có")
            st.write("**Kỹ năng còn thiếu:**", ", ".join(display_skill(s) for s in presence["missing"]) or "Không có")
        st.caption("Điểm gợi ý role được tính riêng bằng heuristic.")

    with tabs[2]:
        if selected_mode == "Theo level tự khai báo":
            if gap_result is not None:
                budget = st.number_input("Ngân sách giờ học mỗi tuần", min_value=0.5, max_value=40.0, value=8.0, step=0.5, key=f"study_budget_{revision}")
                timed_result = build_timed_roadmap(gap_result, load_resources(), hours_per_week=budget)
                render_timed_roadmap(timed_result)
            else:
                st.info("Xác nhận quy ước level chưa khai báo ở tab Khoảng cách để xem lộ trình.")
        elif presence["missing"]:
            weekly_roadmap = build_roadmap(presence["missing"], load_resources(), missing_details=presence["missing_details"])
            render_roadmap(weekly_roadmap)
        else:
            st.success("Hồ sơ của bạn đã có đủ các kỹ năng được liệt kê cho vị trí này.")

    with tabs[3]:
        st.subheader("Tài liệu được tham chiếu")
        if timed_result is not None:
            for key, item in timed_result["resources"].items():
                st.markdown(f"[{item.get('title', 'Tài liệu học tập')}]({item.get('url', '')})")
                st.caption(f"{', '.join(item.get('skills', []))} · {item.get('duration_kind', 'unknown')} · {key}")
                evidence = item.get("duration_evidence", {})
                if evidence.get("source"):
                    st.caption(f"Nguồn thời lượng: {evidence['source']}")
                if item.get("review_note"):
                    st.caption(item["review_note"])
                if item.get("access_note"):
                    st.caption(item["access_note"])
            if timed_result["unknown_duration"] or timed_result["unresolved"]:
                st.warning("Có tài liệu/gap thiếu duration hoặc review; tổng tuần chưa xác định.")
        elif weekly_roadmap is not None:
            catalog = {r["key"]: r for week in weekly_roadmap for r in week["resources"]}
            seen = set()
            for week in weekly_roadmap:
                for skill, keys in week["resource_keys"].items():
                    for key in keys:
                        if key in seen:
                            continue
                        seen.add(key)
                        item = catalog[key]
                        first_week = next(w["week"] for w in weekly_roadmap if any(r["key"] == key for r in w["resources"]))
                        st.markdown(f"[{item.get('title', 'Tài liệu học tập')}]({item.get('url', '')}) · {', '.join(item.get('skills', []))}")
                        st.caption(f"Giới thiệu lần đầu ở tuần {first_week}.")
            if any(w["skills_without_resources"] for w in weekly_roadmap):
                st.warning("Một số kỹ năng chưa có tài liệu.")
        else:
            st.info("Chưa có tài liệu để xuất.")
        exported_profile = {**profile, "role_id": role["id"]}
        st.download_button("Tải báo cáo Markdown", export_report(exported_profile, gap_result or presence, timed_result or weekly_roadmap or []),
                           "bao-cao-ho-so.md", "text/markdown")
        st.download_button("Tải báo cáo CSV", export_report(exported_profile, gap_result or presence, timed_result or weekly_roadmap or [], "csv"),
                           "bao-cao-ho-so.csv", "text/csv")

    with tabs[4]:
        st.caption("Phỏng vấn theo gap hiện tại; rubric chưa có sẽ ghi rõ chưa chấm.")
        focus = gap_result["missing"] if gap_result is not None else presence["missing"]
        render_interview_practice(role, focus_skills=focus, assessment="levels" if gap_result is not None else "presence")


def render_timed_roadmap(roadmap: dict) -> None:
    st.subheader("Lộ trình theo giờ")
    st.caption("Hoàn thành tài liệu không chứng nhận đạt level.")
    st.metric("Tổng giờ công bố đã chọn", f"{roadmap['total_known_hours']:.2f}")
    st.metric("Giờ ước lượng biên tập", f"{roadmap['total_estimated_hours']:.2f}")
    st.metric("Số tuần toàn lộ trình", "Chưa xác định" if roadmap["total_weeks"] is None else str(roadmap["total_weeks"]))
    st.caption(f"Phần đã phân bổ: {roadmap['known_weeks']} tuần; ngân sách {roadmap['hours_per_week']} giờ/tuần.")
    if roadmap["is_estimated"]:
        st.warning("Lịch có giờ ước lượng biên tập; số tuần là dự kiến theo căn cứ.")
    for phase in roadmap["phases"]:
        with st.expander(f"Tuần học {phase['week']} · {phase['hours']:.2f} giờ"):
            for segment in phase["segments"]:
                item = roadmap["resources"][segment["resource_key"]]
                st.markdown(f"[{item['title']}]({item['url']}) · phần {segment['part']} · {segment['hours']:.2f} giờ")
                st.caption(f"{segment['duration_kind']} · {', '.join(item['skills'])}")
                evidence = item.get("duration_evidence", {})
                if segment["duration_kind"] == "estimated":
                    st.caption(f"Cơ sở ước lượng: {evidence.get('basis') or item.get('estimated_duration_basis') or item.get('duration_basis') or 'chưa có thông tin'}")
                elif evidence.get("source"):
                    st.caption(f"Nguồn thời lượng: {evidence['source']}")
                if item.get("review_note"):
                    st.caption(item["review_note"])
                if item.get("access_note"):
                    st.caption(item["access_note"])
    for item in roadmap["unresolved"]:
        st.warning(f"Chưa giải quyết: {item.get('skill') or ', '.join(item.get('skills', []))} · {item['reason']}")
    for item in roadmap["unknown_duration"]:
        record = roadmap["resources"][item["resource_key"]]
        st.markdown(f"[{record['title']}]({record['url']}) · thời lượng chưa xác định")


def render_roadmap(roadmap: list[dict]) -> None:
    """Resolve shared documents across the whole roadmap, including prior weeks."""
    catalog = {
        resource["key"]: (resource, week["week"])
        for week in roadmap for resource in week["resources"]
    }
    st.subheader("Lộ trình học theo tuần")
    st.caption("Ưu tiên theo trọng số; phân bổ kỹ năng theo tuần, chưa lập lịch theo giờ hoặc level.")
    for week in roadmap:
        with st.expander(f"Tuần {week['week']} · {', '.join(display_skill(s) for s in week['skills'])}"):
            for resource in week["resources"]:
                title = resource.get("title", "Tài liệu học tập")
                url = resource.get("url")
                st.markdown(f"[{title}]({url})" if url else title)
                details = [resource.get(key) for key in ("provider", "type", "language", "cost")]
                st.caption(" · ".join(str(item) for item in details if item))
            for skill, keys in week["resource_keys"].items():
                for key in keys:
                    resource, introduced_week = catalog[key]
                    if introduced_week < week["week"]:
                        title = resource.get("title", "Tài liệu học tập")
                        url = resource.get("url")
                        link = f"[{title}]({url})" if url else title
                        st.markdown(f"{display_skill(skill)}: {link} (đã giới thiệu ở tuần {introduced_week})")
            if week["skills_without_resources"]:
                st.info("Chưa có tài liệu cho: " + ", ".join(display_skill(s) for s in week["skills_without_resources"]))


def render_interview_practice(position: dict, focus_skills=None, assessment="presence") -> None:
    """Ask first; show feedback and reference material only after submission."""
    role_id = position["id"]
    st.subheader("Luyện phỏng vấn")
    st.caption("Điểm rubric chỉ phản ánh khái niệm được nhắc; không xác minh tính đúng của toàn bộ câu trả lời.")
    context = (role_id, assessment, tuple(focus_skills or []))
    previous = st.session_state.get("interview_session")
    if previous and previous.get("context") != context:
        st.session_state.pop("interview_session", None)
    count = st.number_input("Số câu hỏi", min_value=1, max_value=10, value=3, step=1,
                            key=f"interview_count_{role_id}")
    if st.button("Tạo bộ câu hỏi", key=f"start_interview_{role_id}", icon=":material/quiz:"):
        try:
            questions = get_questions(role_id, int(count), focus_skills=focus_skills)
            st.session_state["interview_session"] = {
                "role_id": role_id, "batch_id": uuid4().hex[:10], "questions": questions,
                "answered_ids": [], "scores": {}, "context": context,
            }
        except ValueError as exc:
            st.error(str(exc))

    session = st.session_state.get("interview_session")
    if not session or session.get("role_id") != role_id:
        return
    if not session.get("questions"):
        st.info("Chưa có câu hỏi cho vị trí này.")
        return
    answered = set(session.get("answered_ids", []))
    for index, question in enumerate(session["questions"], 1):
        question_id = question["id"]
        key = f"answer_{session['batch_id']}_{question_id}"
        kind = "Tình huống" if question.get("type") == "scenario" else "Kỹ thuật"
        duration = f" · {question['time_minutes']} phút" if question.get("time_minutes") else ""
        with st.container():
            st.caption(f"Câu {index} · {kind}{duration}")
            st.markdown(f"**{question.get('question', '')}**")
            with st.form(f"answer_form_{session['batch_id']}_{question_id}"):
                answer = st.text_area("Câu trả lời của bạn", key=key, height=120)
                submitted = st.form_submit_button("Gửi câu trả lời")
            if submitted:
                if answer.strip():
                    session["scores"][question_id] = score_answer(question_id, answer)
                    answered.add(question_id)
                    session["answered_ids"] = list(answered)
                    st.session_state["interview_session"] = session
                else:
                    st.warning("Hãy nhập câu trả lời trước khi xem ý tham khảo.")
            if question_id in answered:
                result = session["scores"][question_id]
                st.caption("Feedback phản ánh câu trả lời đã gửi gần nhất.")
                if result["status"] == "scored":
                    st.write(f"**Điểm rubric:** {result['score']}/10")
                else:
                    st.info("Chưa có điểm: rubric chưa sẵn sàng.")
                for note in result["feedback"]:
                    st.caption(note)
                st.caption("Phép chấm từ khóa không xác minh độ đúng, ngữ cảnh hoặc trải nghiệm thực tế.")
                try:
                    feedback = get_question_feedback(question_id)
                except ValueError as exc:
                    st.warning(str(exc))
                    continue
                has_answer = feedback.get("has_reference_answer", bool(feedback.get("reference_answer")))
                if has_answer:
                    st.markdown("**Đáp án mẫu tham khảo**")
                    st.markdown(feedback["reference_answer"])
                    if feedback.get("good_answer_points"):
                        st.markdown("**Các ý nên có trong câu trả lời**")
                        for point in feedback["good_answer_points"]:
                            st.markdown(f"- {point}")
                else:
                    st.markdown("**Các ý tham khảo**")
                    st.markdown(feedback["reference_answer"])
                if feedback["red_flags"]:
                    st.caption("Điểm cần tránh")
                    for flag in feedback["red_flags"]:
                        st.markdown(f"- {flag}")


def run_app() -> None:
    st.set_page_config(page_title="AI Career Coach | Cộng đồng nghề nghiệp", page_icon="✦", layout="wide")
    inject_styles()
    render_landing_page()
    render_toolkit()
    render_closing_sections()


if __name__ == "__main__":
    run_app()
