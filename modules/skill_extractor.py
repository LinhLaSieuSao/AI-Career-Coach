"""Normalize skill names against the project's sample career data."""

from __future__ import annotations

import json
import unicodedata
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
SKILL_ALIASES = {"py": "python"}


@lru_cache(maxsize=1)
def _skill_catalog() -> dict[str, str]:
    """Load canonical skills from all bundled sample data files."""
    catalog: dict[str, str] = {}

    def add_values(values: list[str] | str) -> None:
        if isinstance(values, str):
            values = [values]
        for value in values:
            cleaned = " ".join(str(value).split())
            if cleaned:
                catalog.setdefault(cleaned.casefold(), cleaned)

    roles_path = DATA_DIR / "roles.json"
    if not roles_path.exists():
        roles_path = DATA_DIR / "careers.json"
    with roles_path.open(encoding="utf-8") as data_file:
        for role in json.load(data_file).get("positions", []):
            add_values(role.get("required_skills", []))

    resources_path = DATA_DIR / "resources.json"
    if not resources_path.exists():
        resources_path = DATA_DIR / "courses.json"
    with resources_path.open(encoding="utf-8") as data_file:
        for resource in json.load(data_file).get("courses", []):
            add_values(resource.get("skills_achieved", []))

    with (DATA_DIR / "interview_questions.json").open(encoding="utf-8") as data_file:
        questions_data = json.load(data_file)
    if isinstance(questions_data.get("interview_questions"), list):
        for entry in questions_data["interview_questions"]:
            add_values(entry.get("skill", []))
    else:
        for role_questions in questions_data.values():
            for question in role_questions:
                add_values(question.get("keywords", []))

    return catalog


def normalize_skill(value: str | None) -> str | None:
    """Return a canonical sample-data skill, or ``None`` if it is unknown.

    Matching ignores case and surrounding whitespace, supports the ``py`` alias,
    and accepts close spellings when the match is sufficiently strong.
    """
    cleaned = " ".join(unicodedata.normalize("NFC", value or "").split())
    if not cleaned:
        return None

    key = cleaned.casefold()
    key = SKILL_ALIASES.get(key, key)
    catalog = _skill_catalog()
    if key in catalog:
        return catalog[key]

    candidate = get_close_matches(key, catalog.keys(), n=1, cutoff=0.80)
    return catalog[candidate[0]] if candidate else None
