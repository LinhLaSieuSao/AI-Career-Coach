"""Interview answer guidance, bounded question data and review provenance."""

from collections import Counter
from copy import deepcopy

import pytest

import modules
from modules import interview
from modules.catalog import DATA_DIR


def question(qid, skill, kind="technical", quality="unreviewed"):
    return {"id": qid, "skill": skill, "type": kind, "question": "Question?", "level": 1,
            "weight": 1, "quality": quality, "reference_answer": "REFERENCE ANSWER",
            "good_answer_points": ["GOOD POINT"], "red_flags": ["RED FLAG"],
            "quality_note": "PRIVATE NOTE"}


@pytest.fixture
def bank(monkeypatch):
    questions = [question("other", "python"), question("focus1", "javascript"),
                 question("scenario", "giao tiếp", "scenario"), question("focus2", "javascript", "scenario")]
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": questions})
    monkeypatch.setattr(interview, "_role_id_by_name", lambda: {})
    return questions


def test_focus_alias_seed_and_backfill_no_repeat_or_private_metadata(bank):
    result = interview.get_questions("r", n=3, seed=14, focus_skills=["JS"])
    assert [q["skill"] for q in result[:2]] == ["javascript", "javascript"]
    assert result == interview.get_questions("r", 3, 14, ["javascript"])
    assert len({q["id"] for q in result}) == 3
    assert result[2]["skill"] != "javascript"
    assert {q["type"] for q in result[:2]} == {"technical", "scenario"}
    private_fields = {"reference_answer", "good_answer_points", "red_flags", "rubric",
                      "quality_note", "quality_review_note", "quality_sources"}
    for q in result:
        assert not private_fields & q.keys()
        assert "REFERENCE" not in str(q) and "PRIVATE" not in str(q)
    result[0]["question"] = "mutated"
    assert all(q["question"] != "mutated" for q in bank)


def test_none_empty_and_absent_focus_preserve_seeded_behavior(bank):
    old = interview.get_questions("r", 4, 123)
    assert old == interview.get_questions("r", 4, 123, None)
    assert old == interview.get_questions("r", 4, 123, [])
    assert old == interview.get_questions("r", 4, 123, ["missing"])
    assert len(interview.get_questions("r", 20, 123, ["JS"])) == 4


def test_review_filter_orders_internal_then_ai_assisted_then_unreviewed(bank, monkeypatch):
    reviewed = question("human", "sql", quality="reviewed")
    reviewed.update(quality_reviewed_at="2026-10-24", quality_review_note="Internal review.",
                    quality_sources=["https://example.org/sql"])
    ai_assisted = question("ai", "sql", quality="ai_reviewed_internal")
    ai_assisted.update(quality_reviewed_at="2026-10-25", quality_reviewer="AI assistant",
                       quality_review_note="AI review, not an independent review.",
                       quality_sources=["https://example.org/sql"])
    unreviewed = question("plain", "sql")
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [unreviewed, ai_assisted, reviewed]})

    selected = interview.get_questions("r", 3, seed=123, prefer_reviewed=True)
    assert [item["id"] for item in selected] == ["human", "ai", "plain"]


def test_answer_guidance_reports_review_status_and_only_sources_for_reviewed_content(bank, monkeypatch):
    reviewed = question("reviewed", "sql")
    reviewed.update(quality="reviewed", quality_reviewed_at="2026-10-24",
                    quality_review_note="Internal review only", quality_sources=["https://example.org/sql"])
    unreviewed = question("unreviewed", "sql", "scenario")
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [reviewed, unreviewed]})

    reviewed_feedback = interview.get_question_feedback("reviewed")
    assert reviewed_feedback["content_reviewed"] is True
    assert reviewed_feedback["quality_sources"] == ["https://example.org/sql"]
    assert reviewed_feedback["question_type"] == "technical"
    unreviewed_feedback = interview.get_question_feedback("unreviewed")
    assert unreviewed_feedback["content_reviewed"] is False
    assert unreviewed_feedback["quality_sources"] == []
    assert unreviewed_feedback["question_type"] == "scenario"


def test_ai_assisted_review_is_distinct_and_requires_explicit_limitations(bank, monkeypatch):
    assisted = question("ai-reviewed", "sql")
    assisted.update(
        quality="ai_reviewed_internal",
        quality_reviewed_at="2026-10-25",
        quality_reviewer="Codex (AI-assisted editorial review)",
        quality_review_note="AI-assisted editorial review; not an independent review.",
        quality_sources=["https://www.postgresql.org/docs/current/tutorial-transactions.html"],
    )
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [assisted]})

    feedback = interview.get_question_feedback("ai-reviewed")
    assert feedback["content_reviewed"] is True
    assert feedback["quality"] == "ai_reviewed_internal"
    assert "AI hỗ trợ" in feedback["quality_label"]
    assert "Codex" in feedback["quality_reviewer"]

    assisted["quality_review_note"] = "Reviewed internally."
    assert interview.get_question_feedback("ai-reviewed")["content_reviewed"] is False


def test_reviewed_question_without_provenance_is_not_called_reviewed(bank, monkeypatch):
    incomplete = question("reviewed", "sql", quality="reviewed")
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [incomplete]})
    feedback = interview.get_question_feedback("reviewed")
    assert feedback["content_reviewed"] is False
    assert feedback["quality_sources"] == []


def test_missing_duplicate_and_invalid_question_ids_raise(bank, monkeypatch):
    with pytest.raises(ValueError, match="Không tìm thấy"):
        interview.get_question_feedback("missing")
    with pytest.raises(ValueError, match="question_id"):
        interview.get_question_feedback("")
    question_row = bank[0]
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [question_row, deepcopy(question_row)]})
    with pytest.raises(ValueError, match="trùng"):
        interview.get_question_feedback(question_row["id"])


def test_real_bank_review_provenance_question_count_and_scoring_removal():
    interview._clear_cache()
    questions = [q for bank in interview._load_question_data().values() for q in bank]
    quality = Counter(q.get("quality", "unreviewed") for q in questions)
    assert len(questions) == 766
    assert quality == {"unreviewed": 766}
    for q in questions:
        if q.get("quality") == "reviewed":
            feedback = interview.get_question_feedback(q["id"])
            assert feedback["content_reviewed"]
            assert feedback["quality_sources"]
            assert q["quality_reviewed_at"] and q["quality_review_note"]
        if q.get("quality") == "ai_reviewed_internal":
            assert interview.get_question_feedback(q["id"])["content_reviewed"]
            assert "AI" in q["quality_reviewer"]
            assert "not an independent" in q["quality_review_note"].casefold()
    assert not hasattr(interview, "score_answer")
    assert not hasattr(interview, "get_rubric_coverage")
    assert not hasattr(modules, "score_answer")
    assert not hasattr(modules, "get_rubric_coverage")


def test_question_quality_summary_keeps_interview_backlog_separate_and_current():
    summary = interview.question_bank_quality_summary()
    assert summary == {
        "role_count": 131,
        "total": 766,
        "reviewed_internal": 0,
        "ai_reviewed_internal": 0,
        "template": 0,
        "unreviewed": 766,
    }


@pytest.mark.parametrize("role_id", ["data_analyst", "frontend_developer_react", "backend_developer_java"])
def test_demo_role_question_banks_have_draft_guidance_pending_review(role_id):
    questions = interview._load_question_data()[role_id]
    assert questions
    assert all(q.get("reference_answer") and q.get("good_answer_points") for q in questions)
    assert all(q.get("context_scenario") and all(q["evaluation_rubric"].values()) for q in questions)
    assert all(not interview.get_question_feedback(q["id"])["content_reviewed"] for q in questions)


def test_no_rubric_machine_score_file_remains():
    assert not (DATA_DIR / "interview_rubrics.json").exists()
