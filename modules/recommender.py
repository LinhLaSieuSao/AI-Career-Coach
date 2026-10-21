import json
import os
from typing import List, Dict, Iterable

# Path to the JSON file containing course information.
COURSES_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data", "courses.json")


def _load_courses() -> List[Dict]:
    """Load the list of courses from the JSON file.

    Returns
    -------
    List[Dict]
        Each dict corresponds to a course entry as defined in ``courses.json``.
    """
    try:
        with open(COURSES_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # The file uses a top‑level key ``courses``.
        return data.get("courses", [])
    except Exception as exc:
        # If the file cannot be read, return an empty list – callers can decide how to handle it.
        raise FileNotFoundError(f"Unable to load courses from {COURSES_JSON_PATH}: {exc}")


def get_course_recommendations(missing_skills: Iterable[str]) -> List[Dict]:
    """Return courses that cover at least one of the missing skills.

    Parameters
    ----------
    missing_skills: Iterable[str]
        A collection of skill names that the user still needs to acquire.

    Returns
    -------
    List[Dict]
        A list of course dictionaries (as stored in ``courses.json``) that match the
        provided skills. Each returned dict contains the original keys, e.g.
        ``course_name``, ``link`` and ``skills_achieved``.
    """
    missing_set = {skill.strip().lower() for skill in missing_skills}
    if not missing_set:
        return []

    courses = _load_courses()
    recommendations: List[Dict] = []
    for course in courses:
        # Normalise the course's skill list for case‑insensitive comparison.
        course_skills = {s.strip().lower() for s in course.get("skills_achieved", [])}
        if missing_set.intersection(course_skills):
            recommendations.append(course)
    return recommendations

