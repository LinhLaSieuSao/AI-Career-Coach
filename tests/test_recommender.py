"""Acceptance tests for weekly roadmaps and the Matcher/resource handoff."""

from __future__ import annotations

import json
import unicodedata
from copy import deepcopy
from pathlib import Path

import pytest

from modules import build_roadmap, recommender
from modules.curriculum import merge_academic_curriculum
from modules.matcher import match_cv_to_jd, match_role


ROOT = Path(__file__).resolve().parents[1]


def test_shared_textbook_keeps_each_skills_practice_link_separate():
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    roadmap = build_roadmap(["power bi", "tableau"], merge_academic_curriculum(resources))
    book = next(item for item in _documents(roadmap) if item.get("academic_source"))
    assert "Power BI" in book["practice_title"]
    assert "Power BI" in book["practice_by_skill"]["power bi"]["title"]
    # Tableau's stored URL contains a placeholder and the live check returned
    # 403. It remains in the data, but must not be presented as verified.
    assert "tableau" not in book["practice_by_skill"]
    assert not any("playlist_id" in item.get("url", "") for item in _documents(roadmap))


def test_timed_plan_does_not_show_another_skills_companion():
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    gap = {"items": [
        {"skill": "power bi", "current": 0, "required": 1, "gap": 1, "priority": 2},
        {"skill": "tableau", "current": 0, "required": 1, "gap": 1, "priority": 1},
    ]}
    roadmap = recommender.build_timed_roadmap(gap, merge_academic_curriculum(resources))
    steps = {step["skill"]: step for step in roadmap["learning_steps"]}
    assert "Power BI" in steps["power bi"]["resource"]["practice_title"]
    tableau = steps["tableau"]["resource"]
    assert not tableau.get("practice_url")
    assert not tableau.get("verified_companion_url")


def test_inconclusive_link_check_is_explained_without_erasing_prior_review():
    resources = _catalog("sql")
    record = resources["sql"]["resources"][0]
    record["latest_transport_check"] = {"status": "blocked", "http_status": 403}
    original = deepcopy(resources)
    recommendation = _documents(build_roadmap(["sql"], resources))[0]
    assert recommendation["verified"] is True  # Historical review stays intact.
    assert "chưa xác nhận" in recommendation["access_note"]
    assert resources == original
    academic = merge_academic_curriculum(resources)["sql"]["resources"][-1]
    assert not academic.get("practice_url")


def test_independent_recognition_skills_without_resources_are_kept_and_reported():
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    missing = ["pandas", "mysql", "english", "google tag manager", ".net core"]
    roadmap = build_roadmap(missing, resources)
    assert [skill for week in roadmap for skill in week["skills"]] == missing
    assert [skill for week in roadmap for skill in week["skills_without_resources"]] == missing
    assert all(week["resources"] == [] for week in roadmap)
    assert all(keys == [] for week in roadmap for keys in week["resource_keys"].values())


def test_sales_and_soft_skill_gaps_get_experience_routes_without_course_dependency():
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    roadmap = build_roadmap(["bán hàng", "bán hàng b2b", "thuyết phục", "giao tiếp", "quản lý đội ngũ", "viết nội dung"], resources, weeks=1)
    routes = roadmap[0]["practice_routes"]
    by_skill = {route["skill"]: route for route in routes}
    assert set(by_skill) == {"bán hàng", "bán hàng b2b", "thuyết phục", "giao tiếp", "quản lý đội ngũ", "viết nội dung"}
    assert by_skill["thuyết phục"]["title"] == by_skill["bán hàng"]["title"]
    assert by_skill["bán hàng b2b"]["title"] == by_skill["bán hàng"]["title"]
    assert "đóng vai khách hàng" in " ".join(by_skill["bán hàng"]["steps"])
    assert "người quan sát" in by_skill["bán hàng"]["evidence"]
    assert "không tính điểm" not in by_skill["bán hàng"]["evidence"]
    assert "phản hồi" in " ".join(by_skill["giao tiếp"]["steps"])
    assert "điều phối" in " ".join(by_skill["quản lý đội ngũ"]["steps"])
    assert "portfolio" in by_skill["viết nội dung"]["title"]


def _resource(name: str, **overrides) -> dict:
    return {
        "id": name,
        "title": name + " tutorial",
        "url": "https://example.org/" + name,
        "provider": "Example",
        "duration_hours": None,
        "verified": True,
        "content_review_status": "reviewed",
        "review_note": "Reviewed for this test fixture.",
        **overrides,
    }


def _catalog(*skills: str) -> dict:
    return {
        skill: {"skill_name": skill, "category": "technical", "resources": [_resource(skill)]}
        for skill in skills
    }


def _scheduled(roadmap: list[dict]) -> list[str]:
    return [skill for week in roadmap for skill in week["skills"]]


def _documents(roadmap: list[dict]) -> list[dict]:
    return [resource for week in roadmap for resource in week["resources"]]


@pytest.mark.parametrize("missing", [None, [], "", ["  ", "\n"]])
def test_no_missing_skills_returns_no_roadmap(missing) -> None:
    assert build_roadmap(missing, {}) == []


def test_basic_output_is_weekly_and_keeps_resource_metadata() -> None:
    resources = _catalog("python", "sql")

    roadmap = build_roadmap(["python", "sql"], resources)

    assert [week["week"] for week in roadmap] == [1, 2]
    assert [week["skills"] for week in roadmap] == [["python"], ["sql"]]
    assert roadmap[0]["resources"] == [
        {**resources["python"]["resources"][0], "key": "url:https://example.org/python", "skills": ["python"]}
    ]
    assert roadmap[0]["resource_keys"] == {"python": ["url:https://example.org/python"]}
    assert all(not week["skills_without_resources"] for week in roadmap)


def test_many_missing_skills_are_balanced_without_reordering() -> None:
    missing = [f"skill {number}" for number in range(11)]

    roadmap = build_roadmap(missing, _catalog(*missing), weeks=4)

    assert [len(week["skills"]) for week in roadmap] == [3, 3, 3, 2]
    assert _scheduled(roadmap) == missing
    assert all(week["resources"] for week in roadmap)


@pytest.mark.parametrize("weeks, expected_sizes", [(1, [3]), (2, [2, 1]), (3, [1, 1, 1]), (20, [1, 1, 1])])
def test_week_count_never_creates_empty_study_weeks(weeks, expected_sizes) -> None:
    roadmap = build_roadmap(["python", "sql", "git"], _catalog("python", "sql", "git"), weeks)

    assert [len(week["skills"]) for week in roadmap] == expected_sizes


def test_weights_prioritize_skills_with_stable_ties_and_partial_metadata() -> None:
    missing = ["git", "sql", "python", "docker"]
    details = [
        {"name": "python", "weight": 3, "level": 1},
        {"name": "sql", "weight": 3, "level": 3},
        {"name": "docker", "weight": 1, "level": 3},
    ]

    roadmap = build_roadmap(missing, _catalog(*missing), weeks=2, missing_details=details)

    assert [week["skills"] for week in roadmap] == [["sql", "python"], ["git", "docker"]]


def test_empty_metadata_keeps_missing_order() -> None:
    assert _scheduled(build_roadmap(["sql", "git"], {}, missing_details=[])) == ["sql", "git"]


def test_level_alone_does_not_change_priority_or_filter_resources() -> None:
    missing = ["git", "sql"]
    resources = _catalog(*missing)
    resources["git"]["resources"][0].update(level_from=3, level_to=3)
    low = [{"name": "git", "weight": 1, "level": 1}, {"name": "sql", "weight": 1, "level": 3}]
    high = [{"name": "git", "weight": 1, "level": 3}, {"name": "sql", "weight": 1, "level": 1}]

    assert build_roadmap(missing, resources, missing_details=low) == build_roadmap(
        missing, resources, missing_details=high
    )


def test_unknown_and_empty_resource_skills_remain_scheduled() -> None:
    resources = _catalog("python")
    resources["sql"] = {"resources": []}

    roadmap = build_roadmap(["python", "sql", "unknown"], resources, weeks=2)

    assert _scheduled(roadmap) == ["python", "sql", "unknown"]
    assert roadmap[0]["skills_without_resources"] == ["sql"]
    assert roadmap[1]["skills_without_resources"] == ["unknown"]
    assert roadmap[1]["resources"] == []
    assert roadmap[1]["resource_keys"] == {"unknown": []}


def test_names_normalize_case_whitespace_unicode_and_duplicates() -> None:
    decomposed = unicodedata.normalize("NFD", "giao tiếp")
    resources = {" GIAO  TIẾP ": {"resources": [_resource("communication")]}}

    roadmap = build_roadmap([" GIAO  TIẾP ", decomposed, ""], resources)

    assert _scheduled(roadmap) == ["giao tiếp"]
    assert len(_documents(roadmap)) == 1


def test_string_and_generator_inputs_are_supported() -> None:
    assert _scheduled(build_roadmap("Python", _catalog("python"))) == ["python"]
    assert _scheduled(build_roadmap((s for s in ["sql", "git"]), {})) == ["sql", "git"]


def test_shared_url_is_scheduled_once_and_referenced_across_weeks() -> None:
    resources = {
        "sql": {"resources": [_resource("sql", url="https://EXAMPLE.org/shared/#intro")]},
        "python": {"resources": [_resource("python", url="https://example.org/shared")]},
    }

    roadmap = build_roadmap(["sql", "python"], resources, weeks=2)

    assert len(_documents(roadmap)) == 1
    assert roadmap[0]["resources"][0]["skills"] == ["sql", "python"]
    assert roadmap[1]["resources"] == []
    assert roadmap[1]["resource_keys"]["python"] == roadmap[0]["resource_keys"]["sql"]
    assert roadmap[1]["skills_without_resources"] == []


def test_same_id_with_different_urls_is_one_resource() -> None:
    resources = _catalog("sql", "python")
    resources["sql"]["resources"][0]["id"] = "shared"
    resources["python"]["resources"][0]["id"] = "shared"

    assert len(_documents(build_roadmap(["sql", "python"], resources))) == 1


def test_duplicate_identity_chains_merge_all_skill_references() -> None:
    resources = {
        "a": {"resources": [_resource("first", url="https://example.org/a")]},
        "b": {"resources": [_resource("second", url="https://example.org/b")]},
        "c": {"resources": [_resource("second", url="https://example.org/a")]},
    }

    roadmap = build_roadmap(["a", "b", "c"], resources)

    assert len(_documents(roadmap)) == 1
    assert _documents(roadmap)[0]["skills"] == ["a", "b", "c"]
    assert {key for week in roadmap for keys in week["resource_keys"].values() for key in keys} == {
        "url:https://example.org/a"
    }


def test_multiple_resources_for_one_skill_are_kept_once() -> None:
    resources = {"sql": {"resources": [_resource("a"), _resource("b"), _resource("a")]}}

    roadmap = build_roadmap(["sql"], resources)

    assert [r["id"] for r in _documents(roadmap)] == ["a", "b"]
    assert len(roadmap[0]["resource_keys"]["sql"]) == 2


def test_url_path_and_query_case_are_not_conflated() -> None:
    resources = {"sql": {"resources": [
        _resource("upper-path", url="https://example.org/Docs?topic=SQL"),
        _resource("lower-path", url="https://example.org/docs?topic=SQL"),
        _resource("lower-query", url="https://example.org/docs?topic=sql"),
    ]}}

    assert len(_documents(build_roadmap(["sql"], resources))) == 3


def test_id_only_and_url_only_resources_have_usable_keys() -> None:
    resources = {"sql": {"resources": [
        _resource("offline", url=""),
        _resource("url-only", url="https://example.org/sql"),
    ]}}

    assert [r["key"] for r in _documents(build_roadmap(["sql"], resources))] == [
        "url:https://example.org/sql"
    ]


def test_records_without_resource_identity_do_not_hide_missing_materials() -> None:
    resources = {"sql": {"resources": [{"title": "No reference"}, {"url": "javascript:alert(1)"}]}}

    roadmap = build_roadmap(["sql"], resources)

    assert roadmap[0]["resources"] == []
    assert roadmap[0]["skills_without_resources"] == ["sql"]


def test_inputs_and_nested_resource_metadata_are_not_mutated() -> None:
    missing = ["sql", "python"]
    details = [{"name": "python", "weight": 3, "level": 2}]
    resources = _catalog(*missing)
    resources["python"]["resources"][0]["extra"] = {"tags": ["beginner"]}
    original = deepcopy((missing, resources, details))

    roadmap = build_roadmap(missing, resources, missing_details=details)
    assert (missing, resources, details) == original
    roadmap[0]["resources"][0]["extra"]["tags"].append("changed")
    roadmap[0]["skills"].clear()

    assert (missing, resources, details) == original
    assert build_roadmap(missing, resources, missing_details=details)[0]["skills"] == ["python"]


@pytest.mark.parametrize("weeks", [0, -1, True, False, 1.5, "4", None])
def test_invalid_week_counts_raise(weeks) -> None:
    with pytest.raises(ValueError, match="weeks"):
        build_roadmap(["sql"], {}, weeks)


@pytest.mark.parametrize("resources", [None, [], "resources.json"])
def test_resource_catalog_must_be_a_mapping(resources) -> None:
    with pytest.raises(TypeError, match="resources"):
        build_roadmap(["sql"], resources)


@pytest.mark.parametrize("missing", [["sql", 3], [None]])
def test_missing_skill_entries_must_be_strings(missing) -> None:
    with pytest.raises(TypeError, match="chuỗi"):
        build_roadmap(missing, {})


@pytest.mark.parametrize("weight", [0, -1, True, "3", None, float("nan"), float("inf")])
def test_invalid_metadata_weights_raise(weight) -> None:
    with pytest.raises(ValueError, match="weight"):
        build_roadmap(["sql"], {}, missing_details=[{"name": "sql", "weight": weight}])


@pytest.mark.parametrize("details", [
    ["sql"], [{}], [{"name": "unknown"}], [{"name": "sql"}, {"name": " SQL "}],
])
def test_inconsistent_metadata_is_rejected(details) -> None:
    with pytest.raises(ValueError, match="missing_details"):
        build_roadmap(["sql"], {}, missing_details=details)


@pytest.mark.parametrize("resources", [
    {"sql": []}, {"sql": {}}, {"sql": {"resources": "url"}},
    {"sql": {"resources": [None]}}, {"sql": {"resources": ["url"]}},
    {"sql": {"resources": []}, " SQL ": {"resources": []}}, {3: {"resources": []}},
])
def test_malformed_requested_resource_data_is_rejected(resources) -> None:
    with pytest.raises(ValueError):
        build_roadmap(["sql"], resources)


def test_every_repository_role_can_flow_from_matcher_to_roadmap() -> None:
    roles = json.loads((ROOT / "data/roles.json").read_text(encoding="utf-8"))
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))

    for role in roles:
        gap = match_role([], role)
        roadmap = build_roadmap(gap["missing"], resources, missing_details=gap["missing_details"])
        expected = [skill["name"] for skill in sorted(role["skills"], key=lambda s: -s["weight"])]
        assert _scheduled(roadmap) == expected, role["id"]
        documents = _documents(roadmap)
        assert len({doc["key"] for doc in documents}) == len(documents), role["id"]
        assert len({doc["id"] for doc in documents}) == len(documents), role["id"]
        assert len({doc["url"] for doc in documents}) == len(documents), role["id"]
        introduced: set[str] = set()
        for week in roadmap:
            introduced.update(doc["key"] for doc in week["resources"])
            issues = {issue["skill"] for issue in week["unresolved"]}
            assert set(week["skills_without_resources"]) <= issues, role["id"]
            for skill, keys in week["resource_keys"].items():
                assert not keys or set(keys) <= introduced, (role["id"], skill)
                assert all(
                    catalog_resource["verified"] is True
                    and catalog_resource["content_review_status"] in {"reviewed", "partial"}
                    and catalog_resource.get("review_note", "").strip()
                    for catalog_resource in (next(doc for doc in documents if doc["key"] == key) for key in keys)
                ), (role["id"], skill)
        assert build_roadmap(gap["missing"], resources, missing_details=gap["missing_details"]) == roadmap


def test_cv_jd_gap_can_build_roadmap_without_metadata() -> None:
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    gap = match_cv_to_jd("Python developer", "Python, SQL and Docker")

    roadmap = build_roadmap(gap["missing"], resources)

    assert _scheduled(roadmap) == gap["missing"] == ["sql", "docker"]
    assert _documents(roadmap)


def test_legacy_app_adapter_loads_relative_to_module_and_returns_flat_cards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    resources = _catalog("sql", "python")
    resources["python"]["resources"][0]["url"] = resources["sql"]["resources"][0]["url"]
    (data_dir / "resources.json").write_text(json.dumps(resources), encoding="utf-8")
    monkeypatch.setattr(recommender, "_DATA_DIR", data_dir)
    monkeypatch.chdir(tmp_path)

    cards = recommender.get_course_recommendations(["SQL", "python"])

    assert len(cards) == 1
    assert cards[0]["course_name"] == "sql tutorial"
    assert cards[0]["link"] == "https://example.org/sql"
    assert cards[0]["skills_achieved"] == ["sql", "python"]
    assert recommender.get_course_recommendations([]) == []
