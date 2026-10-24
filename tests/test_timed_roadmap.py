from copy import deepcopy
import json

import pytest

from modules import build_timed_roadmap, compute_gap
from modules.catalog import DATA_DIR, load_roles


def gap(*skills):
    return compute_gap({}, {"id": "r", "skills": [
        {"name": name, "level": level, "weight": weight} for name, level, weight in skills]})


def resource(rid="r", hours=10, **kwargs):
    return {"id": rid, "url": "https://example.org/"+rid, "title": "Course "+rid,
            "level_from": 1, "level_to": 3, "verified": True, "content_review_status": "reviewed",
            "duration_hours": hours, "duration_source": "https://example.org/evidence", "duration_basis": "publisher",
            **kwargs}


def catalog(**records):
    return {name: {"resources": values} for name, values in records.items()}


def test_long_shared_resource_is_split_once_and_respects_budget_without_mutation():
    g = gap(("python", 3, 1), ("sql", 2, 1))
    r = catalog(python=[resource(hours=19)], sql=[resource("other_id", 19, url="https://example.org/r")])
    before = deepcopy(r)
    result = build_timed_roadmap(g, r, 8)
    assert len(result["resources"]) == 1
    assert result["total_weeks"] == result["known_weeks"] == 3
    assert result["total_known_hours"] == 19
    assert result["total_estimated_hours"] == 0
    assert [p["hours"] for p in result["phases"]] == [8, 8, 3]
    keys = {s["resource_key"] for p in result["phases"] for s in p["segments"]}
    assert keys == set(result["resource_keys"]["sql"]) == set(result["resource_keys"]["python"])
    assert next(iter(result["resources"].values()))["skills"] == ["python", "sql"]
    assert r == before


def test_priority_then_stable_tie_and_multiple_resources_pack_into_one_week():
    g = gap(("python", 1, 1), ("sql", 1, 3), ("git", 1, 1))
    result = build_timed_roadmap(g, catalog(python=[resource("py", 2)], sql=[resource("db", 5)], git=[resource("git", 2)]))
    assert [s["resource_key"] for p in result["phases"] for s in p["segments"]] == [
        "url:https://example.org/db", "url:https://example.org/py", "url:https://example.org/git", "url:https://example.org/git"]
    assert [p["hours"] for p in result["phases"]] == [8, 1]
    assert result["total_known_hours"] == 9


def test_null_duration_keeps_known_part_and_never_claims_complete_weeks():
    result = build_timed_roadmap(gap(("python", 1, 1), ("sql", 1, 1)),
                                 catalog(python=[resource(hours=2)], sql=[resource("unknown", None)]))
    assert result["total_known_hours"] == 2 and result["known_weeks"] == 1
    assert result["total_weeks"] is None
    assert result["unknown_duration"][0]["skills"] == ["sql"]
    assert result["resource_keys"]["sql"]  # The unknown document is still available for inspection.


def test_estimate_is_separate_and_requires_its_basis():
    g = gap(("sql", 2, 1))
    r = resource(hours=None, estimated_duration_hours=9, estimated_duration_basis="Trial lesson 3h + two similar exercises")
    result = build_timed_roadmap(g, catalog(sql=[r]))
    assert result["total_known_hours"] == 0 and result["total_estimated_hours"] == 9
    assert result["is_estimated"] and result["total_weeks"] == 2
    assert all(s["duration_kind"] == "estimated" for p in result["phases"] for s in p["segments"])
    r.pop("estimated_duration_basis"); r.pop("duration_basis")
    assert build_timed_roadmap(g, catalog(sql=[r]))["unresolved"][0]["reason"] == "estimate_without_basis"


@pytest.mark.parametrize("reason,r", [
    ("level_mismatch", resource(level_from=1, level_to=1)),
    ("unreviewed_content", resource(content_review_status="unreviewed")),
    ("unreviewed_content", resource(content_review_status="blocked", verified=False)),
    ("unreviewed_content", resource(content_review_status="unsuitable", verified=False)),
])
def test_level_mismatch_and_unreviewed_content_are_not_assumed_sufficient(reason, r):
    g = compute_gap({"sql": 1}, {"skills": [{"name": "sql", "level": 3}]})
    result = build_timed_roadmap(g, catalog(sql=[r]))
    assert result["total_weeks"] is None and result["total_known_hours"] == 0
    assert result["unresolved"][0]["reason"] == reason


def test_partial_content_schedules_useful_hours_but_stays_unresolved():
    result = build_timed_roadmap(gap(("sql", 2, 1)), catalog(sql=[resource(content_review_status="partial")]))
    assert result["total_known_hours"] == 10
    assert result["total_weeks"] is None
    assert result["unresolved"][0]["reason"] == "partial_content"


def test_sourced_hours_required_and_prefer_one_suitable_reviewed_alternative():
    r = catalog(sql=[resource("unbacked", 4, duration_source=None), resource("actual", 3), resource("unused", 10)])
    result = build_timed_roadmap(gap(("sql", 1, 1)), r)
    assert list(result["resources"]) == ["url:https://example.org/actual"]
    result = build_timed_roadmap(gap(("sql", 1, 1)), catalog(sql=r["sql"]["resources"][:1]))
    assert result["unknown_duration"][0]["reason"] == "unverified_duration"


def test_shared_url_uses_per_skill_level_metadata_and_conflict_hours_are_unknown():
    g = gap(("python", 1, 1), ("sql", 3, 1))
    r = catalog(python=[resource(level_to=1)], sql=[resource(level_to=3)])
    result = build_timed_roadmap(g, r)
    assert not result["unresolved"] and len(result["resources"]) == 1
    assert {x["skill"] for x in result["level_coverage"]} == {"python", "sql"}
    r["sql"]["resources"][0]["duration_hours"] = 12
    result = build_timed_roadmap(g, r)
    assert result["total_weeks"] is None and result["total_known_hours"] == 0
    assert result["unknown_duration"][0]["reason"] == "conflicting_duration"


def test_missing_resources_and_empty_gap():
    result = build_timed_roadmap(gap(("unknown", 2, 1)), {})
    assert result["unresolved"] == [{"skill": "unknown", "reason": "no_resources", "levels": [1, 2]}]
    assert result["total_weeks"] is None and result["phases"] == []
    empty = build_timed_roadmap(gap(), {})
    assert empty["total_weeks"] == 0 and empty["total_known_hours"] == 0 and empty["unresolved"] == []


@pytest.mark.parametrize("first,second", [(None, 4), (4, None)])
def test_shared_identity_can_use_sourced_hours_when_other_mapping_has_no_hours(first, second):
    result = build_timed_roadmap(gap(("python", 1, 1), ("sql", 1, 1)),
                                 catalog(python=[resource(hours=first)], sql=[resource(hours=second)]))
    assert result["total_known_hours"] == 4 and result["total_weeks"] == 1
    assert len(result["resources"]) == 1 and result["unknown_duration"] == []
    evidence = next(iter(result["resources"].values()))["duration_evidence"]
    assert evidence["hours"] == 4 and evidence["source"] == "https://example.org/evidence"


def test_published_hours_override_editorial_estimate_for_shared_identity():
    result = build_timed_roadmap(gap(("python", 1, 1), ("sql", 1, 1)), catalog(
        python=[resource(hours=None, estimated_duration_hours=8)], sql=[resource(hours=4)]))
    assert result["total_known_hours"] == 4 and result["total_estimated_hours"] == 0
    assert not result["is_estimated"] and result["total_weeks"] == 1


def test_fractional_budget_does_not_accumulate_rounding_into_extra_week():
    records = {f"s{i}": [resource(str(i), .1)] for i in range(10)}
    result = build_timed_roadmap(gap(*[(name, 1, 1) for name in records]), catalog(**records), .5)
    assert [p["hours"] for p in result["phases"]] == [.5, .5]
    assert result["total_weeks"] == 2 and result["total_known_hours"] == 1


def test_inconsistent_gap_duplicate_alias_and_invalid_priority_are_rejected():
    g = gap(("sql", 1, 1)); g["items"][0]["gap"] = 0
    with pytest.raises(ValueError, match="nhất quán"):
        build_timed_roadmap(g, {})
    g = gap(("sql", 1, 1)); g["items"].append(deepcopy(g["items"][0]))
    with pytest.raises(ValueError, match="trùng"):
        build_timed_roadmap(g, {})
    g = gap(("sql", 1, 1)); g["items"][0]["priority"] = True
    with pytest.raises(ValueError, match="priority"):
        build_timed_roadmap(g, {})


@pytest.mark.parametrize("budget", [0, -1, True, float("inf"), float("nan"), "8"])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        build_timed_roadmap(gap(), {}, budget)


@pytest.mark.parametrize("patch", [{"duration_hours": -1}, {"duration_hours": True}, {"duration_hours": float("nan")},
                                   {"level_from": True}, {"level_to": 0}, {"level_from": 3, "level_to": 1}])
def test_invalid_resource_metadata(patch):
    with pytest.raises(ValueError):
        build_timed_roadmap(gap(("sql", 1, 1)), catalog(sql=[resource(**patch)]))


@pytest.mark.parametrize("rid", ["backend_developer_java", "data_analyst", "sales_executive"])
def test_real_demo_data_never_claims_full_duration_or_level_coverage(rid):
    role = next(r for r in load_roles() if r["id"] == rid)
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf8"))
    result = build_timed_roadmap(compute_gap({}, role), resources)
    assert result["total_weeks"] is None and result["unresolved"]
    assert result["total_known_hours"] > 0
    assert all(phase["hours"] <= 8 for phase in result["phases"])
    assert result["total_estimated_hours"] == 0
