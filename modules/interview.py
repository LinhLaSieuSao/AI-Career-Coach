import json
import os
import random
from typing import List, Iterable, Dict

# Path to the JSON file with interview questions.
INTERVIEW_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "Data", "interview_questions.json"
)


def _load_questions() -> List[Dict]:
    """Load interview questions from the JSON file.

    Returns a list of dicts, each with keys ``skill`` and ``questions``.
    """
    with open(INTERVIEW_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("interview_questions", [])


def generate_interview_questions(missing_skills: Iterable[str], max_per_skill: int = 2) -> List[str]:
    """Return a random selection of interview questions for the given skills.

    Parameters
    ----------
    missing_skills: Iterable[str]
        Skills the user needs to improve.
    max_per_skill: int, optional
        Maximum number of questions to pick for each skill (default 2).

    Returns
    -------
    List[str]
        A flat list of question strings.
    """
    skill_set = {s.strip().lower() for s in missing_skills}
    if not skill_set:
        return []

    questions_data = _load_questions()
    selected: List[str] = []
    for entry in questions_data:
        skill = entry.get("skill", "").strip().lower()
        if skill in skill_set:
            pool = entry.get("questions", [])
            if not pool:
                continue
            # Choose up to max_per_skill questions randomly without replacement.
            count = min(max_per_skill, len(pool))
            selected.extend(random.sample(pool, count))
    return selected

