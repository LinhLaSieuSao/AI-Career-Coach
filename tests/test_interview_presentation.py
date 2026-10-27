"""Coverage for the interview presentation and its truthful method notices."""

import pytest
from streamlit.testing.v1 import AppTest


def start(role="data_analyst"):
    return AppTest.from_string(
        f"from app import render_interview_practice\nrender_interview_practice({{'id': {role!r}}})",
        default_timeout=20,
    ).run()


def markdown(app):
    return "\n".join(item.value for item in app.markdown)


def submit(app, answer):
    app.text_area[0].input(answer)
    next(button for button in app.button if button.label == "Gửi câu trả lời").click().run()
    return app


@pytest.mark.parametrize("role", ["sales_executive", "frontend_developer_react", "data_analyst", "backend_developer_java"])
def test_real_demo_roles_show_question_status_and_empty_answer(role):
    app = start(role)
    app.button(key=f"start_interview_{role}").click().run()
    assert not app.exception
    assert "Trạng thái nội dung:" in markdown(app)
    assert "Chưa duyệt nội dung" in markdown(app)
    assert "Nhóm câu hỏi:" in " ".join(c.value for c in app.caption)
    submit(app, "  ")
    assert any("Hãy nhập câu trả lời" in item.value for item in app.error)
    assert not app.session_state["interview_session"]["answered_ids"]


@pytest.mark.parametrize("met_count", [0, 3])
def test_offline_results_render_each_criterion_and_accurate_notice(monkeypatch, met_count):
    import modules
    def review(question_id, answer, **kwargs):
        return {"source": "offline_rubric", "score": met_count * 10 / 3,
                "criteria": [{"point": f"Ý thứ {i}; chi tiết.", "met": i <= met_count, "evidence": ""} for i in range(1, 4)],
                "red_flags_hit": [], "feedback": "", "improvement": "ignored", "fallback_reason": "no_key"}
    monkeypatch.setattr(modules, "review_answer", review)
    app = start()
    app.button(key="start_interview_data_analyst").click().run()
    submit(app, "Câu trả lời để kiểm tra giao diện.")
    assert not app.exception
    text = markdown(app)
    assert f"{met_count}/3 ý trong tiêu chí chấm" in text
    assert text.count("Đã thấy:") == met_count
    assert text.count("Chưa thấy:") == 3 - met_count
    if not met_count:
        assert "- Ý thứ 1; chi tiết." in text
        assert ".;" not in text and "chi tiết.." not in text
    else:
        assert "thêm ví dụ hoặc kết quả thực tế" in text
    warning = app.warning[0].value
    assert "không dùng AI" in warning and "chưa qua duyệt chuyên môn" in warning


def test_ai_and_fallback_notices_follow_actual_result(monkeypatch):
    import modules
    def review(question_id, answer, **kwargs):
        is_ai = bool(kwargs.get("api_key"))
        return {"source": "llm" if is_ai else "offline_rubric", "score": 0,
                "criteria": [], "red_flags_hit": [], "feedback": "Nhận xét AI",
                "improvement": "Nêu thêm ví dụ.", "model": "test" if is_ai else None,
                "fallback_reason": None if is_ai else "timeout"}
    monkeypatch.setattr(modules, "review_answer", review)
    app = start()
    app.radio(key="interview_review_mode").set_value("Nhận góp ý từ AI").run()
    app.text_input(key="llm_cfg_api_key").input("key-thu").run()
    app.button(key="start_interview_data_analyst").click().run()
    submit(app, "Câu trả lời để kiểm tra.")
    assert not app.exception
    assert "Nhận xét được tạo bằng dịch vụ AI" in app.warning[0].value
    assert "Nêu thêm ví dụ." in markdown(app)
    monkeypatch.setattr(modules, "review_answer", lambda *args, **kwargs: review(*args, api_key="", **{k:v for k,v in kwargs.items() if k != "api_key"}))
    submit(app, "Câu trả lời để kiểm tra lần nữa.")
    assert "không dùng AI" in app.warning[0].value
    assert any("Chưa nhận được góp ý từ AI" in item.value for item in app.info)


def test_no_questions_shows_message_without_input(monkeypatch):
    import app as application
    monkeypatch.setattr(application, "get_questions", lambda *args, **kwargs: [])
    app = start()
    assert not app.exception
    assert any("Chưa có câu hỏi" in item.value for item in app.info)
    assert not app.number_input
