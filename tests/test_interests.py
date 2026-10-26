"""Static, normalized Holland-interest mappings and conservative resolution."""

from __future__ import annotations

import math

import pytest

from modules.catalog import load_roles
from modules.interests import (
    DIMENSIONS,
    interest_fit,
    load_interest_activities,
    load_role_family_vectors,
    resolve_activity_ids,
    user_interest_vector,
)
from modules.submission import SUBMISSION_REQUIRED_INPUT_MESSAGE, validate_submission_input


def test_activity_and_role_vectors_are_normalized_and_cover_catalog():
    activities = load_interest_activities()
    assert len(activities) == 18
    assert {activity["dimension"] for activity in activities} == set(DIMENSIONS)
    for row in activities:
        assert math.isclose(sum(value**2 for value in row["vector"].values()), 1.0, abs_tol=1e-8)
    role_vectors = load_role_family_vectors()
    assert set(role_vectors) == {role["id"] for role in load_roles()}
    assert len({item["family_id"] for item in role_vectors.values()}) == 15


def test_interest_mapping_is_exact_curated_and_cosine_bounded():
    assert resolve_activity_ids(free_text_interests=["Tìm quy luật và phân tích số liệu"]) == ["analyze_data"]
    assert resolve_activity_ids(free_text_interests=["analyze_data-ish unrelated phrase"]) == []
    vector = user_interest_vector(["analyze_data"])
    assert vector is not None and math.isclose(sum(value**2 for value in vector.values()), 1.0)
    assert interest_fit(vector, vector) == pytest.approx(1.0)
    assert 0 <= interest_fit(vector, {dimension: 0 for dimension in DIMENSIONS}) <= 1


@pytest.mark.parametrize(
    "skills,cv_present,expected",
    [([], False, False), (["  "], False, False), (["sql"], False, True), ([], True, True), ([" ", "python"], True, True)],
)
def test_submission_gate_has_one_shared_minimum_rule(skills, cv_present, expected):
    accepted, message = validate_submission_input(skills, cv_present)
    assert accepted is expected
    assert (message == "") is expected
    if not expected:
        assert message == SUBMISSION_REQUIRED_INPUT_MESSAGE


def test_submission_gate_rejects_wrong_input_types():
    with pytest.raises(TypeError):
        validate_submission_input("sql", False)
    with pytest.raises(TypeError):
        validate_submission_input(["sql"], 1)
