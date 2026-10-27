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
        "<dl class='faq-levels'><div><dt>0 · Chưa biết</dt><dd>Chưa học hoặc chưa nắm được kỹ năng.</dd></div><div><dt>1 · Cơ bản</dt><dd>Hiểu khái niệm, làm việc đơn giản khi có hướng dẫn.</dd></div><div><dt>2 · Độc lập</dt><dd>Tự làm các tác vụ quen thuộc.</dd></div><div><dt>3 · Nâng cao</dt><dd>Xử lý việc phức tạp, có thể hướng dẫn người khác.</dd></div></dl><p>Nếu chưa khai báo Level, chế độ <strong>“Theo kỹ năng đã có”</strong> chỉ xét có hay chưa có. Ở chế độ <strong>“Theo level tự khai báo”</strong>, kỹ năng chưa khai báo được tính là mức 0 <em>chỉ khi bạn xác nhận đồng ý</em>; đây không phải kết luận về năng lực thật.</p>",
    ),
    (
        "Vì sao mình có đúng sở thích mà điểm gợi ý nghề vẫn thấp?",
        "<p>Điểm gợi ý dựa chủ yếu vào <strong>mức khớp kỹ năng có trọng số</strong> (75%), cùng với sở thích (25%). Khi mức khớp kỹ năng dưới ngưỡng 15%, điểm gợi ý bị giới hạn tối đa 5/100. Điều này nhắc bạn cần xây thêm nền tảng kỹ năng, <strong>không kết luận bạn không hợp nghề</strong>.</p>",
    ),
    (
        "Vì sao có kỹ năng chưa có tài liệu hoặc không có link khóa học?",
        "<p>Web chỉ đề xuất tài liệu đáp ứng tiêu chí kiểm tra nguồn, nội dung và mức độ phù hợp. Khi chưa đủ căn cứ, web báo <strong>“Chưa có tài liệu được xác minh”</strong> thay vì gợi ý bừa. Với kỹ năng mềm, web ưu tiên bài tập thực hành, tình huống và gợi ý tự đánh giá; không mặc định rằng xem một khóa học là đủ để thành thạo.</p>",
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
        return json.load(source)


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
        'fill="#1B7A66"/><text x="48" y="48" text-anchor="middle" '
        'font-family="Arial,sans-serif" font-size="34" font-weight="700" '
        'fill="#fff">AI</text></svg>'
    )
    encoded = base64.b64encode(fallback_svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def display_skill(skill: str) -> str:
    """Translate descriptive skill labels while preserving technology names."""
    return SKILL_NAMES_VI.get(skill.casefold(), skill)


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
              <h1>Đi xa hơn với một <em>lộ trình nghề nghiệp rõ ràng.</em></h1>
              <div class="hero-copy">Khám phá điểm mạnh từ kỹ năng và CV, đối chiếu với vị trí bạn quan tâm, rồi chọn từng bước học tập phù hợp với mục tiêu của mình.</div>
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
                  <span class="how-panel-number">01</span>
                  <h3 tabindex="-1">Tạo hoặc nạp hồ sơ</h3>
                  <p class="how-lead">Bắt đầu tại mục Hồ sơ nghề nghiệp ngay dưới phần hướng dẫn.</p>
                  <ol class="how-detail-list">
                    <li><span class="how-detail-index" aria-hidden="true">1</span><div><strong>Thử nhanh hoặc nhập thông tin của bạn</strong><p>Chọn một hồ sơ mẫu, hoặc tự nhập kỹ năng, sở thích và kinh nghiệm.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">2</span><div><strong>Chuẩn bị thông tin bắt buộc</strong><p>Nếu tự nhập, cần ít nhất một kỹ năng, ví dụ “Python, SQL” (cách nhau bằng dấu phẩy), hoặc tải CV PDF/DOCX. JD và các mục còn lại là tùy chọn.</p></div></li>
                    <li><span class="how-detail-index" aria-hidden="true">3</span><div><strong>Chuyển sang rà soát</strong><p>Nhấn “Tiếp tục rà soát hồ sơ” ở cuối biểu mẫu.</p></div></li>
                  </ol>
                  <p class="how-outcome"><strong>Sau bước này</strong> Bạn sẽ thấy những kỹ năng cần kiểm tra trước khi tạo kết quả.</p>
                </article>
                <article class="how-panel" data-step-panel="2" hidden>
                  <span class="how-panel-number">02</span>
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
                  <span class="how-panel-number">03</span>
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


@st.dialog("Chọn Nhóm nghề, Nghề hoặc Chuyên môn", width="large")
def open_role_taxonomy_dialog(positions: list[dict], role_by_id: dict[str, dict], taxonomy: dict[str, list[dict]]) -> None:
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
        family_icons = {
            "Phát triển phần mềm": "💻",
            "Kiểm thử và đảm bảo chất lượng": "🧪",
            "Phân tích dữ liệu": "📊",
            "Dữ liệu, AI và nền tảng dữ liệu": "🤖",
            "Hạ tầng, cloud và an ninh mạng": "☁️",
            "Sản phẩm, dự án và phân tích nghiệp vụ": "📋",
            "Thiết kế và nghiên cứu trải nghiệm": "🎨",
            "Marketing, nội dung và truyền thông": "📢",
            "Kinh doanh và chăm sóc khách hàng": "🤝",
            "Tài chính và kế toán": "💰",
            "Nhân sự, pháp lý và tuân thủ": "⚖️",
            "Logistics và chuỗi cung ứng": "🚚",
            "Kỹ thuật và sản xuất": "⚙️",
            "Xây dựng, kiến trúc và an toàn": "🏗️",
            "Y tế, giáo dục và dịch vụ": "🏥",
        }

        default_idx = 0
        if current_role_id:
            for idx, (f_name, r_list) in enumerate(taxonomy.items()):
                if any(r["id"] == current_role_id for r in r_list):
                    default_idx = idx
                    break

        with col_left:
            st.markdown("**NHÓM NGHỀ**")
            selected_family = st.radio(
                "Nhóm nghề",
                options=family_names,
                index=default_idx,
                format_func=lambda name: f"{family_icons.get(name, '📁')} {name}",
                key="dlg_selected_family_radio",
                label_visibility="collapsed",
            )

        with col_right:
            roles_in_group = taxonomy.get(selected_family, [])
            st.markdown(f"**VỊ TRÍ CHUYÊN MÔN · {selected_family}** ({len(roles_in_group)} vị trí)")
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

    c_foot_l, c_foot_r = st.columns([3, 1])
    with c_foot_l:
        if current_role_id and current_role_id in role_by_id:
            st.markdown(f"Đã chọn: <b style='color:var(--color-plume-600);'>{format_role(role_by_id[current_role_id])}</b>", unsafe_allow_html=True)
    with c_foot_r:
        if st.button("Đóng hộp thoại", key="dlg_close_btn", use_container_width=True):
            st.rerun()


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
            st.markdown("### Bước 1/2 · Tạo hoặc nạp hồ sơ")
            skills_text = st.text_area("Kỹ năng bạn muốn đưa vào hồ sơ (*)", placeholder="Python, SQL, phân tích dữ liệu", key="skills_input")
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
                placeholder="Dán phần kinh nghiệm, dự án và kỹ năng từ CV. Kỹ năng nhận diện sẽ được đưa sang bước rà soát.",
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
                demo_icons = {"backend-java": "☕", "data-analyst": "📊", "sales-executive": "🤝"}
                for col, demo in zip(cols, load_demo_profiles()):
                    icon = demo_icons.get(demo["id"], "✦")
                    skills_preview = ", ".join(demo["profile"]["skills"][:3])
                    col.markdown(
                        f'<div style="padding:10px 14px;border:1px solid var(--color-line);border-radius:12px;background:var(--color-paper-sunken);margin-bottom:8px;">'
                        f'<div style="font-weight:700;font-size:13px;color:var(--color-ink);display:flex;align-items:center;gap:6px;">'
                        f'<span>{icon}</span><span>{demo["label"]}</span>'
                        f'</div>'
                        f'<div style="font-size:11px;color:var(--color-ink-soft);margin-top:4px;">'
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

            job_description = st.text_area("Mô tả công việc cần đối chiếu (không bắt buộc)", key="job_description_input")
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
            if cv_jd["overall_percent"] is not None:
                st.metric("Chỉ số bao phủ JD tổng hợp · heuristic 85/15", f"{cv_jd['overall_percent']}%")
                st.caption("Chỉ số chỉ tính nhóm bắt buộc và ưu tiên đã xác nhận (85%/15%); nhóm chưa phân loại được hiển thị riêng. Đây không phải đánh giá đủ điều kiện ứng tuyển, năng lực thực tế hay xác suất được tuyển.")
            else:
                st.info("Chưa có kỹ năng nào được xác nhận là bắt buộc; ứng dụng không tạo điểm tổng hợp. Kỹ năng chưa phân loại vẫn được đối chiếu riêng.")
            st.caption(f"Đối chiếu theo kỹ năng trong catalog do người dùng xác nhận; không đánh giá level hoặc năng lực thực tế. Số kỹ năng JD đã phân loại: {cv_jd.get('recognized_count', len(cv_jd['jd_skills']))}.")
            if cv_jd.get("low_confidence"):
                st.warning("Có dưới 3 kỹ năng bắt buộc được xác nhận; chỉ số tổng hợp có phạm vi đầu vào hẹp.")
            for kind, label in metric_specs:
                category = cv_jd[kind]
                st.write(f"**{label} khớp hồ sơ:**", ", ".join(display_skill(s) for s in category["matched"]) or "Chưa có")
                st.write(f"**{label} chưa có trong hồ sơ:**", ", ".join(display_skill(s) for s in category["missing"]) or "Không có")
        if cv_extraction:
            if not cv_jd:
                if st.session_state.get("jd_provided"):
                    st.info("Đã gộp kỹ năng nhận diện từ CV vào hồ sơ; lần gửi này chưa tạo được kết quả đối chiếu JD.")
                else:
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
            st.caption("Chọn kỹ năng muốn giữ lại trong hồ sơ. Tên chưa nhận diện không được tính vào điểm đối chiếu hoặc học liệu gợi ý.")
            for skill in profile["unrecognized_skills"]:
                if st.checkbox(f"Giữ ‘{skill}’ trong hồ sơ", value=True, key=f"keep_unknown_{revision}_{skill}"):
                    retained.append(skill)
        effective_skills = [
            skill for skill in profile["skills"]
            if skill not in profile["unrecognized_skills"] or skill in retained
        ]
        st.subheader("Hồ sơ của bạn")
        st.write("**Kỹ năng:**", ", ".join(display_skill(s) for s in effective_skills) or "Chưa có thông tin")
        if profile.get("skills_from_cv"):
            st.caption("Kỹ năng trích từ CV và đã xác nhận: " + ", ".join(display_skill(s) for s in profile["skills_from_cv"]))
        if profile.get("skills_from_experience"):
            st.caption("Kỹ năng trích từ kinh nghiệm và đã xác nhận: " + ", ".join(display_skill(s) for s in profile["skills_from_experience"]))
        elif profile.get("experience"):
            st.caption("Kinh nghiệm được lưu để tham khảo; hệ thống chỉ dùng kỹ năng trong đó khi nhận diện được và bạn xác nhận, không chấm số năm hay thâm niên.")
        st.write("**Sở thích:**", ", ".join(profile["interests"]) or "Chưa có thông tin")
        if profile.get("interest_activity_ids"):
            st.write(
                "**Hoạt động nghề nghiệp đã chọn:**",
                ", ".join(activity_label(value) for value in profile["interest_activity_ids"]),
            )
        st.write("**Kinh nghiệm:**", profile["experience"] or "Chưa có thông tin")
        levels_map = profile.get("levels", {})
        if levels_map:
            level_items = [f"**{display_skill(k)}**: Cấp độ {v}" for k, v in levels_map.items()]
            levels_display = " · ".join(level_items)
        else:
            levels_display = "Chưa khai báo; không suy từ CV"
        st.write("**Level đã khai báo:**", levels_display)

        st.subheader("Vị trí gợi ý từ hồ sơ")
        with st.expander("Cách đọc và hiểu đúng điểm số gợi ý"):
            st.markdown(
                "- **Skill fit:** Tỷ lệ bao phủ kỹ năng yêu cầu của nghề, có tính trọng số đặc thù Role-IDF.\n"
                "- **Interest fit:** Độ tương đồng giữa sở thích nghề nghiệp và hồ sơ RIASEC sáu chiều của họ nghề.\n"
                "- **Điểm gợi ý:** Kết hợp 75% skill fit và 25% interest fit; nếu skill fit dưới 15%, điểm bị giới hạn tối đa 5/100.\n"
                "- *Lưu ý:* Đây là định hướng heuristic, không phải xác suất tuyển dụng thực tế hoặc kết luận về năng lực."
            )
        st.caption("Điểm heuristic theo kỹ năng/sở thích; không là xác suất tuyển dụng hay đánh giá level.")
        if profile.get("unrecognized_skills"):
            st.warning(
                "⚠️ Có kỹ năng bạn nhập chưa thuộc catalog nên chưa được tính vào điểm khớp. "
                "Hãy dùng tên kỹ năng chuẩn trong biểu mẫu hồ sơ phía trên để hệ thống đối chiếu chính xác hơn."
            )
        suggestions = suggest_roles({**profile, "skills": effective_skills})
        if role_recommendation_is_low_confidence({"skills": effective_skills}):
            st.warning(LOW_CONFIDENCE_ROLE_MESSAGE)
        if not effective_skills and (profile.get("interests") or profile.get("interest_activity_ids")):
            st.info(
                "Chỉ có sở thích được ánh xạ; gợi ý bị giới hạn tối đa "
                f"{100 * LOW_SKILL_ROLE_SCORE_CAP:.0f}/100 vì chưa có kỹ năng trùng. "
                "Điểm này không phản ánh mức đáp ứng kỹ năng."
            )
        if not suggestions:
            st.caption("Chưa có tín hiệu khớp catalog để xếp hạng vị trí.")
        for item in suggestions:
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f'''<div style="padding:10px 14px;border:1px solid var(--color-line);border-radius:12px;background:var(--color-paper-raised);margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;">'''
                    f'''<span style="font-weight:700;font-size:15px;color:var(--color-ink);">{item['role_name']}</span>'''
                    f'''<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;background:var(--color-plume-50);color:var(--color-plume-700);border:1px solid var(--color-plume-200);">{item['score']}% Phù hợp</span>'''
                    f'''</div>''',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button(f"Chọn {item['role_name']}", key=f"choose_role_{revision}_{item['role_id']}"):
                    st.session_state["career_role_id"] = item["role_id"]
                    st.session_state["pending_career_role"] = item["role_id"]
                    st.session_state.pop("interview_session", None)
                    st.rerun()

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
            st.caption("Chỉ tính kỹ năng đã xác nhận, gồm mục trích từ CV/kinh nghiệm; không tính sở thích, thâm niên hay xác suất tuyển dụng.")
            st.write("**Kỹ năng khớp vị trí:**", ", ".join(display_skill(s) for s in presence["matched"]) or "Chưa có")
            st.write("**Kỹ năng còn thiếu:**", ", ".join(display_skill(s) for s in presence["missing"]) or "Không có")
        st.caption("Điểm gợi ý role được tính riêng bằng heuristic.")

    with tabs[2]:
        if selected_mode == "Theo level tự khai báo":
            if gap_result is not None:
                budget = st.number_input("Ngân sách giờ học mỗi tuần", min_value=0.5, max_value=40.0, value=8.0, step=0.5, key=f"study_budget_{revision}")
                timed_result = build_timed_roadmap(gap_result, load_resources(), hours_per_week=budget)
                render_timed_roadmap(timed_result, role_context=format_role(role), target_levels=target_levels)
            else:
                st.info("Xác nhận quy ước level chưa khai báo ở tab Khoảng cách để xem lộ trình.")
        elif presence["missing"]:
            weekly_roadmap = build_roadmap(presence["missing"], load_resources(), missing_details=presence["missing_details"])
            render_roadmap(weekly_roadmap, role_context=format_role(role), target_levels=target_levels)
        else:
            st.success("Hồ sơ của bạn đã có đủ các kỹ năng được liệt kê cho vị trí này.")

    with tabs[3]:
        st.subheader("Tài liệu được tham chiếu")
        _render_resource_quality_disclosure(load_resources())
        if timed_result is not None:
            for key, item in timed_result["resources"].items():
                st.markdown(f"[{item.get('title', 'Tài liệu học tập')}]({item.get('url', '')})")
                st.caption(f"{', '.join(item.get('skills', []))} · {item.get('duration_kind', 'unknown')} · {key}")
                _render_resource_level_scope(item, target_levels, warn_gap=False)
                evidence = item.get("duration_evidence", {})
                if evidence.get("source"):
                    st.caption(f"Nguồn thời lượng: {evidence['source']}")
                if item.get("review_note"):
                    st.caption(item["review_note"])
                if item.get("duration_issue") == "conflicting_duration":
                    st.warning("Các nguồn công bố thời lượng mâu thuẫn; thời lượng không được cộng vào lịch.")
                _render_partial_practice_assignments(
                    item.get("skills", []), item, role_context=format_role(role),
                    resources=load_resources(),
                )
                for skill in item.get("skills", []):
                    caution = skill_scope_caution(skill)
                    if caution:
                        st.warning(caution)
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
                        first_phase = next(w["week"] for w in weekly_roadmap if any(r["key"] == key for r in w["resources"]))
                        st.markdown(f"[{item.get('title', 'Tài liệu học tập')}]({item.get('url', '')}) · {', '.join(item.get('skills', []))}")
                        st.caption(f"Giới thiệu lần đầu ở giai đoạn {first_phase}; đây không phải lịch theo tuần.")
                        _render_resource_level_scope(item, target_levels)
                        status = item.get("content_review_status", "unreviewed")
                        st.caption("Trạng thái nội dung: " + resource_review_label(status))
                        review_note = item.get("review_note")
                        if status == "partial" and isinstance(review_note, str) and review_note.strip():
                            st.warning("Phạm vi review một phần: " + review_note)
                            _render_partial_practice_assignments(
                                item.get("skills", []), item, role_context=format_role(role),
                                resources=load_resources(),
                            )
                        for skill in item.get("skills", []):
                            caution = skill_scope_caution(skill)
                            if caution:
                                st.warning(caution)
                        if item.get("access_note"):
                            st.caption(item["access_note"])
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
    st.subheader("Lộ trình theo giờ")
    st.caption("Hoàn thành tài liệu không chứng nhận đạt level.")
    st.metric("Tổng giờ công bố đã chọn", f"{roadmap['total_known_hours']:.2f}")
    st.metric("Giờ ước lượng biên tập", f"{roadmap['total_estimated_hours']:.2f}")
    st.metric("Số tuần toàn lộ trình", "Chưa xác định" if roadmap["total_weeks"] is None else str(roadmap["total_weeks"]))
    st.caption(f"Phần đã phân bổ: {roadmap['known_weeks']} tuần; ngân sách {roadmap['hours_per_week']} giờ/tuần.")
    _render_roadmap_diagram([
        {
            "week": phase["week"],
            "label": f"{phase['hours']:.2f} giờ · {len(phase['segments'])} phần",
            "warning": any(roadmap["resources"][segment["resource_key"]]["duration_kind"] == "estimated" for segment in phase["segments"]),
        }
        for phase in roadmap["phases"]
    ], alt="Sơ đồ các tuần học theo số giờ và phần tài liệu đã xếp lịch.")
    _render_practice_routes(roadmap.get("practice_routes", []))
    if roadmap["is_estimated"]:
        st.warning("Lịch có giờ ước lượng biên tập; số tuần là dự kiến theo căn cứ.")
    for phase in roadmap["phases"]:
        with st.expander(f"Tuần học {phase['week']} · {phase['hours']:.2f} giờ"):
            for segment in phase["segments"]:
                item = roadmap["resources"][segment["resource_key"]]
                st.markdown(f"[{item['title']}]({item['url']}) · phần {segment['part']} · {segment['hours']:.2f} giờ")
                st.caption(f"{segment['duration_kind']} · {', '.join(item['skills'])}")
                _render_resource_level_scope(item, target_levels, warn_gap=False)
                status = item.get("content_review_status", "unreviewed")
                st.caption("Trạng thái nội dung: " + resource_review_label(status))
                evidence = item.get("duration_evidence", {})
                if segment["duration_kind"] == "estimated":
                    st.caption(f"Cơ sở ước lượng: {evidence.get('basis') or item.get('estimated_duration_basis') or item.get('duration_basis') or 'chưa có thông tin'}")
                elif evidence.get("source"):
                    st.caption(f"Nguồn thời lượng: {evidence['source']}")
                if item.get("review_note"):
                    st.caption(item["review_note"])
                if item.get("access_note"):
                    st.caption(item["access_note"])
                if item.get("duration_issue") == "conflicting_duration":
                    st.warning("Các nguồn công bố thời lượng mâu thuẫn; thời lượng không được cộng vào lịch.")
                _render_partial_practice_assignments(
                    item.get("skills", []), item, role_context=role_context, resources=load_resources()
                )
    for item in roadmap["unresolved"]:
        skill = item.get("skill") or ", ".join(item.get("skills", []))
        st.warning(f"{display_skill(skill)}: {RESOURCE_REASON_LABELS.get(item['reason'], 'Chưa đủ dữ liệu để xếp lịch.')}")
        caution = skill_scope_caution(skill)
        if caution:
            st.warning(caution)
        if item.get("resource_statuses"):
            st.caption("Trạng thái tài liệu hiện có: " + ", ".join(item["resource_statuses"]))
    for item in roadmap["unknown_duration"]:
        record = roadmap["resources"][item["resource_key"]]
        st.markdown(f"[{record['title']}]({record['url']}) · thời lượng chưa xác định")


def _render_resource_level_scope(resource: dict, target_levels: dict[str, int] | None, *, warn_gap: bool = True) -> None:
    """Distinguish the page's teaching range from the role's target level."""
    st.caption("Mức bằng chứng: " + resource_evidence_badge(resource))
    lower, upper = resource.get("level_from"), resource.get("level_to")
    if type(lower) is not int or type(upper) is not int or not 1 <= lower <= upper <= 3:
        return
    label = f"Level {lower}" if lower == upper else f"Level {lower}–{upper}"
    st.caption(f"Level do dự án gán cho mapping: {label}; đọc tài liệu không chứng nhận đã đạt Level.")
    scope = resource.get("scope_granularity")
    locator = resource.get("evidence_locator")
    if not has_granular_level_evidence(resource):
        st.warning(
            "Chưa xác định đủ bài học/mục cụ thể và dẫn chứng để xác nhận mapping đúng Level. "
            "Hãy dùng liên kết này như tài liệu tham khảo; không tính là đã phủ yêu cầu nghề."
        )
    else:
        st.caption(f"Đơn vị nội dung: {scope} · Vị trí đối chiếu nội bộ: {locator}")
        st.caption("Phạm vi và Level của đơn vị này vẫn cần chủ dự án/chuyên gia xác nhận độc lập.")
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
    st.subheader("Lộ trình theo giai đoạn")
    st.caption("Các giai đoạn thể hiện thứ tự ưu tiên theo trọng số vị trí, không cam kết thời gian hoàn thành. Chỉ đề xuất mapping đã review nội dung; partial luôn kèm ghi chú phạm vi. Lộ trình này chưa lập lịch theo giờ hoặc level.")
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
                details = [resource.get(key) for key in ("provider", "type", "language", "cost")]
                st.caption(" · ".join(str(item) for item in details if item))
                _render_resource_level_scope(resource, target_levels)
                status = resource.get("content_review_status", "unreviewed")
                st.caption("Trạng thái nội dung: " + resource_review_label(status))
                if status == "partial" and resource.get("review_note"):
                    st.warning("Phạm vi review một phần: " + resource["review_note"])
                    _render_partial_practice_assignments(
                        resource.get("skills", []), resource,
                        role_context=role_context, resources=load_resources(),
                    )
                for skill in resource.get("skills", []):
                    caution = skill_scope_caution(skill)
                    if caution:
                        st.warning(caution)
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
                    st.info(f"{display_skill(issue['skill'])}: {label}")
                    caution = skill_scope_caution(issue["skill"])
                    if caution:
                        st.warning(caution)
                    reasons = [
                        RESOURCE_REASON_LABELS.get(reason, reason)
                        for reason in (issue.get("exclusion_reasons") or [])
                        if isinstance(reason, str) and reason
                    ]
                    if reasons:
                        st.caption("Các lý do loại tài liệu: " + " ".join(reasons))


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
                if item.get("warning"):
                    st.caption("Có phần cần xem lại phạm vi hoặc dữ liệu")
                else:
                    st.caption("Có học liệu đã qua review")
            column_index += 1
            if index < len(row) - 1:
                with columns[column_index]:
                    st.markdown("→")
                column_index += 1


def _render_practice_routes(routes: list[dict]) -> None:
    if not routes:
        return
    st.markdown("**Luyện kỹ năng qua công việc và phản hồi**")
    st.caption("Với kỹ năng mềm, thực hành có quan sát và phản hồi là một lộ trình chính; không cần hoàn thành khóa học để được xem là tiến bộ. Bài tập do dự án biên soạn, chưa phải chứng nhận năng lực hay review chuyên gia.")
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


def _render_resource_quality_disclosure(resources: dict) -> dict:
    summary = summarize_resource_reviews(resources)
    st.caption(
        f"Kiểm kê mapping kỹ năng–học liệu riêng: {summary['mapping_count']} mapping; "
        f"{summary['reviewed']} reviewed, {summary['partial']} partial, "
        f"{summary['unsuitable']} unsuitable, {summary['blocked']} blocked, "
        f"{summary['unreviewed']} unreviewed."
    )
    st.warning(
        "Đây là rà soát nội bộ về nội dung và phạm vi mapping, không phải review độc lập "
        "bởi chuyên gia nghề nghiệp hoặc pháp lý. Số liệu này không bao gồm ngân hàng câu hỏi phỏng vấn."
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
    """Ask first; show answer guidance after submission without automatic scoring."""
    role_id = position["id"]
    st.subheader("Luyện phỏng vấn")
    st.caption("Hệ thống không chấm điểm câu trả lời. Sau khi gửi, bạn sẽ thấy khung tham khảo và checklist tự rà soát; tình huống thực tế không có một đáp án chung.")
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
                if answer.strip():
                    session.setdefault("submitted_answers", {})[question_id] = answer.strip()
                    for review_key, _ in INTERVIEW_SELF_REVIEW:
                        st.session_state.pop(f"self_review_{session['batch_id']}_{question_id}_{review_key}", None)
                    answered.add(question_id)
                    session["answered_ids"] = list(answered)
                    st.session_state["interview_session"] = session
                else:
                    st.warning("Hãy nhập câu trả lời trước khi xem ý tham khảo.")
            if question_id in answered:
                st.caption(POST_SUBMISSION_GUIDANCE_NOTICE)
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
