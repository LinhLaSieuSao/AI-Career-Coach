"""Load, select, and reveal interview question guidance from bundled data."""

from __future__ import annotations

import json
import logging
import random
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "Data"
# Keep these aliases because existing tests and integrations patch the old
# module-level paths when loading isolated question banks.
_PROJECT_ROOT = PROJECT_ROOT
_DATA_DIR = DATA_DIR / "interview_questions"
_LEGACY_DATA_DIR = DATA_DIR / "interview_question"
_SINGLE_FILE = DATA_DIR / "interview_questions.json"
QUESTION_DIRS = (_DATA_DIR, _LEGACY_DATA_DIR)
SINGLE_FILE = _SINGLE_FILE
ROLES_FILE = DATA_DIR / "roles.json"


def _records_by_role(payload: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return {}
    roles = payload.get("roles")
    if isinstance(roles, dict):
        return {
            str(role_id): [record for record in records if isinstance(record, dict)]
            for role_id, records in roles.items()
            if isinstance(records, list)
        }
    # Older bundled files have role names as the top-level keys.
    return {
        str(role_id): [record for record in records if isinstance(record, dict)]
        for role_id, records in payload.items()
        if isinstance(records, list)
    }


@lru_cache(maxsize=1)
def _load_question_data() -> dict[str, list[dict[str, Any]]]:
    """Load every question bank while keeping the first definition of a role."""
    merged: dict[str, list[dict[str, Any]]] = {}
    paths = [
        path
        for directory in (_DATA_DIR, _LEGACY_DATA_DIR)
        if directory.is_dir()
        for path in sorted(directory.glob("*.json"), key=lambda item: item.name)
    ]
    # A directory bank is authoritative. The single-file bank is only a
    # fallback for older deployments that have no question directory.
    if not paths and _SINGLE_FILE.is_file():
        paths.append(_SINGLE_FILE)

    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as source:
                payload = json.load(source)
            for role_id, questions in _records_by_role(payload).items():
                if role_id in merged:
                    logger.warning(
                        "role_id %s bị trùng trong %s; giữ dữ liệu đã đọc trước",
                        role_id,
                        path.name,
                    )
                    continue
                merged[role_id] = questions
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.error("Không đọc được dữ liệu câu hỏi %s: %s", path, exc)

    if not paths:
        logger.error("Không tìm thấy thư mục hoặc file dữ liệu câu hỏi trong %s", DATA_DIR)
    return merged


def _clear_cache() -> None:
    """Clear cached question data after replacing a data file."""
    _load_question_data.cache_clear()


@lru_cache(maxsize=1)
def _role_id_by_name() -> dict[str, str]:
    """Map the display names in roles.json to IDs used by the question bank."""
    try:
        with ROLES_FILE.open("r", encoding="utf-8") as source:
            payload = json.load(source)
    except (OSError, json.JSONDecodeError):
        return {}

    roles = payload.get("roles", []) if isinstance(payload, dict) else []
    return {
        str(name).strip().casefold(): str(role["id"])
        for role in roles
        if isinstance(role, dict) and role.get("id")
        for name in (role.get("name"), role.get("name_vi"))
        if isinstance(name, str) and name.strip()
    }


def _question_for_id(question_id: str) -> dict[str, Any]:
    matches = [
        question
        for questions in _load_question_data().values()
        for question in questions
        if question.get("id") == question_id
    ]
    if not matches:
        raise ValueError(f"Không tìm thấy câu hỏi có ID '{question_id}'.")
    if len(matches) > 1:
        raise ValueError(f"ID câu hỏi '{question_id}' bị trùng trong ngân hàng dữ liệu.")
    return matches[0]


def get_questions(role_id: str, n: int = 5, seed: int | None = None) -> list[dict[str, Any]]:
    """Select up to ``n`` questions, alternating types and hiding answer rubrics."""
    if n <= 0:
        raise ValueError("Số câu hỏi phải lớn hơn 0.")

    roles = _load_question_data()
    if role_id not in roles:
        if not roles:
            raise ValueError("Không có dữ liệu câu hỏi trong thư mục Data/interview_question/.")
        raise ValueError(f"Không tìm thấy câu hỏi cho vị trí '{role_id}'.")

    questions = roles[role_id]
    by_type: dict[str, list[dict[str, Any]]] = {"technical": [], "scenario": []}
    for question in questions:
        raw_kind = str(question.get("type", "")).casefold()
        kind = {
            "technical": "technical",
            "kỹ thuật": "technical",
            "scenario": "scenario",
            "tình huống": "scenario",
        }.get(raw_kind)
        if kind in by_type:
            by_type[kind].append(question)

    rng = random.Random(seed)
    for group in by_type.values():
        rng.shuffle(group)

    first_type = next((kind for kind in ("technical", "scenario") if by_type[kind]), "technical")
    order = [first_type, "scenario" if first_type == "technical" else "technical"]
    target = min(n, sum(len(group) for group in by_type.values()))
    selected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    safe_fields = ("id", "type", "skill", "level", "weight", "question", "time_minutes")

    while len(selected) < target:
        progressed = False
        for kind in order:
            while by_type[kind]:
                question = by_type[kind].pop()
                question_id = question.get("id")
                if not isinstance(question_id, str) or question_id in seen_ids:
                    continue
                seen_ids.add(question_id)
                public_question = {key: deepcopy(question[key]) for key in safe_fields if key in question}
                public_question["type"] = kind
                public_question["role_id"] = role_id
                selected.append(public_question)
                progressed = True
                break
            if len(selected) >= target:
                break
        if not progressed:
            break
    return selected


def get_question_feedback(question_id: str) -> dict[str, Any]:
    """Return reference points and warnings after a candidate submits an answer."""
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question_id phải là chuỗi không rỗng.")

    question = _question_for_id(question_id)
    answer = question.get("reference_answer")
    has_reference_answer = isinstance(answer, str) and bool(answer.strip())
    points = question.get("good_answer_points")
    good_answer_points = (
        [point.strip() for point in points if isinstance(point, str) and point.strip()]
        if isinstance(points, list)
        else []
    )
    if has_reference_answer:
        reference_answer = answer.strip()
    else:
        if not good_answer_points:
            raise ValueError(f"Câu hỏi '{question_id}' chưa có đáp án tham khảo.")
        reference_answer = "\n".join(f"- {point}" for point in good_answer_points)

    red_flags = question.get("red_flags", [])
    return {
        "reference_answer": reference_answer,
        "has_reference_answer": has_reference_answer,
        "good_answer_points": good_answer_points,
        "red_flags": [item for item in red_flags if isinstance(item, str)] if isinstance(red_flags, list) else [],
        "time_minutes": question.get("time_minutes"),
    }


def get_reference_answer(question_id: str) -> str:
    """Return a sample answer or scoring points for a question ID."""
    return get_question_feedback(question_id)["reference_answer"]


def generate_interview_questions(
    missing_skills: Iterable[str],
    max_per_skill: int = 2,
    *,
    role: str | None = None,
) -> list[str]:
    """Compatibility API for callers that still expect question strings."""
    if max_per_skill <= 0:
        return []

    question_data = _load_question_data()
    role_id = role if role in question_data else _role_id_by_name().get((role or "").strip().casefold())
    if role_id:
        return [item["question"] for item in get_questions(role_id, max_per_skill) if item.get("question")]

    skills = {skill.strip().casefold() for skill in missing_skills if isinstance(skill, str) and skill.strip()}
    if not skills:
        return []

    exact_matches: list[str] = []
    other_matches: list[str] = []
    for questions in question_data.values():
        for question in questions:
            question_skill = question.get("skill", "")
            keywords = question.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            values = {str(value).strip().casefold() for value in keywords if value}
            if isinstance(question_skill, str) and question_skill.strip():
                values.add(question_skill.strip().casefold())
            if not skills.intersection(values) or not question.get("question"):
                continue
            target = exact_matches if question.get("keywords") else other_matches
            target.append(question["question"])

    rng = random.Random()
    selected: list[str] = []
    for pool in (exact_matches, other_matches):
        remaining = max_per_skill - len(selected)
        if remaining > 0 and pool:
            selected.extend(rng.sample(pool, min(remaining, len(pool))))
    return selected
