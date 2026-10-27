"""Structural checks for the bundled catalogs used by the web app."""

import json
from copy import deepcopy

import pytest

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary, summarize_data_provenance
from modules.curriculum import load_academic_curriculum, merge_academic_curriculum
from modules.interview import question_bank_quality_summary
from modules.matcher import load_interest_activities, load_role_family_vectors
from modules.recommender import get_practice_routes
from modules.schemas import RoleRequirement
from modules.skill_extractor import load_aliases, normalize_skill
from scripts.build_academic_curriculum import preserve_curated_data


def test_role_and_interest_catalogs_cover_every_role():
    roles = load_roles()
    assert len(roles) == 131
    assert len({role["id"] for role in roles}) == len(roles)
    for role in roles:
        RoleRequirement.model_validate(role)
    families = json.loads((DATA_DIR / "role_families_riasec.json").read_text(encoding="utf-8"))["families"]
    assert len(families) == 15
    assert len(load_role_family_vectors()) == len(roles)
    assert load_interest_activities()


def test_aliases_and_resources_use_recognized_skills():
    vocabulary = load_skill_vocabulary()
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    assert aliases and all(target in vocabulary for target in aliases.values())
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    assert isinstance(resources, dict) and resources
    for skill, group in resources.items():
        assert normalize_skill(skill) in vocabulary
        assert isinstance(group.get("resources"), list)
        for record in group["resources"]:
            assert isinstance(record.get("url"), str) and record["url"].startswith(("http://", "https://"))


def test_question_banks_have_unique_ids_and_known_roles():
    role_ids = {role["id"] for role in load_roles()}
    files = sorted((DATA_DIR / "interview_questions").glob("*.json"))
    assert len(files) == 10
    seen = set()
    count = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for role_id, questions in payload["roles"].items():
            assert role_id in role_ids
            for question in questions:
                assert question["id"] not in seen
                seen.add(question["id"])
                assert question.get("question")
                count += 1
    assert count == question_bank_quality_summary()["total"] == 766


def test_every_role_skill_has_practice_guidance_without_fabricating_reviews():
    curriculum = load_academic_curriculum()
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    merged = merge_academic_curriculum(resources)
    skills = {
        normalize_skill(item["name"] if isinstance(item, dict) else item)
        for role in load_roles() for item in role["skills"]
    }
    assert skills == set(curriculum["skills"])
    for skill in skills:
        routes = get_practice_routes([skill], merged)
        assert len(routes) == 1, skill
        assert len(routes[0]["steps"]) >= 3, skill
        assert all("{skill}" not in step for step in routes[0]["steps"]), skill
    health = get_practice_routes(["chăm sóc bệnh nhân"], merged)[0]
    assert "không tự chẩn đoán" in health["framing"]
    assert "giám sát" in health["steps"][-1]


def test_link_checks_are_distinct_from_content_review():
    curriculum = load_academic_curriculum()
    resources = merge_academic_curriculum({}, curriculum=curriculum)
    source = resources["power bi"]["resources"][0]
    assert source["verified"] is True
    assert source["access_check"]["http_status"] == 200
    assert source["provenance"]["reviewed_at"] is None
    restricted = resources["phong thủy cơ bản"]["resources"][0]
    assert restricted["access_check"]["http_status"] == 429
    assert restricted["verified"] is False


def test_provenance_summary_reports_missing_fields_without_claiming_permission(tmp_path):
    (tmp_path / "roles.json").write_text(json.dumps([
        {"id": "r1", "skills": [], "provenance": {"source_url": None, "rights_basis": None}},
        {"id": "r2", "skills": [], "provenance": {"source_url": "https://example.org", "rights_basis": "pending"}},
    ]), encoding="utf-8")
    (tmp_path / "resources.json").write_text(json.dumps({
        "skill": {"resources": [{"provenance": {"source_url": "https://example.org"}}, {}]}
    }), encoding="utf-8")
    report = summarize_data_provenance(tmp_path)
    assert report["roles"]["source_url_missing"] == 1
    assert report["roles"]["rights_basis_recorded"] == 1
    assert report["resource_mappings"]["rights_basis_missing"] == 2
    assert "không tự chứng minh" in report["notice"]


def test_regenerating_curriculum_keeps_curated_plans_and_never_reuses_changed_url_evidence():
    fresh = {
        "schema_version": 1,
        "sources": {"s": {"url": "https://example.org/source"}},
        "skills": {"skill": {"source_id": "s", "learning_plan": {"steps": ["generated"]}}},
    }
    previous = deepcopy(fresh)
    previous["sources"]["s"]["access_check"] = {"http_status": 200}
    previous["skills"]["skill"]["learning_plan"]["user_steps"] = ["curated"]
    previous["practice_tracks"] = {"track": {"sources": ["s"]}}
    merged = preserve_curated_data(fresh, previous)
    assert merged["sources"]["s"]["access_check"]["http_status"] == 200
    assert merged["skills"]["skill"]["learning_plan"]["user_steps"] == ["curated"]
    assert merged["practice_tracks"] == previous["practice_tracks"]
    assert "access_check" not in fresh["sources"]["s"]
    fresh["sources"]["s"]["url"] = "https://example.org/changed"
    with pytest.raises(ValueError, match="URL đã đổi"):
        preserve_curated_data(fresh, previous)
