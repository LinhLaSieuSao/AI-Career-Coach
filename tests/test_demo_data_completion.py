"""Regression checks for the exact editorial scope and honest evidence labels."""

import json

from modules.resource_policy import is_recommendable_resource
from scripts.apply_demo_resource_checks import MANIFEST, TARGET, apply_checks
from scripts.audit_demo_role_quality import DATA_DIR, audit_demo_roles
from scripts.audit_excluded_resources import inventory
from scripts.complete_demo_questions import complete


def test_demo_question_draft_is_complete_without_claiming_review():
    report = audit_demo_roles(DATA_DIR)
    assert report["summary"]["role_skill_requirements"] == 39
    assert report["summary"]["questions"] == 39
    for key in ("question_missing_skill", "question_generic_prompt", "question_missing_context",
                "question_missing_target_rubric", "question_missing_all_level_rubric", "question_wrong_level"):
        assert report["summary"]["issue_occurrences_by_role"][key] == 0
    assert report["summary"]["issue_occurrences_by_role"]["question_template_or_unreviewed"] == 39
    assert complete(apply=False)["questions_changed"] == 0


def test_opened_resource_checks_are_exact_and_idempotent():
    assert apply_checks(apply=False)["records_changed"] == 0
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    records = {record["id"]: record for group in data.values() for record in group["resources"]}
    assert len(spec["records"]) == 29
    for entry in spec["records"]:
        record = records[entry["id"]]
        assert record["url"] == entry["source_url"]
        assert record["scope_granularity"] == entry["scope"]
        assert record["evidence_locator"] == entry["locator"]
        assert record["verification_axes"]["access_status"] == "independently_accessible"
        assert record["verification_axes"]["last_live_checked"] == "2026-10-26"
        if "language" in entry:
            assert record["language"] == entry["language"]


def test_all_rejected_mappings_remain_excluded_from_recommendations():
    result = inventory()
    assert result["total"] == 216
    assert result["by_status"] == {"unsuitable": 175, "blocked": 41}
    resources = json.loads(TARGET.read_text(encoding="utf-8"))
    for skill, group in resources.items():
        for record in group["resources"]:
            if record.get("content_review_status") in {"unsuitable", "blocked"}:
                assert not is_recommendable_resource(record, require_verified=True, skill=skill)
