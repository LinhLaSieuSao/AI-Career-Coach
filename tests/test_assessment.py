"""Explicit levels, weighted gaps, and local explainable role ranking."""

from copy import deepcopy
import socket

import pytest

from modules import compute_gap, suggest_roles
from modules import matcher
from modules.profile import build_profile, build_profile_from_cv, undo_profile_move
from modules.submission import prepare_submission


def role(skills=None, rid="sample"):
    return {"id": rid, "name": "Data engineer", "name_vi": "Kỹ sư dữ liệu",
            "skills": skills if skills is not None else [
                {"name": "python", "level": 3, "weight": 3},
                {"name": "sql", "level": 2, "weight": 1}]}


def test_profile_levels_are_explicit_canonical_and_do_not_infer_cv_proficiency():
    p = build_profile_from_cv({"levels": {"JS": 2, "New Skill": 1, "SQL": 0}}, "Python developer")
    assert p["levels"] == {"javascript": 2, "new skill": 1, "sql": 0}
    assert p["skills"] == ["javascript", "new skill", "python"]
    assert p["unrecognized_skills"] == ["new skill"]
    assert "python" not in p["levels"]
    assert build_profile({"skills": "SQL"})["levels"] == {}
    moved = build_profile({"skills": "interest: Git", "levels": {"JS": 2}})
    assert undo_profile_move(moved, 0)["levels"] == {"javascript": 2}


@pytest.mark.parametrize("levels", [None, [], {"SQL": True}, {"SQL": 1.0}, {"SQL": -1}, {"SQL": 4},
                                    {"": 1}, {" JS ": 1, "javascript": 2}])
def test_invalid_levels_reject_in_profile_gap_and_submission(levels):
    with pytest.raises((ValueError, TypeError)):
        build_profile({"skills": "SQL", "levels": levels})
    with pytest.raises((ValueError, TypeError)):
        compute_gap(levels, role())
    result = prepare_submission({"skills": "SQL", "levels": levels})
    assert result["accepted"] is False and result["profile"] is None and result["errors"]


def test_gap_counts_under_level_skills_as_missing_and_weights_partial_attainment():
    levels = {"Python3": 1, "SQL": 2}
    r = role(); before = deepcopy(r)
    result = compute_gap(levels, r)
    assert result == {"role_id": "sample", "items": [
        {"skill": "python", "required": 3, "current": 1, "gap": 2, "priority": 6, "status": "below_required"},
        {"skill": "sql", "required": 2, "current": 2, "gap": 0, "priority": 0, "status": "met"}],
        "match_percent": 50.0, "missing": ["python"]}
    assert matcher.match_role(["python", "sql"], r)["percent"] == 100.0
    assert r == before and levels == {"Python3": 1, "SQL": 2}


def test_gap_undeclared_zero_overqualified_and_empty_role():
    assert compute_gap({}, role())["items"][0]["status"] == "missing"
    assert compute_gap({}, role())["missing"] == ["python", "sql"]
    assert compute_gap({"python": 3, "sql": 3}, role())["match_percent"] == 100
    assert compute_gap({}, role([])) == {"role_id": "sample", "items": [], "match_percent": 0.0, "missing": []}
    assert compute_gap({}, role([{"name": "sql", "level": 0, "weight": 1}]))["items"][0]["status"] == "met"


def test_zero_requirement_is_excluded_even_when_its_weight_is_large():
    r = role([{"name": "sql", "level": 0, "weight": 1e308},
              {"name": "python", "level": 1, "weight": 1e-308}])
    assert compute_gap({"python": 1}, r)["match_percent"] == 100


@pytest.mark.parametrize("field,value", [("level", True), ("level", None), ("level", -1), ("level", 4),
                                        ("weight", 0), ("weight", True), ("weight", float("nan")), ("weight", float("inf"))])
def test_invalid_role_gap(field, value):
    r = role(); r["skills"][0][field] = value
    with pytest.raises(ValueError):
        compute_gap({}, r)


def test_gap_rejects_duplicate_alias_role_skills():
    with pytest.raises(ValueError, match="trùng"):
        compute_gap({}, role([{"name": "JS", "level": 1}, {"name": "javascript", "level": 2}]))


@pytest.fixture
def catalog(monkeypatch):
    roles = [role(rid="z"), role(rid="a"), {"id": "sales", "name": "Sales", "name_vi": "Bán hàng",
                                           "skills": [{"name": "giao tiếp", "weight": 1, "level": 2}]}]
    monkeypatch.setattr(matcher, "_load_role_catalog", lambda: roles)
    return roles


def test_suggestions_skill_only_tie_topk_and_reasons(catalog):
    result = suggest_roles({"skills": ["Python3"]}, top_k=2)
    assert [r["role_id"] for r in result] == ["a", "z"]
    assert result[0]["score"] == result[0]["skill_percent"] == 75
    assert result[0]["matched"] == ["python"] and result[0]["missing"] == ["sql"]
    assert result[0]["reasons"] and result[0]["method"] == "heuristic"
    assert suggest_roles({"skills": ["python"]}, top_k=0) == []


def test_suggestions_interest_only_combined_and_no_signal(catalog):
    assert [r["role_id"] for r in suggest_roles({"interests": "Bán hàng"})] == ["sales"]
    result = suggest_roles({"skills": ["python"], "interests": ["Data", "Sales"]})
    assert result[0]["score"] == 70  # 0.8*75 + 0.2*50, components normalized first.
    for profile in ({}, {"levels": {"sql": 3}}, {"skills": ["unknown"]}, {"interests": ["ai"]}):
        assert suggest_roles(profile) == []


def test_interest_phrase_cannot_bridge_independent_catalog_fields(catalog):
    assert suggest_roles({"interests": ["engineer kỹ"]}) == []


@pytest.mark.parametrize("k", [True, -1, 1.2, "5"])
def test_suggestions_invalid_k(catalog, k):
    with pytest.raises(ValueError):
        suggest_roles({"skills": ["sql"]}, k)


def test_real_catalog_suggestions_are_offline_and_do_not_mutate_profile(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    p = {"skills": ["java", "spring boot"], "interests": ["backend"], "levels": {"java": 1}}
    before = deepcopy(p)
    result = suggest_roles(p)
    assert result and len(result) <= 5
    assert any(r["role_id"] == "backend_developer_java" for r in result)
    assert all(0 < r["score"] <= 100 for r in result)
    assert p == before
