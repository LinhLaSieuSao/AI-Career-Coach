"""Tests for skill-based role and CV-to-JD matching."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from modules import matcher


@pytest.fixture
def skill_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a small isolated role catalog and alias map."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    roles = [
        {
            "id": "sample_role",
            "name": "Sample Role",
            "name_vi": "Vị trí mẫu",
            "skills": [
                {"name": "python", "level": 2, "weight": 3},
                {"name": "sql", "level": 1, "weight": 2},
                {"name": "nodejs", "level": 2, "weight": 1},
                {"name": "docker", "level": 1, "weight": 2},
            ],
        }
    ]
    (data_dir / "roles.json").write_text(json.dumps(roles), encoding="utf-8")
    (data_dir / "skill_aliases.json").write_text(
        json.dumps({"node.js": "nodejs", "py": "python"}), encoding="utf-8"
    )
    monkeypatch.setattr(matcher, "_DATA_DIR", data_dir)
    matcher._load_role_catalog.cache_clear()
    matcher._load_alias_map.cache_clear()
    yield data_dir
    matcher._load_role_catalog.cache_clear()
    matcher._load_alias_map.cache_clear()


@pytest.fixture
def jd_skill_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "JDData"
    data_dir.mkdir()
    skills = ["python", "sql", "nodejs", "docker", "postgresql", "giải quyết vấn đề", "git"]
    roles = [{"id": "sample_role", "name": "Sample Role", "skills": skills}]
    (data_dir / "roles.json").write_text(json.dumps(roles, ensure_ascii=False), encoding="utf-8")
    (data_dir / "skill_aliases.json").write_text(
        json.dumps({"node.js": "nodejs", "xử lý vấn đề": "giải quyết vấn đề"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(matcher, "_DATA_DIR", data_dir)
    matcher._load_role_catalog.cache_clear()
    matcher._load_alias_map.cache_clear()
    yield data_dir
    matcher._load_role_catalog.cache_clear()
    matcher._load_alias_map.cache_clear()


def _role() -> dict:
    return {
        "id": "sample_role",
        "name": "Sample Role",
        "skills": [
            {"name": "python", "level": 2, "weight": 3},
            {"name": "sql", "level": 1, "weight": 2},
            {"name": "nodejs", "level": 2, "weight": 1},
            {"name": "docker", "level": 1, "weight": 2},
        ],
    }


def test_match_role_all_skills_match_with_alias_and_case(skill_data: Path) -> None:
    result = matcher.match_role(["PYTHON", "SQL", "Node.js", "Docker"], _role())

    assert result == {
        "role_id": "sample_role",
        "role_name": "Sample Role",
        "percent": 100.0,
        "matched": ["python", "sql", "nodejs", "docker"],
        "missing": [],
        "missing_details": [],
    }


def test_match_role_uses_role_weights_and_lists_missing_in_role_order(
    skill_data: Path,
) -> None:
    result = matcher.match_role(["python", "Node.js"], _role())

    assert result["percent"] == 50.0  # (3 + 1) / (3 + 2 + 1 + 2)
    assert result["matched"] == ["python", "nodejs"]
    assert result["missing"] == ["sql", "docker"]
    assert result["missing_details"] == [
        {"name": "sql", "weight": 2, "level": 1},
        {"name": "docker", "weight": 2, "level": 1},
    ]


def test_match_role_no_matching_skills_returns_zero(skill_data: Path) -> None:
    result = matcher.match_role(["unlisted skill"], _role())

    assert result["percent"] == 0.0
    assert result["matched"] == []
    assert result["missing"] == ["python", "sql", "nodejs", "docker"]
    assert result["missing_details"] == _role()["skills"]


@pytest.mark.parametrize("skills", [None, [], "", ["  "]])
def test_match_role_empty_skills_returns_zero(skills, skill_data: Path) -> None:
    result = matcher.match_role(skills, _role())

    assert result["percent"] == 0.0
    assert result["matched"] == []
    assert result["missing"] == ["python", "sql", "nodejs", "docker"]
    assert result["missing_details"] == _role()["skills"]


def test_match_role_deduplicates_candidate_skills(skill_data: Path) -> None:
    result = matcher.match_role(["Python", "python", "PY", "py"], _role())

    assert result["percent"] == 37.5
    assert result["matched"] == ["python"]


def test_match_role_ignores_extra_candidate_skills(skill_data: Path) -> None:
    result = matcher.match_role(["python", "unknown", "sql"], _role())

    assert result["percent"] == 62.5
    assert result["matched"] == ["python", "sql"]


def test_match_role_empty_role_has_zero_percent(skill_data: Path) -> None:
    result = matcher.match_role(["python"], {"id": "empty", "skills": []})

    assert result["percent"] == 0.0
    assert result["matched"] == []
    assert result["missing"] == []
    assert result["missing_details"] == []


def test_match_role_accepts_string_skill_entries_with_default_weight(
    skill_data: Path,
) -> None:
    role = {"id": "legacy", "name": "Legacy", "skills": ["python", "sql"]}

    result = matcher.match_role(["python"], role)

    assert result["percent"] == 50.0
    assert result["matched"] == ["python"]
    assert result["missing"] == ["sql"]
    assert result["missing_details"] == [{"name": "sql", "weight": 1, "level": None}]


def test_missing_details_preserves_role_order_values_and_normalized_names(
    skill_data: Path,
) -> None:
    role = {
        "skills": [
            {"name": " SQL ", "weight": 1.5, "level": 2},
            {"name": "Node.js", "weight": 3, "level": 1},
            {"name": "python", "weight": 2, "level": 3},
        ]
    }

    result = matcher.match_role(["py"], role)

    assert result["missing"] == ["SQL", "Node.js"]
    assert result["missing_details"] == [
        {"name": "SQL", "weight": 1.5, "level": 2},
        {"name": "Node.js", "weight": 3, "level": 1},
    ]


def test_missing_details_defaults_for_role_entries_without_metadata(skill_data: Path) -> None:
    role = {"skills": [{"name": "python"}, {"name": "sql", "weight": 2}]}

    result = matcher.match_role([], role)

    assert result["missing_details"] == [
        {"name": "python", "weight": 1, "level": None},
        {"name": "sql", "weight": 2, "level": None},
    ]


def test_required_level_does_not_change_presence_based_matching(skill_data: Path) -> None:
    role = _role()
    original = matcher.match_role(["py"], role)
    role["skills"][0]["level"] = 3

    assert matcher.match_role(["py"], role) == original


def test_missing_details_does_not_mutate_or_expose_role_records(skill_data: Path) -> None:
    role = _role()
    before = deepcopy(role)

    result = matcher.match_role(["py"], role)
    assert role == before
    result["missing_details"][0]["weight"] = 99
    result["missing_details"][0]["level"] = 99
    result["missing_details"][0]["name"] = "changed"
    result["missing_details"].clear()

    assert role == before
    assert matcher.match_role(["py"], role)["missing_details"] == before["skills"][1:]


@pytest.mark.parametrize(
    "role, message",
    [
        ({"id": "bad"}, "trường 'skills'"),
        ({"skills": [{"weight": 1}]}, "thiếu tên kỹ năng"),
        ({"skills": [{"name": "python", "weight": 0}]}, "số dương"),
        ({"skills": [{"name": "python", "weight": float("inf")}]}, "số dương"),
        ({"skills": [{"name": "python", "weight": float("nan")}]}, "số dương"),
        (
            {"skills": [{"name": "python"}, {"name": " PYTHON "}]},
            "kỹ năng trùng",
        ),
    ],
)
def test_match_role_rejects_invalid_role_data(role, message, skill_data: Path) -> None:
    with pytest.raises(ValueError, match=message):
        matcher.match_role(["python"], role)


def test_match_role_requires_role_mapping(skill_data: Path) -> None:
    with pytest.raises(TypeError, match="role phải là"):
        matcher.match_role(["python"], "sample_role")


def test_match_role_rejects_non_string_candidate_skill(skill_data: Path) -> None:
    with pytest.raises(TypeError, match="Mỗi kỹ năng ứng viên phải là chuỗi"):
        matcher.match_role(["python", 3], _role())


def test_match_cv_to_jd_returns_extracted_and_missing_skills(skill_data: Path) -> None:
    result = matcher.match_cv_to_jd(
        "I use Python and Node.js.",
        "Need Python, SQL, Node.js, and Docker.",
    )

    assert result == {
        "percent": 50.0,
        "cv_skills": ["python", "nodejs"],
        "jd_skills": ["python", "sql", "nodejs", "docker"],
        "matched": ["python", "nodejs"],
        "missing": ["sql", "docker"],
    }


@pytest.mark.parametrize(
    "cv_text, jd_text, message",
    [
        ("", "Need Python", "CV không có nội dung"),
        ("Python", "   ", "Mô tả công việc đang trống"),
        ("No known technical terms", "Need Python", "Không nhận diện được kỹ năng trong CV"),
        ("Python developer", "No known technical terms", "Không nhận diện được kỹ năng trong mô tả công việc"),
    ],
)
def test_match_cv_to_jd_rejects_empty_or_unrecognized_text(
    cv_text: str, jd_text: str, message: str, skill_data: Path
) -> None:
    with pytest.raises(ValueError, match=message):
        matcher.match_cv_to_jd(cv_text, jd_text)


def test_role_and_alias_files_are_loaded_relative_to_module_data_dir(
    skill_data: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    result = matcher.match_cv_to_jd("Node.js", "Need nodejs")

    assert result["percent"] == 100.0
    assert result["matched"] == ["nodejs"]


def test_match_role_works_with_a_role_from_repository_data() -> None:
    roles = matcher._load_role_catalog()
    role = next(role for role in roles if role["id"] == "backend_developer_java")

    result = matcher.match_role(["Java", "GitHub"], role)

    assert result["percent"] == 23.8
    assert result["matched"] == ["java", "git"]
    assert result["missing"] == [
        "spring boot",
        "rest api",
        "sql",
        "giải quyết vấn đề",
        "docker",
        "giao tiếp",
        "làm việc nhóm",
        "linux",
    ]


def test_missing_details_matches_repository_roles_and_resource_keys() -> None:
    roles = matcher._load_role_catalog()
    resources = json.loads((matcher._DATA_DIR / "resources.json").read_text(encoding="utf-8"))

    for role in roles:
        candidate_skills = [role["skills"][0]["name"]] if role["skills"] else []
        result = matcher.match_role(candidate_skills, role)
        expected = [skill for skill in role["skills"] if skill["name"] not in result["matched"]]

        assert result["missing_details"] == expected, role["id"]
        assert [detail["name"] for detail in result["missing_details"]] == result["missing"]
        assert all(name in resources for name in result["missing"]), role["id"]


def test_cv_jd_independent_catalog_skills_do_not_match_parent_technologies():
    result = matcher.match_cv_to_jd("pandas MySQL English Google Tag Manager .NET Core", "Python SQL tiếng Anh chuyên ngành Google Analytics ASP.NET Core")
    assert result["cv_skills"] == ["pandas", "mysql", "english", "google tag manager", ".net core"]
    assert result["percent"] == 0.0
    assert result["matched"] == []
    assert result["missing"] == result["jd_skills"]
    exact = matcher.match_cv_to_jd("pandas MySQL English GTM .NET Core", "pandas MySQL English Google Tag Manager .NET Core")
    assert exact["percent"] == 100.0


def test_jd_extractor_classifies_only_explicit_sections_and_preserves_unclassified(jd_skill_data):
    result = matcher.extract_jd_skill_requirements(
        "Trách nhiệm:\nDùng Node.js hằng ngày.\n"
        "Yêu cầu bắt buộc: Python và SQL.\n"
        "Ưu tiên:\nDocker"
    )

    assert result == {
        "all_skills": ["nodejs", "python", "sql", "docker"],
        "must_have": ["python", "sql"],
        "nice_to_have": ["docker"],
        "unclassified": ["nodejs"],
    }


def test_jd_extractor_keeps_skills_unclassified_without_explicit_heading(jd_skill_data):
    result = matcher.extract_jd_skill_requirements("Python, SQL và Docker là những công cụ quen thuộc.")

    assert result["must_have"] == []
    assert result["nice_to_have"] == []
    assert result["unclassified"] == ["python", "sql", "docker"]


def test_jd_extractor_handles_multiple_explicit_sections_in_one_paragraph(jd_skill_data):
    result = matcher.extract_jd_skill_requirements(
        "Yêu cầu bắt buộc: Python và SQL. Ưu tiên: Docker; Trách nhiệm: Node.js"
    )

    assert result["must_have"] == ["python", "sql"]
    assert result["nice_to_have"] == ["docker"]
    assert result["unclassified"] == ["nodejs"]


def test_jd_extractor_normalizes_alias_in_explicit_must_have_section(jd_skill_data):
    result = matcher.extract_jd_skill_requirements("Yêu cầu:\nCó khả năng xử lý vấn đề.")

    assert result["must_have"] == ["giải quyết vấn đề"]
    assert result["unclassified"] == []


def test_categorized_jd_matching_uses_85_15_and_excludes_unclassified(jd_skill_data):
    result = matcher.compare_confirmed_jd_requirements(
        ["python", "sql", "nodejs", "postgresql", "xử lý vấn đề"],
        ["python", "sql", "nodejs", "docker", "postgresql"],
        ["giải quyết vấn đề", "git"],
        ["javascript"],
    )

    assert result["must_have"]["percent"] == 80.0
    assert result["nice_to_have"]["percent"] == 50.0
    assert result["unclassified"]["percent"] == 0.0
    assert result["overall_percent"] == 75.5
    assert result["method"] == "confirmed_categorized_skill_overlap"


def test_categorized_jd_matching_does_not_create_aggregate_without_must_have(jd_skill_data):
    result = matcher.compare_confirmed_jd_requirements(
        ["python"], [], ["python", "sql"], ["docker"]
    )

    assert result["overall_percent"] is None
    assert result["nice_to_have"]["percent"] == 50.0
    assert result["unclassified"]["percent"] == 0.0


def test_categorized_jd_matching_rejects_skill_assigned_to_multiple_groups(jd_skill_data):
    with pytest.raises(ValueError, match="đang nằm ở cả"):
        matcher.compare_confirmed_jd_requirements(["python"], ["python"], [], ["PYTHON"])
