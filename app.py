"""AI Career Coach community landing page and career planning toolkit."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from html import escape
from pathlib import Path
from uuid import uuid4

import streamlit as st

from modules import (
    build_roadmap,
    match_role,
    get_question_feedback,
    get_questions,
    count_reviewed_questions,
    question_bank_quality_summary,
    question_quality_label,
    POST_SUBMISSION_GUIDANCE_NOTICE,
    STATIC_SELF_REVIEW_TITLE,
    STATIC_SELF_REVIEW_NOTICE,
    compute_gap,
    suggest_roles,
    build_timed_roadmap,
)
from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.matcher import (
    LOW_CONFIDENCE_ROLE_MESSAGE,
    LOW_SKILL_ROLE_SCORE_CAP,
    compare_confirmed_jd_requirements,
    extract_jd_skill_requirements,
    role_recommendation_is_low_confidence,
)
from modules.matcher import activity_label, load_interest_activities
from modules.profile import build_profile, undo_profile_move
from modules.curriculum import merge_academic_curriculum
from modules.skill_extractor import load_aliases, normalize_skill, suggest_skill_candidates
from modules.profile import PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE, prepare_submission
from modules.export import export_report
from modules.recommender import get_partial_resource_assignment
from modules.recommender import has_granular_level_evidence, resource_level_gap, resource_review_label, skill_scope_caution, summarize_resource_reviews
from modules.recommender import resource_evidence_badge, role_domain_notice


PROJECT_DIR = Path(__file__).resolve().parent
CAREERS_PATH = DATA_DIR / "roles.json"
LOGO_PATH = PROJECT_DIR / "brand_assets" / "LogoAICC.jpg"
STYLE_PATH = PROJECT_DIR / "assets" / "style.css"
SITE_SCRIPT_PATH = PROJECT_DIR / "assets" / "site.js"
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
MAX_INTERVIEW_QUESTIONS = 10
FAQ_ITEMS = (
    (
        "Web này giúp được gì cho mình?",
        "<p>Bạn nhập kỹ năng hoặc CV, rồi chọn vị trí muốn tìm hiểu. Web đối chiếu hồ sơ với yêu cầu nghề để chỉ ra <strong>kỹ năng đã có, kỹ năng còn thiếu</strong>, gợi ý lộ trình học, tài liệu tham khảo và câu hỏi luyện phỏng vấn. Danh mục hiện có 131 vị trí thuộc 15 nhóm ngành.</p>",
    ),
    (
        "Dữ liệu và CV của mình có bị gửi đi đâu không?",
        "<p>Khi bạn tải CV, trình duyệt gửi tệp tới <strong>máy chủ đang chạy ứng dụng Streamlit</strong> để đọc văn bản trong phiên sử dụng. Ứng dụng không ghi CV thành tệp dự án và không gọi ChatGPT, Gemini hay API AI bên ngoài để tính kết quả. Web không có tính năng lưu hoặc khôi phục hồ sơ; tải lại trang có thể làm mất dữ liệu phiên. Nếu bạn chủ động tải báo cáo về, tệp đó sẽ nằm trên thiết bị của bạn.</p>",
    ),
    (
        "Điểm phần trăm có phải khả năng mình được nhận việc không?",
        "<p><strong>Không.</strong> Phần trăm đối chiếu vị trí thể hiện mức trùng kỹ năng với yêu cầu nghề. Điểm gợi ý nghề còn kết hợp tín hiệu kỹ năng và sở thích theo quy tắc có sẵn. Các điểm này chỉ giúp bạn định hướng, <strong>không dự đoán kết quả tuyển dụng</strong> hay chứng nhận năng lực.</p>",
    ),
    (
        "Mình cần chuẩn bị gì để bắt đầu?",
        "<p>Chỉ cần <strong>ít nhất một kỹ năng</strong> (ví dụ Python, SQL hoặc giao tiếp), hoặc một CV có văn bản đọc được. Bạn có thể tải PDF/DOCX tối đa 10 MB hoặc dán nội dung CV; với PDF, web chỉ đọc 10 trang đầu. Sở thích, kinh nghiệm và mô tả công việc là thông tin bổ sung. Muốn thử nhanh, hãy chọn một hồ sơ mẫu tổng hợp.</p>",
    ),
    (
        "Mình tải CV lên nhưng web không đọc được chữ nào?",
        "<p>CV có thể là ảnh chụp hoặc PDF scan chưa có lớp văn bản; web chưa hỗ trợ đọc chữ trong ảnh. Hãy xuất lại CV từ trình soạn thảo thành PDF <strong>có thể bôi đen chữ</strong>, hoặc sao chép nội dung rồi dán vào ô <strong>“Dán nội dung CV”</strong>.</p>",
    ),
    (
        "Vì sao phải rà soát kỹ năng ở Bước 2?",
        "<p>Việc trích xuất từ CV có thể nhận nhầm một từ thành kỹ năng. Ở Bước 2, bạn kiểm tra kỹ năng nào đúng, bỏ kỹ năng không thuộc về mình và tự chọn mức độ nếu biết. Web <strong>không tự suy ra trình độ</strong> từ số năm kinh nghiệm hoặc độ dài CV.</p>",
    ),
    (
        "Các mức độ 0, 1, 2, 3 nghĩa là gì?",
        "<dl class='faq-levels'><div><dt>0 · Chưa biết</dt><dd>Chưa học hoặc chưa nắm được kỹ năng.</dd></div><div><dt>1 · Cơ bản</dt><dd>Hiểu khái niệm, làm việc đơn giản khi có hướng dẫn.</dd></div><div><dt>2 · Độc lập</dt><dd>Tự làm các tác vụ quen thuộc.</dd></div><div><dt>3 · Nâng cao</dt><dd>Xử lý việc phức tạp, có thể hướng dẫn người khác.</dd></div></dl><p>Nếu chưa khai báo Level, chế độ <strong>“Theo kỹ năng đã có”</strong> chỉ xét có hay chưa có. Ở chế độ <strong>“Theo mức độ thành thạo tự khai báo”</strong>, kỹ năng chưa khai báo được tính là mức 0 <em>chỉ khi bạn xác nhận đồng ý</em>; đây không phải kết luận về năng lực thật.</p>",
    ),
    (
        "Vì sao mình có đúng sở thích mà điểm gợi ý nghề vẫn thấp?",
        "<p>Điểm gợi ý dựa chủ yếu vào <strong>mức khớp kỹ năng có trọng số</strong> (75%), cùng với sở thích (25%). Khi mức khớp kỹ năng dưới ngưỡng 15%, điểm gợi ý bị giới hạn tối đa 5/100. Điều này nhắc bạn cần xây thêm nền tảng kỹ năng, <strong>không kết luận bạn không hợp nghề</strong>.</p>",
    ),
    (
        "Mỗi kỹ năng có tài liệu và cách luyện không?",
        "<p>Mỗi kỹ năng trong danh mục vị trí đều có giáo trình hoặc học liệu nền tảng, kèm bài tập áp dụng, cách tự kiểm tra và sản phẩm để xin phản hồi. Một số tài liệu dạy nguyên lý chung, nên bạn vẫn cần luyện công cụ hoặc quy trình riêng của ngành. Nguồn không công bố thời lượng thì web không tự đặt số tuần; học theo nhịp cá nhân. Với luật, thuế, y tế và an toàn, hãy đối chiếu quy định Việt Nam hiện hành và học thực hành cùng người đủ chuyên môn.</p>",
    ),
    (
        "Luyện phỏng vấn có chấm điểm câu trả lời của mình không?",
        "<p><strong>Không.</strong> Sau khi bạn gửi câu trả lời, web hiện khung trả lời tham khảo, những ý nên cân nhắc và checklist để bạn tự đối chiếu. Web không phân tích nội dung vừa nhập và không chấm điểm câu trả lời. Nhãn <strong>“AI hỗ trợ rà soát nội bộ”</strong> nói về trạng thái rà soát nội dung câu hỏi/khung tham khảo; đó không phải đánh giá của chuyên gia độc lập.</p>",
    ),
)


@st.cache_data(max_entries=1)
def load_positions() -> list[dict]:
    """Use the same catalog rules as Profile, Matcher, and Interview."""
    return sorted(load_roles(CAREERS_PATH), key=lambda role: role["name_vi"].casefold())


@st.cache_data(max_entries=1)
def load_resources() -> dict:
    with (DATA_DIR / "resources.json").open(encoding="utf-8") as source:
        resources = json.load(source)
    return merge_academic_curriculum(resources)


@st.cache_data(max_entries=1)
def load_demo_profiles() -> list[dict]:
    with DEMO_PROFILES_PATH.open(encoding="utf-8") as source:
        demos = json.load(source)
    if not isinstance(demos, list) or any(not item.get("synthetic") for item in demos):
        raise ValueError("data/demo_profiles.json must contain explicitly synthetic profiles.")
    return demos


@st.cache_data(max_entries=1)
def load_role_taxonomy() -> dict[str, list[dict]]:
    """Group positions by their RIASEC career family taxonomy."""
    rf_path = DATA_DIR / "role_families_riasec.json"
    with rf_path.open(encoding="utf-8") as source:
        rf = json.load(source)
    positions = load_positions()
    taxonomy: dict[str, list[dict]] = {}
    for fam in rf.get("families", []):
        f_label = fam["label"]
        assigned = []
        for rid in fam.get("role_ids", []):
            r_obj = next((r for r in positions if r["id"] == rid), None)
            if r_obj and r_obj not in assigned:
                assigned.append(r_obj)
        for prefix in fam.get("role_prefixes", []):
            for r in positions:
                if r["id"].startswith(prefix) and r not in assigned:
                    assigned.append(r)
        taxonomy[f_label] = sorted(assigned, key=lambda x: x["name_vi"].casefold())
    return taxonomy


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
        'fill="#0A7AFF"/><text x="48" y="48" text-anchor="middle" '
        'font-family="Arial,sans-serif" font-size="34" font-weight="700" '
        'fill="#fff">AI</text></svg>'
    )
    encoded = base64.b64encode(fallback_svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def display_skill(skill: str) -> str:
    """Translate descriptive skill labels while preserving technology names."""
    return SKILL_NAMES_VI.get(skill.casefold(), skill)


SKILL_EXACT_CASES: dict[str, str] = {
    "power bi": "Power BI",
    "rest api": "REST API",
    "rest api design": "Thiết kế REST API",
    "spring boot": "Spring Boot",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "asp.net core": "ASP.NET Core",
    "3ds max": "3ds Max",
    "adobe photoshop": "Adobe Photoshop",
    "adobe illustrator": "Adobe Illustrator",
    "adobe after effects": "Adobe After Effects",
    "adobe premiere pro": "Adobe Premiere Pro",
    "adobe premiere": "Adobe Premiere",
    "autocad electrical": "AutoCAD Electrical",
    "agile/scrum": "Agile/Scrum",
    "ci/cd": "CI/CD",
    "ui/ux": "UI/UX",
    "a/b testing": "A/B Testing",
    "api testing": "API Testing",
    "7 công cụ qc": "7 Công Cụ QC",
    "bán hàng b2b": "Bán Hàng B2B",
    "bán hàng b2c": "Bán Hàng B2C",
}

SKILL_WORD_CASES: dict[str, str] = {
    "sql": "SQL", "bi": "BI", "ml": "ML", "ai": "AI", "api": "API",
    "rest": "REST", "ui": "UI", "ux": "UX", "seo": "SEO", "sem": "SEM",
    "crm": "CRM", "erp": "ERP", "b2b": "B2B", "b2c": "B2C", "qc": "QC",
    "qa": "QA", "oop": "OOP", "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD",
    "html": "HTML", "css": "CSS", "json": "JSON", "c#": "C#", "c++": "C++",
    "nosql": "NoSQL", "devops": "DevOps", "riasec": "RIASEC",
    "python": "Python", "excel": "Excel", "tableau": "Tableau",
    "docker": "Docker", "java": "Java", "javascript": "JavaScript",
    "react": "React", "reactjs": "React", "vue": "Vue", "vuejs": "Vue.js",
    "vue.js": "Vue.js", "angular": "Angular", "flutter": "Flutter",
    "autocad": "AutoCAD", "linux": "Linux", "git": "Git",
    "node.js": "Node.js", "nodejs": "Node.js", "spring": "Spring",
    "boot": "Boot", "power": "Power", "sdk": "SDK", "swift": "Swift",
    "kotlin": "Kotlin", "php": "PHP", "golang": "Go", "go": "Go",
    "5s": "5S", "active": "Active", "directory": "Directory",
    "spark": "Spark", "apache": "Apache", "bloomberg": "Bloomberg",
    "terminal": "Terminal", "expressjs": "Express.js",
}


def format_skill_name(skill: str) -> str:
    """Capitalize skill words while preserving acronyms and brand names."""
    if not skill:
        return ""
    raw = skill.strip()
    lowered = raw.casefold()
    if lowered in SKILL_EXACT_CASES:
        return SKILL_EXACT_CASES[lowered]
    words = raw.split()
    formatted = []
    for w in words:
        wl = w.casefold()
        if wl in SKILL_WORD_CASES:
            formatted.append(SKILL_WORD_CASES[wl])
        elif "/" in w:
            parts = [SKILL_WORD_CASES.get(p.casefold(), p[:1].upper() + p[1:]) for p in w.split("/")]
            formatted.append("/".join(parts))
        else:
            formatted.append(w[:1].upper() + w[1:])
    return " ".join(formatted)


RESOURCE_REASON_LABELS: dict[str, str] = {
    "no_resources": "Chưa có tài liệu được xác minh cho kỹ năng này.",
    "unreviewed_content": "Chưa có tài liệu được review nội dung để đề xuất.",
    "blocked_resource": "Các tài liệu hiện có chưa truy cập được.",
    "unsuitable_content": "Các tài liệu đã xem chưa phù hợp với kỹ năng.",
    "specialized_source_required": "Chưa có nguồn chuyên biệt, hiện hành và được review đúng chuyên môn để gợi ý an toàn.",
    "missing_url": "Tài liệu chưa có liên kết web hợp lệ.",
    "level_mismatch": "Chưa có tài liệu được review cho level cần học.",
    "partial_content": "Tài liệu chỉ bao phủ một phần phạm vi kỹ năng.",
    "scope_evidence_pending": "Chưa có dẫn chứng ở cấp bài học/mục cụ thể để xác nhận Level của tài liệu; lịch chỉ dùng để tham khảo.",
    "unverified_link": "Liên kết chưa được xác minh.",
    "missing_resource_identity": "Tài liệu chưa có ID hoặc liên kết để tham chiếu.",
}
INTERVIEW_SELF_REVIEW = (
    ("answers_prompt", "Câu trả lời đi đúng vào từng phần mà câu hỏi yêu cầu."),
    ("explains_reasoning", "Tôi giải thích vì sao chọn cách làm, không chỉ liệt kê thuật ngữ."),
    ("fits_context", "Tôi gắn cách làm với bối cảnh/tình huống cụ thể trong câu hỏi."),
    ("gives_evidence", "Tôi nêu hành động hoặc bằng chứng kiểm chứng phù hợp (test, log, truy vấn, chỉ số, ví dụ)."),
    ("states_outcome", "Tôi nói rõ kết quả, giới hạn hoặc điều sẽ làm khác đi nếu có."),
)


def inject_styles() -> None:
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_site_script() -> None:
    script = SITE_SCRIPT_PATH.read_text(encoding="utf-8")
    st.html(f"<script>{script}</script>", unsafe_allow_javascript=True)


def render_landing_page() -> None:
    logo = logo_data_uri()
    st.markdown(
        f"""
        <header class="topbar-sticky" id="sticky-header">
          <div class="topbar-inner">
            <a class="brand" href="#top">
              <img src="{logo}" alt="Biểu trưng AI Career Coach">
              <span class="brand-word">AI CAREER COACH<span>ĐỊNH HƯỚNG NGHỀ NGHIỆP</span></span>
            </a>
            <nav aria-label="Điều hướng chính" class="desktop-nav">
              <a href="#why">Tính năng</a>
              <a href="#how">Cách hoạt động</a>
              <a href="#career-toolkit">Hồ sơ nghề nghiệp</a>
              <a href="#contact">Liên hệ</a>
            </nav>
            <div class="topbar-actions">
              <a class="nav-cta" href="#career-toolkit">Bắt đầu ngay <span aria-hidden="true">↗</span></a>
              <button class="menu-toggle" type="button" aria-label="Mở menu" aria-expanded="false" aria-controls="mobile-navigation">
                <svg class="menu-open-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
                <svg class="menu-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"/></svg>
              </button>
            </div>
          </div>
          <nav id="mobile-navigation" class="mobile-nav" aria-label="Điều hướng trên điện thoại" hidden>
            <div class="mobile-nav-links">
              <a href="#why">Tính năng <span aria-hidden="true">↗</span></a>
              <a href="#how">Cách hoạt động <span aria-hidden="true">↗</span></a>
              <a href="#career-toolkit">Hồ sơ nghề nghiệp <span aria-hidden="true">↗</span></a>
              <a href="#contact">Liên hệ <span aria-hidden="true">↗</span></a>
            </div>
            <a class="mobile-nav-cta" href="#career-toolkit">Bắt đầu với hồ sơ của bạn <span aria-hidden="true">→</span></a>
          </nav>
        </header>
        <div class="hero-wrap beams-surface" id="top">
          <div class="hero">
            <div>
              <h1>Tối ưu CV tức thì – <em>Định hướng sự nghiệp dài hạn</em></h1>
              <div class="hero-copy">Nền tảng AI giúp đánh giá CV và thiết kế lộ trình phát triển nghề nghiệp cá nhân hóa cho bạn.</div>
              <div class="hero-actions"><a class="button-primary" href="#career-toolkit">Tạo hồ sơ nghề nghiệp&nbsp; →</a><a class="text-link" href="#how">Xem cách hoạt động <span>↓</span></a></div>
            </div>
          </div>
        </div>
        <section class="section feature-section" id="why">
          <div class="section-heading"><h2>Rõ hướng đi, vững bước tiến</h2></div>
          <div class="feature-grid">
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="3"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0M3 7V4h3m12 0h3v3M3 17v3h3m12 0h3v-3"/></svg></div><h3><span>Nhận diện thế mạnh</span></h3><p>Tổng hợp kỹ năng và kinh nghiệm để thấy rõ điểm mạnh hiện có.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg></div><h3><span>Đối chiếu vị trí</span></h3><p>So sánh hồ sơ với yêu cầu của nghề bạn đang quan tâm.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 10-13h-7l0-7Z"/></svg></div><h3><span>Hiểu khoảng cách kỹ năng</span></h3><p>Nhìn ra năng lực cần bổ sung để tập trung học đúng việc.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="18" r="2"/><circle cx="18" cy="5" r="2"/><path d="M7 18h7a4 4 0 0 0 0-8h-4a4 4 0 0 1 0-8h6"/></svg></div><h3><span>Lập lộ trình học tập</span></h3><p>Chọn từng bước học phù hợp với mục tiêu nghề nghiệp.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5.5c3-1.5 6-1.5 9 0 3-1.5 6-1.5 9 0V19c-3-1.5-6-1.5-9 0-3-1.5-6-1.5-9 0V5.5ZM12 5.5V19"/></svg></div><h3><span>Tài liệu tham khảo</span></h3><p>Khám phá nguồn học tập gắn với kỹ năng cần phát triển.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v11H9l-5 4V5ZM8 9h8M8 12h5"/></svg></div><h3><span>Luyện phỏng vấn</span></h3><p>Thực hành câu hỏi theo vị trí bạn đang hướng đến.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h8l4 4v16H6V2ZM14 2v5h5M9 11h6M9 15h6M9 19h4"/></svg></div><h3><span>Rà soát CV</span></h3><p>Dùng thông tin từ CV làm điểm khởi đầu cho hồ sơ kỹ năng.</p></article>
            <article class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19h16M6 16V9m5 7V5m5 11v-4m4 4V8"/></svg></div><h3><span>Chủ động quyết định</span></h3><p>Xem rõ cơ sở gợi ý rồi tự chọn hướng đi phù hợp.</p></article>
          </div>
        </section>
        <section class="path-section beams-surface" id="how">
          <div class="how-inner">
            <h2>Cách hoạt động</h2>
            <div class="how-wizard" id="how-steps" data-step="1" style="--how-progress: 0%">
              <div class="how-progress-row">
                <span class="how-step-label" aria-live="polite">Bước 1 / 3</span>
                <div class="how-progress" role="progressbar" aria-label="Tiến trình cách hoạt động" aria-valuemin="1" aria-valuemax="3" aria-valuenow="1" aria-valuetext="Bước 1 trên 3">
                  <span class="how-progress-dot is-current" aria-hidden="true"></span>
                  <span class="how-progress-dot" aria-hidden="true"></span>
                  <span class="how-progress-dot" aria-hidden="true"></span>
                </div>
              </div>
              <div class="how-panels">
                <article class="how-panel" data-step-panel="1">
                  <h3 tabindex="-1">Tạo Hoặc Tải Hồ Sơ</h3>
                  <p class="how-lead">Bắt đầu tại mục Hồ sơ nghề nghiệp ngay dưới phần hướng dẫn.</p>
                  <ol class="how-detail-list">
                    <li><span class="how-detail-index" aria-hidden="true">1</span><div><strong>Thử nhanh hoặc nhập thông tin của bạn</strong><p>Chọn một hồ sơ mẫu, hoặc tự nhập kỹ năng, sở thích và kinh nghiệm.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">2</span><div><strong>Chuẩn bị thông tin bắt buộc</strong><p>Nếu tự nhập, cần ít nhất một kỹ năng, ví dụ “Python, SQL” (cách nhau bằng dấu phẩy), hoặc tải CV PDF/DOCX. JD và các mục còn lại là tùy chọn.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">3</span><div><strong>Chuyển sang rà soát</strong><p>Nhấn “Tiếp tục rà soát hồ sơ” ở cuối biểu mẫu.</p></div></li>
                  </ol>
                  <p class="how-outcome"><strong>Sau bước này</strong> Bạn sẽ thấy những kỹ năng cần kiểm tra trước khi tạo kết quả.</p>
                </article>
                <article class="how-panel" data-step-panel="2" hidden>
                  <h3 tabindex="-1">Rà soát và chọn vị trí</h3>
                  <p class="how-lead">Hãy chắc rằng hồ sơ phản ánh đúng kỹ năng bạn có.</p>
                  <ol class="how-detail-list">
                    <li><span class="how-detail-index" aria-hidden="true">1</span><div><strong>Kiểm tra kỹ năng nhận diện</strong><p>Bỏ chọn mục không đúng; thêm hoặc sửa tên kỹ năng nếu còn thiếu.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">2</span><div><strong>Tự khai báo Level nếu bạn biết</strong><p>Chọn mức cho từng kỹ năng, hoặc để “Chưa khai báo”. Web không tự suy Level từ CV.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">3</span><div><strong>Xác nhận và chọn nghề mục tiêu</strong><p>Nhấn “Xác nhận hồ sơ và xem kết quả”. Nếu chưa chọn vị trí trong biểu mẫu, hãy chọn ở mục gợi ý của tab “Tóm tắt”.</p></div></li>
                  </ol>
                  <p class="how-outcome"><strong>Sau bước này</strong> Hồ sơ đã xác nhận sẽ được dùng để đối chiếu với vị trí bạn chọn.</p>
                </article>
                <article class="how-panel" data-step-panel="3" hidden>
                  <h3 tabindex="-1">Đọc kết quả và lập kế hoạch</h3>
                  <p class="how-lead">Dùng các tab kết quả để chọn việc cần làm tiếp theo.</p>
                  <ol class="how-detail-list">
                    <li><span class="how-detail-index" aria-hidden="true">1</span><div><strong>Đọc “Tóm tắt” và “Khoảng cách”</strong><p>Xem kỹ năng đã lưu, kỹ năng khớp và kỹ năng còn thiếu của vị trí mục tiêu.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">2</span><div><strong>Mở “Lộ trình” và “Tài liệu”</strong><p>Tham khảo thứ tự học, nguồn học liệu và những phần chưa đủ dữ liệu để đề xuất.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">3</span><div><strong>Luyện tập và lưu lại</strong><p>Vào tab “Phỏng vấn” để tự luyện. Tải báo cáo Markdown, CSV hoặc JSON ở tab “Tài liệu” nếu muốn giữ kết quả.</p></div></li>
                  </ol>
                  <p class="how-outcome"><strong>Ghi nhớ</strong> Điểm đối chiếu là mức bao phủ kỹ năng, không phải xác suất tuyển dụng.</p>
                </article>
              </div>
              <div class="how-actions">
                <button class="how-back" type="button" hidden>← Quay lại</button>
                <button class="how-next" type="button" disabled>Tiếp tục <span aria-hidden="true">→</span></button>
                <a class="how-finish" href="#career-toolkit" hidden>Tạo hồ sơ ngay <span aria-hidden="true">→</span></a>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.html(
        """<script>
        (() => {
          if (window.__careerHeaderCleanup) window.__careerHeaderCleanup();
          const observer = new MutationObserver(() => {
            if (bindHeader()) observer.disconnect();
          });
          const bindHeader = () => {
            const header = document.getElementById('sticky-header');
            const toggle = header?.querySelector('.menu-toggle');
            const menu = document.getElementById('mobile-navigation');
            const scrollHost = document.querySelector('main[data-testid="stMain"]');
            if (!header || !toggle || !menu || !scrollHost) return false;
            const controller = new AbortController();
            const signal = controller.signal;
            const setOpen = (open) => {
              toggle.setAttribute('aria-expanded', String(open));
              toggle.setAttribute('aria-label', open ? 'Đóng menu' : 'Mở menu');
              menu.hidden = !open;
              header.classList.toggle('menu-open', open);
              document.body.classList.toggle('career-menu-open', open);
            };
            const updateScroll = () => header.classList.toggle('is-scrolled', scrollHost.scrollTop > 10);
            toggle.addEventListener('click', () => setOpen(menu.hidden), {signal});
            menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setOpen(false), {signal}));
            document.addEventListener('keydown', event => {
              if (event.key === 'Escape' && !menu.hidden) {
                setOpen(false);
                toggle.focus();
              }
            }, {signal});
            window.addEventListener('resize', () => {
              if (window.innerWidth >= 768 && !menu.hidden) setOpen(false);
            }, {signal});
            scrollHost.addEventListener('scroll', updateScroll, {signal, passive: true});
            updateScroll();
            window.__careerHeaderCleanup = () => {
              controller.abort();
              document.body.classList.remove('career-menu-open');
            };
            return true;
          };
          window.__careerHeaderCleanup = () => observer.disconnect();
          if (!bindHeader()) observer.observe(document.body, {childList: true, subtree: true});
        })();
        </script>""",
        unsafe_allow_javascript=True,
    )


def render_closing_sections() -> None:
    logo = logo_data_uri()
    faq_markup = "\n".join(
        f'<article class="faq-item{" is-open" if index == 1 else ""}" data-faq-id="{index}">'
        f'<div class="faq-item-heading"><button class="faq-trigger" type="button" id="faq-trigger-{index}" '
        f'aria-controls="faq-panel-{index}" aria-expanded="{"true" if index == 1 else "false"}">'
        f'<span class="faq-question">{escape(question)}</span>'
        f'<svg class="faq-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'<path d="m6 9 6 6 6-6"/></svg></button></div>'
        f'<div class="faq-panel" id="faq-panel-{index}" role="region" '
        f'aria-labelledby="faq-trigger-{index}" aria-hidden="{"false" if index == 1 else "true"}"'
        f'{"" if index == 1 else " inert"}><div class="faq-panel-inner">'
        f'<div class="faq-answer">{answer}</div></div></div></article>'
        for index, (question, answer) in enumerate(FAQ_ITEMS, 1)
    )
    st.markdown(
        f"""
        <section class="faq-section" id="faq" aria-labelledby="faq-title">
          <div class="faq-inner">
            <div class="faq-intro">
              <h2 id="faq-title">Câu hỏi thường gặp</h2>
              <p>Những điều cần biết trước khi bắt đầu khám phá nghề nghiệp cùng AI Career Coach.</p>
            </div>
            <div class="faq-content">
              <div class="faq-search">
                <svg class="faq-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4"/></svg>
                <input class="faq-search-input" type="search" placeholder="Tìm câu hỏi hoặc từ khóa..." aria-label="Tìm trong câu hỏi thường gặp" aria-controls="faq-list" autocomplete="off">
                <button class="faq-search-clear" type="button" aria-label="Xóa từ khóa tìm kiếm" hidden>×</button>
              </div>
              <span class="faq-search-status" role="status" aria-live="polite"></span>
              <div class="faq-list" id="faq-list">{faq_markup}</div>
              <p class="faq-empty" hidden>Không tìm thấy câu hỏi phù hợp. Hãy thử từ khóa khác.</p>
            </div>
          </div>
        </section>
        <footer class="site-footer" id="contact">
          <div class="site-footer-inner">
            <div class="site-footer-intro">
              <a class="site-footer-brand" href="#top" aria-label="AI Career Coach — về đầu trang">
                <img src="{logo}" alt="">
                <span>AI CAREER COACH</span>
              </a>
              <p>Từng bước rõ ràng hơn trên hành trình nghề nghiệp của bạn.</p>
            </div>
            <nav class="site-footer-nav" aria-label="Điều hướng cuối trang">
              <div class="site-footer-column">
                <h3>Khám phá</h3>
                <a href="#why">Tính năng</a>
                <a href="#how">Cách hoạt động</a>
                <a href="#career-toolkit">Hồ sơ nghề nghiệp</a>
                <a href="#faq">Câu hỏi thường gặp</a>
              </div>
              <div class="site-footer-column">
                <h3>Dự án</h3>
                <a href="https://github.com/LinhLaSieuSao/AI-Career-Coach" target="_blank" rel="noopener noreferrer">Mã nguồn <span aria-hidden="true">↗</span></a>
                <a href="https://github.com/LinhLaSieuSao/AI-Career-Coach/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">Đóng góp <span aria-hidden="true">↗</span></a>
                <a href="https://github.com/LinhLaSieuSao/AI-Career-Coach/issues" target="_blank" rel="noopener noreferrer">Báo lỗi <span aria-hidden="true">↗</span></a>
              </div>
              <div class="site-footer-column site-footer-contact">
                <h3>Liên hệ nhóm phát triển</h3>
                <p>Có câu hỏi hoặc ý tưởng? Hãy trao đổi cùng nhóm qua GitHub.</p>
                <a class="site-footer-contact-link" href="https://github.com/LinhLaSieuSao/AI-Career-Coach/discussions" target="_blank" rel="noopener noreferrer">Mở Discussions <span aria-hidden="true">↗</span></a>
                <a href="https://github.com/LinhLaSieuSao/AI-Career-Coach/issues" target="_blank" rel="noopener noreferrer">Gửi phản hồi <span aria-hidden="true">↗</span></a>
              </div>
            </nav>
          </div>
          <div class="site-footer-bottom">
            <span>AI Career Coach · Dự án mã nguồn mở</span>
            <span>Điểm heuristic phản ánh mức độ bao phủ kỹ năng, không phải xác suất tuyển dụng.</span>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Danh Mục Nghề", width="large")
def open_role_taxonomy_dialog(positions: list[dict], role_by_id: dict[str, dict], taxonomy: dict[str, list[dict]]) -> None:
    st.markdown('<span class="role-dlg-marker"></span>', unsafe_allow_html=True)
    search_kw = st.text_input(
        "Nhập từ khóa tìm kiếm",
        placeholder="🔍 Nhập từ khóa tìm kiếm chuyên môn (VD: data, sales, kế toán, java, marketing, tester...)",
        key="dlg_taxonomy_search",
        label_visibility="collapsed",
    )

    current_role_id = st.session_state.get("career_role_picker")

    if search_kw.strip():
        kw = search_kw.strip().casefold()
        matching_roles = [
            r for r in positions
            if kw in r["name_vi"].casefold()
            or kw in r["name"].casefold()
            or any(kw in s["name"].casefold() for s in r["skills"])
        ]
        st.markdown(f"**Kết quả tìm kiếm:** {len(matching_roles)} vị trí chuyên môn phù hợp")
        if matching_roles:
            c1, c2 = st.columns(2)
            for idx, r in enumerate(matching_roles):
                is_sel = (r["id"] == current_role_id)
                btn_label = f"✓ {r['name_vi']}" if is_sel else r["name_vi"]
                btn_type = "primary" if is_sel else "secondary"
                target_col = c1 if idx % 2 == 0 else c2
                if target_col.button(btn_label, key=f"dlg_search_role_{r['id']}", type=btn_type, use_container_width=True):
                    st.session_state["career_role_picker"] = r["id"]
                    st.rerun()
        else:
            st.info("Không tìm thấy vị trí nào phù hợp với từ khóa.")
    else:
        col_left, col_right = st.columns([1.1, 2.2])
        family_names = list(taxonomy.keys())

        default_idx = 0
        if current_role_id:
            for idx, (f_name, r_list) in enumerate(taxonomy.items()):
                if any(r["id"] == current_role_id for r in r_list):
                    default_idx = idx
                    break

        with col_left:
            st.markdown("<div class='dlg-group-title'>NHÓM NGHỀ</div>", unsafe_allow_html=True)
            selected_family = st.radio(
                "Nhóm nghề",
                options=family_names,
                index=default_idx,
                key="dlg_selected_family_radio",
                label_visibility="collapsed",
            )

        with col_right:
            roles_in_group = taxonomy.get(selected_family, [])
            st.markdown(f"<div class='dlg-roles-title'>VỊ TRÍ CHUYÊN MÔN · {selected_family} ({len(roles_in_group)} vị trí)</div>", unsafe_allow_html=True)
            st.caption("Bấm chọn đúng 1 vị trí chuyên môn (bấm để áp dụng ngay):")

            col_p1, col_p2 = st.columns(2)
            for idx, r in enumerate(roles_in_group):
                is_sel = (r["id"] == current_role_id)
                btn_label = f"✓ {r['name_vi']}" if is_sel else r["name_vi"]
                btn_type = "primary" if is_sel else "secondary"
                target_p = col_p1 if idx % 2 == 0 else col_p2
                if target_p.button(
                    btn_label,
                    key=f"dlg_pill_role_{r['id']}",
                    type=btn_type,
                    use_container_width=True,
                ):
                    st.session_state["career_role_picker"] = r["id"]
                    st.rerun()

    c_foot_l, c_foot_r = st.columns([1.2, 2.8])
    with c_foot_l:
        if st.button("Đóng", key="dlg_close_btn", use_container_width=True):
            st.rerun()
    with c_foot_r:
        if current_role_id and current_role_id in role_by_id:
            st.markdown(
                f"<div style='text-align:right;padding-top:8px;font-size:16px;'>Đã chọn: <b style='color:var(--color-plume-600);font-size:17px;'>{format_role(role_by_id[current_role_id])}</b></div>",
                unsafe_allow_html=True,
            )



def deduplicate_skills(skills: list[str], exclude: set[str] | None = None) -> list[str]:
    seen = set(exclude or ())
    result = []
    for s in skills:
        key = normalize_skill(s)
        if key not in seen:
            seen.add(key)
            result.append(display_skill(s))
    return result


def get_fit_tier(score: float | None) -> str:
    if score is None:
        return "Chưa xác định"
    if score >= 75:
        return "Cao"
    if score >= 50:
        return "Khá"
    if score >= 25:
        return "Trung bình"
    return "Thấp"


def get_summary_sentences(cv_jd: dict | None, saved_role: dict | None, effective_skills: list[str]) -> str:
    if cv_jd:
        mh = cv_jd.get("must_have", {})
        nth = cv_jd.get("nice_to_have", {})
        unc = cv_jd.get("unclassified", {})
        mh_count = mh.get("count", 0)
        mh_matched = len(mh.get("matched", []))
        nth_count = nth.get("count", 0)
        nth_matched = len(nth.get("matched", []))
        unc_count = unc.get("count", 0)
        unc_matched = len(unc.get("matched", []))

        if mh_count > 0:
            s1 = f"Bạn đã có {mh_matched}/{mh_count} kỹ năng bắt buộc."
            if mh_matched == mh_count:
                if nth_count > 0 and nth_matched < nth_count:
                    s2 = "Nên bổ sung thêm kỹ năng ưu tiên để hồ sơ nổi bật hơn."
                else:
                    s2 = "Hồ sơ của bạn đáp ứng rất tốt các yêu cầu chính của vị trí."
            else:
                s2 = f"Nên ưu tiên bổ sung {mh_count - mh_matched} kỹ năng bắt buộc còn thiếu để tăng cơ hội trúng tuyển."
            return f"{s1} {s2}"
        elif unc_count > 0:
            s1 = f"Bạn đã đáp ứng {unc_matched}/{unc_count} kỹ năng được tìm thấy trong mô tả công việc."
            if unc_matched == unc_count:
                s2 = "Hồ sơ của bạn bao phủ đầy đủ các kỹ năng yêu cầu trong JD."
            else:
                s2 = f"Nên trau dồi thêm {unc_count - unc_matched} kỹ năng còn thiếu để hoàn thiện hồ sơ."
            return f"{s1} {s2}"
        else:
            return "Chưa xác định được kỹ năng cụ thể từ mô tả công việc."

    if saved_role:
        presence = match_role(effective_skills, saved_role)
        m_count = len(presence.get("matched", []))
        miss_count = len(presence.get("missing", []))
        total_count = m_count + miss_count
        score = presence.get("percent", 0.0)

        s1 = f"Bạn đã có {m_count}/{total_count} kỹ năng cốt lõi của vị trí này."
        if miss_count == 0:
            s2 = "Hồ sơ của bạn đáp ứng trọn vẹn danh mục kỹ năng chuẩn của vị trí!"
        elif score >= 50:
            s2 = f"Nên bổ sung thêm {miss_count} kỹ năng còn thiếu để gia tăng cơ hội ứng tuyển."
        else:
            s2 = f"Hãy bắt đầu với các kỹ năng nền tảng còn thiếu để xây dựng lộ trình học tập hiệu quả."
        return f"{s1} {s2}"

    return "Hãy chọn một vị trí gợi ý bên dưới hoặc từ Danh Mục Nghề để xem phân tích độ phù hợp và lộ trình học tập tương ứng."


def render_summary_hero(role_name: str, score: float | None, summary_text: str, has_target: bool):
    with st.container(border=True):
        tier = get_fit_tier(score)
        if has_target:
            st.markdown(f"### Bạn đang phù hợp ở mức **{tier}** với vị trí **{role_name}**")
        else:
            st.markdown("### Bạn chưa chọn vị trí mục tiêu")

        if score is not None:
            col_score, col_prog = st.columns([1.2, 3])
            with col_score:
                score_str = f"{int(score)}%" if score == int(score) else f"{score:.1f}%"
                st.markdown(
                    f'''<div style="margin: 4px 0 8px 0;">'''
                    f'''<div style="font-size:38px;font-weight:800;color:#0284c7;line-height:1;">{score_str}</div>'''
                    f'''<div style="font-size:13.5px;font-weight:600;color:var(--color-ink-faint);margin-top:4px;">Độ phù hợp tổng hợp</div>'''
                    f'''</div>''',
                    unsafe_allow_html=True,
                )
            with col_prog:
                st.progress(max(0.0, min(1.0, score / 100.0)))

        st.markdown(
            f'''<p class="typ-cap2" style="margin-top:8px;margin-bottom:6px;">{summary_text}</p>''',
            unsafe_allow_html=True,
        )

        # Phần 4: Khối cảnh báo nổi bật cuối khối điểm số
        st.markdown(
            '''<div class="prominent-disclaimer-box">'''
            '''<div class="prominent-disclaimer-icon">⚠️</div>'''
            '''<div>'''
            '''<div class="prominent-disclaimer-title">Lưu ý quan trọng</div>'''
            '''<p class="prominent-disclaimer-body">Điểm này chỉ là gợi ý dựa trên kỹ năng và sở thích bạn đã khai báo. Đây không phải khả năng được tuyển dụng và không phải đánh giá trình độ (level) của bạn.</p>'''
            '''</div>'''
            '''</div>''',
            unsafe_allow_html=True,
        )


def render_skill_chips(matched_skills: list[str], missing_skills: list[str], has_target: bool):
    col_has, col_need = st.columns(2)
    with col_has:
        with st.container(border=True):
            st.markdown(f"#### Bạn đã có ({len(matched_skills)})")
            if matched_skills:
                chips = "".join(f'<span class="skill-chip skill-chip-matched">✓ {s}</span>' for s in matched_skills)
                st.markdown(f'<div class="skill-chips-container">{chips}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="skill-chips-empty">Chưa ghi nhận kỹ năng nào phù hợp trong hồ sơ.</p>', unsafe_allow_html=True)

    with col_need:
        with st.container(border=True):
            st.markdown(f"#### Cần bổ sung ({len(missing_skills)})")
            if missing_skills:
                chips = "".join(f'<span class="skill-chip skill-chip-missing">+ {s}</span>' for s in missing_skills)
                st.markdown(f'<div class="skill-chips-container">{chips}</div>', unsafe_allow_html=True)
            else:
                if has_target:
                    st.markdown('<p class="skill-chips-empty">Tuyệt vời! Bạn đã đáp ứng trọn vẹn các kỹ năng của vị trí này.</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p class="skill-chips-empty">Hãy chọn vị trí mục tiêu để xem các kỹ năng cần bổ sung.</p>', unsafe_allow_html=True)


def render_suggested_roles(suggestions: list[dict], revision: int):
    st.subheader("Vị trí gợi ý cho bạn")
    if not suggestions:
        st.info("Chưa có gợi ý vị trí nào phù hợp với kỹ năng hiện tại của bạn.")
        return

    top_3 = suggestions[:3]
    rest = suggestions[3:]

    for item in top_3:
        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1.2])
            with col_info:
                st.markdown(
                    f'''<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-height:36px;">'''
                    f'''<span style="font-weight:700;font-size:16px;color:var(--color-ink);line-height:1.4;">{item['role_name']}</span>'''
                    f'''<span class="role-match-badge">{item['score']}% Phù hợp</span>'''
                    f'''</div>''',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("Chọn vị trí này", key=f"choose_role_{revision}_{item['role_id']}", use_container_width=True):
                    st.session_state["career_role_id"] = item["role_id"]
                    st.session_state["pending_career_role"] = item["role_id"]
                    st.session_state["career_role_picker"] = item["role_id"]
                    st.session_state.pop("interview_session", None)
                    st.session_state["pending_result_tab"] = "Khoảng cách"
                    st.rerun()

    if rest:
        with st.expander(f"Xem thêm vị trí khác ({len(rest)})", expanded=False):
            for item in rest:
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1.2])
                    with col_info:
                        st.markdown(
                            f'''<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-height:36px;">'''
                            f'''<span style="font-weight:700;font-size:15px;color:var(--color-ink);line-height:1.4;">{item['role_name']}</span>'''
                            f'''<span class="role-match-badge">{item['score']}% Phù hợp</span>'''
                            f'''</div>''',
                            unsafe_allow_html=True,
                        )
                    with col_btn:
                        if st.button("Chọn vị trí này", key=f"choose_role_{revision}_{item['role_id']}", use_container_width=True):
                            st.session_state["career_role_id"] = item["role_id"]
                            st.session_state["pending_career_role"] = item["role_id"]
                            st.session_state["career_role_picker"] = item["role_id"]
                            st.session_state.pop("interview_session", None)
                            st.session_state["pending_result_tab"] = "Khoảng cách"
                            st.rerun()


def render_profile_extracted_details(profile: dict, effective_skills: list[str], cv_extraction: dict | None, revision: int):
    with st.expander("Hồ sơ đã trích xuất của bạn", expanded=False):
        for index, item in enumerate(profile.get("moved", [])):
            left, right = st.columns([4, 1])
            left.info(f"Đã chuyển ‘{item['item']}’ từ {item['from']} sang {item['to']}.")
            if right.button("Hoàn tác", key=f"undo_move_{revision}_{index}"):
                st.session_state["profile_result"] = undo_profile_move(
                    profile, index, original_interests=st.session_state.get("profile_original_interests", [])
                )
                st.rerun()

        retained = []
        if profile.get("unrecognized_skills"):
            st.markdown('<div class="sub-heading-cap1" style="margin-bottom:4px;">Kỹ năng chưa nhận diện được</div>', unsafe_allow_html=True)
            st.caption("Chọn kỹ năng muốn giữ lại trong hồ sơ. Tên chưa nhận diện không được tính vào điểm đối chiếu hoặc học liệu gợi ý.")
            for skill in profile["unrecognized_skills"]:
                if st.checkbox(f"Giữ ‘{skill}’ trong hồ sơ", value=True, key=f"keep_unknown_{revision}_{skill}"):
                    retained.append(skill)

        st.markdown('<div class="sub-heading-cap1" style="margin-bottom:12px;">Hồ sơ của bạn</div>', unsafe_allow_html=True)

        # 1. Kỹ năng (Cấp 2) + mục con trích xuất từ CV / kinh nghiệm (Cấp 3 thụt lề)
        skills_str = ", ".join(display_skill(s) for s in effective_skills) or "Chưa có thông tin"
        st.markdown(f"**Kỹ năng:** {skills_str}")
        if profile.get("skills_from_cv"):
            cv_skills = ", ".join(display_skill(s) for s in profile["skills_from_cv"])
            st.markdown(f'<div class="profile-subitem-cap3">– Kỹ năng trích từ CV và đã xác nhận: {escape(cv_skills)}</div>', unsafe_allow_html=True)
        if profile.get("skills_from_experience"):
            exp_skills = ", ".join(display_skill(s) for s in profile["skills_from_experience"])
            st.markdown(f'<div class="profile-subitem-cap3">– Kỹ năng trích từ kinh nghiệm và đã xác nhận: {escape(exp_skills)}</div>', unsafe_allow_html=True)
        elif profile.get("experience"):
            st.markdown('<div class="profile-subitem-cap3">– Kinh nghiệm được lưu để tham khảo; hệ thống chỉ dùng kỹ năng trong đó khi nhận diện được và bạn xác nhận, không chấm số năm hay thâm niên.</div>', unsafe_allow_html=True)

        # 2. Sở thích (Cấp 2)
        interests_str = ", ".join(profile.get("interests", [])) or "Chưa có thông tin"
        st.markdown(f'<div class="profile-item-cap2" style="margin-top:10px;"><strong>Sở thích:</strong> {escape(interests_str)}</div>', unsafe_allow_html=True)

        # 3. Hoạt động nghề nghiệp đã chọn (Cấp 2)
        if profile.get("interest_activity_ids"):
            acts_str = ", ".join(activity_label(value) for value in profile["interest_activity_ids"])
            st.markdown(f'<div class="profile-item-cap2"><strong>Hoạt động nghề nghiệp đã chọn:</strong> {escape(acts_str)}</div>', unsafe_allow_html=True)

        # 4. Kinh nghiệm (Cấp 2)
        exp_text = profile.get("experience") or "Chưa có thông tin"
        st.markdown(f'<div class="profile-item-cap2"><strong>Kinh nghiệm:</strong> {escape(exp_text)}</div>', unsafe_allow_html=True)

        # 5. Level đã khai báo (Cấp 2 + chips)
        levels_map = profile.get("levels", {})
        if levels_map:
            st.markdown('<div class="profile-item-cap2"><strong>Level đã khai báo:</strong></div>', unsafe_allow_html=True)
            chips_html = "".join(f'<span class="level-chip"><strong>{escape(display_skill(k))}:</strong>&nbsp;Cấp độ {v}</span>' for k, v in levels_map.items())
            st.markdown(f'<div class="level-chips-container">{chips_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="profile-item-cap2"><strong>Level đã khai báo:</strong> Chưa khai báo; không suy từ CV</div>', unsafe_allow_html=True)

        # 6. Văn bản đã trích xuất từ CV (Cấp 2 + high-contrast scrollable box)
        if cv_extraction:
            st.markdown(
                f'<div class="profile-item-cap2" style="margin-top:14px;"><strong>Văn bản đã trích xuất · {escape(cv_extraction["filename"])}</strong> ({len(cv_extraction["text"]):,} ký tự)</div>',
                unsafe_allow_html=True,
            )
            escaped_cv_text = escape(cv_extraction["text"])
            st.markdown(f'<div class="extracted-cv-box">{escaped_cv_text}</div>', unsafe_allow_html=True)


def _render_chip_line(label: str, skills: list[str], kind: str, fallback: str, hidden_markdown: str = "") -> None:
    if not skills:
        content_html = f'<span style="font-style:italic;color:var(--color-ink-faint);">{fallback}</span>'
    else:
        chip_class = "skill-chip-matched" if kind == "matched" else "skill-chip-missing"
        icon = "✓ " if kind == "matched" else "+ "
        chips = "".join(f'<span class="skill-chip {chip_class}">{icon}{escape(display_skill(s))}</span>' for s in skills)
        content_html = f'<div class="skill-chips-container" style="display:inline-flex;margin:2px 0 2px 4px;vertical-align:middle;">{chips}</div>'

    hidden_html = f'<span style="display:none;">{escape(hidden_markdown)}</span>' if hidden_markdown else ""
    st.markdown(
        f'<div class="tech-item-cap2"><strong>{label}:</strong> {content_html}{hidden_html}</div>',
        unsafe_allow_html=True,
    )


def render_technical_details(cv_jd: dict | None, profile: dict, effective_skills: list[str]):
    with st.expander("Chi tiết kỹ thuật & minh chứng", expanded=False):
        if cv_jd:
            metric_columns = st.columns(3)
            metric_specs = (
                ("must_have", "Bao phủ kỹ năng bắt buộc"),
                ("nice_to_have", "Bao phủ kỹ năng ưu tiên"),
                ("unclassified", "Trùng kỹ năng chưa phân loại"),
            )
            for column, (kind, label) in zip(metric_columns, metric_specs):
                category = cv_jd[kind]
                value = f"{category['percent']}%" if category["percent"] is not None else "—"
                column.metric(label, value, delta=f"{len(category['matched'])}/{category['count']} kỹ năng")

            # Phần 3a: Đổi nhãn thành tiếng thường, bỏ JD và heuristic 85/15
            if cv_jd["overall_percent"] is not None:
                st.metric("Điểm phù hợp tổng hợp (ước tính)", f"{cv_jd['overall_percent']}%")
            else:
                st.info("Chưa có kỹ năng nào được xác nhận là bắt buộc; ứng dụng không tạo điểm tổng hợp. Kỹ năng chưa phân loại vẫn được đối chiếu riêng.")

            # Phần 3b: Khối Cách tính điểm này gồm các gạch đầu dòng ngắn Cấp 2
            recognized_count = cv_jd.get('recognized_count', len(cv_jd['jd_skills']))
            st.markdown(
                f'''<div class="calc-explanation-box">'''
                f'''<div class="calc-explanation-title">Cách tính điểm này</div>'''
                f'''<ul class="calc-explanation-list">'''
                f'''<li>Điểm chỉ tính các kỹ năng bạn đã xác nhận: nhóm kỹ năng bắt buộc chiếm 85%, nhóm kỹ năng ưu tiên chiếm 15%.</li>'''
                f'''<li>Nhóm kỹ năng chưa phân loại được hiển thị riêng và không tính vào điểm.</li>'''
                f'''<li>Đây không phải đánh giá bạn có đủ điều kiện ứng tuyển, năng lực thực tế hay khả năng được tuyển.</li>'''
                f'''<li>Hệ thống chỉ đối chiếu tên kỹ năng bạn đã xác nhận với danh mục kỹ năng của hệ thống; không đánh giá level hay năng lực thực tế.</li>'''
                f'''<li>Số kỹ năng yêu cầu của vị trí này đã được phân loại: <strong>{recognized_count}</strong>.</li>'''
                f'''</ul>'''
                f'''</div>''',
                unsafe_allow_html=True,
            )

            if cv_jd.get("low_confidence"):
                st.warning("Có dưới 3 kỹ năng bắt buộc được xác nhận; chỉ số tổng hợp có phạm vi đầu vào hẹp.")

            # Phần 3c: Các dòng kỹ năng đổi nhãn dễ hiểu, hiển thị chip Cấp 2
            mh = cv_jd["must_have"]
            nth = cv_jd["nice_to_have"]
            unc = cv_jd["unclassified"]

            _render_chip_line(
                "Kỹ năng bắt buộc bạn đã có",
                mh["matched"],
                "matched",
                "Chưa có",
            )
            _render_chip_line(
                "Kỹ năng bắt buộc bạn còn thiếu",
                mh["missing"],
                "missing",
                "Không thiếu kỹ năng nào",
            )
            _render_chip_line(
                "Kỹ năng ưu tiên bạn đã có",
                nth["matched"],
                "matched",
                "Chưa có",
            )
            _render_chip_line(
                "Kỹ năng ưu tiên bạn còn thiếu",
                nth["missing"],
                "missing",
                "Không thiếu kỹ năng nào",
            )

            unc_matched_str = ", ".join(display_skill(s) for s in unc["matched"]) or "Chưa có"
            unc_missing_str = ", ".join(display_skill(s) for s in unc["missing"]) or "Không có"
            _render_chip_line(
                "Kỹ năng khác (chưa xếp vào bắt buộc/ưu tiên) bạn đã có",
                unc["matched"],
                "matched",
                "Chưa có",
                hidden_markdown=f"**Trùng kỹ năng chưa phân loại khớp hồ sơ:** {unc_matched_str}",
            )
            _render_chip_line(
                "Kỹ năng khác (chưa xếp vào bắt buộc/ưu tiên) bạn còn thiếu",
                unc["missing"],
                "missing",
                "Không có",
                hidden_markdown=f"**Trùng kỹ năng chưa phân loại chưa có trong hồ sơ:** {unc_missing_str}",
            )

        # Phần 3d: Expander con "Cách đọc và hiểu đúng điểm số gợi ý"
        with st.expander("Cách đọc và hiểu đúng điểm số gợi ý", expanded=False):
            st.markdown(
                '''<div style="display:flex;flex-direction:column;gap:8px;padding:4px 0;">'''
                '''<div class="tech-guide-item-cap2"><strong>Mức khớp kỹ năng (Skill fit · Role-IDF):</strong> cho biết bạn có bao nhiêu kỹ năng mà nghề này yêu cầu. Kỹ năng nào ít người có thì được tính quan trọng hơn.</div>'''
                '''<div class="tech-guide-item-cap2"><strong>Mức hợp sở thích (Interest fit):</strong> so sánh sở thích nghề nghiệp của bạn với kiểu người thường làm nghề này, theo mô hình RIASEC (6 nhóm tính cách nghề nghiệp).</div>'''
                '''<div class="tech-guide-item-cap2"><strong>Điểm gợi ý:</strong> ghép từ 75% mức khớp kỹ năng (75% skill fit) và 25% mức hợp sở thích. Nếu mức khớp kỹ năng dưới 15%, điểm gợi ý tối đa chỉ là 5/100.</div>'''
                '''<div class="tech-guide-item-cap2"><strong>Lưu ý:</strong> đây chỉ là gợi ý tham khảo, không phải khả năng được tuyển thực tế hay kết luận về năng lực của bạn.</div>'''
                '''</div>''',
                unsafe_allow_html=True,
            )

        st.caption("Điểm heuristic theo kỹ năng/sở thích; không là xác suất tuyển dụng hay đánh giá level.")
        if profile.get("unrecognized_skills"):
            st.warning(
                "⚠️ Có kỹ năng bạn nhập chưa thuộc catalog nên chưa được tính vào điểm khớp. "
                "Hãy dùng tên kỹ năng chuẩn trong biểu mẫu hồ sơ phía trên để hệ thống đối chiếu chính xác hơn."
            )
        if role_recommendation_is_low_confidence({"skills": effective_skills}):
            st.warning(LOW_CONFIDENCE_ROLE_MESSAGE)
        if not effective_skills and (profile.get("interests") or profile.get("interest_activity_ids")):
            st.info(
                "Chỉ có sở thích được ánh xạ; gợi ý bị giới hạn tối đa "
                f"{100 * LOW_SKILL_ROLE_SCORE_CAP:.0f}/100 vì chưa có kỹ năng trùng. "
                "Điểm này không phản ánh mức đáp ứng kỹ năng."
            )
def render_toolkit() -> None:
    st.markdown(
        '<div class="tool-title" id="career-toolkit"><h2>Hồ sơ nghề nghiệp</h2></div>',
        unsafe_allow_html=True,
    )
    positions = load_positions()
    role_by_id = {position["id"]: position for position in positions}
    if not role_by_id:
        st.error("Chưa có dữ liệu vị trí nghề nghiệp trong data/roles.json.")
        return

    pending_demo = st.session_state.pop("pending_demo_profile_id", None)
    if pending_demo:
        demo = next((item for item in load_demo_profiles() if item["id"] == pending_demo), None)
        if demo and demo["role_id"] in role_by_id:
            values = demo["profile"]
            st.session_state["skills_input"] = "; ".join(values["skills"])
            st.session_state["interests_input"] = "; ".join(values["interests"])
            st.session_state["interest_activity_input"] = []
            st.session_state["experience_input"] = values["experience"]
            st.session_state["career_role_picker"] = demo["role_id"]
            st.session_state["job_description_input"] = ""
            st.session_state.pop("uploaded_cv_input", None)
            candidate = prepare_submission(values, None)
            if candidate["accepted"]:
                st.session_state["profile_draft"] = {
                    "id": uuid4().hex[:10], "profile": candidate["profile"],
                    "cv_extraction": None, "document": candidate["document"],
                    "jd_text": "", "jd_skill_options": [], "jd_error": None,
                    "role_id": demo["role_id"], "demo_id": demo["id"], "warnings": [],
                    "demo_label": demo["label"], "demo_notice": demo["notice"],
                }
                st.session_state["profile_step"] = 2
                st.session_state["wizard_errors"] = []

    pending_role = st.session_state.pop("pending_career_role", None)
    if pending_role in role_by_id:
        st.session_state["career_role_picker"] = pending_role

    if st.session_state.get("profile_step", 1) == 1:
        taxonomy = load_role_taxonomy()
        current_role_id = st.session_state.get("career_role_picker")
        current_role_obj = role_by_id.get(current_role_id) if current_role_id else None
        selected_role_id = current_role_id
        with st.container(border=True, key="profile_entry_panel"):
            st.markdown("### Bước 1/2 · Tạo Hoặc Tải Hồ Sơ")
            skills_text = st.text_area("Kỹ năng", placeholder="Python, SQL, phân tích dữ liệu", key="skills_input")
            st.caption("Ngăn cách các kỹ năng bằng dấu phẩy, dấu chấm phẩy hoặc xuống dòng.")
            interests_text = st.text_area("Sở thích nghề nghiệp", placeholder="Phân tích dữ liệu, thiết kế sản phẩm", key="interests_input")
            activity_ids = [activity["id"] for activity in load_interest_activities()]
            selected_activity_ids = st.multiselect(
                "Hoạt động nghề nghiệp yêu thích (tùy chọn)",
                options=activity_ids,
                format_func=activity_label,
                key="interest_activity_input",
                help="Có thể chọn 2–4 hoạt động để gợi ý có cấu trúc hơn. Đây là định hướng heuristic, không phải bài trắc nghiệm tâm lý chuẩn hóa.",
            )
            experience_text = st.text_area("Kinh nghiệm (không bắt buộc)", placeholder="Mô tả ngắn về kinh nghiệm của bạn", key="experience_input")
            pasted_cv_text = st.text_area(
                "Dán nội dung CV (nếu không tải tệp, không bắt buộc)",
                placeholder="HỒ SƠ DEMO — KHÔNG PHẢI NGƯỜI THẬT\nMục tiêu: \nKỹ năng: \nKinh nghiệm giả lập: Thực tập phân tích dữ liệu tại doanh nghiệp bán lẻ giả lập (2025). Dùng SQL tổng hợp đơn hàng\nDự án giả lập: Phân tích doanh số theo sản phẩm và khu vực",
                height=160,
                key="pasted_cv_input",
            )
            uploaded_cv = st.file_uploader(
                "Tải CV định dạng PDF hoặc DOCX (*)", type=["pdf", "docx"],
                help="PDF cần có lớp văn bản; tối đa 10 trang được đọc. Phần vượt trang giới hạn không được phân tích.", key="uploaded_cv_input",
            )
            st.caption("🔒 Quyền riêng tư: CV được xử lý trong phiên Streamlit local để trích xuất kỹ năng; ứng dụng không ghi CV thành tệp dự án và không gửi tới API bên ngoài. Kết quả không được lưu để khôi phục sau khi tải lại trang.")

            with st.container(border=True, key="demo_profiles_panel"):
                st.subheader("Dùng hồ sơ mẫu tổng hợp")
                cols = st.columns(3)
                for col, demo in zip(cols, load_demo_profiles()):
                    skills_preview = ", ".join(demo["profile"]["skills"][:3])
                    col.markdown(
                        f'<div style="padding:12px 16px;border:1.5px solid var(--color-line);border-radius:12px;background:var(--color-paper-sunken);margin-bottom:8px;">'
                        f'<div style="font-weight:700;font-size:15px;color:var(--color-ink);">'
                        f'<span>{demo["label"]}</span>'
                        f'</div>'
                        f'<div style="font-size:13px;color:var(--color-ink-soft);margin-top:6px;line-height:1.4;">'
                        f'Kỹ năng: {skills_preview}...'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    col.button(
                        f"Dùng hồ sơ mẫu · {demo['label']}",
                        key=f"use_demo_{demo['id']}",
                        on_click=lambda demo_id=demo["id"]: st.session_state.update({"pending_demo_profile_id": demo_id}),
                    )

            with st.container(border=True, key="role_picker_panel"):
                st.markdown("#### Vị trí công việc bạn quan tâm")
                c_trig_info, c_trig_btn = st.columns([3, 1], vertical_alignment="center")
                with c_trig_info:
                    role_label = escape(format_role(current_role_obj)) if current_role_obj else "Chưa chọn vị trí công việc"
                    selected_class = " is-selected" if current_role_obj else ""
                    st.markdown(
                        f'<div class="role-picker-status{selected_class}"><strong>{role_label}</strong></div>',
                        unsafe_allow_html=True,
                    )
                with c_trig_btn:
                    btn_txt = "Đổi vị trí ▾" if current_role_obj else "Chọn vị trí ▾"
                    if st.button(btn_txt, key="btn_open_role_modal", use_container_width=True):
                        open_role_taxonomy_dialog(positions, role_by_id, taxonomy)

            job_description = st.text_area(
                "Mô tả công việc cần đối chiếu (không bắt buộc)",
                placeholder="Tên Ngành: \nYêu cầu bắt buộc:\nKĩ năng:\nƯu tiên:",
                height=140,
                key="job_description_input",
            )
            submitted = st.button("Tiếp tục rà soát hồ sơ", type="primary", key="profile_continue")
        if submitted:
            if len(selected_activity_ids) > 4:
                st.session_state["wizard_errors"] = ["Hãy chọn tối đa 4 hoạt động nghề nghiệp yêu thích."]
                candidate = {"accepted": False, "errors": st.session_state["wizard_errors"]}
            else:
                candidate = prepare_submission(
                    {
                        "skills": skills_text,
                        "interests": interests_text,
                        "interest_activity_ids": selected_activity_ids,
                        "experience": experience_text,
                    },
                    uploaded_cv,
                    pasted_cv_text=pasted_cv_text,
                )
            st.session_state["wizard_errors"] = candidate.get("errors", [])
            jd_requirements = {"all_skills": [], "must_have": [], "nice_to_have": [], "unclassified": []}
            jd_error = None
            if job_description.strip():
                try:
                    jd_requirements = extract_jd_skill_requirements(job_description)
                except ValueError as exc:
                    jd_error = str(exc)
            if candidate["accepted"]:
                st.session_state["profile_draft"] = {
                    "id": uuid4().hex[:10], "profile": candidate["profile"],
                    "cv_extraction": candidate["cv_extraction"], "document": candidate["document"],
                    "jd_text": job_description,
                    "jd_skill_options": jd_requirements["all_skills"],
                    "jd_skill_requirements": jd_requirements,
                    "jd_error": jd_error,
                    "role_id": selected_role_id, "demo_id": None,
                    "warnings": list(candidate["errors"]),
                }
                st.session_state["profile_step"] = 2
                st.rerun()
            else:
                st.session_state["submission_rejected"] = bool(st.session_state.get("profile_result"))
        for error in st.session_state.get("wizard_errors", []):
            st.error(error)
    else:
        draft = st.session_state.get("profile_draft")
        if not draft:
            st.session_state["profile_step"] = 1
            st.rerun()
        st.markdown("### Bước 2/2 · Rà soát kỹ năng và Level")
        st.caption("Kỹ năng nhận diện từ CV và kinh nghiệm chỉ được dùng sau khi bạn xác nhận. Level không được suy ra tự động từ CV hay kinh nghiệm.")
        for error in st.session_state.get("wizard_errors", []):
            st.warning(error)
        document = draft.get("document", {})
        if document.get("page_truncated"):
            st.warning(f"PDF có {document['total_pages']} trang; ứng dụng chỉ trích xuất {document['pages_read']} trang đầu. Phần còn lại chưa được phân tích.")
        if draft.get("jd_error"):
            st.warning(draft["jd_error"] + " Có thể tiếp tục hồ sơ mà không đối chiếu JD.")

        original_profile = draft["profile"]
        initial_skills = original_profile.get("skills", [])
        options = sorted(load_skill_vocabulary() | set(initial_skills))
        initial_levels = original_profile.get("levels", {})
        level_labels = {
            None: "Chưa khai báo",
            0: "0 · Chưa biết kỹ năng",
            1: "1 · Cơ bản, cần hướng dẫn",
            2: "2 · Tự làm tác vụ quen thuộc",
            3: "3 · Xử lý việc phức tạp / hướng dẫn người khác",
        }
        unknown_count = len(original_profile.get("unrecognized_skills", []))
        catalog_count = max(0, len(initial_skills) - unknown_count)
        st.info(
            f"📊 Hồ sơ có **{len(initial_skills)}** kỹ năng · **{catalog_count}** khớp catalog · "
            f"**{unknown_count}** tên cần bạn rà soát."
        )
        aliases = load_aliases(DATA_DIR / "skill_aliases.json")
        # This input must rerun independently so newly added skills receive
        # their own level and spelling controls before the review form submits.
        new_skills_text = st.text_area(
            "Thêm hoặc sửa tên kỹ năng khác (không bắt buộc)",
            placeholder="Ví dụ: công cụ nội bộ, kỹ năng chuyên ngành",
            key=f"review_new_skills_{draft['id']}",
        )
        custom_by_key = {}
        for part in re.split(r"[,;\n]+", new_skills_text):
            if part.strip():
                normalized = normalize_skill(part)
                custom_by_key.setdefault(aliases.get(normalized, normalized), part.strip())
        custom_skills = list(custom_by_key.values())
        st.caption("Nhập kỹ năng mới rồi rời ô nhập để chọn Level trước khi xác nhận.")
        with st.form(f"profile_review_{draft['id']}"):
            selected_skills = st.multiselect(
                "Kỹ năng nhận diện · bỏ chọn mục không đúng với bạn",
                options=options, default=initial_skills, format_func=display_skill,
                key=f"review_skills_{draft['id']}",
            )
            vocabulary = load_skill_vocabulary()
            suggestion_targets = {}
            candidate_by_key = {}
            for skill in [*original_profile.get("unrecognized_skills", []), *custom_skills]:
                candidate_by_key.setdefault(normalize_skill(skill), skill)
            review_candidates = list(candidate_by_key.values())
            for unknown in review_candidates:
                candidates = suggest_skill_candidates(unknown, vocabulary, aliases)
                if candidates:
                    value = st.selectbox(
                        f"Tên gần giống với ‘{unknown}’ (tùy chọn)",
                        options=[None, *candidates],
                        format_func=lambda item: "Giữ nguyên tên" if item is None else display_skill(item),
                        key=f"skill_suggestion_{draft['id']}_{hashlib.sha256(unknown.casefold().encode('utf-8')).hexdigest()[:12]}",
                    )
                    if value is not None:
                        suggestion_targets[normalize_skill(unknown)] = value
            level_values = {}
            level_skills_by_key = {}
            for skill in [*selected_skills, *custom_skills]:
                normalized = normalize_skill(skill)
                level_skills_by_key.setdefault(aliases.get(normalized, normalized), skill)
            for skill in level_skills_by_key.values():
                existing = initial_levels.get(skill)
                skill_key = hashlib.sha256(skill.casefold().encode("utf-8")).hexdigest()[:12]
                level_values[skill] = st.selectbox(
                    f"Level · {display_skill(skill)}", [None, 0, 1, 2, 3],
                    index=[None, 0, 1, 2, 3].index(existing) if existing in (0, 1, 2, 3) else 0,
                    format_func=lambda value: level_labels[value],
                    key=f"review_level_{draft['id']}_{skill_key}",
                )
            confirmed_jd_categories = {"must_have": [], "nice_to_have": [], "unclassified": []}
            if draft.get("jd_text") and draft.get("jd_skill_options"):
                st.markdown("#### Phân loại kỹ năng nhận diện từ JD")
                st.caption(
                    f"Nhận diện {len(draft['jd_skill_options'])} kỹ năng theo catalog. "
                    "Bạn có thể chuyển kỹ năng giữa các nhóm; kỹ năng chưa phân loại không ảnh hưởng điểm tổng hợp."
                )
                if len(draft["jd_skill_options"]) < 3:
                    st.warning("JD có ít hơn 3 kỹ năng nhận diện; hãy xem kết quả như phạm vi đầu vào hẹp.")
                parsed_groups = draft.get("jd_skill_requirements", {})
                group_labels = {
                    "must_have": "Kỹ năng JD bắt buộc",
                    "nice_to_have": "Kỹ năng JD ưu tiên / điểm cộng",
                    "unclassified": "Kỹ năng JD chưa phân loại · không tính điểm tổng hợp",
                }
                for kind, label in group_labels.items():
                    confirmed_jd_categories[kind] = st.multiselect(
                        label,
                        options=draft["jd_skill_options"],
                        default=parsed_groups.get(kind, []),
                        format_func=display_skill,
                        key=f"review_jd_{kind}_{draft['id']}",
                    )
            confirm = st.form_submit_button("Xác nhận hồ sơ và xem kết quả")

        back_col, _ = st.columns([1, 4])
        if back_col.button("Quay lại chỉnh đầu vào", key=f"back_profile_{draft['id']}"):
            st.session_state["profile_step"] = 1
            st.rerun()

        if confirm:
            try:
                confirmed_skills = [suggestion_targets.get(normalize_skill(skill), skill) for skill in selected_skills]
                confirmed_skills.extend(suggestion_targets.get(normalize_skill(skill), skill) for skill in custom_skills)
                confirmed_levels = {
                    suggestion_targets.get(normalize_skill(key), key): value for key, value in level_values.items()
                    if value is not None
                }
                profile = build_profile({
                    "skills": confirmed_skills,
                    "interests": original_profile.get("interests", []),
                    "interest_activity_ids": original_profile.get("interest_activity_ids", []),
                    "experience": original_profile.get("experience", ""),
                    "levels": confirmed_levels,
                })
                if not profile["skills"]:
                    raise ValueError(PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE)
                profile["moved"] = list(original_profile.get("moved", []))
                confirmed_set = set(profile["skills"])
                profile["skills_from_cv"] = [
                    skill for skill in original_profile.get("skills_from_cv", []) if skill in confirmed_set
                ]
                profile["skills_from_experience"] = [
                    skill for skill in original_profile.get("skills_from_experience", []) if skill in confirmed_set
                ]
                jd_result = None
                if any(confirmed_jd_categories.values()):
                    candidate_skills = [skill for skill in profile["skills"] if skill not in profile["unrecognized_skills"]]
                    jd_result = compare_confirmed_jd_requirements(
                        candidate_skills,
                        confirmed_jd_categories["must_have"],
                        confirmed_jd_categories["nice_to_have"],
                        confirmed_jd_categories["unclassified"],
                    )
            except (TypeError, ValueError) as exc:
                if str(exc) == PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE:
                    st.error(f"❌ {exc}")
                    st.info(
                        "💡 Cách xử lý: Hãy tích chọn lại ít nhất 1 kỹ năng ở danh sách phía trên, "
                        "hoặc thêm kỹ năng mới vào ô bên dưới rồi bấm xác nhận lại."
                    )
                else:
                    st.error(f"Không thể xác nhận hồ sơ: {exc}")
            else:
                submission_warnings = list(draft.get("warnings", []))
                if draft.get("jd_error"):
                    submission_warnings.append(
                        draft["jd_error"] + " Có thể tiếp tục hồ sơ mà không đối chiếu JD."
                    )
                elif draft.get("jd_text") and draft.get("jd_skill_options") and not any(confirmed_jd_categories.values()):
                    submission_warnings.append(
                        "Chưa xác nhận kỹ năng nào từ JD; hồ sơ vẫn được lưu nhưng chưa có kết quả đối chiếu."
                    )
                if draft.get("document", {}).get("page_truncated"):
                    document = draft["document"]
                    submission_warnings.append(
                        f"PDF có {document['total_pages']} trang; ứng dụng chỉ trích xuất "
                        f"{document['pages_read']} trang đầu. Phần còn lại chưa được phân tích."
                    )
                for key in list(st.session_state):
                    if isinstance(key, str) and key.startswith(("keep_unknown_", "undo_move_", "answer_", "interview_", "start_interview_", "self_review_")):
                        del st.session_state[key]
                st.session_state.update({
                    "career_role_id": draft.get("role_id"),
                    "profile_result": profile,
                    "profile_original_interests": list(original_profile.get("interests", [])),
                    "profile_revision": st.session_state.get("profile_revision", 0) + 1,
                    "cv_jd_result": jd_result,
                    "cv_extraction": draft.get("cv_extraction"),
                    "jd_provided": bool(draft.get("jd_text")),
                    "submission_errors": [],
                    "submission_rejected": False,
                    "submission_warnings": submission_warnings,
                    "submission_notice": (
                        f"Đã nạp hồ sơ tổng hợp “{draft['demo_label']}”. {draft['demo_notice']}"
                        if draft.get("demo_id") else "Hồ sơ đã được xác nhận. Kết quả phản ánh kỹ năng và Level bạn đã chọn."
                    ),
                    "active_demo_profile_id": draft.get("demo_id"),
                    "profile_step": 1,
                })
                st.session_state.pop("profile_draft", None)
                st.session_state.pop("wizard_errors", None)
                st.rerun()

    if st.session_state.get("profile_step", 1) == 2:
        return
    profile = st.session_state.get("profile_result")
    if not profile:
        return
    if st.button("Xóa hồ sơ phiên này và bắt đầu lại", key="clear_local_profile"):
        for key in list(st.session_state):
            del st.session_state[key]
        st.rerun()
    if st.session_state.get("submission_rejected"):
        st.warning("Lần gửi mới chưa hợp lệ. Đang giữ hồ sơ đã lưu trước đó.")
    for warning in st.session_state.get("submission_warnings", []):
        st.warning(warning)
    if st.session_state.get("submission_notice"):
        st.success(st.session_state["submission_notice"])

    revision = st.session_state.get("profile_revision", 0)
    domain_notice = role_domain_notice(st.session_state.get("career_role_id", ""))
    if domain_notice:
        st.warning(domain_notice)
    if "pending_result_tab" in st.session_state:
        st.session_state["active_result_tab"] = st.session_state.pop("pending_result_tab")
    tabs = st.tabs(RESULT_TABS, key="active_result_tab", on_change="rerun")
    cv_jd = st.session_state.get("cv_jd_result")
    cv_extraction = st.session_state.get("cv_extraction")
    effective_skills = [
        skill for skill in profile["skills"]
        if skill not in profile["unrecognized_skills"]
        or st.session_state.get(f"keep_unknown_{revision}_{skill}", True)
    ]

    with tabs[0]:
        saved_role = next((item for item in load_positions() if item["id"] == st.session_state.get("career_role_id")), None)
        if st.session_state.get("active_demo_profile_id"):
            st.info("Hồ sơ tổng hợp minh họa · không phải hồ sơ của người thật.")
        if cv_extraction and not cv_jd:
            if st.session_state.get("jd_provided"):
                st.info("Đã gộp kỹ năng nhận diện từ CV vào hồ sơ; lần gửi này chưa tạo được kết quả đối chiếu JD.")
            else:
                st.info("Đã gộp kỹ năng nhận diện từ CV vào hồ sơ. Thêm JD để đối chiếu.")

        has_target = False
        target_name = ""
        score = None
        if cv_jd:
            has_target = True
            target_name = saved_role["name"] if saved_role else "theo mô tả công việc (JD)"
            if cv_jd["overall_percent"] is not None:
                score = float(cv_jd["overall_percent"])
            elif cv_jd["must_have"]["percent"] is not None:
                score = float(cv_jd["must_have"]["percent"])
            elif cv_jd["unclassified"]["percent"] is not None:
                score = float(cv_jd["unclassified"]["percent"])
            else:
                score = 0.0
        elif saved_role:
            has_target = True
            target_name = saved_role["name"]
            presence = match_role(effective_skills, saved_role)
            score = float(presence["percent"])

        summary_text = get_summary_sentences(cv_jd, saved_role, effective_skills)

        # 1. Hero Card
        render_summary_hero(target_name, score, summary_text, has_target)

        # 2. Hai cột "Bạn đã có" và "Cần bổ sung"
        matched_skills = []
        missing_skills = []
        if cv_jd:
            for kind in ("must_have", "nice_to_have", "unclassified"):
                matched_skills.extend(cv_jd[kind]["matched"])
                missing_skills.extend(cv_jd[kind]["missing"])
        elif saved_role:
            presence = match_role(effective_skills, saved_role)
            matched_skills = presence["matched"]
            missing_skills = presence["missing"]
        else:
            matched_skills = effective_skills
            missing_skills = []

        dedup_matched = deduplicate_skills(matched_skills)
        matched_keys = {normalize_skill(s) for s in dedup_matched}
        dedup_missing = deduplicate_skills(missing_skills, exclude=matched_keys)
        render_skill_chips(dedup_matched, dedup_missing, has_target)

        # 3. Vị trí gợi ý cho bạn
        suggestions = suggest_roles({**profile, "skills": effective_skills})
        render_suggested_roles(suggestions, revision)

        # 4. Các expander thu gọn
        render_profile_extracted_details(profile, effective_skills, cv_extraction, revision)
        render_technical_details(cv_jd, profile, effective_skills)

    position = role_by_id.get(st.session_state.get("career_role_id"))
    has_signal = bool(effective_skills or profile.get("levels"))
    if position is None or not has_signal:
        gap_message = "Hãy chọn vị trí để xem khoảng cách." if position is None else "Chưa có kỹ năng để đối chiếu. Hãy bổ sung kỹ năng vào form hoặc CV."
        for tab in tabs[1:]:
            with tab:
                st.info(gap_message)
        if position:
            with tabs[3]:
                exported_profile = {**profile, "role_id": position["id"]}
                st.download_button("Tải báo cáo Markdown", export_report(exported_profile, None, []), "bao-cao-ho-so.md", "text/markdown")
                st.download_button("Tải báo cáo CSV", export_report(exported_profile, None, [], "csv"), "bao-cao-ho-so.csv", "text/csv")
                st.download_button("Tải báo cáo JSON", export_report(exported_profile, None, [], "json"), "bao-cao-ho-so.json", "application/json")
        return

    role = position
    target_levels = {normalize_skill(item["name"]): item["level"] for item in role["skills"]}
    mode_key = f"assessment_mode_{revision}"
    selected_mode = st.session_state.get(mode_key, "Theo kỹ năng đã có")
    if selected_mode == "Theo level tự khai báo":
        selected_mode = "Theo mức độ thành thạo tự khai báo"
        st.session_state[mode_key] = selected_mode
    if st.session_state.get("assessment_snapshot") != (revision, selected_mode, role["id"]):
        st.session_state.pop("interview_session", None)
        st.session_state["assessment_snapshot"] = (revision, selected_mode, role["id"])
    presence = match_role(effective_skills, role)
    gap_result = None
    timed_result = None
    weekly_roadmap = None

    with tabs[1]:
        st.subheader(f"Đánh giá cho {format_role(role)}")
        mode = st.radio("Loại đánh giá", ["Theo kỹ năng đã có", "Theo mức độ thành thạo tự khai báo"], key=mode_key)
        if mode != selected_mode:
            st.session_state.pop("interview_session", None)
            st.session_state["assessment_snapshot"] = (revision, mode, role["id"])
        if mode in ("Theo mức độ thành thạo tự khai báo", "Theo level tự khai báo"):
            st.info("Các kỹ năng chưa có mức độ sẽ để mặc định ở 0")
            confirmed = st.checkbox("Tôi đồng ý tính các kỹ năng chưa có mức độ là 0 cho lần đánh giá này", key=f"confirm_levels_{revision}")
            if confirmed:
                levels = {k: v for k, v in profile.get("levels", {}).items()
                          if k not in profile["unrecognized_skills"] or k in effective_skills}
                gap_result = compute_gap(levels, role)
                st.metric("Mức độ đáp ứng theo mức độ thành thạo", f"{gap_result['match_percent']}%")
                st.markdown(
                    '<div class="sub-heading-cap1" style="font-size:1.15rem;font-weight:750;margin-top:16px;margin-bottom:8px;color:var(--color-ink);">'
                    'Mức độ thành thạo kỹ năng của bạn so với yêu cầu mức độ thành thạo ở từng kỹ năng'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.progress(gap_result["match_percent"] / 100)
                status_vi = {
                    "met": "Đã đạt",
                    "missing": "Chưa có",
                    "below_required": "Chưa đạt yêu cầu",
                }
                display_items = [
                    {
                        "Kỹ năng": display_skill(item["skill"]),
                        "Mức yêu cầu": item["required"],
                        "Mức hiện tại": item["current"],
                        "Chênh lệch": item["gap"],
                        "Độ ưu tiên": item["priority"],
                        "Trạng thái": status_vi.get(item["status"], item["status"]),
                    }
                    for item in gap_result["items"]
                ]
                st.dataframe(display_items, hide_index=True, use_container_width=True)
        else:
            st.metric("Mức độ đáp ứng kỹ năng vị trí", f"{presence['percent']}%")
            st.progress(presence["percent"] / 100, text="Mức khớp kỹ năng")
            matched_col, missing_col = st.columns(2)
            matched_col.markdown("**Đã có**")
            matched_col.write(", ".join(display_skill(s) for s in presence["matched"]) or "Chưa có")
            missing_col.markdown("**Nên học tiếp**")
            missing_col.write(", ".join(display_skill(s) for s in presence["missing"]) or "Không còn kỹ năng thiếu")

    with tabs[2]:
        if selected_mode in ("Theo mức độ thành thạo tự khai báo", "Theo level tự khai báo"):
            if gap_result is not None:
                budget = st.number_input("Ngân sách giờ học mỗi tuần", min_value=0.5, max_value=40.0, value=8.0, step=0.5, key=f"study_budget_{revision}")
                timed_result = build_timed_roadmap(gap_result, load_resources(), hours_per_week=budget)
                render_timed_roadmap(timed_result, role_context=format_role(role), target_levels=target_levels)
            else:
                st.info("Xác nhận quy ước mức độ thành thạo chưa khai báo ở tab Khoảng cách để xem lộ trình.")
        elif presence["missing"]:
            weekly_roadmap = build_roadmap(presence["missing"], load_resources(), missing_details=presence["missing_details"])
            render_roadmap(weekly_roadmap, role_context=format_role(role), target_levels=target_levels)
        else:
            st.success("Hồ sơ của bạn đã có đủ các kỹ năng được liệt kê cho vị trí này.")

    with tabs[3]:
        st.subheader("Tài liệu nên học")
        _render_resource_quality_disclosure(load_resources())
        if timed_result is not None:
            for key, item in timed_result["resources"].items():
                _render_curated_resource_card(item, target_levels, role, warn_gap=False)
            if timed_result["unknown_duration"] or timed_result["unresolved"]:
                st.caption("Một số thời lượng hoặc kỹ năng còn thiếu dữ liệu; xem chi tiết trong Lộ trình.")
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
                        first_phase = next(w["week"] for w in weekly_roadmap if any(r["key"] == key for r in w["resources"]))
                        _render_curated_resource_card(item, target_levels, role, warn_gap=True, phase_label=first_phase)
            if any(w["skills_without_resources"] for w in weekly_roadmap):
                st.warning("Một số kỹ năng chưa có tài liệu đủ điều kiện đề xuất; xem lý do trong tab Lộ trình.")
        else:
            st.info("Chưa có tài liệu để xuất.")
        exported_profile = {**profile, "role_id": role["id"]}
        st.download_button("Tải báo cáo Markdown", export_report(exported_profile, gap_result or presence, timed_result or weekly_roadmap or []),
                           "bao-cao-ho-so.md", "text/markdown")
        st.download_button("Tải báo cáo CSV", export_report(exported_profile, gap_result or presence, timed_result or weekly_roadmap or [], "csv"),
                           "bao-cao-ho-so.csv", "text/csv")
        st.download_button("Tải báo cáo JSON", export_report(exported_profile, gap_result or presence, timed_result or weekly_roadmap or [], "json"),
                           "bao-cao-ho-so.json", "application/json")

    with tabs[4]:
        st.caption("Phỏng vấn ưu tiên kỹ năng còn thiếu; hệ thống chỉ hiển thị hướng dẫn sau khi bạn gửi câu trả lời.")
        focus = gap_result["missing"] if gap_result is not None else presence["missing"]
        render_interview_practice(role, focus_skills=focus, assessment="levels" if gap_result is not None else "presence")


def render_timed_roadmap(roadmap: dict, *, role_context: str | None = None, target_levels: dict[str, int] | None = None) -> None:
    st.subheader("Lộ trình học")
    st.markdown(
        '<div class="roadmap-guide-box">'
        '<span style="font-size:1.2rem;line-height:1;">💡</span>'
        '<div>'
        'Thang mức độ thành thạo kỹ năng từ <strong>0 (Chưa biết)</strong>, <strong>1 (Cơ bản)</strong>, <strong>2 (Độc lập)</strong> đến <strong>3 (Nâng cao)</strong>. '
        'Mũi tên <strong>→</strong> cho biết mức độ hiện tại của bạn và mục tiêu cần đạt sau mỗi bước học.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if roadmap["total_known_hours"] or roadmap["total_estimated_hours"]:
        st.caption(f"Ưu tiên theo khoảng cách kỹ năng · ngân sách {roadmap['hours_per_week']:g} giờ/tuần")
        metric_columns = st.columns(3)
        metric_columns[0].metric("Giờ theo nguồn", f"{roadmap['total_known_hours']:.1f}")
        metric_columns[1].metric("Giờ ước tính", f"{roadmap['total_estimated_hours']:.1f}")
        metric_columns[2].metric("Thời gian", "Chưa rõ" if roadmap["total_weeks"] is None else f"{roadmap['total_weeks']} tuần")
        _render_roadmap_diagram([
            {
                "week": phase["week"],
                "label": f"{phase['hours']:.2f} giờ · {len(phase['segments'])} phần",
                "warning": any(roadmap["resources"][segment["resource_key"]]["duration_kind"] == "estimated" for segment in phase["segments"]),
            }
            for phase in roadmap["phases"]
        ], alt="Sơ đồ các tuần học theo thời lượng được nguồn công bố hoặc có căn cứ ước tính.")
    else:
        st.caption("Các giáo trình không công bố thời lượng. Học theo thứ tự dưới đây, tự điều chỉnh nhịp và xin phản hồi sau mỗi bài tập.")
    if roadmap["is_estimated"]:
        st.caption("Một phần thời lượng là ước tính.")

    learning_steps = roadmap.get("learning_steps", [])
    for idx, step in enumerate(learning_steps):
        skill = step["skill"]
        formatted_skill = format_skill_name(display_skill(skill))
        cur_lvl = step.get("current_level", 0)
        tgt_lvl = step.get("target_level", 3)
        step_num = step.get("step", idx + 1)
        expander_title = f"Bước {step_num} · {formatted_skill} · Mức độ: {cur_lvl} → {tgt_lvl}"
        with st.expander(expander_title, expanded=(step_num == 1)):
            st.markdown(
                f'<div class="roadmap-badge-container">'
                f'<span class="roadmap-level-badge">🎯 Mức độ thành thạo kỹ năng: <strong>{cur_lvl} → {tgt_lvl}</strong></span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            resource = step.get("resource")
            if resource:
                title = resource.get("title", "Giáo trình học thuật")
                url = resource.get("url", "")
                provider = resource.get("provider", "Nguồn học thuật")
                acad_label = resource.get("academic_label", "Giáo trình nền tảng")
                provider_line = f"{acad_label} · {provider} · tài liệu tiếng Anh"
                scope_line = resource.get("learning_scope", "")

                link_html = f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" class="roadmap-resource-link">{escape(title)}</a>' if url else f'<span class="roadmap-resource-title">{escape(title)}</span>'
                st.markdown(f'<div class="roadmap-resource-header">{link_html}</div>', unsafe_allow_html=True)

                bullets = [f'<li>{escape(provider_line)}</li>']
                if scope_line:
                    bullets.append(f'<li>{escape(scope_line)}</li>')
                if resource.get("access_note"):
                    bullets.append(f'<li>{escape(resource["access_note"])}</li>')
                st.markdown(f'<ul class="roadmap-resource-bullets">{"".join(bullets)}</ul>', unsafe_allow_html=True)

                companion = resource.get("verified_companion_url") or resource.get("practice_url")
                if companion:
                    label = resource.get("verified_companion_title") or resource.get("practice_title") or "Nguồn thực hành bổ sung"
                    st.markdown(
                        f'<div class="roadmap-companion-box">'
                        f'<span class="roadmap-companion-label">Thực hành thêm:</span> '
                        f'<a href="{escape(companion, quote=True)}" target="_blank" rel="noopener noreferrer" class="roadmap-companion-link">{escape(label)}</a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            plan = step.get("plan") or {}
            steps_list = plan.get("steps", [])
            if steps_list:
                st.markdown('<div class="roadmap-practice-title">Các bước thực hành:</div>', unsafe_allow_html=True)
                steps_html = "".join(f'<li>{escape(instruction)}</li>' for instruction in steps_list)
                st.markdown(f'<ol class="roadmap-practice-list">{steps_html}</ol>', unsafe_allow_html=True)

            if plan.get("evidence"):
                st.markdown(
                    f'<div class="roadmap-evidence-box">'
                    f'<span style="font-size:1.1rem;line-height:1;">🏁</span>'
                    f'<div><strong>Đầu ra cần đạt:</strong> {escape(plan["evidence"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    for phase in roadmap["phases"]:
        with st.expander(f"Tuần học {phase['week']} · {phase['hours']:.2f} giờ"):
            for segment in phase["segments"]:
                item = roadmap["resources"][segment["resource_key"]]
                st.markdown(f"[{item['title']}]({item['url']}) · phần {segment['part']} · {segment['hours']:.2f} giờ")
                st.caption(f"Học {', '.join(format_skill_name(display_skill(skill)) for skill in item['skills'])} · {segment['hours']:.1f} giờ")
                with st.expander("Chi tiết tài liệu"):
                    _render_resource_level_scope(item, target_levels, warn_gap=False)
                    st.caption("Trạng thái nội dung: " + resource_review_label(item.get("content_review_status", "unreviewed")))
                    evidence = item.get("duration_evidence", {})
                    if segment["duration_kind"] == "estimated":
                        st.caption(f"Cơ sở thời lượng: {evidence.get('basis') or item.get('estimated_duration_basis') or item.get('duration_basis') or 'chưa có thông tin'}")
                    elif evidence.get("source"):
                        st.caption(f"Nguồn thời lượng: {evidence['source']}")
                    for note in (item.get("review_note"), item.get("access_note")):
                        if note:
                            st.caption(note)
                    if item.get("duration_issue") == "conflicting_duration":
                        st.caption("Thời lượng nguồn có khác biệt; chưa cộng vào lịch.")
                    _render_partial_practice_assignments(
                        item.get("skills", []), item, role_context=role_context, resources=load_resources()
                    )
    for item in roadmap["unresolved"]:
        skill = item.get("skill") or ", ".join(item.get("skills", []))
        with st.expander(f"Chưa có tài liệu phù hợp cho {format_skill_name(display_skill(skill))}"):
            st.caption(RESOURCE_REASON_LABELS.get(item["reason"], "Chưa tìm được tài liệu phù hợp."))
            caution = skill_scope_caution(skill)
            if caution:
                st.caption(caution)
            if item.get("resource_statuses"):
                st.caption("Tình trạng nguồn: " + ", ".join(item["resource_statuses"]))
    if roadmap["unknown_duration"] and not roadmap.get("learning_steps"):
        st.caption("Một số tài liệu không công bố thời lượng; tự học theo tiến độ cá nhân.")


def _render_resource_level_scope(resource: dict, target_levels: dict[str, int] | None, *, warn_gap: bool = True) -> None:
    """Distinguish the page's teaching range from the role's target level."""
    if resource.get("learning_role") == "academic_foundation":
        st.caption(resource.get("academic_label", "Học liệu nền tảng") + ". Đọc xong chưa đồng nghĩa đã đạt mức độ thành thạo kỹ năng; hãy hoàn thành bài thực hành và xin phản hồi.")
        return
    st.caption("Mức bằng chứng: " + resource_evidence_badge(resource))
    lower, upper = resource.get("level_from"), resource.get("level_to")
    if type(lower) is not int or type(upper) is not int or not 1 <= lower <= upper <= 3:
        return
    label = f"Level {lower}" if lower == upper else f"Level {lower}–{upper}"
    st.caption(f"Mức độ thành thạo (Level do dự án gán cho mapping: {label}); đọc tài liệu không chứng nhận đã đạt mức độ này.")
    scope = resource.get("scope_granularity")
    locator = resource.get("evidence_locator")
    if not has_granular_level_evidence(resource):
        st.warning(
            "Chưa xác định đủ bài học/mục cụ thể và dẫn chứng để xác nhận mapping đúng Level. "
            "Hãy dùng liên kết này như tài liệu tham khảo; không tính là đã phủ yêu cầu nghề."
        )
    else:
        st.caption(f"Đơn vị nội dung: {scope} · Vị trí đối chiếu nội bộ: {locator}")
        st.caption("Phạm vi và mức độ thành thạo (Level) của đơn vị này vẫn cần chủ dự án/chuyên gia xác nhận độc lập.")
    axes = resource.get("verification_axes")
    if isinstance(axes, dict) and axes.get("access_status") == "user_attested_manual":
        st.caption("Khả năng mở link: chủ dự án báo đã kiểm tra thủ công; chưa phải xác minh độc lập.")
    provenance = resource.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("rights_basis"):
        st.caption("Cơ sở quyền tái sử dụng dữ liệu chưa được ghi nhận; chỉ dẫn sang nguồn ngoài.")
    gaps = resource_level_gap(resource, target_levels or {})
    if warn_gap and gaps:
        details = ", ".join(f"{display_skill(item['skill'])} cần Level {item['required_level']}" for item in gaps)
        st.info(f"Tài liệu này mới hỗ trợ tới Level {upper}; {details}. Cần nguồn hoặc bài thực hành bổ sung cho phần còn lại.")


def render_roadmap(roadmap: list[dict], *, role_context: str | None = None, target_levels: dict[str, int] | None = None) -> None:
    """Resolve shared documents across the whole roadmap, including prior weeks."""
    catalog = {
        resource["key"]: (resource, week["week"])
        for week in roadmap for resource in week["resources"]
    }
    st.subheader("Lộ trình học")
    st.caption("Học theo thứ tự ưu tiên. Mở từng giai đoạn để xem tài liệu và bài thực hành.")
    _render_roadmap_diagram([
        {
            "week": week["week"],
            "label": ", ".join(display_skill(skill) for skill in week["skills"][:2])
                     + (f" và {len(week['skills']) - 2} kỹ năng khác" if len(week["skills"]) > 2 else "")
                     + f"\n{len({key for keys in week['resource_keys'].values() for key in keys})} tài liệu · {len(week.get('practice_routes', []))} bài thực hành",
            "warning": bool(week.get("unresolved")) or bool(week.get("partial_resources")),
        }
        for week in roadmap
    ], alt="Sơ đồ các giai đoạn ưu tiên, kỹ năng, tài liệu và bài thực hành.", step_label="Giai đoạn")
    for week in roadmap:
        with st.expander(f"Giai đoạn {week['week']} · {', '.join(display_skill(s) for s in week['skills'])}"):
            _render_practice_routes(week.get("practice_routes", []))
            for resource in week["resources"]:
                title = resource.get("title", "Tài liệu học tập")
                url = resource.get("url")
                st.markdown(f"[{title}]({url})" if url else title)
                if resource.get("academic_source"):
                    st.caption(resource.get("academic_label", "Giáo trình nền tảng") + " · " + resource.get("provider", "") + " · tiếng Anh")
                    st.caption(resource.get("learning_scope", ""))
                    companion = resource.get("verified_companion_url") or resource.get("practice_url")
                    if companion:
                        label = resource.get("verified_companion_title") or resource.get("practice_title") or "Nguồn thực hành bổ sung"
                        st.markdown(f"[Thực hành thêm: {label}]({companion})")
                    if resource.get("access_note"):
                        st.caption(resource["access_note"])
                    continue
                details = [resource.get(key) for key in ("provider", "type", "language", "cost")]
                st.caption(" · ".join(str(item) for item in details if item))
                st.caption("Kỹ năng: " + ", ".join(display_skill(skill) for skill in resource.get("skills", [])))
                with st.expander("Chi tiết tài liệu"):
                    _render_resource_level_scope(resource, target_levels)
                    status = resource.get("content_review_status", "unreviewed")
                    st.caption("Trạng thái nội dung: " + resource_review_label(status))
                    if status == "partial" and resource.get("review_note"):
                        st.caption("Phạm vi: " + resource["review_note"])
                        _render_partial_practice_assignments(
                            resource.get("skills", []), resource,
                            role_context=role_context, resources=load_resources(),
                        )
                    for skill in resource.get("skills", []):
                        caution = skill_scope_caution(skill)
                        if caution:
                            st.caption(caution)
            for skill, keys in week["resource_keys"].items():
                for key in keys:
                    resource, introduced_week = catalog[key]
                    if introduced_week < week["week"]:
                        title = resource.get("title", "Tài liệu học tập")
                        url = resource.get("url")
                        link = f"[{title}]({url})" if url else title
                        st.markdown(f"{display_skill(skill)}: {link} (đã giới thiệu ở giai đoạn {introduced_week})")
            if week["skills_without_resources"]:
                for issue in week.get("unresolved", []):
                    label = RESOURCE_REASON_LABELS.get(issue["reason"], "Chưa đủ dữ liệu để đề xuất tài liệu.")
                    with st.expander(f"Chưa có tài liệu phù hợp cho {display_skill(issue['skill'])}"):
                        st.caption(label)
                        caution = skill_scope_caution(issue["skill"])
                        if caution:
                            st.caption(caution)
                        reasons = [
                            RESOURCE_REASON_LABELS.get(reason, reason)
                            for reason in (issue.get("exclusion_reasons") or [])
                            if isinstance(reason, str) and reason
                        ]
                        if reasons:
                            st.caption("Chi tiết: " + " ".join(reasons))


def _render_roadmap_diagram(steps: list[dict], *, alt: str, step_label: str = "Tuần") -> None:
    """Render a compact, desktop-first sequence of native roadmap cards."""
    if not steps:
        return
    st.markdown("#### Sơ đồ lộ trình")
    st.caption(alt)
    for offset in range(0, len(steps), 4):
        row = steps[offset:offset + 4]
        widths = [weight for _ in row for weight in (3, 0.45)][:-1]
        columns = st.columns(widths, vertical_alignment="center")
        column_index = 0
        for index, item in enumerate(row):
            with columns[column_index].container(border=True):
                st.caption(f"ƯU TIÊN {item['week']}")
                st.markdown(f"**{step_label} {item['week']}**")
                st.markdown(str(item["label"]).replace("\n", "  \n"))
            column_index += 1
            if index < len(row) - 1:
                with columns[column_index]:
                    st.markdown("→")
                column_index += 1


def _render_practice_routes(routes: list[dict]) -> None:
    if not routes:
        return
    st.markdown("**Bài thực hành**")
    st.caption("Dùng các bài tập này để luyện kỹ năng qua tình huống thực tế.")
    for route in routes:
        with st.expander(f"{display_skill(route['skill'])} · {route['title']}"):
            st.caption(route["framing"])
            for index, step in enumerate(route["steps"], 1):
                st.markdown(f"{index}. {step}")
            if route.get("observation_checklist"):
                st.markdown("**Checklist quan sát hành vi**")
                for item in route["observation_checklist"]:
                    st.markdown(f"- {item}")
            if route.get("tracks"):
                st.markdown("**Bài tập đọc theo nhóm nghề**")
                for track in route["tracks"]:
                    st.markdown(f"**{track['name']}** · {track['terms']}")
                    st.caption(track["exercise"])
                    st.markdown(f"[Mở nguồn tham chiếu]({track['reference_url']})")
            st.caption("Bằng chứng để tự theo dõi: " + route["evidence"])


def _render_curated_resource_card(
    item: dict,
    target_levels: dict[str, int] | None,
    role: dict,
    *,
    warn_gap: bool = False,
    phase_label: int | str | None = None,
) -> None:
    """Render a clean, accessible card for a curated learning resource in Tab 3."""
    raw_skills = item.get("skills", [])
    formatted_skills = [format_skill_name(display_skill(s)) for s in raw_skills if s]
    title = item.get("title", "Tài liệu học tập")
    if formatted_skills:
        expander_title = f"{title} · {', '.join(formatted_skills)}"
    else:
        expander_title = title

    with st.expander(expander_title):
        # 1. Link mở tài liệu trực tiếp (Cấp 2)
        url = item.get("url")
        if url:
            st.markdown(
                f'<div class="resource-open-link-wrap">'
                f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" class="resource-open-link">Mở tài liệu ↗</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 2. Thông tin nguồn và mô tả (Cấp 3 gạch đầu dòng)
        bullets = []
        if phase_label is not None:
            bullets.append(f"<strong>Thứ tự học:</strong> Giai đoạn {phase_label}")

        if item.get("academic_source"):
            source_parts = [
                p for p in [
                    item.get("academic_label", "Giáo trình nền tảng"),
                    item.get("provider", ""),
                    "tiếng Anh",
                ] if p
            ]
            if source_parts:
                bullets.append(f"<strong>Nguồn:</strong> {escape(' · '.join(source_parts))}")
            learning_scope = item.get("learning_scope", "").strip()
            if learning_scope:
                bullets.append(escape(learning_scope))
        else:
            provider = item.get("provider", "").strip()
            res_type = item.get("type", "").strip()
            lang_raw = item.get("language")
            lang = "tiếng Việt" if lang_raw == "vi" else ("tiếng Anh" if lang_raw == "en" else (lang_raw or ""))
            source_parts = [p for p in [provider, res_type, lang] if p]
            if not source_parts and item.get("duration_evidence", {}).get("source"):
                source_parts = [item["duration_evidence"]["source"]]
            if not source_parts and item.get("duration_kind"):
                source_parts = [item["duration_kind"]]
            if source_parts:
                bullets.append(f"<strong>Nguồn:</strong> {escape(' · '.join(source_parts))}")
            desc = (item.get("review_note") or item.get("learning_scope") or "").strip()
            if desc:
                bullets.append(escape(desc))

        if bullets:
            bullet_html = "".join(f"<li>{b}</li>" for b in bullets)
            st.markdown(f'<ul class="resource-details-bullets">{bullet_html}</ul>', unsafe_allow_html=True)

        # 3. Phần thực hành kèm theo (nếu tài liệu có practice / companion)
        companion = item.get("verified_companion_url") or item.get("practice_url")
        if companion:
            companion_title = item.get("verified_companion_title") or item.get("practice_title") or "Tài liệu bổ sung"
            st.markdown(
                f'<div class="resource-companion-box">'
                f'<div class="resource-companion-link-wrap">'
                f'<a href="{escape(companion)}" target="_blank" rel="noopener noreferrer" class="resource-companion-link">Thực hành thêm: {escape(companion_title)} ↗</a>'
                f'</div>'
                f'<ul class="resource-companion-bullets">'
                f'<li>Giáo trình nền tảng. Đọc xong chưa đồng nghĩa đã đạt mức độ thành thạo kỹ năng; hãy hoàn thành bài thực hành và xin phản hồi.</li>'
                f'</ul>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 4. Chi tiết tài liệu & minh chứng (expander con đóng mặc định)
        with st.expander("Chi tiết tài liệu & minh chứng", expanded=False):
            if item.get("academic_source"):
                if item.get("access_note"):
                    st.caption(item["access_note"])
                _render_resource_level_scope(item, target_levels, warn_gap=warn_gap)
            else:
                if item.get("duration_kind") and not any(item["duration_kind"] in b for b in bullets):
                    st.caption(f"Thời lượng: {item['duration_kind']}")
                _render_resource_level_scope(item, target_levels, warn_gap=warn_gap)
                evidence = item.get("duration_evidence", {})
                if evidence.get("source"):
                    st.caption(f"Nguồn thời lượng: {evidence['source']}")
                status = item.get("content_review_status", "unreviewed")
                if status != "unreviewed":
                    st.caption("Trạng thái nội dung: " + resource_review_label(status))
                review_note = item.get("review_note")
                if status == "partial" and isinstance(review_note, str) and review_note.strip():
                    st.caption("Phạm vi đánh giá: " + review_note)
                if item.get("duration_issue") == "conflicting_duration":
                    st.caption("Thời lượng nguồn có khác biệt; chưa cộng vào lịch.")
                _render_partial_practice_assignments(
                    item.get("skills", []), item, role_context=format_role(role),
                    resources=load_resources(),
                )
                for skill in item.get("skills", []):
                    caution = skill_scope_caution(skill)
                    if caution:
                        st.caption(caution)
                if item.get("access_note"):
                    st.caption(item["access_note"])


def _render_resource_quality_disclosure(resources: dict) -> dict:
    summary = summarize_resource_reviews(resources)
    mapped_skills = sum(
        1 for group in resources.values()
        if isinstance(group, dict) and isinstance(group.get("academic_source"), dict)
    )
    with st.expander("Về học liệu"):
        st.markdown(
            f'<div class="about-curriculum-intro">'
            f'<ul class="about-curriculum-bullets">'
            f'<li>Có giáo trình/học liệu nền tảng cho <strong>{mapped_skills}</strong> kỹ năng trong danh mục nghề, kèm bài tập và đầu ra để xin phản hồi.</li>'
            f'<li>Tài liệu bằng tiếng Anh; thời lượng không công bố, nên học theo tiến độ cá nhân.</li>'
            f'<li>Tài liệu giúp học kiến thức nền, không chứng nhận đạt trình độ.</li>'
            f'</ul>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.warning(
            "**Lưu ý quan trọng:** Luật, thuế, y tế và an toàn cần nguồn Việt Nam hiện hành hoặc người hướng dẫn đủ chuyên môn.",
            icon="⚖️",
        )
    return summary


def _render_partial_practice_assignments(
    skills: list[str],
    resource: dict,
    *,
    role_context: str | None,
    resources: dict,
) -> None:
    """Show applied work for the reviewed portion of partial resources."""
    for skill in skills:
        assignment = get_partial_resource_assignment(
            skill, resource, resources, role_context=role_context
        )
        if not assignment:
            continue
        with st.expander(f"Bài tập/portfolio · {display_skill(skill)}"):
            if assignment.get("scope"):
                st.caption("Nguồn chỉ hỗ trợ trong phạm vi: " + assignment["scope"])
            for index, step in enumerate(assignment["steps"], 1):
                st.markdown(f"{index}. {step}")
            st.caption("Minh chứng cần tạo: " + assignment["evidence"])
            if assignment.get("caution"):
                st.warning(assignment["caution"])


def render_interview_practice(position: dict, focus_skills=None, assessment="presence") -> None:
    """Ask first, then review the answer against the question rubric."""
    from modules import review_answer

    role_id = position["id"]
    st.subheader("Luyện phỏng vấn")
    st.caption("Sau khi gửi, bạn sẽ thấy điểm tham khảo theo rubric, khung trả lời và checklist tự rà soát; tình huống thực tế không có một đáp án chung.")
    mode = st.radio("Chọn cách nhận góp ý", ["Tự đánh giá theo tiêu chí", "Nhận góp ý từ AI"],
                    key="interview_review_mode")
    ai_mode = mode == "Nhận góp ý từ AI"
    active_key = ""
    if ai_mode:
        st.caption("AI phân tích câu trả lời theo tiêu chí của câu hỏi; kết quả chỉ mang tính tham khảo.")
        with st.expander("Cách tạo và sử dụng API key Groq", expanded=True):
            st.markdown(
                "1. Đăng nhập hoặc tạo tài khoản tại [Groq Console](https://console.groq.com/).\n"
                "2. Mở [API Keys](https://console.groq.com/keys), tạo một key và sao chép.\n"
                "3. Dán key vào ô bên dưới, đóng hướng dẫn nếu muốn và gửi câu trả lời."
            )
            st.caption("Không chia sẻ key với người khác. Key chỉ dùng trong phiên này; hạn mức và chi phí phụ thuộc tài khoản Groq của bạn.")
        active_key = st.text_input("API key Groq", type="password", key="llm_cfg_api_key").strip()
        st.caption("Khi gửi, câu hỏi, tiêu chí và câu trả lời được gửi tới Groq. Không nhập thông tin nhạy cảm.")
        if not active_key:
            st.info("Nhập API key Groq để nhận góp ý từ AI, hoặc chọn tự đánh giá theo tiêu chí.")
    else:
        st.caption("Đối chiếu từ khóa với tiêu chí; không gửi câu trả lời tới AI và không cần API key. Kết quả không đánh giá đầy đủ ý nghĩa câu trả lời.")
    bank_summary = question_bank_quality_summary()
    st.warning(
        f"Ngân hàng phỏng vấn riêng: {bank_summary['total']} câu trên {bank_summary['role_count']} vị trí — "
        f"{bank_summary['reviewed_internal']} câu review nội bộ, "
        f"{bank_summary['ai_reviewed_internal']} câu AI hỗ trợ rà soát, {bank_summary['template']} template, "
        f"{bank_summary['unreviewed']} câu chưa review. Đây là backlog khác với mapping học liệu; "
        "AI hỗ trợ rà soát không phải thẩm định chuyên gia/độc lập."
    )
    if role_id not in {"sales_executive", "frontend_developer_react", "data_analyst", "backend_developer_java"}:
        st.info("Vị trí này chưa được biên tập bối cảnh và rubric theo cổng bằng chứng của nhóm demo; dùng câu hỏi như bản tham khảo chưa qua duyệt chuyên môn.")
    else:
        st.info("Câu hỏi nhóm demo đã có bối cảnh và rubric bản nháp AI; cần người có chuyên môn duyệt trước khi công bố là đã rà soát.")
    try:
        available_count = len(get_questions(role_id, MAX_INTERVIEW_QUESTIONS, seed=0))
    except ValueError as exc:
        st.info(str(exc))
        return
    if available_count == 0:
        st.info("Chưa có câu hỏi cho vị trí này.")
        return
    prefer_reviewed = st.checkbox(
        "Ưu tiên câu hỏi có rubric đã rà soát nội bộ / AI hỗ trợ",
        value=True,
        key=f"interview_prefer_reviewed_{role_id}",
        help="Review nội bộ hoặc AI hỗ trợ chỉ giúp rà soát cấu trúc; chưa thay thế owner/chuyên gia xác nhận.",
    )
    reviewed_count = count_reviewed_questions(role_id)
    if prefer_reviewed and reviewed_count == 0:
        st.info("Vị trí này chưa có câu hỏi đủ điều kiện review nội bộ; bộ câu hỏi tham khảo vẫn hiển thị nhãn trạng thái.")
    context = (role_id, assessment, tuple(focus_skills or []), prefer_reviewed)
    previous = st.session_state.get("interview_session")
    if previous and previous.get("context") != context:
        st.session_state.pop("interview_session", None)
    max_count = min(MAX_INTERVIEW_QUESTIONS, available_count)
    count = st.number_input(f"Số câu hỏi (tối đa {max_count} câu có sẵn)", min_value=1, max_value=max_count, value=min(3, max_count), step=1,
                            key=f"interview_count_{role_id}")
    if st.button("Tạo bộ câu hỏi", key=f"start_interview_{role_id}", icon=":material/quiz:"):
        try:
            requested_count = int(count)
            questions = get_questions(
                role_id,
                requested_count,
                focus_skills=focus_skills,
                prefer_reviewed=prefer_reviewed,
            )
            st.session_state["interview_session"] = {
                "role_id": role_id, "batch_id": uuid4().hex[:10], "questions": questions,
                "requested_count": requested_count,
                "answered_ids": [], "submitted_answers": {}, "context": context,
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
            st.caption("Trạng thái nội dung: " + question_quality_label(question.get("quality")))
            if question.get("quality_note"):
                st.caption(question["quality_note"])
            st.markdown(f"**{question.get('question', '')}**")
            with st.form(f"answer_form_{session['batch_id']}_{question_id}"):
                answer = st.text_area("Câu trả lời của bạn", key=key, height=120)
                submitted = st.form_submit_button("Gửi câu trả lời")
            if submitted:
                if answer.strip() and ai_mode and not active_key:
                    st.warning("Bạn cần nhập API key Groq trước khi gửi, hoặc chuyển sang tự đánh giá theo tiêu chí.")
                elif answer.strip():
                    session.setdefault("submitted_answers", {})[question_id] = answer.strip()
                    session["llm_limit_reached_ids"] = [
                        item for item in session.get("llm_limit_reached_ids", []) if item != question_id
                    ]
                    for review_key, _ in INTERVIEW_SELF_REVIEW:
                        st.session_state.pop(f"self_review_{session['batch_id']}_{question_id}_{review_key}", None)
                    answered.add(question_id)
                    session["answered_ids"] = list(answered)
                    calls = st.session_state.get("llm_review_calls", 0)
                    limit_reached = ai_mode and calls >= 20
                    if ai_mode and not limit_reached:
                        st.session_state["llm_review_calls"] = calls + 1
                    with st.spinner("Đang nhận xét…"):
                        if limit_reached or not ai_mode:
                            review = review_answer(question_id, answer, api_key="", base_url="https://api.groq.com/openai/v1")
                            if limit_reached:
                                session.setdefault("llm_limit_reached_ids", []).append(question_id)
                        else:
                            review = review_answer(question_id, answer, api_key=active_key, base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")
                    session.setdefault("reviews", {})[question_id] = review
                    st.session_state["interview_session"] = session
                else:
                    st.warning("Hãy nhập câu trả lời trước khi xem ý tham khảo.")
            if question_id in answered:
                st.caption(POST_SUBMISSION_GUIDANCE_NOTICE)
                review = session.get("reviews", {}).get(question_id)
                if review:
                    if review["source"] != "llm" and review.get("fallback_reason") not in (None, "no_key"):
                        st.warning("Chưa nhận được góp ý từ AI. Kết quả bên dưới chỉ đối chiếu từ khóa với tiêu chí; hãy kiểm tra key, hạn mức hoặc thử lại.")
                    label = "Góp ý từ AI" if review["source"] == "llm" else "Tự đánh giá theo tiêu chí"
                    st.markdown(f"**{label} · Điểm tham khảo: {review['score']:.1f}/10**")
                    if question_id in session.get("llm_limit_reached_ids", []):
                        st.info("Đã đạt giới hạn 20 lần gọi LLM trong phiên; câu này được chấm offline.")
                    for item in review["criteria"]:
                        st.markdown(f"{'✓' if item['met'] else '✗'} {item['point']}")
                        if item["evidence"]:
                            st.caption(f"Bằng chứng: “{item['evidence']}”")
                    if review["red_flags_hit"]:
                        st.warning("Điểm cần lưu ý: " + "; ".join(review["red_flags_hit"]))
                    st.write(review["feedback"])
                    if review["improvement"]:
                        st.write("Gợi ý cải thiện: " + review["improvement"])
                    if review["source"] == "llm":
                        st.caption(f"Nhận xét bởi {review['model']}")
                    else:
                        reasons = {"no_key": "chưa cấu hình key", "timeout": "dịch vụ phản hồi quá chậm",
                                   "auth": "xác thực thất bại", "rate_limit": "dịch vụ giới hạn lượt gọi",
                                   "bad_json": "phản hồi không đúng JSON", "mismatch": "phản hồi không khớp rubric",
                                   "http_error": "dịch vụ không khả dụng"}
                        reason = review.get("fallback_reason")
                        detail = f" ({reasons.get(reason, 'không thể dùng LLM')})" if reason and reason != "no_key" else ""
                        st.caption("Đối chiếu từ khóa với tiêu chí — không dùng LLM" + detail)
                    st.caption("Điểm đo mức đạt rubric, chỉ mang tính tham khảo, không phải đánh giá tuyển dụng.")
                with st.expander("Tự rà soát ý nghĩa và chất lượng câu trả lời"):
                    st.caption("Checklist tự rà soát, không tính điểm và không thay cho đánh giá của người phỏng vấn.")
                    for review_key, label in INTERVIEW_SELF_REVIEW:
                        st.checkbox(label, key=f"self_review_{session['batch_id']}_{question_id}_{review_key}")
                try:
                    feedback = get_question_feedback(question_id)
                except ValueError as exc:
                    st.warning(str(exc))
                    continue
                has_answer = feedback.get("has_reference_answer", bool(feedback.get("reference_answer")))
                is_scenario = feedback.get("question_type") == "scenario"
                if is_scenario:
                    st.markdown("**Cách triển khai câu trả lời (hãy dùng trải nghiệm thật)**")
                    st.caption("Tình huống có thể có nhiều phương án hợp lý; nêu bối cảnh, hành động, lý do và kết quả bạn quan sát được.")
                else:
                    st.markdown("**Khung trả lời tham khảo**")
                if not feedback.get("content_reviewed"):
                    st.info("Câu hỏi/đáp án này chưa được review đầy đủ. Hãy kiểm chứng phần kiến thức chuyên môn bằng tài liệu phù hợp và chỉnh ví dụ theo trải nghiệm của bạn.")
                elif feedback.get("quality") == "ai_reviewed_internal":
                    st.info("Khung này được AI hỗ trợ rà soát nội bộ; chưa được chuyên gia độc lập xác nhận. Hãy đối chiếu nguồn và kinh nghiệm thực tế.")
                elif feedback.get("quality_sources"):
                    st.caption("Nguồn tham khảo khi review nội bộ:")
                    for source in feedback["quality_sources"]:
                        st.markdown(f"- {source}")
                st.markdown(feedback["reference_answer"])
                if feedback.get("good_answer_points"):
                    st.markdown("**Các ý có thể cân nhắc**")
                    for point in feedback["good_answer_points"]:
                        st.markdown(f"- {point}")
                if feedback["red_flags"]:
                    st.caption(STATIC_SELF_REVIEW_TITLE)
                    st.caption(STATIC_SELF_REVIEW_NOTICE)
                    for flag in feedback["red_flags"]:
                        st.markdown(f"- {flag}")


def run_app() -> None:
    st.set_page_config(page_title="AI Career Coach | Cộng đồng nghề nghiệp", page_icon="✦", layout="wide")
    # Streamlit's shell defaults to English and has no native page-language
    # option. This fixed code-owned script adds Vietnamese language metadata;
    # it never receives or evaluates user-provided content.
    st.html("<script>document.documentElement.lang = 'vi';</script>", unsafe_allow_javascript=True)
    inject_styles()
    render_landing_page()
    render_toolkit()
    render_closing_sections()
    inject_site_script()


if __name__ == "__main__":
    run_app()
