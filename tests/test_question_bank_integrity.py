"""Regression coverage for whole-bank integrity and review provenance checks."""

from __future__ import annotations

from scripts.validate_question_bank import validate_question_bank, validate_question_records


def test_bundled_interview_bank_integrity_and_expected_size():
    report = validate_question_bank()
    assert report["question_count"] == 766
    assert report["role_count"] == 131
    assert report["integrity_errors"] == []
    assert report["review_status_counts"] == {
        "unreviewed": 766,
    }


def test_validator_flags_short_duplicate_and_missing_catalog_links():
    records = [
        ("missing_role", {"id": "q1", "question": "Too short", "type": "technical", "skill": "unknown",
                           "reference_answer": "answer"}),
        ("role", {"id": "q1", "question": "Too short", "type": "unexpected", "skill": "sql",
                   "good_answer_points": ["answer"]}),
    ]
    errors = validate_question_records(records, role_ids={"role"}, skill_vocabulary={"sql"})
    assert any("role_id" in error for error in errors)
    assert any("ngắn hơn 20" in error for error in errors)
    assert any("id câu hỏi bị trùng" in error for error in errors)
    assert any("type" in error for error in errors)
    assert any("skill" in error and "không tồn tại" in error for error in errors)


def test_validator_rejects_ai_review_without_provenance_and_limit_note():
    question = {
        "id": "ai-q", "question": "Explain how SQL transactions maintain consistency?",
        "type": "technical", "skill": "sql", "reference_answer": "A useful answer.",
        "quality": "ai_reviewed_internal", "quality_reviewed_at": "2026-10-25",
        "quality_review_note": "Reviewed.", "quality_reviewer": "Assistant",
        "quality_sources": ["not-a-url"],
    }
    errors = validate_question_records([("role", question)], role_ids={"role"}, skill_vocabulary={"sql"})
    assert any("URL không hợp lệ" in error for error in errors)
    assert any("reviewer" in error for error in errors)
    assert any("chưa thẩm định độc lập" in error for error in errors)
