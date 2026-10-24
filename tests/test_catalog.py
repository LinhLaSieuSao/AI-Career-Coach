"""Catalog schema, metadata, and cwd regressions shared by app and Interview."""

import json

import pytest

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.skill_extractor import build_vocabulary


@pytest.mark.parametrize("wrapper", [None, "roles", "positions"])
def test_catalog_formats_preserve_skill_metadata(tmp_path, wrapper):
    role = {
        "id": "sample", "name": "Sample", "name_vi": "Mẫu", "category": "custom",
        "skills": [{"name": "python", "weight": 3, "level": 2, "extra": "kept"}],
    }
    payload = [role] if wrapper is None else {wrapper: [role]}
    path = tmp_path / "roles.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_roles(path)
    assert len(loaded) == 1
    assert loaded[0]["skills"] == role["skills"]
    assert loaded[0]["category"] == "custom"
    assert loaded[0]["name_vi"] == "Mẫu"
    assert loaded[0]["title"] == "Sample"


def test_legacy_positions_are_matcher_ready(tmp_path):
    path = tmp_path / "roles.json"
    path.write_text(json.dumps({"positions": [{
        "title": "Legacy", "required_skills": ["Python", {"name": "SQL", "weight": 2}],
    }]}), encoding="utf-8")
    role = load_roles(path)[0]
    assert role["id"] == role["name"] == role["title"] == "Legacy"
    assert role["skills"] == ["Python", {"name": "SQL", "weight": 2}]


@pytest.mark.parametrize("payload", [
    {}, {"roles": {}}, {"roles": None}, ["bad"], [{"name": "no ID"}],
    [{"id": "duplicate"}, {"id": "duplicate"}], [{"id": "bad", "skills": {}}],
])
def test_invalid_catalog_fails_explicitly(tmp_path, payload):
    path = tmp_path / "roles.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_roles(path)


def test_real_catalog_is_complete_and_independent_of_cwd(tmp_path, monkeypatch):
    raw = json.loads((DATA_DIR / "roles.json").read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)
    roles = load_roles()
    assert len(roles) == len(raw) == 131
    assert {role["id"] for role in roles} == {role["id"] for role in raw}
    assert [role["skills"] for role in roles] == [role["skills"] for role in raw]


def test_recognition_vocabulary_extends_roles_without_adding_requirements(tmp_path, monkeypatch):
    roles = load_roles()
    monkeypatch.chdir(tmp_path)
    vocabulary = load_skill_vocabulary()
    independent = {"pandas", "mysql", "english", "google tag manager", ".net core"}
    assert independent <= vocabulary
    assert independent.isdisjoint(build_vocabulary(roles))
    assert build_vocabulary(roles) <= vocabulary
    assert roles == load_roles()


@pytest.mark.parametrize("payload", [{}, [""], [42], ["MySQL", "mysql"]])
def test_recognition_catalog_rejects_invalid_or_duplicate_entries(tmp_path, payload):
    (tmp_path / "skill_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_skill_vocabulary([], data_dir=tmp_path)


def test_legacy_or_isolated_catalog_without_extension_keeps_role_vocabulary(tmp_path):
    assert load_skill_vocabulary([{"skills": ["SQL"]}], data_dir=tmp_path) == {"sql"}
