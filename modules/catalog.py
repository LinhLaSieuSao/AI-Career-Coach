"""Read the shared role catalog without depending on the process directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .skill_extractor import build_vocabulary, normalize_skill

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_roles(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Accept a role list, {roles: [...]}, or legacy {positions: [...]}.

    Preserve all role and skill metadata. Legacy title/required_skills fields
    are adapted to name/skills so every caller can pass the result to Matcher.
    Invalid catalogs fail explicitly instead of silently producing no roles.
    """
    source_path = Path(path) if path is not None else DATA_DIR / "roles.json"
    with source_path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if isinstance(payload, dict):
        if "roles" in payload:
            payload = payload["roles"]
        elif "positions" in payload:
            payload = payload["positions"]
    if not isinstance(payload, list):
        raise ValueError(f"Dữ liệu role phải là list hoặc object roles/positions trong {source_path}.")

    roles: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ValueError(f"Role tại vị trí {index} phải là object trong {source_path}.")
        role = dict(record)
        role_id = str(role.get("id") or role.get("title") or "").strip()
        if not role_id or role_id in seen_ids:
            raise ValueError(f"Role tại vị trí {index} thiếu ID hoặc trùng ID trong {source_path}.")
        skills = role.get("skills", role.get("required_skills", []))
        if not isinstance(skills, list):
            raise ValueError(f"Role {role_id!r} phải có skills là list.")
        name = role.get("name") or role.get("title") or role_id
        roles.append({
            **role,
            "id": role_id,
            "name": name,
            "title": role.get("title") or name,
            "name_vi": role.get("name_vi") or name,
            "skills": skills,
        })
        seen_ids.add(role_id)
    return roles


def load_skill_vocabulary(
    roles: list[dict] | None = None, *, data_dir: str | Path | None = None,
) -> set[str]:
    """Unite role skills and independent recognition-only canonical entries.

    Independent skills do not add role requirements or imply resource coverage.
    Isolated/legacy catalogs without skill_catalog.json still support role skills.
    """
    directory = Path(data_dir) if data_dir is not None else DATA_DIR
    vocabulary = build_vocabulary(roles if roles is not None else load_roles(directory / "roles.json"))
    path = directory / "skill_catalog.json"
    if path.is_file():
        with path.open(encoding="utf-8") as source:
            extra = json.load(source)
        if not isinstance(extra, list) or any(not isinstance(name, str) or not normalize_skill(name) for name in extra):
            raise ValueError(f"Catalog nhận diện phải là list tên kỹ năng không rỗng trong {path}.")
        canonical = [normalize_skill(name) for name in extra]
        if len(set(canonical)) != len(canonical):
            raise ValueError(f"Catalog nhận diện chứa kỹ năng trùng trong {path}.")
        vocabulary.update(canonical)
    return vocabulary
