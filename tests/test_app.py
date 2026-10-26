"""Exercise the actual Streamlit script and its core-module handoffs."""

import importlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import modules
from modules.catalog import DATA_DIR, load_roles
from modules.matcher import match_role
from modules.profile import build_profile_from_cv
from modules.recommender import build_roadmap
from modules.submission import PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE, SUBMISSION_REQUIRED_INPUT_MESSAGE
from document_fixtures import docx_bytes, pdf_bytes


ROOT = Path(__file__).resolve().parents[1]


def _start():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    return app


def _field(app, label):
    return next(field for field in app.text_area if field.label == label or field.label.startswith(label + " (*)"))


def _draft(app, skills="", role_id="data_analyst", jd=""):
    if app.session_state.get("profile_step", 1) != 2:
        _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input(skills)
        _field(app, "Mô tả công việc cần đối chiếu (không bắt buộc)").input(jd)
        app.selectbox[0].select(role_id)
        next(button for button in app.button if button.label == "Tiếp tục rà soát hồ sơ").click().run()
        assert not app.exception
    return app


def _submit(app, skills="", role_id="data_analyst", jd="", levels=None):
    app = _draft(app, skills, role_id, jd)
    if app.session_state.get("profile_step") == 2:
        for skill, value in (levels or {}).items():
            next(box for box in app.selectbox if box.label == f"Level · {skill}").select(value)
        next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()
        assert not app.exception
    return app


def _metric(app, label):
    return next(metric.value for metric in app.metric if metric.label == label)


def _markdown(app):
    return "\n".join(item.value for item in app.markdown)


def _upload(app, text):
    # Streamlit 1.66 supports the uploader directly; exercise the real widget
    # deserializer, parser, and controller instead of patching st.file_uploader.
    app.file_uploader[0].set_value(("resume.docx", docx_bytes(text), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    return app


def test_app_import_and_real_loader_from_another_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app_module = importlib.import_module("app")
    app_module.load_positions.clear()
    positions = app_module.load_positions()
    raw = load_roles()
    assert len(positions) == len(raw) == 131
    assert {role["id"]: role["skills"] for role in positions} == {
        role["id"]: role["skills"] for role in raw
    }
    assert callable(app_module.run_app)
    app_module.load_positions.clear()


def test_streamlit_startup_loads_all_real_roles_without_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = _start()
    assert len(app.selectbox[0].options) == len(load_roles()) == 131
    assert app.selectbox[0].value is None
    assert not app.error
    assert len(app.get("file_uploader")) == 1
    assert any("document.documentElement.lang = 'vi'" in item.value for item in app.html)


def test_high_risk_role_disclosure_appears_before_results() -> None:
    app = _submit(_start(), "kế toán thuế", role_id="tax_accountant")
    assert not app.exception
    assert any("quy định hiện hành" in item.value for item in app.warning)


def test_user_can_clear_local_profile_and_results() -> None:
    app = _submit(_start(), "Python; SQL")
    assert app.session_state["profile_result"]
    next(button for button in app.button if button.label == "Xóa hồ sơ phiên này và bắt đầu lại").click().run()
    assert not app.exception
    assert "profile_result" not in app.session_state
    assert any(button.label == "Tiếp tục rà soát hồ sơ" for button in app.button)


def test_manual_profile_ui_uses_matcher_weights_and_roadmap_metadata(monkeypatch):
    calls = []
    match_calls = []

    def matcher_spy(skills, role):
        match_calls.append((list(skills), role))
        return match_role(skills, role)

    def roadmap_spy(missing, resources, weeks=4, *, missing_details=None):
        calls.append((missing, missing_details))
        return build_roadmap(missing, resources, weeks, missing_details=missing_details)

    monkeypatch.setattr(modules, "build_roadmap", roadmap_spy)
    monkeypatch.setattr(modules, "match_role", matcher_spy)
    app = _submit(_start(), "Python3; Custom Skill")
    profile = app.session_state["profile_result"]
    assert profile["skills"] == ["custom skill", "python"]
    assert profile["unrecognized_skills"] == ["custom skill"]
    role = next(role for role in load_roles() if role["id"] == "data_analyst")
    assert match_calls[-1] == (profile["skills"], role)
    expected = match_role(profile["skills"], role)
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == f"{expected['percent']}%"
    assert calls[-1] == (expected["missing"], expected["missing_details"])
    text = _markdown(app)
    assert any(exp.label == "Cách đọc và hiểu đúng điểm số gợi ý" for exp in app.expander)
    assert "Role-IDF" in text and "75% skill fit" in text and "5/100" in text
    assert any("chưa thuộc catalog" in item.value for item in app.warning)
    assert "**Kỹ năng khớp vị trí:** python" in text
    for skill in expected["missing"]:
        assert skill in text
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    expected_roadmap = build_roadmap(expected["missing"], resources, missing_details=expected["missing_details"])
    expander_labels = [exp.label for exp in app.expander]
    assert [label for label in expander_labels if label.startswith("Giai đoạn ")] == [
        f"Giai đoạn {week['week']} · {', '.join(week['skills'])}" for week in expected_roadmap
    ]
    assert any(item.value == "Lộ trình theo giai đoạn" for item in app.subheader)
    assert any("không cam kết thời gian hoàn thành" in item.value for item in app.caption)
    assert any("Luyện qua nhiệm vụ và phản hồi" in label for label in expander_labels)
    # Unknown claims stay available by default and can be excluded explicitly.
    assert app.checkbox[0].value is True
    app.checkbox[0].uncheck().run()
    assert not app.exception
    assert match_calls[-1][0] == ["python"]
    assert "custom skill" not in next(item.value for item in app.markdown if item.value.startswith("**Kỹ năng:**"))


@pytest.mark.parametrize("skills", ["", "SQL; Custom Skill; Python"])
def test_uploaded_cv_and_form_reach_profile_and_role_results(skills):
    cv_text = "Python3 and Node.js developer"
    app = _submit(_upload(_start(), cv_text), skills)
    expected_profile = build_profile_from_cv(
        {"skills": skills}, cv_text, include_source_metadata=True
    )
    assert app.session_state["profile_result"] == expected_profile
    assert "python" in expected_profile["skills"]
    assert "nodejs" in expected_profile["skills"]
    role = next(role for role in load_roles() if role["id"] == "data_analyst")
    expected = match_role(expected_profile["skills"], role)
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == f"{expected['percent']}%"
    assert not app.error


def test_cv_jd_ui_shows_skill_percent_matched_and_missing():
    cv_text = "Python developer"
    jd_text = "Python and SQL"
    app = _submit(_upload(_start(), cv_text), skills="SQL", jd=jd_text)
    result = app.session_state["cv_jd_result"]
    assert result["method"] == "confirmed_categorized_skill_overlap"
    assert result["overall_percent"] is None
    assert result["candidate_skills"] == ["python", "sql"]
    assert result["matched"] == ["python", "sql"] and result["missing"] == []
    assert _metric(app, "Trùng kỹ năng chưa phân loại") == "100.0%"
    text = _markdown(app)
    assert "**Trùng kỹ năng chưa phân loại khớp hồ sơ:**" in text
    assert "**Trùng kỹ năng chưa phân loại chưa có trong hồ sơ:** Không có" in text
    assert "confirmed_categorized_skill_overlap" not in text
    assert not app.error
    # A new submission must clear the previous result when extraction/JD fails.
    app = _submit(app, "Python", jd="no known skills here")
    assert app.session_state["cv_jd_result"] is None
    assert any("Không nhận diện được kỹ năng" in item.value for item in app.warning)
    assert app.session_state["profile_result"]["skills"] == ["python"]


def test_cv_jd_ui_separates_must_have_and_nice_to_have_coverage():
    app = _submit(
        _start(),
        skills="Python",
        jd="Yêu cầu bắt buộc:\nPython\nSQL\nƯu tiên:\nDocker",
    )

    result = app.session_state["cv_jd_result"]
    assert result["must_have"]["matched"] == ["python"]
    assert result["must_have"]["missing"] == ["sql"]
    assert result["nice_to_have"]["missing"] == ["docker"]
    assert result["overall_percent"] == 42.5
    assert _metric(app, "Bao phủ kỹ năng bắt buộc") == "50.0%"
    assert _metric(app, "Bao phủ kỹ năng ưu tiên") == "0.0%"


def test_user_can_reject_all_extracted_jd_skills_without_getting_a_fake_comparison():
    app = _draft(_upload(_start(), "Python developer"), skills="SQL", jd="Python and SQL")
    for label in (
        "Kỹ năng JD bắt buộc",
        "Kỹ năng JD ưu tiên / điểm cộng",
        "Kỹ năng JD chưa phân loại · không tính điểm tổng hợp",
    ):
        next(item for item in app.multiselect if item.label == label).set_value([])
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()

    assert not app.exception
    assert app.session_state["cv_jd_result"] is None
    assert app.session_state["jd_provided"] is True
    assert any("Chưa xác nhận kỹ năng nào từ JD" in warning.value for warning in app.warning)
    assert any("chưa tạo được kết quả đối chiếu JD" in info.value for info in app.info)


def test_jd_skill_cannot_be_confirmed_in_multiple_categories():
    app = _draft(_start(), skills="Python", jd="Yêu cầu bắt buộc:\nPython")
    next(item for item in app.multiselect if item.label == "Kỹ năng JD ưu tiên / điểm cộng").set_value(["python"])
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()

    assert not app.exception
    assert app.session_state["profile_step"] == 2
    assert "profile_result" not in app.session_state or app.session_state["profile_result"] is None
    assert any("đang nằm ở cả" in error.value for error in app.error)


def test_user_can_return_to_step_one_and_replace_the_draft():
    app = _draft(_start(), skills="Python")
    next(button for button in app.button if button.label == "Quay lại chỉnh đầu vào").click().run()
    assert app.session_state["profile_step"] == 1
    app = _submit(app, "SQL")

    assert app.session_state["profile_result"]["skills"] == ["sql"]
    assert app.session_state["profile_revision"] == 1


def test_jd_without_cv_requests_upload_and_still_keeps_form_profile():
    app = _submit(_start(), "Python", jd="SQL")
    assert app.session_state["profile_result"]["skills"] == ["python"]
    assert app.session_state["cv_jd_result"]["missing"] == ["sql"]


def test_invalid_upload_preserves_manual_profile_and_reports_extraction_error():
    app = _start()
    app.file_uploader[0].set_value(("broken.docx", b"not a DOCX", "application/octet-stream"))
    app = _submit(app, "Python; Unknown Skill")
    assert any("không khớp phần mở rộng" in item.value for item in app.warning)
    assert app.session_state["submission_warnings"]
    assert app.session_state["cv_extraction"] is None
    assert app.session_state["profile_result"]["skills"] == ["python", "unknown skill"]
    assert app.session_state["profile_result"]["unrecognized_skills"] == ["unknown skill"]


def test_complete_role_skills_show_full_match_without_roadmap():
    role = next(role for role in load_roles() if role["id"] == "data_analyst")
    app = _submit(_start(), ";".join(skill["name"] for skill in role["skills"]))
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == "100.0%"
    assert any("đã có đủ" in item.value for item in app.success)
    assert not any(exp.label.startswith("Giai đoạn ") for exp in app.expander)


def test_roadmap_ui_resolves_previous_week_document_and_only_flags_actual_gaps():
    shared = {
        "id": "shared", "title": "Shared tutorial", "url": "https://example.org/shared",
        "verified": True, "content_review_status": "reviewed",
        "review_note": "Covers the shared learning outcome.",
    }
    resources = {skill: {"resources": [shared]} for skill in ("python", "sql")}
    roadmap = build_roadmap(["python", "sql", "unknown"], resources, weeks=3)
    assert roadmap[1]["resources"] == []
    assert roadmap[1]["resource_keys"]["sql"]
    app = AppTest.from_string(
        f"from app import render_roadmap\nrender_roadmap({roadmap!r})", default_timeout=20
    ).run()
    assert not app.exception
    assert "sql: [Shared tutorial](https://example.org/shared) (đã giới thiệu ở giai đoạn 1)" in _markdown(app)
    assert [item.value for item in app.info] == ["unknown: Chưa có tài liệu được xác minh cho kỹ năng này."]


def test_roadmap_ui_does_not_link_unreviewed_material_and_explains_the_gap():
    resources = {"sql": {"resources": [{
        "id": "sql_unreviewed", "title": "Unreviewed SQL resource",
        "url": "https://example.org/unreviewed-sql", "verified": True,
        "content_review_status": "unreviewed",
    }]}}
    roadmap = build_roadmap(["sql"], resources)
    assert roadmap[0]["resources"] == []
    assert roadmap[0]["skills_without_resources"] == ["sql"]
    app = AppTest.from_string(
        f"from app import render_roadmap\nrender_roadmap({roadmap!r})", default_timeout=20
    ).run()

    assert not app.exception
    assert any("Chưa có tài liệu được review nội dung" in item.value for item in app.info)
    assert "https://example.org/unreviewed-sql" not in _markdown(app)


def test_presence_roadmap_discloses_resource_level_below_role_requirement():
    resources = {"c#": {"resources": [{
        "id": "csharp_intro", "title": "C# introduction", "url": "https://example.org/csharp",
        "verified": True, "content_review_status": "reviewed", "review_note": "Introduction only.",
        "level_from": 1, "level_to": 1,
    }]}}
    roadmap = build_roadmap(["c#"], resources)
    app = AppTest.from_string(
        f"from app import render_roadmap\nrender_roadmap({roadmap!r}, target_levels={{'c#': 3}})",
        default_timeout=20,
    ).run()
    assert not app.exception
    assert any("Level do dự án gán cho mapping: Level 1" in item.value for item in app.caption)
    assert any("Chưa xác định đủ bài học/mục cụ thể" in item.value for item in app.warning)
    assert any("cần Level 3" in item.value for item in app.info)


def test_interview_ui_can_create_questions_for_selected_real_role():
    app = _submit(_start(), "Python")
    app.button(key="start_interview_data_analyst").click().run()
    assert not app.exception
    questions = app.session_state["interview_session"]["questions"]
    assert len(questions) == 3
    assert all(question["role_id"] == "data_analyst" for question in questions)


@pytest.mark.parametrize("count_kind", ["minimum", "available_maximum"])
def test_user_can_choose_an_interview_count_within_real_question_bank(count_kind):
    app = _submit(_start(), "Python")
    available = len(modules.get_questions("data_analyst", 10, seed=0))
    widget = next(item for item in app.number_input if item.label == f"Số câu hỏi (tối đa {available} câu có sẵn)")
    assert widget.proto.min == 1 and widget.proto.max == available
    count = 1 if count_kind == "minimum" else available
    widget.set_value(count)
    app.button(key="start_interview_data_analyst").click().run()

    questions = app.session_state["interview_session"]["questions"]
    assert not app.exception
    assert len(questions) == count
    assert len({question["id"] for question in questions}) == len(questions)
    assert "scores" not in app.session_state["interview_session"]


@pytest.mark.parametrize("skills", ["", " ,; \n ", "interest: games"])
def test_empty_or_interest_only_form_cannot_create_results(skills):
    app = _start()
    _field(app, "Sở thích nghề nghiệp").input("AI")
    _field(app, "Kinh nghiệm (không bắt buộc)").input("Developer")
    app = _submit(app, skills, role_id=None)
    assert "profile_result" not in app.session_state
    assert "ít nhất một kỹ năng" in app.error[0].value
    assert not app.metric
    assert not app.expander
    assert not app.number_input


def test_jd_only_cannot_create_profile_or_report_scan():
    app = _submit(_start(), role_id=None, jd="Python")
    assert "profile_result" not in app.session_state
    assert len(app.error) == 1
    assert app.error[0].value == SUBMISSION_REQUIRED_INPUT_MESSAGE
    assert "ảnh" not in app.error[0].value
    assert not app.metric


def test_profile_without_role_is_saved_until_explicit_role_selection():
    app = _submit(_start(), "JS", role_id=None)
    assert app.session_state["profile_result"]["skills"] == ["javascript"]
    assert app.session_state["career_role_id"] is None
    assert not app.metric
    assert not app.number_input
    assert "Hãy chọn vị trí" in app.info[0].value
    app = _submit(app, "JS", role_id="backend_developer_nodejs")
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == f"{match_role(['javascript'], next(r for r in load_roles() if r['id']=='backend_developer_nodejs'))['percent']}%"
    assert {item.label for item in app.get("download_button")} >= {
        "Tải báo cáo Markdown", "Tải báo cáo CSV"
    }


def test_cv_jd_without_role_can_compare_but_cannot_show_role_recommendations():
    app = _submit(_upload(_start(), "Python"), role_id=None, jd="Python SQL")
    assert app.session_state["profile_result"]["skills"] == ["python"]
    assert _metric(app, "Trùng kỹ năng chưa phân loại") == "50.0%"
    assert len(app.metric) == 3
    assert not app.number_input


@pytest.mark.parametrize("name,content,message", [
    ("broken.pdf", b"broken PDF", "không khớp phần mở rộng"),
    ("blank.pdf", pdf_bytes(), "không có văn bản"),
    ("drawing.pdf", pdf_bytes(vector=True), "không có văn bản"),
    ("image.pdf", pdf_bytes(image=True), "trang ảnh"),
    ("blank.docx", docx_bytes(), "không có văn bản"),
    ("zero.docx", b"", "không có văn bản"),
], ids=["broken-pdf", "blank-pdf", "vector-pdf", "image-pdf", "blank-docx", "zero-byte"])
def test_upload_widget_reports_parser_errors_without_profile(name, content, message):
    app = _start()
    app.file_uploader[0].set_value((name, content, "application/octet-stream"))
    app = _submit(app, role_id=None)
    assert "profile_result" not in app.session_state
    assert message in app.error[0].value
    assert not app.metric
    if name != "image.pdf":
        assert "trang ảnh" not in app.error[0].value


def test_user_removing_all_cv_skills_does_not_create_a_role_assessment():
    app = _draft(_upload(_start(), "Python developer"))
    next(item for item in app.multiselect if item.label.startswith("Kỹ năng nhận diện")).set_value([])
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()

    assert not app.exception
    assert app.session_state["profile_step"] == 2
    assert "profile_result" not in app.session_state or app.session_state["profile_result"] is None
    assert any(PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE in item.value for item in app.error)
    assert any("Cách xử lý:" in item.value for item in app.info)
    assert not app.metric and not app.number_input


def test_step_two_summarizes_catalog_and_review_counts_without_claiming_all_are_auto_detected():
    app = _draft(_start(), "Python; Custom Skill")
    message = next(item.value for item in app.info if item.value.startswith("Hồ sơ có"))

    assert "**2** kỹ năng" in message
    assert "**1** khớp catalog" in message
    assert "**1** tên cần bạn rà soát" in message
    assert "nhận diện tự động" not in message


def test_user_is_told_when_only_the_first_ten_pdf_pages_were_read():
    app = _start()
    app.file_uploader[0].set_value(("eleven-pages.pdf", pdf_bytes("Python developer", pages=11), "application/pdf"))
    app = _draft(app, role_id=None)
    assert any("11 trang" in warning.value and "10 trang đầu" in warning.value for warning in app.warning)
    assert app.session_state["profile_draft"]["document"]["pages_read"] == 10
    assert app.session_state["profile_draft"]["document"]["page_truncated"] is True
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()

    assert not app.exception
    assert any("11 trang" in warning.value and "10 trang đầu" in warning.value for warning in app.warning)
    assert app.session_state["cv_extraction"] is not None


def test_failed_new_submission_keeps_saved_profile_role_cv_and_comparison():
    app = _submit(_upload(_start(), "Python"), "SQL", jd="Python SQL")
    saved = {key: app.session_state[key] for key in ("profile_result", "career_role_id", "cv_extraction", "cv_jd_result", "profile_revision")}
    app.file_uploader[0].set_value(("broken.pdf", b"broken", "application/pdf"))
    app = _submit(app, role_id=None)
    assert {key: app.session_state[key] for key in saved} == saved
    assert "không khớp phần mở rộng" in app.error[0].value
    assert any("đang giữ hồ sơ đã lưu trước đó" in item.value.casefold() for item in app.warning)
    assert _metric(app, "Trùng kỹ năng chưa phân loại") == "100.0%"
    # A corrected draft replaces the complete snapshot and removes old errors.
    app.file_uploader[0].clear()
    app = _submit(app, "JS", role_id=None)
    assert app.session_state["profile_revision"] == saved["profile_revision"] + 1
    assert app.session_state["profile_result"]["skills"] == ["javascript"]
    assert app.session_state["cv_jd_result"] is None
    assert app.session_state["cv_extraction"] is None
    assert not app.error
    assert not any("broken" in item.value.casefold() or "đang giữ hồ sơ đã lưu trước đó" in item.value.casefold()
                   for item in app.warning)
    assert not app.metric


def test_valid_cv_without_recognized_skills_does_not_fabricate_role_results():
    app = _draft(_upload(_start(), "No catalog terms here"))
    assert app.session_state["profile_step"] == 2
    assert app.session_state["profile_draft"]["profile"]["skills"] == []
    assert not app.number_input
    assert app.session_state.get("profile_result") is None


def test_undo_repeated_moves_reruns_without_stale_messages_or_checkbox_resets():
    app = _submit(_start(), "Python; ZZZ; interest: Node.js; interest: AAA", role_id=None)
    app.checkbox[0].uncheck().run()  # Keep the user's exclusion through undo.
    assert app.checkbox[0].label == "Giữ ‘zzz’ trong hồ sơ"
    undo = lambda: next(button for button in app.button if button.label == "Hoàn tác")
    undo().click().run()
    assert not app.exception
    assert app.session_state["profile_result"]["skills"] == ["nodejs", "python", "zzz"]
    assert len(app.session_state["profile_result"]["moved"]) == 1
    assert not any("Node.js" in item.value for item in app.info)
    assert app.checkbox[0].value is False
    undo().click().run()
    assert not app.exception
    profile = app.session_state["profile_result"]
    assert profile["moved"] == []
    assert profile["interests"] == ["AAA", "Node.js"]
    assert profile["unrecognized_skills"] == ["aaa", "zzz"]
    assert not any("Đã chuyển" in item.value for item in app.info)
    assert {checkbox.label: checkbox.value for checkbox in app.checkbox} == {
        "Giữ ‘aaa’ trong hồ sơ": True, "Giữ ‘zzz’ trong hồ sơ": False,
    }
    assert not any(button.label == "Hoàn tác" for button in app.button)
    # A fresh accepted profile gets fresh unknown controls, with no old moves.
    app = _submit(app, "ZZZ; English", role_id=None)
    assert app.checkbox[0].value is True
    assert app.session_state["profile_result"]["skills"] == ["english", "zzz"]
    assert app.session_state["profile_result"]["moved"] == []


def test_new_profile_resets_prior_interview_session_and_answer_widgets():
    app = _submit(_start(), "Python")
    app.button(key="start_interview_data_analyst").click().run()
    assert "interview_session" in app.session_state
    _field(app, "Câu trả lời của bạn").input("Previous answer")
    app = _submit(app, "SQL")
    assert "interview_session" not in app.session_state
    assert not any(field.label == "Câu trả lời của bạn" for field in app.text_area)
