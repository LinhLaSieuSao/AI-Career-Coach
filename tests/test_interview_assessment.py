"""Gap selection, rubric fallback, review provenance and public/private boundaries."""

from collections import Counter
from copy import deepcopy
import json

import pytest

from modules import interview
from modules.catalog import DATA_DIR
from modules.data_quality import inspect_rubrics


def question(qid, skill, kind="technical", quality="template"):
    return {"id": qid, "skill": skill, "type": kind, "question": "Question?", "level": 1,
            "quality": quality, "reference_answer": "SECRET ANSWER", "good_answer_points": ["SECRET"],
            "red_flags": ["SECRET"], "rubric": {"SECRET": True}, "quality_note": "PRIVATE NOTE"}


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
    for q in result:
        assert not {"reference_answer", "good_answer_points", "red_flags", "rubric", "quality_note"} & q.keys()
        assert "SECRET" not in json.dumps(q) and "PRIVATE" not in json.dumps(q)
    result[0]["question"] = "mutated"
    assert all(q["question"] != "mutated" for q in bank)


def test_none_empty_and_absent_focus_preserve_old_seeded_behavior(bank):
    old = interview.get_questions("r", 4, 123)
    assert old == interview.get_questions("r", 4, 123, None)
    assert old == interview.get_questions("r", 4, 123, [])
    assert old == interview.get_questions("r", 4, 123, ["missing"])
    assert len(interview.get_questions("r", 20, 123, ["JS"])) == 4


@pytest.fixture
def rubric_bank(monkeypatch):
    q = question("reviewed", "sql", quality="reviewed")
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [q, question("template", "sql")]})
    rubric = {"review_status": "reviewed", "review_note": "Criteria checked for this question", "criteria": [
        {"id": "grain", "label": "grain and key", "points": 4, "groups": [["grain", "mức chi tiết"], ["key", "khóa"]]},
        {"id": "check", "label": "compare source", "points": 6, "groups": [["đối soát", "reconcile"], ["nguồn", "source"]]},
    ]}
    monkeypatch.setattr(interview, "_load_rubrics", lambda: {"reviewed": rubric})
    return q, rubric


def test_rubric_scores_concept_groups_partial_empty_and_feedback(rubric_bank):
    result = interview.score_answer("reviewed", "Tôi xác định mức chi tiết và khóa, rồi đối soát với nguồn.")
    assert result["score"] == 10 and result["status"] == "scored" and result["method"] == "rubric"
    assert all(c["met"] for c in result["criteria"])
    assert "không xác minh" in result["feedback"][-1]
    assert interview.score_answer("reviewed", "grain key")["score"] == 4
    assert interview.score_answer("reviewed", "grain only")["score"] == 0
    assert interview.score_answer("reviewed", "")["score"] == 0
    assert interview.score_answer("reviewed", "unrelated long answer "*300)["score"] == 0
    assert interview.score_answer("reviewed", "SECRET ANSWER")["score"] == 0


def test_rubric_does_not_match_substring_or_simple_negation(rubric_bank):
    assert interview.score_answer("reviewed", "grain keypress")["score"] == 0
    assert interview.score_answer("reviewed", "không xác định grain key")["score"] == 0
    assert interview.score_answer("reviewed", "reconcile source")["score"] == 6


def test_no_rubric_or_unreviewed_question_returns_unavailable_including_empty(rubric_bank):
    result = interview.score_answer("template", "")
    assert result["status"] == "unavailable" and result["score"] is None
    assert result["reason"] and result["criteria"] == []
    rubric_bank[0]["quality"] = "template"
    assert interview.score_answer("reviewed", "grain key reconcile source")["score"] is None


@pytest.mark.parametrize("change", ["missing_groups", "points", "unreviewed", "duplicate_id"])
def test_malformed_rubric_cannot_generate_fake_score(rubric_bank, change):
    _, rubric = rubric_bank
    if change == "missing_groups":
        rubric["criteria"][0].pop("groups")
    elif change == "points":
        rubric["criteria"][0]["points"] = True
    elif change == "unreviewed":
        rubric["review_status"] = "template"
    else:
        rubric["criteria"][1]["id"] = "grain"
    assert interview.score_answer("reviewed", "grain key reconcile source")["status"] == "unavailable"


def test_unknown_id_wrong_type_and_duplicate_id_errors(rubric_bank, monkeypatch):
    with pytest.raises(ValueError, match="Không tìm thấy"):
        interview.score_answer("not-found", "answer")
    with pytest.raises(ValueError, match="question_id"):
        interview.score_answer("", "answer")
    with pytest.raises(TypeError, match="answer"):
        interview.score_answer("reviewed", None)
    q = rubric_bank[0]
    monkeypatch.setattr(interview, "_load_question_data", lambda: {"r": [q, deepcopy(q)]})
    with pytest.raises(ValueError, match="trùng"):
        interview.score_answer("reviewed", "answer")


def test_real_demo_reviewed_questions_have_individual_rubrics_and_templates_fallback():
    interview._clear_cache()
    rubrics = json.loads((DATA_DIR / "interview_rubrics.json").read_text(encoding="utf8"))["questions"]
    demo_ids = ("backend_developer_java", "data_analyst", "sales_executive")
    questions = [q for rid in demo_ids for q in interview._load_question_data()[rid]]
    assert Counter(q["quality"] for q in questions) == {"reviewed": 6, "template": 12}
    for q in questions:
        if q["quality"] == "reviewed":
            assert q["quality_reviewed_at"] and interview._valid_rubric(rubrics[q["id"]])
            assert rubrics[q["id"]]["sources"] and rubrics[q["id"]]["reviewed_at"]
            assert interview.score_answer(q["id"], q["reference_answer"])["score"] == 10
        else:
            assert interview.score_answer(q["id"], q["reference_answer"])["score"] is None
    assert set(rubrics) == {q["id"] for q in questions if q["quality"] == "reviewed"}
    public = [q for rid in demo_ids for q in interview.get_questions(rid, 99, 42)]
    assert all(not {"rubric", "criteria", "review_note", "sources", "reference_answer"} & q.keys() for q in public)


def test_rubric_integrity_rejects_foreign_key_missing_review_and_bad_criteria():
    q = question("q", "sql", quality="reviewed")
    banks = [("fixture", {"roles": {"r": [q]}})]
    assert inspect_rubrics({"questions": {}}, banks) == []  # Review of content need not imply a machine rubric.
    assert any("unknown question" in e for e in inspect_rubrics({"questions": {"foreign": {}}}, banks))
    assert any("invalid machine criteria" in e for e in inspect_rubrics({"questions": {"q": {}}}, banks))


def test_missing_or_corrupt_rubric_file_is_unavailable_without_invented_points(tmp_path, monkeypatch):
    monkeypatch.setattr(interview, "_RUBRICS_FILE", tmp_path / "rubrics.json")
    interview._load_rubrics.cache_clear()
    assert interview.score_answer("data_analyst_q01", "grain key")["status"] == "unavailable"
    (tmp_path / "rubrics.json").write_text("{broken", encoding="utf8")
    interview._load_rubrics.cache_clear()
    assert interview.score_answer("data_analyst_q01", "grain key")["score"] is None
    interview._load_rubrics.cache_clear()
