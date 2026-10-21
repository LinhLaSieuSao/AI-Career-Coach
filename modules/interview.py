"""Load practice questions from the role-oriented or legacy JSON format."""

import json
import os
import random
from typing import Dict, Iterable, List


INTERVIEW_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "Data", "interview_questions.json"
)


def _load_questions() -> dict:
    """Read role-oriented interview questions from the bundled JSON file."""
    with open(INTERVIEW_JSON_PATH, "r", encoding="utf-8") as data_file:
        return json.load(data_file)


def _pick_questions(records: list[dict], limit: int) -> List[str]:
    pool = [record.get("question", "") for record in records if record.get("question")]
    return random.sample(pool, min(limit, len(pool))) if pool and limit > 0 else []


def generate_interview_questions(
    missing_skills: Iterable[str],
    max_per_skill: int = 2,
    *,
    role: str | None = None,
) -> List[str]:
    """Return practice questions for a selected role or matching skill keywords.

    The current data format groups records by role and stores each question's
    keywords. The old ``interview_questions`` skill-list format remains supported.
    """
    if max_per_skill <= 0:
        return []

    questions_data = _load_questions()
    role_keys = {key.casefold(): key for key, value in questions_data.items() if isinstance(value, list)}

    if role and role.casefold() in role_keys:
        return _pick_questions(questions_data[role_keys[role.casefold()]], max_per_skill)

    skills = {skill.strip().casefold() for skill in missing_skills if skill and skill.strip()}
    if not skills:
        return []

    # Current format: find role questions whose keyword list mentions a missing skill.
    if role_keys:
        matching: list[dict] = []
        for role_name in role_keys.values():
            for record in questions_data[role_name]:
                keywords = {word.strip().casefold() for word in record.get("keywords", [])}
                if skills.intersection(keywords):
                    matching.append(record)
        return _pick_questions(matching, max_per_skill)

    # Legacy format: one entry per skill with a pool of questions.
    legacy_entries = questions_data.get("interview_questions", [])
    selected: List[str] = []
    for entry in legacy_entries:
        skill = entry.get("skill", "").strip().casefold()
        pool = entry.get("questions", [])
        if skill in skills and pool:
            selected.extend(random.sample(pool, min(max_per_skill, len(pool))))
    return selected
