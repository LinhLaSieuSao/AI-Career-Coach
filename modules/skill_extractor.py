"""Normalize skill names using every role, course, resource, and question file."""

from __future__ import annotations

import json
import unicodedata
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
SKILL_ALIASES = {"py": "python"}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def _add_skill_values(catalog: dict[str, str], values: Any) -> None:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return
    for value in values:
        cleaned = " ".join(str(value).split())
        if cleaned:
            catalog.setdefault(cleaned.casefold(), cleaned)


def _add_question_skills(catalog: dict[str, str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    entries = payload.get("interview_questions")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                _add_skill_values(catalog, entry.get("skill"))
                _add_skill_values(catalog, entry.get("keywords", []))
        return

    role_groups = payload.get("roles")
    if not isinstance(role_groups, dict):
        role_groups = {
            key: value for key, value in payload.items() if isinstance(value, list)
        }
    for questions in role_groups.values():
        if not isinstance(questions, list):
            continue
        for question in questions:
            if isinstance(question, dict):
                _add_skill_values(catalog, question.get("skill"))
                _add_skill_values(catalog, question.get("keywords", []))


@lru_cache(maxsize=1)
def _skill_catalog() -> dict[str, str]:
    """Build one cached catalog from all available data formats."""
    catalog: dict[str, str] = {}

    roles_path = DATA_DIR / "roles.json"
    if not roles_path.exists():
        roles_path = DATA_DIR / "careers.json"
    if roles_path.exists():
        role_data = _read_json(roles_path)
        if isinstance(role_data, list):
            role_groups = role_data
        elif isinstance(role_data, dict):
            role_groups = list(role_data.get("positions", [])) + list(role_data.get("roles", []))
        else:
            role_groups = []
        for role in role_groups:
            if not isinstance(role, dict):
                continue
            _add_skill_values(catalog, role.get("required_skills", []))
            skills = role.get("skills", [])
            if isinstance(skills, list):
                _add_skill_values(
                    catalog,
                    [
                        skill["name"]
                        for skill in skills
                        if isinstance(skill, dict) and isinstance(skill.get("name"), str)
                    ],
                )

    resources_path = DATA_DIR / "resources.json"
    if not resources_path.exists():
        resources_path = DATA_DIR / "courses.json"
    if resources_path.exists():
        resources_data = _read_json(resources_path)
        if isinstance(resources_data, dict):
            for key, group in resources_data.items():
                if key == "courses" and isinstance(group, list):
                    for course in group:
                        if isinstance(course, dict):
                            _add_skill_values(catalog, course.get("skills_achieved", []))
                    continue
                if not isinstance(group, dict):
                    continue
                _add_skill_values(catalog, group.get("skill_name", key))
                for resource in group.get("resources", []):
                    if isinstance(resource, dict):
                        _add_skill_values(catalog, resource.get("skills_achieved", []))

    question_files = [
        path
        for directory in (DATA_DIR / "interview_questions", DATA_DIR / "interview_question")
        if directory.is_dir()
        for path in sorted(directory.glob("*.json"), key=lambda item: item.name)
    ]
    single_file = DATA_DIR / "interview_questions.json"
    if single_file.is_file():
        question_files.append(single_file)
    for path in question_files:
        try:
            _add_question_skills(catalog, _read_json(path))
        except (OSError, json.JSONDecodeError):
            # Bad optional question data should not prevent the rest of the app loading.
            continue

    return catalog


def normalize_skill(value: str | None) -> str | None:
    """Return a canonical skill spelling, ignoring case and surrounding spaces."""
    cleaned = " ".join(unicodedata.normalize("NFC", value or "").split())
    if not cleaned:
        return None

    key = SKILL_ALIASES.get(cleaned.casefold(), cleaned.casefold())
    catalog = _skill_catalog()
    if key in catalog:
        return catalog[key]

    candidate = get_close_matches(key, catalog.keys(), n=1, cutoff=0.80)
    return catalog[candidate[0]] if candidate else None
