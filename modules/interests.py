"""Small, static RIASEC activity mapping for transparent career exploration."""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from .catalog import DATA_DIR, load_roles
from .skill_extractor import normalize_skill


DIMENSIONS = ("R", "I", "A", "S", "E", "C")
INTERESTS_FILE = DATA_DIR / "interests.json"
ROLE_FAMILIES_FILE = DATA_DIR / "role_families_riasec.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError(f"Dữ liệu RIASEC phải là object: {path.name}.")
    return payload


def _validated_unit_vector(raw: Any, label: str) -> dict[str, float]:
    if not isinstance(raw, Mapping) or set(raw) != set(DIMENSIONS):
        raise ValueError(f"Vector RIASEC {label} phải có đủ sáu chiều {DIMENSIONS}.")
    values: dict[str, float] = {}
    for dimension in DIMENSIONS:
        value = raw[dimension]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Vector RIASEC {label} chứa giá trị không hợp lệ.")
        values[dimension] = float(value)
    norm = math.sqrt(sum(value * value for value in values.values()))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-4):
        raise ValueError(f"Vector RIASEC {label} phải được chuẩn hóa độ dài 1.")
    return values


@lru_cache(maxsize=1)
def load_interest_activities() -> tuple[dict[str, Any], ...]:
    """Load and validate the structured activity choices used by the form."""
    payload = _load_json(INTERESTS_FILE)
    if payload.get("dimensions") != list(DIMENSIONS):
        raise ValueError("Data/interests.json có thứ tự dimension không hợp lệ.")
    activities = payload.get("activities")
    if not isinstance(activities, list):
        raise ValueError("Data/interests.json phải có activities dạng list.")
    result = []
    seen: set[str] = set()
    for record in activities:
        if not isinstance(record, dict):
            raise ValueError("Mỗi hoạt động RIASEC phải là object.")
        activity_id = record.get("id")
        label = record.get("label")
        dimension = record.get("dimension")
        if not isinstance(activity_id, str) or not activity_id or activity_id in seen:
            raise ValueError("ID hoạt động RIASEC bị thiếu hoặc trùng.")
        if not isinstance(label, str) or not label.strip() or dimension not in DIMENSIONS:
            raise ValueError(f"Hoạt động RIASEC {activity_id!r} thiếu nhãn/chiều hợp lệ.")
        aliases = record.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(item, str) or not item.strip() for item in aliases):
            raise ValueError(f"aliases của hoạt động {activity_id!r} không hợp lệ.")
        vector = _validated_unit_vector(record.get("vector"), activity_id)
        if max(vector, key=vector.get) != dimension or vector[dimension] < 0.999:
            raise ValueError(f"Hoạt động {activity_id!r} phải ánh xạ vào đúng chiều RIASEC.")
        result.append({**record, "vector": vector, "aliases": tuple(aliases)})
        seen.add(activity_id)
    return tuple(result)


def activity_label(activity_id: str) -> str:
    for activity in load_interest_activities():
        if activity["id"] == activity_id:
            return activity["label"]
    return activity_id


@lru_cache(maxsize=1)
def load_role_family_vectors() -> dict[str, dict[str, Any]]:
    """Expand the static role-family taxonomy and require exact catalog coverage."""
    payload = _load_json(ROLE_FAMILIES_FILE)
    if payload.get("dimensions") != list(DIMENSIONS):
        raise ValueError("Data/role_families_riasec.json có dimensions không hợp lệ.")
    families = payload.get("families")
    if not isinstance(families, list):
        raise ValueError("Data/role_families_riasec.json phải có families dạng list.")
    role_vectors: dict[str, dict[str, Any]] = {}
    family_ids: set[str] = set()
    roles = load_roles(DATA_DIR / "roles.json")
    catalog_ids = {role["id"] for role in roles}
    for family in families:
        if not isinstance(family, dict) or not isinstance(family.get("id"), str):
            raise ValueError("Mỗi họ nghề RIASEC cần có ID hợp lệ.")
        family_id = family["id"]
        if family_id in family_ids:
            raise ValueError(f"Họ nghề RIASEC bị trùng: {family_id}.")
        family_ids.add(family_id)
        label = family.get("label")
        prefixes = family.get("role_prefixes", [])
        explicit_ids = family.get("role_ids", [])
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Họ nghề RIASEC {family_id!r} thiếu nhãn.")
        if not isinstance(prefixes, list) or any(not isinstance(value, str) for value in prefixes):
            raise ValueError(f"role_prefixes của {family_id!r} không hợp lệ.")
        if not isinstance(explicit_ids, list) or any(not isinstance(value, str) for value in explicit_ids):
            raise ValueError(f"role_ids của {family_id!r} không hợp lệ.")
        vector = _validated_unit_vector(family.get("vector"), family_id)
        unknown_ids = set(explicit_ids) - catalog_ids
        if unknown_ids:
            raise ValueError(f"Họ nghề {family_id!r} tham chiếu role không tồn tại: {sorted(unknown_ids)}.")
        selected = set(explicit_ids)
        selected.update(
            role_id for role_id in catalog_ids
            if any(role_id.startswith(prefix) for prefix in prefixes)
        )
        for role_id in selected:
            if role_id in role_vectors:
                raise ValueError(f"Role {role_id!r} được gán vào nhiều họ nghề RIASEC.")
            role_vectors[role_id] = {
                "family_id": family_id,
                "family_label": label,
                "vector": vector,
            }
    missing = catalog_ids - role_vectors.keys()
    if missing:
        raise ValueError(f"Chưa gán họ nghề RIASEC cho role: {sorted(missing)}.")
    return role_vectors


def _interest_texts(values: Iterable[str] | str | None) -> list[str]:
    if values is None:
        return []
    sources = [values] if isinstance(values, str) else values
    results = []
    for source in sources:
        if isinstance(source, str) and source.strip():
            results.extend(part.strip() for part in re.split(r"[,;\n]+", source) if part.strip())
    return results


def resolve_activity_ids(
    activity_ids: Iterable[str] | None = None,
    free_text_interests: Iterable[str] | str | None = None,
) -> list[str]:
    """Resolve selected IDs and exact curated free-text aliases without guessing."""
    activities = load_interest_activities()
    by_id = {activity["id"]: activity["id"] for activity in activities}
    alias_index: dict[str, str] = {}
    aliases: list[tuple[str, str]] = []
    for activity in activities:
        for alias in (activity["label"], *activity["aliases"]):
            normalized = normalize_skill(alias)
            owner = alias_index.get(normalized)
            if owner is not None and owner != activity["id"]:
                raise ValueError(f"Alias sở thích RIASEC bị trùng: {alias!r}.")
            alias_index[normalized] = activity["id"]
            aliases.append((normalized, activity["id"]))
    resolved: list[str] = []
    seen: set[str] = set()
    for activity_id in activity_ids or ():
        if isinstance(activity_id, str) and activity_id in by_id and activity_id not in seen:
            resolved.append(activity_id)
            seen.add(activity_id)
    aliases.sort(key=lambda pair: (-len(pair[0]), pair[0]))
    for raw in _interest_texts(free_text_interests):
        normalized = normalize_skill(raw)
        exact = alias_index.get(normalized)
        matched_ids = [exact] if exact else []
        if not matched_ids:
            for alias, activity_id in aliases:
                if re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", normalized):
                    matched_ids.append(activity_id)
        for activity_id in matched_ids:
            if activity_id not in seen:
                resolved.append(activity_id)
                seen.add(activity_id)
    return resolved


def user_interest_vector(
    activity_ids: Iterable[str] | None = None,
    free_text_interests: Iterable[str] | str | None = None,
) -> dict[str, float] | None:
    """Average mapped activity vectors and normalize the user's interest vector."""
    selected = resolve_activity_ids(activity_ids, free_text_interests)
    if not selected:
        return None
    by_id = {activity["id"]: activity for activity in load_interest_activities()}
    totals = {dimension: 0.0 for dimension in DIMENSIONS}
    for activity_id in selected:
        for dimension in DIMENSIONS:
            totals[dimension] += by_id[activity_id]["vector"][dimension]
    return _unit_vector(totals)


def _unit_vector(values: Mapping[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(float(values.get(dimension, 0.0)) ** 2 for dimension in DIMENSIONS))
    if not math.isfinite(norm) or norm <= 0:
        return {dimension: 0.0 for dimension in DIMENSIONS}
    return {dimension: float(values.get(dimension, 0.0)) / norm for dimension in DIMENSIONS}


def interest_fit(
    user_riasec_vec: Mapping[str, float] | None,
    role_riasec_vec: Mapping[str, float] | None,
) -> float:
    """Return cosine similarity in [0, 1] for nonnegative RIASEC vectors."""
    if not isinstance(user_riasec_vec, Mapping) or not isinstance(role_riasec_vec, Mapping):
        return 0.0
    left = _unit_vector(user_riasec_vec)
    right = _unit_vector(role_riasec_vec)
    if not any(left.values()) or not any(right.values()):
        return 0.0
    cosine = sum(left[key] * right[key] for key in DIMENSIONS)
    return min(1.0, max(0.0, cosine))
