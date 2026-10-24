"""Exercise the actual Streamlit script and its core-module handoffs."""

import importlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import modules
from modules.catalog import DATA_DIR, load_roles
from modules.matcher import match_cv_to_jd, match_role
from modules.profile import build_profile_from_cv
from modules.recommender import build_roadmap
from document_fixtures import docx_bytes, pdf_bytes


ROOT = Path(__file__).resolve().parents[1]


def _start():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    return app


def _field(app, label):
    return next(field for field in app.text_area if field.label == label)


def _submit(app, skills="", role_id="data_analyst", jd=""):
    _field(app, "Kỹ năng").input(skills)
    _field(app, "Mô tả công việc cần đối chiếu (không bắt buộc)").input(jd)
    app.selectbox[0].select(role_id)
    next(button for button in app.button if button.label == "Tạo hồ sơ nghề nghiệp").click().run()
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
    assert "**Kỹ năng khớp vị trí:** python" in text
    for skill in expected["missing"]:
        assert skill in text
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    expected_roadmap = build_roadmap(expected["missing"], resources, missing_details=expected["missing_details"])
    assert [exp.label for exp in app.expander] == [
        f"Tuần {week['week']} · {', '.join(week['skills'])}" for week in expected_roadmap
    ]
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
    expected_profile = build_profile_from_cv({"skills": skills}, cv_text)
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
    expected = match_cv_to_jd(cv_text, jd_text)
    assert app.session_state["cv_jd_result"] == expected
    assert _metric(app, "Mức độ phù hợp giữa CV và mô tả công việc") == "50.0%"
    text = _markdown(app)
    assert "**Kỹ năng CV khớp JD:** python" in text
    assert "**Kỹ năng JD còn thiếu trong CV:** sql" in text
    assert "độ tương đồng từ ngữ" not in text
    assert not app.error
    # A new submission must clear the previous result when extraction/JD fails.
    app = _submit(app, jd="no known skills here")
    assert app.session_state["cv_jd_result"] is None
    assert "Không nhận diện được kỹ năng" in app.error[0].value
    assert app.session_state["profile_result"]["skills"] == ["python"]


def test_jd_without_cv_requests_upload_and_still_keeps_form_profile():
    app = _submit(_start(), "Python", jd="SQL")
    assert "Hãy tải lên CV" in app.error[0].value
    assert app.session_state["profile_result"]["skills"] == ["python"]


def test_invalid_upload_preserves_manual_profile_and_reports_extraction_error():
    app = _start()
    app.file_uploader[0].set_value(("broken.docx", b"not a DOCX", "application/octet-stream"))
    app = _submit(app, "Python; Unknown Skill")
    assert "Không đọc được tệp" in app.error[0].value
    assert app.session_state["cv_extraction"] is None
    assert app.session_state["profile_result"]["skills"] == ["python", "unknown skill"]
    assert app.session_state["profile_result"]["unrecognized_skills"] == ["unknown skill"]


def test_complete_role_skills_show_full_match_without_roadmap():
    role = next(role for role in load_roles() if role["id"] == "data_analyst")
    app = _submit(_start(), ";".join(skill["name"] for skill in role["skills"]))
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == "100.0%"
    assert any("đã có đủ" in item.value for item in app.success)
    assert len(app.expander) == 0


def test_roadmap_ui_resolves_previous_week_document_and_only_flags_actual_gaps():
    shared = {"id": "shared", "title": "Shared tutorial", "url": "https://example.org/shared"}
    resources = {skill: {"resources": [shared]} for skill in ("python", "sql")}
    roadmap = build_roadmap(["python", "sql", "unknown"], resources, weeks=3)
    assert roadmap[1]["resources"] == []
    assert roadmap[1]["resource_keys"]["sql"]
    app = AppTest.from_string(
        f"from app import render_roadmap\nrender_roadmap({roadmap!r})", default_timeout=20
    ).run()
    assert not app.exception
    assert "sql: [Shared tutorial](https://example.org/shared) (đã giới thiệu ở tuần 1)" in _markdown(app)
    assert [item.value for item in app.info] == ["Chưa có tài liệu cho: unknown"]


def test_interview_ui_can_create_questions_for_selected_real_role():
    app = _submit(_start(), "Python")
    app.button(key="start_interview_data_analyst").click().run()
    assert not app.exception
    questions = app.session_state["interview_session"]["questions"]
    assert len(questions) == 3
    assert all(question["role_id"] == "data_analyst" for question in questions)


@pytest.mark.parametrize("skills", ["", " ,; \n ", "interest: games"])
def test_empty_or_interest_only_form_cannot_create_results(skills):
    app = _start()
    _field(app, "Sở thích nghề nghiệp").input("AI")
    _field(app, "Kinh nghiệm").input("Developer")
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
    assert "Hãy tải lên CV" in app.error[0].value
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


def test_cv_jd_without_role_can_compare_but_cannot_show_role_recommendations():
    app = _submit(_upload(_start(), "Python"), role_id=None, jd="Python SQL")
    assert app.session_state["profile_result"]["skills"] == ["python"]
    assert _metric(app, "Mức độ phù hợp giữa CV và mô tả công việc") == "50.0%"
    assert len(app.metric) == 1
    assert not app.number_input


@pytest.mark.parametrize("name,content,message", [
    ("broken.pdf", b"broken PDF", "Không đọc được tệp"),
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


def test_failed_new_submission_keeps_saved_profile_role_cv_and_comparison():
    app = _submit(_upload(_start(), "Python"), "SQL", jd="Python SQL")
    saved = {key: app.session_state[key] for key in ("profile_result", "career_role_id", "cv_extraction", "cv_jd_result", "profile_revision")}
    app.file_uploader[0].set_value(("broken.pdf", b"broken", "application/pdf"))
    app = _submit(app, role_id=None)
    assert {key: app.session_state[key] for key in saved} == saved
    assert "Không đọc được tệp" in app.error[0].value
    assert "đã lưu trước đó" in app.warning[0].value
    assert _metric(app, "Mức độ phù hợp giữa CV và mô tả công việc") == "50.0%"
    # A corrected draft replaces the complete snapshot and removes old errors.
    app.file_uploader[0].clear()
    app = _submit(app, "JS", role_id=None)
    assert app.session_state["profile_revision"] == saved["profile_revision"] + 1
    assert app.session_state["profile_result"]["skills"] == ["javascript"]
    assert app.session_state["cv_jd_result"] is None
    assert app.session_state["cv_extraction"] is None
    assert not app.error
    assert not app.warning
    assert not app.metric


def test_valid_cv_without_recognized_skills_does_not_fabricate_role_results():
    app = _submit(_upload(_start(), "No catalog terms here"))
    assert app.session_state["profile_result"]["skills"] == []
    assert any("Chưa có kỹ năng để đối chiếu" in item.value for item in app.info)
    assert not app.metric
    assert not app.number_input


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
    assert profile["interests"] == []
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
