"""Offline integrity, foreign keys, and intentional quality gaps."""

from copy import deepcopy
import json

import pytest

from modules.catalog import DATA_DIR
from modules.data_quality import audit_project, inspect_data, top_skills
from modules.recommender import build_roadmap


def fixture_data():
    roles = [{"id": "role", "name": "Role", "name_vi": "Vị trí", "skills": [{"name": "python", "level": 2, "weight": 3}]}]
    resource = {"id": "python_001", "title": "Python tutorial", "provider": "Example", "url": "https://example.org/python", "language": "en", "type": "doc", "cost": "free", "level_from": 1, "level_to": 2, "verified": False, "duration_hours": None}
    resources = {"python": {"skill_name": "python", "category": "technical", "resources": [resource]}}
    question = {"id": "role_q01", "type": "technical", "skill": "python", "level": 2, "weight": 1, "question": "How?", "reference_answer": "Example"}
    return roles, resources, {"py": "python"}, ["mysql"], [("part.json", {"roles": {"role": [question]}})]


def test_real_data_integrity_and_separate_recognition_gaps():
    result = audit_project()
    assert result["errors"] == []
    assert result["stats"]["roles"] > 0
    assert result["stats"]["questions"] > 0
    assert all("recognition_only" in warning for warning in result["warnings"])


@pytest.mark.parametrize("section,field,value,expected", [
    ("role", "id", "BAD ID", "invalid ID"),
    ("skill", "name", " Python ", "canonical"),
    ("skill", "level", 0, "level"),
    ("skill", "weight", True, "weight"),
    ("skill", "weight", float("inf"), "weight"),
    ("resource", "id", "", "invalid ID"),
    ("resource", "url", "http://[", "HTTP"),
    ("resource", "language", "unknown", "language"),
    ("resource", "language", [], "language"),
    ("resource", "verified", "true", "boolean"),
    ("resource", "level_from", 3, "level range"),
    ("resource", "duration_hours", -1, "duration"),
    ("resource", "duration_hours", 2, "source and basis"),
    ("resource", "estimated_duration_hours", 2, "estimate"),
    ("resource", "content_review_status", "reviewed", "note and date"),
    ("resource", "content_review_status", "blocked", "cannot be verified"),
    ("question", "skill", "mysql", "not required"),
    ("question", "level", True, "level/weight"),
    ("question", "id", "BAD", "invalid question ID"),
])
def test_invalid_records_fail_with_a_useful_path(section, field, value, expected):
    data = fixture_data()
    targets = {"role": data[0][0], "skill": data[0][0]["skills"][0], "resource": data[1]["python"]["resources"][0], "question": data[4][0][1]["roles"]["role"][0]}
    targets[section][field] = value
    if section == "resource" and value == "blocked":
        targets[section]["verified"] = True
    result = inspect_data(*data)
    assert any(expected in error for error in result["errors"]), result


def test_role_resource_regression_is_strict_but_recognition_only_is_a_warning():
    data = fixture_data()
    result = inspect_data(*data)
    assert result["errors"] == []
    assert result["stats"]["recognition_without_resources"] == ["mysql"]
    data[1].clear()
    assert any("role skill lacks resource" in error for error in inspect_data(*data)["errors"])


def test_duplicate_ids_and_invalid_alias_foreign_keys_are_not_hidden():
    data = fixture_data()
    data[0].append(deepcopy(data[0][0]))
    data[1]["python"]["resources"].append(deepcopy(data[1]["python"]["resources"][0]))
    data[4][0][1]["roles"]["role"].append(deepcopy(data[4][0][1]["roles"]["role"][0]))
    data[2]["bad"] = "missing"
    errors = inspect_data(*data)["errors"]
    assert any("duplicate ID" in e for e in errors)
    assert any("duplicate resource" in e for e in errors)
    assert any("duplicate question" in e for e in errors)
    assert any("target absent" in e for e in errors)


def test_shared_urls_are_legal_and_roadmap_preserves_all_references():
    data = fixture_data()
    data[0][0]["skills"].append({"name": "sql", "level": 1, "weight": 1})
    data[1]["sql"] = deepcopy(data[1]["python"])
    data[1]["sql"]["skill_name"] = "sql"
    data[1]["sql"]["resources"][0]["id"] = "sql_001"
    assert inspect_data(*data)["errors"] == []
    roadmap = build_roadmap(["python", "sql"], data[1], weeks=2)
    assert len(roadmap[0]["resources"]) == 1
    assert roadmap[1]["resources"] == []
    assert roadmap[0]["resource_keys"]["python"] == roadmap[1]["resource_keys"]["sql"]
    assert all(week["skills_without_resources"] == [] for week in roadmap)


def test_real_role_resources_remain_linked_after_whole_roadmap_deduplication():
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    roadmap = build_roadmap(list(resources), resources, weeks=4)
    catalog = {r["key"]: r for week in roadmap for r in week["resources"]}
    assert len(catalog) == sum(len(week["resources"]) for week in roadmap)
    for week in roadmap:
        for skill, keys in week["resource_keys"].items():
            assert keys, skill
            assert all(key in catalog and skill in catalog[key]["skills"] for key in keys)


def test_frequency_counts_roles_once_and_breaks_ties_stably():
    roles = [{"skills": [{"name": "sql"}, {"name": "python"}, {"name": "sql"}]}, {"skills": [{"name": "python"}]}]
    assert top_skills(roles) == [{"name": "python", "role_count": 2}, {"name": "sql", "role_count": 1}]
    assert top_skills([roles[0]]) == [{"name": "python", "role_count": 1}, {"name": "sql", "role_count": 1}]


def test_top30_have_read_vietnamese_sources_with_explicit_scope():
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    for skill in audit_project()["top30"]:
        candidates = [r for r in resources[skill["name"]]["resources"]
                      if r["language"] == "vi" and r.get("content_review_status") in {"reviewed", "partial"}]
        assert candidates, skill["name"]
        for record in candidates:
            assert record["content_reviewed_at"] and record["review_note"]
            assert record["evidence_locator"] and record["access_note"]
    # English fallback pages cannot count as Vietnamese coverage just because of their URL.
    assert all(r["language"] == "en" for r in resources["power bi"]["resources"] if "dot03" in r["id"])


def test_catalog_durations_match_saved_publisher_evidence_and_shared_urls_agree():
    snapshot = json.loads((DATA_DIR.parent / "docs/reports/dot03_published_durations.json").read_text(encoding="utf-8"))
    catalog = {m["uid"]: m for m in snapshot["modules"]}
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    durations = {}
    for group in resources.values():
        for record in group["resources"]:
            hours = record["duration_hours"]
            if hours is None:
                continue
            assert record["duration_source"] and record["duration_basis"] and record["duration_checked_at"]
            if record.get("duration_catalog_uid"):
                published = catalog[record["duration_catalog_uid"]]
                assert hours == published["duration_in_minutes"] / 60
                assert record["url"].rstrip("/") == published["url"].split("?")[0].rstrip("/")
            if record["url"] in durations:
                assert durations[record["url"]] == hours
            durations[record["url"]] = hours
    assert durations  # Evidence contains real, non-null durations, not just schema placeholders.


def test_demo_roles_have_published_resources_but_keep_unknown_hours():
    roles = json.loads((DATA_DIR / "roles.json").read_text(encoding="utf-8"))
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    for rid in ("backend_developer_java", "data_analyst", "sales_executive"):
        role = next(r for r in roles if r["id"] == rid)
        roadmap = build_roadmap([s["name"] for s in role["skills"]], resources)
        records = [r for week in roadmap for r in week["resources"]]
        assert any(r["duration_hours"] is not None for r in records), rid
        assert any(r["duration_hours"] is None for r in records), rid
        assert all(not w["skills_without_resources"] for w in roadmap)


def test_question_alias_can_resolve_into_role_but_foreign_role_cannot():
    data = fixture_data()
    data[4][0][1]["roles"]["role"][0]["skill"] = "py"
    assert inspect_data(*data)["errors"] == []
    data[4][0][1]["roles"]["absent_role"] = data[4][0][1]["roles"].pop("role")
    assert any("unknown role ID" in e for e in inspect_data(*data)["errors"])
