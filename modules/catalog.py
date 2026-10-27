# SPDX-License-Identifier: MIT
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


def summarize_data_provenance(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Count recorded provenance fields without asserting legal permission.

    A recorded source or rights note is a lead for human review, not proof
    that the project can redistribute an item or that licenses are compatible.
    """
    directory = Path(data_dir) if data_dir is not None else DATA_DIR
    roles = load_roles(directory / "roles.json")
    with (directory / "resources.json").open(encoding="utf-8") as source:
        resources = json.load(source)
    if not isinstance(resources, dict):
        raise ValueError("resources.json phải là object theo tên kỹ năng.")

    def count_records(records: list[dict[str, Any]]) -> dict[str, int]:
        source_count = rights_count = 0
        for item in records:
            provenance = item.get("provenance")
            if not isinstance(provenance, dict):
                continue
            source_url = provenance.get("source_url")
            rights = provenance.get("rights_basis")
            source_count += int(isinstance(source_url, str) and bool(source_url.strip()))
            rights_count += int(isinstance(rights, str) and bool(rights.strip()))
        return {
            "total": len(records),
            "source_url_recorded": source_count,
            "source_url_missing": len(records) - source_count,
            "rights_basis_recorded": rights_count,
            "rights_basis_missing": len(records) - rights_count,
        }

    records = []
    for group in resources.values():
        if not isinstance(group, dict) or not isinstance(group.get("resources"), list):
            raise ValueError("Mỗi nhóm resources phải có danh sách resources.")
        for item in group["resources"]:
            if not isinstance(item, dict):
                raise ValueError("Mỗi học liệu phải là object.")
            records.append(item)
    return {
        "roles": count_records(roles),
        "resource_mappings": count_records(records),
        "notice": "Trường có dữ liệu không tự chứng minh quyền phân phối; cần kiểm tra nguồn và giấy phép.",
    }
