"""Verify the bounded data edit, backup, and draft review status."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.rewrite_sales_templates import MANIFEST, TARGET, rewrite


def _baseline(tmp_path):
    bank = json.loads(TARGET.read_text(encoding="utf-8"))
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = {record["id"]: record for record in bank["roles"]["sales_executive"]}
    for entry in spec["records"]:
        by_id[entry["id"]].update(deepcopy(entry["expected"]))
    target = tmp_path / "questions.json"
    target.write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    return target, bank, spec


def test_rewrite_is_dry_by_default_backs_up_and_only_edits_three_questions(tmp_path):
    target, before, spec = _baseline(tmp_path)
    original = target.read_bytes()
    assert rewrite(target)["records_changed"] == 3
    assert target.read_bytes() == original
    backups = tmp_path / "backups"
    result = rewrite(target, apply=True, backup_dir=backups)
    assert result["records_changed"] == 3
    assert Path(result["backup"]).read_bytes() == original
    after = json.loads(target.read_text(encoding="utf-8"))
    edits = {entry["id"]: entry for entry in spec["records"]}
    for role_id, records in before["roles"].items():
        for old, new in zip(records, after["roles"][role_id], strict=True):
            if old["id"] in edits:
                assert new == {**old, **edits[old["id"]]["changes"]}
                assert new["quality"] == "unreviewed"
                assert new["quality_reviewer"] is None and new["quality_reviewed_at"] is None
                assert new["provenance"]["review_tier"] == "ai_assisted_draft"
                assert new["provenance"]["reviewed_at"] is None
                assert all(new["evaluation_rubric"].values())
            else:
                assert new == old
    saved = target.read_bytes()
    assert rewrite(target, apply=True, backup_dir=backups)["records_changed"] == 0
    assert target.read_bytes() == saved


def test_rewrite_refuses_to_overwrite_a_later_editor_change(tmp_path):
    target, bank, _ = _baseline(tmp_path)
    bank["roles"]["sales_executive"][1]["question"] = "Nội dung được người biên tập sửa sau khi lập kế hoạch."
    target.write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    original = target.read_bytes()
    with pytest.raises(ValueError, match="Refusing to overwrite changed record"):
        rewrite(target, apply=True, backup_dir=tmp_path / "backups")
    assert target.read_bytes() == original


def test_sales_drafts_reach_interview_feedback_without_becoming_reviewed():
    from modules import interview

    interview._clear_cache()
    bank = json.loads(TARGET.read_text(encoding="utf-8"))
    targets = {entry["id"] for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["records"]}
    for question in bank["roles"]["sales_executive"]:
        if question["id"] not in targets:
            continue
        assert "Tình huống giả lập" in question["question"]
        assert "[...]" not in question["question"] and "STAR" not in question["question"]
        assert question["context_scenario"] and all(question["evaluation_rubric"].values())
        assert "AI" in question["quality_note"]
        feedback = interview.get_question_feedback(question["id"])
        assert feedback["quality"] == "unreviewed"
        assert not feedback["content_reviewed"]
        assert feedback["reference_answer"] == question["reference_answer"]
