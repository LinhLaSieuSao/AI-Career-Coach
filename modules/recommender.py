"""Recommend legacy courses and the newer skill-indexed learning resources."""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
RESOURCES_JSON_PATH = DATA_DIR / "resources.json"


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFC", value).strip().casefold()


@lru_cache(maxsize=1)
def _load_resources() -> dict[str, Any]:
    try:
        with RESOURCES_JSON_PATH.open("r", encoding="utf-8") as source:
            payload = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise FileNotFoundError(
            f"Unable to load learning resources from {RESOURCES_JSON_PATH}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Learning resource data in {RESOURCES_JSON_PATH} must be an object.")
    return payload


def _legacy_recommendations(missing: set[str], payload: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    courses = payload.get("courses", [])
    if not isinstance(courses, list):
        return recommendations

    for course in courses:
        if not isinstance(course, dict):
            continue
        skills = course.get("skills_achieved", [])
        if isinstance(skills, str):
            skills = [skills]
        matched = [skill for skill in skills if isinstance(skill, str) and _normalize(skill) in missing]
        if matched:
            recommendations.append(
                {
                    "course_name": course.get("course_name", "Tài liệu học tập"),
                    "link": course.get("link", ""),
                    "provider": course.get("provider", ""),
                    "type": course.get("type", "course"),
                    "language": course.get("language", ""),
                    "cost": course.get("cost", ""),
                    "skills_achieved": matched,
                }
            )
    return recommendations


def _skill_resource_recommendations(
    missing: set[str], payload: dict[str, Any]
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for key, group in payload.items():
        if not isinstance(group, dict) or not isinstance(group.get("resources"), list):
            continue
        skill = group.get("skill_name", key)
        if not isinstance(skill, str) or _normalize(skill) not in missing:
            continue

        for resource in group["resources"]:
            if not isinstance(resource, dict):
                continue
            url = resource.get("url", "")
            title = resource.get("title", "Tài liệu học tập")
            recommendations.append(
                {
                    "course_name": title,
                    "link": url,
                    "provider": resource.get("provider", ""),
                    "type": resource.get("type", "resource"),
                    "language": resource.get("language", ""),
                    "cost": resource.get("cost", ""),
                    "skills_achieved": [skill],
                    "resource_id": resource.get("id", ""),
                    "level_from": resource.get("level_from"),
                    "level_to": resource.get("level_to"),
                    "duration_hours": resource.get("duration_hours"),
                    "verified": resource.get("verified"),
                    "last_checked": resource.get("last_checked", ""),
                }
            )
    return recommendations


def get_course_recommendations(missing_skills: Iterable[str]) -> list[dict[str, Any]]:
    """Return recommendations from both the old course list and new resource groups."""
    missing = {
        _normalize(skill)
        for skill in missing_skills
        if isinstance(skill, str) and skill.strip()
    }
    if not missing:
        return []

    payload = _load_resources()
    combined = _legacy_recommendations(missing, payload)
    combined.extend(_skill_resource_recommendations(missing, payload))

    unique: dict[str, dict[str, Any]] = {}
    for item in combined:
        identity = item.get("resource_id") or item.get("link") or item.get("course_name")
        if identity:
            unique.setdefault(str(identity), item)
    return list(unique.values())
