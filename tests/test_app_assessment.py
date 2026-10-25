from streamlit.testing.v1 import AppTest

import modules
from modules import build_timed_roadmap, compute_gap, get_questions, match_role
from modules.catalog import load_roles
from modules.interview import _question_for_id
from test_app import _start, _submit, _field, _metric, _markdown, _upload
from test_timed_roadmap import gap, catalog, resource


def test_level_mode_requires_explicit_consent_and_calls_core_without_inferring_cv(monkeypatch):
    calls = []
    focus_calls = []
    def spy(levels, role):
        calls.append((levels, role))
        return compute_gap(levels, role)
    monkeypatch.setattr(modules, "compute_gap", spy)
    def question_spy(role_id, n=5, seed=None, focus_skills=None):
        focus_calls.append(focus_skills)
        return get_questions(role_id, n, 14, focus_skills)
    monkeypatch.setattr(modules, "get_questions", question_spy)
    app = _upload(_start(), "Python developer")
    _field(app, "Level tự khai báo (JSON, không bắt buộc)").input('{"SQL": 1}')
    app = _submit(app)
    profile = app.session_state["profile_result"]
    assert profile["levels"] == {"sql": 1} and profile["skills"] == ["python", "sql"]
    role = next(r for r in load_roles() if r["id"] == "data_analyst")
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == f"{match_role(profile['skills'], role)['percent']}%"
    app.radio[0].set_value("Theo level tự khai báo").run()
    assert not app.exception and not calls
    assert not app.metric
    assert any("current=0" in info.value for info in app.info)
    next(c for c in app.checkbox if c.label.startswith("Tôi đồng ý")).check().run()
    assert not app.exception
    assert calls[-1][0] == {"sql": 1}
    expected = compute_gap({"sql": 1}, role)
    assert _metric(app, "Mức độ đáp ứng theo level") == f"{expected['match_percent']}%"
    assert _metric(app, "Số tuần toàn lộ trình") == "Chưa xác định"
    assert app.dataframe and any("chưa" in w.value.lower() or "thiếu" in w.value.lower() for w in app.warning)
    assert profile["levels"] == {"sql": 1}
    app.button(key="start_interview_data_analyst").click().run()
    assert not app.exception
    assert focus_calls[-1] == expected["missing"] and "sql" in focus_calls[-1]


def test_level_form_errors_preserve_last_accepted_snapshot():
    app = _submit(_start(), "SQL")
    saved = app.session_state["profile_result"]
    revision = app.session_state["profile_revision"]
    for invalid in ('{"SQL": true}', '{broken', '{"JS":1,"javascript":2}', '{"SQL":1,"SQL":2}'):
        _field(app, "Level tự khai báo (JSON, không bắt buộc)").input(invalid)
        app = _submit(app, "Python")
        assert app.session_state["profile_result"] == saved
        assert app.session_state["profile_revision"] == revision
        assert app.error and app.warning
    _field(app, "Level tự khai báo (JSON, không bắt buộc)").input('{"Python3":2}')
    app = _submit(app, "Python")
    assert app.session_state["profile_result"]["levels"] == {"python": 2}
    assert not app.error


def test_role_suggestions_require_explicit_selection_and_show_explanations():
    app = _submit(_start(), "Java; Spring Boot", role_id=None)
    assert app.session_state["career_role_id"] is None and not app.metric
    assert "không là xác suất tuyển dụng" in " ".join(c.value for c in app.caption)
    choices = [b for b in app.button if b.key and b.key.startswith("choose_role_")]
    assert choices and "Kỹ năng trùng" in " ".join(c.value for c in app.caption)
    chosen_id = choices[0].key.split("_", 3)[-1]
    choices[0].click().run()
    assert not app.exception
    assert app.session_state["career_role_id"] == chosen_id
    assert app.selectbox[0].value == chosen_id
    assert app.metric
    _field(app, "Kỹ năng").input("Java; SQL")
    next(b for b in app.button if b.label == "Tạo hồ sơ nghề nghiệp").click().run()
    assert not app.exception and app.session_state["career_role_id"] == chosen_id


def _interview_with_single_gap(monkeypatch, skill):
    def seeded(role_id, n=5, seed=None, focus_skills=None):
        return get_questions(role_id, n, 14, focus_skills)
    monkeypatch.setattr(modules, "get_questions", seeded)
    role = next(r for r in load_roles() if r["id"] == "data_analyst")
    skills = ";".join(s["name"] for s in role["skills"] if s["name"] != skill)
    app = _submit(_start(), skills)
    app.button(key="start_interview_data_analyst").click().run()
    assert not app.exception
    return app


def test_interview_focus_privacy_empty_answer_and_scoring_after_submission(monkeypatch):
    app = _interview_with_single_gap(monkeypatch, "sql")
    questions = app.session_state["interview_session"]["questions"]
    assert questions[0]["skill"] == "sql"
    assert "Đáp án mẫu tham khảo" not in _markdown(app)
    assert "Điểm rubric:" not in _markdown(app)
    buttons = lambda: [b for b in app.button if b.label == "Gửi câu trả lời"]
    buttons()[0].click().run()
    assert app.warning and app.session_state["interview_session"]["scores"] == {}
    q = _question_for_id(questions[0]["id"])
    _field(app, "Câu trả lời của bạn").input(q["reference_answer"])
    buttons()[0].click().run()
    assert not app.exception
    assert "**Điểm rubric:** 10/10" in _markdown(app)
    assert "Đáp án mẫu tham khảo" in _markdown(app)
    assert "không xác minh" in " ".join(c.value for c in app.caption)
    _field(app, "Câu trả lời của bạn").input("Nội dung không liên quan")
    buttons()[0].click().run()
    assert "**Điểm rubric:** 0/10" in _markdown(app)
    app.radio[0].set_value("Theo level tự khai báo").run()
    assert "interview_session" not in app.session_state
    assert "Đáp án mẫu tham khảo" not in _markdown(app)


def test_template_answer_reveals_reference_after_submit_without_fake_zero(monkeypatch):
    app = _interview_with_single_gap(monkeypatch, "tư duy phân tích")
    assert app.session_state["interview_session"]["questions"][0]["quality"] == "template"
    _field(app, "Câu trả lời của bạn").input("Ví dụ thực tế theo STAR của tôi")
    next(b for b in app.button if b.label == "Gửi câu trả lời").click().run()
    assert not app.exception
    assert any("rubric chưa sẵn sàng" in i.value for i in app.info)
    assert "Đáp án mẫu tham khảo" in _markdown(app) and "Điểm rubric:" not in _markdown(app)


def test_demo_profile_button_populates_widgets_and_creates_labeled_synthetic_profile():
    app = _start()
    _field(app, "Mô tả công việc cần đối chiếu (không bắt buộc)").input("Old profile JD")
    import app as app_module
    assert app_module.RESULT_TABS == ("Tóm tắt", "Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn")
    assert not app.exception
    next(button for button in app.button if button.key == "use_demo_backend-java").click().run()
    assert not app.exception
    assert app.session_state["career_role_id"] == "backend_developer_java"
    assert app.session_state["active_demo_profile_id"] == "backend-java"
    assert app.session_state["profile_result"]["skills"]
    assert "Java" in _field(app, "Kỹ năng").value
    assert app.selectbox[0].value == "backend_developer_java"
    assert _field(app, "Mô tả công việc cần đối chiếu (không bắt buộc)").value == ""
    assert any("Hồ sơ tổng hợp minh họa" in item.value for item in app.info)
    assert not app.error


def test_role_change_and_profile_submit_replace_assessment_without_old_answers():
    app = _submit(_start(), "SQL; Python")
    app.button(key="start_interview_data_analyst").click().run()
    assert "interview_session" in app.session_state
    app.selectbox[0].select("backend_developer_java")
    app = _submit(app, "Java; Spring Boot", role_id="backend_developer_java")
    assert app.session_state["career_role_id"] == "backend_developer_java"
    assert "interview_session" not in app.session_state
    import app as app_module
    assert app_module.RESULT_TABS == ("Tóm tắt", "Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn")
    assert any(item.label == "Tải báo cáo Markdown" for item in app.get("download_button"))


def test_every_demo_profile_uses_a_real_role_and_builds_without_personal_claims():
    import app as app_module
    from modules.submission import prepare_submission

    roles = {role["id"] for role in load_roles()}
    demos = app_module.load_demo_profiles()
    assert len(demos) == 3
    for demo in demos:
        assert demo["synthetic"] is True
        assert demo["role_id"] in roles
        assert "người thật" in demo["notice"]
        candidate = prepare_submission(demo["profile"], None)
        assert candidate["accepted"]
        assert candidate["profile"]["skills"]


def test_timed_ui_can_show_complete_fixture_and_explicit_estimates():
    r = resource(hours=None, estimated_duration_hours=10, estimated_duration_basis="Two measured trial tasks at 5h")
    timed = build_timed_roadmap(gap(("sql", 1, 1)), catalog(sql=[r]), hours_per_week=4)
    app = AppTest.from_string(f"from app import render_timed_roadmap\nrender_timed_roadmap({timed!r})").run()
    assert not app.exception
    assert _metric(app, "Tổng giờ công bố đã chọn") == "0.00"
    assert _metric(app, "Giờ ước lượng biên tập") == "10.00"
    assert _metric(app, "Số tuần toàn lộ trình") == "3"
    assert len(app.expander) == 3
    assert any("ước lượng" in w.value for w in app.warning)
    assert "Two measured trial tasks" in " ".join(c.value for c in app.caption)
