"""AI Career Coach community landing page and career planning toolkit."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from uuid import uuid4

import streamlit as st

from modules import (
    build_profile,
    calculate_match_score,
    extract_text,
    get_question_feedback,
    get_questions,
    get_course_recommendations,
)


PROJECT_DIR = Path(__file__).resolve().parent
CAREERS_PATH = PROJECT_DIR / "Data" / "roles.json"
LOGO_PATH = PROJECT_DIR / "brand_assets" / "LogoAICC.jpg"
ROLE_NAMES_VI = {
    "Data Analyst": "Chuyên viên phân tích dữ liệu",
    "Backend Developer": "Lập trình viên Backend",
    "AI Engineer": "Kỹ sư trí tuệ nhân tạo",
}
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
    """Normalize both legacy positions and the expanded role catalog."""
    with CAREERS_PATH.open(encoding="utf-8") as data_file:
        payload = json.load(data_file)

    roles = payload.get("roles", []) if isinstance(payload, dict) else []
    if isinstance(roles, list) and roles:
        normalized: list[dict] = []
        for role in roles:
            if not isinstance(role, dict) or not role.get("id"):
                continue
            skills = role.get("skills", [])
            required_skills = [
                skill["name"]
                for skill in skills
                if isinstance(skill, dict) and isinstance(skill.get("name"), str)
            ] if isinstance(skills, list) else []
            normalized.append(
                {
                    **role,
                    "id": str(role["id"]),
                    "title": role.get("name", str(role["id"])),
                    "name_vi": role.get("name_vi", role.get("name", str(role["id"]))),
                    "required_skills": required_skills,
                }
            )
        return sorted(normalized, key=lambda role: role["name_vi"].casefold())

    legacy_positions = payload.get("positions", []) if isinstance(payload, dict) else []
    return [
        {
            **position,
            "id": str(position.get("id", position.get("title", ""))),
            "name_vi": position.get("name_vi", ROLE_NAMES_VI.get(position.get("title", ""), position.get("title", ""))),
        }
        for position in legacy_positions
        if isinstance(position, dict) and position.get("title")
    ]


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


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root { --navy:#102f49; --blue:#1556a8; --cyan:#31aeb8; --mint:#38d4bc; --orange:#ee9a4a; --ink:#18334a; --muted:#617588; --line:#e3ecf0; --paper:#f7fafb; }
        html { scroll-behavior:smooth; }
        .stApp { background:#fff; color:var(--ink); font-family:'DM Sans',sans-serif; }
        [data-testid="stHeader"] { background:rgba(255,255,255,.92); }
        [data-testid="stToolbar"], #MainMenu, footer { visibility:hidden; }
        .block-container { max-width:1240px; padding:0 2.4rem 4rem; }
        .hero-wrap { position:relative; overflow:hidden; margin:0 -2.4rem; padding:16px 2.4rem 74px; background:radial-gradient(ellipse at 83% 20%,#e4f7f7 0,rgba(228,247,247,0) 32%),linear-gradient(180deg,#fff 0%,#f9fcfd 100%); }
        .topbar { max-width:1240px; height:76px; margin:0 auto 52px; display:flex; align-items:center; justify-content:space-between; }
        .brand { display:flex; align-items:center; gap:13px; text-decoration:none; color:var(--navy); }
        .brand img { width:78px; height:56px; object-fit:cover; object-position:center; border-radius:9px; mix-blend-mode:multiply; }
        .brand-word { font:800 15px/1.1 'Manrope',sans-serif; letter-spacing:-.4px; }
        .brand-word span { display:block; margin-top:4px; color:var(--cyan); font:700 10px/1 'DM Sans',sans-serif; letter-spacing:2.2px; }
        .nav-links { display:flex; align-items:center; gap:34px; color:#4c6172; font-size:13px; font-weight:600; }
        .nav-links a { color:inherit; text-decoration:none; }
        .nav-cta,.button-primary { background:var(--blue); color:#fff!important; text-decoration:none; border-radius:999px; padding:13px 21px; font-weight:700; box-shadow:0 9px 20px #1556a829; transition:transform .18s,box-shadow .18s; }
        .nav-cta:hover,.button-primary:hover { transform:translateY(-2px); box-shadow:0 12px 26px #1556a838; }
        .hero { max-width:1240px; min-height:470px; margin:auto; display:grid; grid-template-columns:1.04fr .96fr; align-items:center; gap:38px; }
        .eyebrow { color:#168d99; text-transform:uppercase; letter-spacing:2.1px; font-size:11px; font-weight:800; display:flex; align-items:center; gap:9px; }
        .eyebrow:before { content:''; width:26px; height:2px; background:var(--mint); }
        .hero h1 { max-width:620px; margin:22px 0 18px; color:var(--navy); font:800 clamp(40px,5.1vw,66px)/1.06 'Manrope',sans-serif; letter-spacing:-3.2px; }
        .hero h1 em { color:var(--blue); font-style:normal; }
        .hero-copy { max-width:525px; color:#617588; font-size:16px; line-height:1.8; }
        .hero-actions { display:flex; align-items:center; gap:20px; margin-top:29px; }
        .text-link { color:var(--navy); font-size:13px; font-weight:700; text-decoration:none; }
        .text-link span { color:var(--cyan); font-size:18px; margin-left:6px; vertical-align:-1px; }
        .social-proof { display:flex; align-items:center; gap:12px; margin-top:40px; color:#718292; font-size:12px; }
        .avatars { display:flex; padding-left:3px; }
        .avatar { width:29px; height:29px; border:2px solid #fff; margin-left:-4px; border-radius:50%; display:grid; place-items:center; color:#fff; background:#2a739a; font-size:10px; font-weight:700; }
        .avatar:nth-child(2){background:#42aeaa}.avatar:nth-child(3){background:#ec9a4d}.avatar:nth-child(4){background:#5279b7}
        .hero-art { position:relative; min-height:445px; display:grid; place-items:center; }
        .orbit { position:absolute; width:390px; height:390px; border:1px solid #b8e9e8; border-radius:50%; box-shadow:0 0 0 31px #e9f8f7,0 0 0 32px #d3f0ef; }
        .orbit:before,.orbit:after { content:''; position:absolute; border:1px solid #cae8ef; border-radius:50%; inset:48px; }
        .orbit:after { inset:94px; }
        .career-card { position:relative; z-index:1; width:min(390px,90%); background:#fff; border:1px solid #e9eff1; border-radius:22px; padding:24px; box-shadow:0 28px 75px #1e486a1a; transform:rotate(-1deg); }
        .card-kicker { display:flex; justify-content:space-between; align-items:center; color:#8092a0; font-size:10px; font-weight:700; letter-spacing:1.1px; text-transform:uppercase; }
        .live { border-radius:20px; background:#e8f8f4; color:#15957d; padding:6px 9px; letter-spacing:.3px; }
        .role-row { display:flex; align-items:center; gap:13px; margin:22px 0 17px; }
        .role-icon { width:48px;height:48px;border-radius:15px;background:linear-gradient(135deg,#d8f7f1,#dceeff);display:grid;place-items:center;color:#1766a5;font-size:24px; }
        .role-title { color:var(--navy); font:800 19px 'Manrope',sans-serif; }
        .role-sub { margin-top:4px; color:#81909c; font-size:11px; }
        .match-label { display:flex; justify-content:space-between; color:#627687; font-size:11px; font-weight:700; }
        .match-label strong { color:#198e98; }
        .meter { height:8px; margin:10px 0 20px; border-radius:8px; background:#edf2f4; overflow:hidden; }
        .meter i { display:block; width:74%; height:100%; border-radius:8px; background:linear-gradient(90deg,#21a2b1,#39d2b1); }
        .skills { display:flex; gap:7px; flex-wrap:wrap; }
        .skill { border-radius:7px; background:#f0f6fa; color:#47647b; padding:7px 9px; font-size:10px; font-weight:600; }
        .floating { position:absolute; z-index:2; background:#fff; border:1px solid #e7eff1; border-radius:14px; padding:12px 15px; box-shadow:0 15px 38px #16446618; color:#566e7d; font-size:10px; }
        .floating strong { display:block; color:var(--navy); font:700 12px 'Manrope',sans-serif; margin-bottom:3px; }
        .float-top { right:0; top:45px; }.float-bottom { left:2px; bottom:43px; }
        .spark { color:var(--orange); font-size:16px; margin-right:4px; }
        .section { padding:88px 0; }
        .section-heading { max-width:660px; margin:0 auto 42px; text-align:center; }
        .section-heading .eyebrow { justify-content:center; }
        .section h2 { color:var(--navy); font:800 clamp(30px,3.5vw,43px)/1.15 'Manrope',sans-serif; letter-spacing:-1.7px; margin:14px 0; }
        .section-heading p { color:#6a7c8b; font-size:14px; line-height:1.75; }
        .feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:17px; }
        .feature { padding:27px 25px 29px; border:1px solid var(--line); background:#fff; border-radius:16px; transition:transform .2s,box-shadow .2s; }
        .feature:hover { transform:translateY(-4px); box-shadow:0 17px 38px #1c49600d; }
        .feature-icon { width:45px;height:45px;display:grid;place-items:center;border-radius:13px;background:#eaf8f7;color:#118f9a;font-size:21px; }
        .feature:nth-child(2) .feature-icon,.feature:nth-child(5) .feature-icon { background:#edf3fd;color:#2868b0; }
        .feature:nth-child(3) .feature-icon,.feature:nth-child(6) .feature-icon { background:#fff4e8;color:#cc7a2e; }
        .feature h3 { margin:20px 0 8px; color:var(--navy); font:700 16px 'Manrope',sans-serif; }
        .feature p { margin:0;color:#718392;font-size:12px;line-height:1.8; }
        .path-section { margin:0 -2.4rem; padding:78px 2.4rem; background:var(--paper); }
        .path-inner { max-width:1240px; margin:auto; display:grid; grid-template-columns:.88fr 1.12fr; align-items:center; gap:70px; }
        .path-copy .eyebrow { margin-bottom:15px; }
        .path-copy h2 { margin:0 0 18px; color:var(--navy); font:800 39px/1.15 'Manrope',sans-serif; letter-spacing:-1.7px; }
        .path-copy p { color:#6a7c8b;font-size:14px;line-height:1.8; }
        .path-list { margin-top:23px; display:grid; gap:12px; }
        .path-item { display:flex; align-items:center; gap:12px; color:#4a6476;font-size:13px;font-weight:600; }
        .check { display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#dbf6ef;color:#139a82;font-size:12px; }
        .steps { display:grid; gap:13px; }
        .step { display:flex; gap:16px; align-items:flex-start; padding:19px 21px; background:#fff; border:1px solid #e7eef0; border-radius:15px; }
        .step-num { width:32px;height:32px;flex:0 0 32px;display:grid;place-items:center;border-radius:10px;background:#e8f7f6;color:#128d96;font:800 12px 'Manrope',sans-serif; }
        .step h3 { margin:1px 0 5px;color:var(--navy);font:700 14px 'Manrope',sans-serif; }
        .step p { margin:0;color:#758695;font-size:11px;line-height:1.65; }
        .community { padding:83px 0 90px; text-align:center; }
        .community-box { position:relative;overflow:hidden;padding:55px 30px;border-radius:24px;background:linear-gradient(115deg,#113f70,#16589e 60%,#178c99);color:#fff; }
        .community-box:before,.community-box:after { content:'';position:absolute;border:1px solid #ffffff25;border-radius:50%;width:360px;height:360px;top:-250px;left:8%;box-shadow:0 0 0 33px #ffffff0d,0 0 0 67px #ffffff0a; }
        .community-box:after { left:auto;top:auto;bottom:-300px;right:5%; }
        .community-box>* { position:relative;z-index:1; }
        .community-box .eyebrow { color:#93f1df;justify-content:center; }
        .community-box .eyebrow:before { background:#93f1df; }
        .community-box h2 { max-width:690px;margin:17px auto 12px;color:#fff;font:800 clamp(29px,4vw,42px)/1.16 'Manrope',sans-serif;letter-spacing:-1.5px; }
        .community-box p { max-width:580px;margin:0 auto 27px;color:#d3e7f2;font-size:13px;line-height:1.75; }
        .button-light { display:inline-block;background:#fff;color:#174c7e!important;text-decoration:none;padding:13px 22px;border-radius:999px;font-size:12px;font-weight:800;box-shadow:0 9px 20px #082a3b35; }
        .footer { display:flex;justify-content:space-between;align-items:center;padding:25px 0 7px;border-top:1px solid var(--line);color:#83919b;font-size:11px; }
        .footer b { color:#476075; }
        .tool-title { margin:58px 0 22px;padding:36px 38px 22px;border:1px solid #e7eef0;border-bottom:0;border-radius:22px 22px 0 0;background:#f7fafb; }
        [data-testid="stForm"] { margin:0 0 52px;padding:4px 38px 34px;border:1px solid #e7eef0;border-top:0;border-radius:0 0 22px 22px;background:#f7fafb; }
        .tool-title .eyebrow { margin-bottom:12px; }
        .tool-title h2 { margin:0 0 9px;color:var(--navy);font:800 31px 'Manrope',sans-serif;letter-spacing:-1px; }
        .tool-title p { color:#6a7c8b;font-size:13px; }
        [data-testid="stTextArea"] label,[data-testid="stSelectbox"] label,[data-testid="stFileUploader"] label { color:#244257;font-weight:700; }
        [data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] [data-baseweb="select"] > div { border-radius:10px;border-color:#dce7ec;background:#fff; }
        [data-testid="stFormSubmitButton"] button { background:#1556a8;color:#fff;border:0;border-radius:999px;padding:10px 22px;font-weight:700; }
        [data-testid="stFormSubmitButton"] button:hover { background:#104985;color:#fff; }
        [data-testid="stFileUploaderDropzoneInstructions"] { display:none; }
        [data-testid="stFileUploaderDropzone"] button { color:transparent!important;font-size:0!important; }
        [data-testid="stFileUploaderDropzone"] button::after { content:'Chọn tệp';color:var(--navy);font-size:14px; }
        [data-testid="stMetric"] { background:#fff;border:1px solid #e5edf0;border-radius:12px;padding:15px; }
        @media(max-width:850px){.block-container{padding:0 1.2rem 3rem}.hero-wrap,.path-section{margin:0 -1.2rem;padding-left:1.2rem;padding-right:1.2rem}.topbar{margin-bottom:25px}.nav-links{gap:17px}.hero{grid-template-columns:1fr;gap:10px}.hero-art{min-height:390px}.hero{padding-top:10px}.feature-grid{grid-template-columns:repeat(2,1fr)}.path-inner{grid-template-columns:1fr;gap:32px}.tool-title{padding:28px 22px 18px}[data-testid="stForm"]{padding:4px 22px 28px}}
        @media(max-width:560px){.topbar{height:65px}.brand{gap:7px;flex-shrink:0}.brand img{width:48px;height:40px}.brand-word{font-size:10px;white-space:nowrap;letter-spacing:-.3px}.brand-word span{font-size:7px;letter-spacing:1px;white-space:nowrap}.nav-links a:not(.nav-cta){display:none}.nav-cta{padding:10px 12px;font-size:11px;white-space:nowrap}.hero h1{font-size:42px;letter-spacing:-2px}.hero-copy{font-size:14px}.hero-art{min-height:360px}.orbit{width:290px;height:290px}.career-card{padding:20px}.float-top{right:-5px;top:10px}.float-bottom{left:-3px;bottom:10px}.feature-grid{grid-template-columns:1fr}.section{padding:65px 0}.path-copy h2{font-size:32px}.footer{gap:12px;align-items:flex-start;flex-direction:column}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    logo = logo_data_uri()
    st.markdown(
        f"""
        <div class="hero-wrap" id="top">
          <div class="topbar">
            <a class="brand" href="#top"><img src="{logo}" alt="Biểu trưng AI Career Coach"><span class="brand-word">AI CAREER COACH<span>CỘNG ĐỒNG NGHỀ NGHIỆP</span></span></a>
            <nav class="nav-links"><a href="#why">Về cộng đồng</a><a href="#how">Cách hoạt động</a><a class="nav-cta" href="#career-toolkit">Bắt đầu ngay&nbsp; →</a></nav>
          </div>
          <div class="hero">
            <div>
              <div class="eyebrow">Cộng đồng đồng hành cùng bạn</div>
              <h1>Tự tin chọn <em>con đường sự nghiệp</em> của bạn.</h1>
              <div class="hero-copy">Khám phá thế mạnh, tìm hiểu công việc phù hợp và biến mục tiêu nghề nghiệp thành những bước đi cụ thể. Bạn không cần phải tự mình tìm lời giải.</div>
              <div class="hero-actions"><a class="button-primary" href="#career-toolkit">Khám phá hồ sơ nghề nghiệp&nbsp; →</a><a class="text-link" href="#why">Tìm hiểu cộng đồng <span>↓</span></a></div>
              <div class="social-proof"><div class="avatars"><span class="avatar">AI</span><span class="avatar">CC</span><span class="avatar">+</span></div><span>Dành cho người học và người đang phát triển sự nghiệp</span></div>
            </div>
            <div class="hero-art" aria-label="Minh họa hồ sơ nghề nghiệp">
              <div class="orbit"></div>
              <div class="career-card"><div class="card-kicker"><span>Hồ sơ nghề nghiệp</span><span class="live">●&nbsp; THEO ĐỊNH HƯỚNG</span></div><div class="role-row"><div class="role-icon">✳</div><div><div class="role-title">Phân tích dữ liệu</div><div class="role-sub">Lựa chọn dựa trên thế mạnh của bạn</div></div></div><div class="match-label"><span>Mức độ phù hợp kỹ năng</span><strong>Đang phát triển</strong></div><div class="meter"><i></i></div><div class="skills"><span class="skill">Python</span><span class="skill">Phân tích dữ liệu</span><span class="skill">SQL</span><span class="skill">+ kỹ năng tiếp theo</span></div></div>
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
            <article class="feature"><div class="feature-icon">♡</div><h3>Cùng nhau phát triển</h3><p>Kết nối với những người đang học hỏi, chia sẻ và định hướng cho tương lai nghề nghiệp.</p></article>
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
        <section class="community"><div class="community-box"><div class="eyebrow">Cùng nhau tiến xa hơn</div><h2>Hành trình mới bắt đầu từ một bước nhỏ.</h2><p>Khám phá thế mạnh, tìm hiểu những lựa chọn phù hợp và xây dựng con đường sự nghiệp của riêng bạn ngay hôm nay.</p><a class="button-light" href="#career-toolkit">Bắt đầu với hồ sơ nghề nghiệp&nbsp; →</a></div></section>
        <div class="footer"><span><b>AI Career Coach</b> &nbsp;·&nbsp; Đồng hành cùng bạn trên hành trình sự nghiệp.</span><span>Cùng kiến tạo tương lai nghề nghiệp.</span></div>
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
    role_ids = list(role_by_id)
    if not role_ids:
        st.error("Chưa có dữ liệu vị trí nghề nghiệp trong Data/roles.json.")
        return

    with st.form("profile_form"):
        skills_text = st.text_area(
            "Kỹ năng",
            placeholder="Python, SQL, phân tích dữ liệu",
        )
        st.caption("Ngăn cách các kỹ năng bằng dấu phẩy, dấu chấm phẩy hoặc xuống dòng.")
        interests_text = st.text_area("Sở thích nghề nghiệp", placeholder="Phân tích dữ liệu, thiết kế sản phẩm")
        experience_text = st.text_area(
            "Kinh nghiệm",
            placeholder="Tên đơn vị, vị trí và mô tả ngắn về kinh nghiệm của bạn",
        )
        st.caption("Mô tả kinh nghiệm bằng lời của bạn.")
        selected_role_id = st.selectbox(
            "Vị trí công việc bạn quan tâm",
            role_ids,
            format_func=lambda role_id: format_role(role_by_id[role_id]),
        )
        uploaded_cv = st.file_uploader(
            "Tải CV định dạng PDF hoặc DOCX (không bắt buộc)",
            type=["pdf", "docx"],
            help="PDF cần có lớp văn bản; PDF scan dạng ảnh chưa được OCR.",
        )
        job_description = st.text_area("Mô tả công việc cần đối chiếu (không bắt buộc)")
        submitted = st.form_submit_button("Tạo hồ sơ nghề nghiệp")
    if submitted:
        st.session_state["career_role_id"] = selected_role_id
        st.session_state["profile_result"] = build_profile(
            {"skills": skills_text, "interests": interests_text, "experience": experience_text}
        )
        st.session_state["match_score"] = None
        st.session_state["match_error"] = None
        st.session_state["cv_extraction"] = None
        if uploaded_cv:
            try:
                cv_text = extract_text(uploaded_cv)
                if not cv_text.strip():
                    raise ValueError(
                        "Không trích xuất được văn bản từ CV. Có thể PDF là bản scan "
                        "hoặc tệp bị lỗi."
                    )
                st.session_state["cv_extraction"] = {
                    "filename": uploaded_cv.name,
                    "text": cv_text,
                }
                if job_description.strip():
                    st.session_state["match_score"] = calculate_match_score(
                        cv_text, job_description
                    )
            except ValueError as exc:
                st.session_state["match_error"] = str(exc)
        elif job_description.strip():
            st.session_state["match_error"] = (
                "Hãy tải lên CV để tính mức độ phù hợp với mô tả công việc."
            )

    profile = st.session_state.get("profile_result")
    if not profile:
        return

    selected_role_id = st.session_state.get("career_role_id", role_ids[0])
    position = role_by_id.get(selected_role_id, role_by_id[role_ids[0]])
    selected_role = position["title"]
    selected_role_vi = format_role(position)

    if st.session_state.get("match_error"):
        st.error(f"Không thể tính mức độ phù hợp giữa CV và mô tả công việc: {st.session_state['match_error']}")
    elif st.session_state.get("match_score") is not None:
        st.metric("Mức độ phù hợp giữa CV và mô tả công việc", f"{st.session_state['match_score']}%")
        st.caption("Điểm phản ánh độ tương đồng từ ngữ giữa CV và mô tả công việc.")

    cv_extraction = st.session_state.get("cv_extraction")
    if cv_extraction:
        extracted_text = cv_extraction["text"]
        if not job_description.strip() and st.session_state.get("match_error") is None:
            st.info("Đã trích xuất CV. Thêm mô tả công việc để tính độ tương đồng.")
        with st.expander(f"Văn bản đã trích xuất · {cv_extraction['filename']}"):
            st.caption(f"{len(extracted_text):,} ký tự")
            st.text_area(
                "Nội dung CV",
                value=extracted_text,
                height=260,
                disabled=True,
                label_visibility="collapsed",
            )

    for index, item in enumerate(profile["moved"]):
        left, right = st.columns([4, 1])
        left.info(f"Đã chuyển ‘{item['item']}’ từ {item['from']} sang {item['to']}.")
        if right.button("Hoàn tác", key=f"undo_move_{index}"):
            profile["interests"] = [interest for interest in profile["interests"] if interest.casefold() != item["item"].casefold()]
            profile["skills"].append(item["item"])
            profile["moved"].pop(index)
            profile["skills"] = sorted(set(profile["skills"]), key=str.casefold)
            st.session_state["profile_result"] = profile
            st.success(f"Đã chuyển ‘{item['item']}’ trở lại mục Kỹ năng.")

    retained_unknowns: list[str] = []
    if profile["unrecognized_skills"]:
        st.subheader("Kỹ năng chưa nhận diện được")
        st.caption("Chọn những kỹ năng bạn muốn giữ lại trong hồ sơ.")
        for index, skill in enumerate(profile["unrecognized_skills"]):
            if st.checkbox(f"Giữ ‘{skill}’ trong hồ sơ", value=True, key=f"keep_unknown_{index}_{skill}"):
                retained_unknowns.append(skill)

    effective_skills = [
        skill for skill in profile["skills"]
        if skill not in profile["unrecognized_skills"] or skill in retained_unknowns
    ]
    st.subheader("Hồ sơ của bạn")
    st.write("**Kỹ năng:**", ", ".join(display_skill(skill) for skill in effective_skills) or "Chưa có thông tin")
    st.write("**Sở thích:**", ", ".join(profile["interests"]) or "Chưa có thông tin")
    st.write("**Kinh nghiệm:**", profile["experience"] or "Chưa có thông tin")

    required = position.get("required_skills", [])
    known_skill_keys = {skill.casefold() for skill in effective_skills}
    missing_skills = [skill for skill in required if skill.casefold() not in known_skill_keys]
    st.subheader(f"Gợi ý cho vị trí {selected_role_vi}")
    matched_count = len(required) - len(missing_skills)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Kỹ năng phù hợp", f"{matched_count}/{len(required)}")
    metric_columns[1].metric("Độ khó", position.get("difficulty", "Chưa có dữ liệu"))
    learning_months = position.get("learning_time_months")
    metric_columns[2].metric(
        "Thời gian học tham khảo",
        f"{learning_months} tháng" if learning_months else "Chưa có dữ liệu",
    )

    if missing_skills:
        st.write("**Kỹ năng nên phát triển:**", ", ".join(display_skill(skill) for skill in missing_skills))
        resources = get_course_recommendations(missing_skills)
        if resources:
            st.markdown(f"**Tài liệu phù hợp ({len(resources)})**")
            for resource in resources:
                with st.container(border=True):
                    title = resource.get("course_name", "Tài liệu học tập")
                    url = resource.get("link")
                    st.markdown(f"[{title}]({url})" if url else title)
                    details = [
                        resource.get("provider"),
                        resource.get("type"),
                        resource.get("language"),
                        resource.get("cost"),
                    ]
                    st.caption(" · ".join(str(item) for item in details if item))
                    if resource.get("duration_hours"):
                        st.caption(f"Thời lượng tham khảo: {resource['duration_hours']} giờ")
        else:
            st.info("Chưa có tài liệu khớp với các kỹ năng còn thiếu trong ngân hàng dữ liệu.")
    else:
        st.success("Hồ sơ của bạn đã có đủ các kỹ năng được liệt kê cho vị trí này.")

    render_interview_practice(position)


def render_interview_practice(position: dict) -> None:
    """Show questions, then reveal reference points after the candidate responds."""
    role_id = position["id"]
    st.subheader("Luyện phỏng vấn")
    st.caption("Trả lời trước, sau đó mở các ý tham khảo và điểm cần tránh.")
    question_count = st.number_input(
        "Số câu hỏi",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key=f"interview_count_{role_id}",
    )
    if st.button("Tạo bộ câu hỏi", key=f"start_interview_{role_id}", icon=":material/quiz:"):
        try:
            questions = get_questions(role_id, int(question_count))
            st.session_state["interview_session"] = {
                "role_id": role_id,
                "batch_id": uuid4().hex[:10],
                "questions": questions,
                "answered_ids": [],
            }
        except ValueError as exc:
            st.error(str(exc))

    session = st.session_state.get("interview_session")
    if not session or session.get("role_id") != role_id:
        return
    if not session.get("questions"):
        st.info("Chưa có câu hỏi cho vị trí này.")
        return

    answered_ids = set(session.get("answered_ids", []))
    for index, question in enumerate(session["questions"], start=1):
        question_id = question["id"]
        answer_key = f"answer_{session['batch_id']}_{question_id}"
        type_label = "Tình huống" if question.get("type") == "scenario" else "Kỹ thuật"
        time_label = f" · {question['time_minutes']} phút" if question.get("time_minutes") else ""
        with st.container(border=True):
            st.caption(f"Câu {index} · {type_label}{time_label}")
            st.markdown(f"**{question.get('question', '')}**")
            with st.form(f"answer_form_{session['batch_id']}_{question_id}"):
                answer_text = st.text_area("Câu trả lời của bạn", key=answer_key, height=120)
                submitted_answer = st.form_submit_button("Gửi câu trả lời")

            if submitted_answer:
                if answer_text.strip():
                    answered_ids.add(question_id)
                    session["answered_ids"] = list(answered_ids)
                    st.session_state["interview_session"] = session
                else:
                    st.warning("Hãy nhập câu trả lời trước khi xem ý tham khảo.")

            if question_id in answered_ids:
                try:
                    feedback = get_question_feedback(question_id)
                except ValueError as exc:
                    st.warning(str(exc))
                    continue
                st.markdown("**Các ý tham khảo**")
                st.markdown(feedback["reference_answer"])
                if feedback["red_flags"]:
                    st.caption("Điểm cần tránh")
                    for red_flag in feedback["red_flags"]:
                        st.markdown(f"- {red_flag}")


def run_app() -> None:
    st.set_page_config(page_title="AI Career Coach | Cộng đồng nghề nghiệp", page_icon="✦", layout="wide")
    inject_styles()
    render_landing_page()
    render_toolkit()
    render_closing_sections()


if __name__ == "__main__":
    run_app()
