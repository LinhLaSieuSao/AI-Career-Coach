# SPDX-License-Identifier: MIT
"""Load the curated academic curriculum and attach it to skill resources."""

from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .skill_extractor import normalize_skill


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _practice_tracks(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Index optional practice guidance by source, preserving older catalogs."""
    tracks = payload.get("practice_tracks", {})
    if not isinstance(tracks, Mapping):
        raise ValueError("practice_tracks phải là một object.")
    result: dict[str, dict[str, Any]] = {}
    for track in tracks.values():
        if not isinstance(track, dict) or not isinstance(track.get("sources"), list):
            raise ValueError("Mỗi nhóm thực hành phải có danh sách sources.")
        if not all(isinstance(track.get(field), str) and track[field].strip()
                   for field in ("title", "framing", "evidence")):
            raise ValueError("Nhóm thực hành thiếu tiêu đề, hướng dẫn hoặc đầu ra.")
        if not isinstance(track.get("steps"), list) or not track["steps"] or not all(
            isinstance(step, str) and step.strip() for step in track["steps"]
        ):
            raise ValueError("Nhóm thực hành phải có các bước không rỗng.")
        for source_id in track["sources"]:
            if not isinstance(source_id, str) or source_id not in payload.get("sources", {}) or source_id in result:
                raise ValueError(f"Nguồn thực hành không hợp lệ hoặc bị trùng: {source_id!r}.")
            result[source_id] = track
    return result


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _academic_label(kind: str) -> str:
    if "guide" in kind:
        return "Danh mục học liệu đại học"
    if "course" in kind:
        return "Học phần đại học"
    if "chapter" in kind:
        return "Chương sách học thuật"
    return "Giáo trình nền tảng"


def load_academic_curriculum(path: str | Path | None = None) -> dict[str, Any]:
    """Read and validate the versioned curriculum mapping file."""
    path = Path(path) if path else DATA_DIR / "academic_curriculum.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("academic_curriculum.json has an unsupported schema_version.")
    sources, skills = payload.get("sources"), payload.get("skills")
    if not isinstance(sources, dict) or not isinstance(skills, dict) or not sources or not skills:
        raise ValueError("Curriculum must define source and skill mappings.")
    for skill, mapping in skills.items():
        if not isinstance(skill, str) or not isinstance(mapping, dict):
            raise ValueError("Every curriculum skill must map to an object.")
        if mapping.get("source_id") not in sources:
            raise ValueError(f"Curriculum source missing for {skill!r}.")
        plan = mapping.get("learning_plan")
        if not isinstance(plan, dict) or not isinstance(plan.get("steps"), list) or not plan["steps"]:
            raise ValueError(f"Curriculum learning steps missing for {skill!r}.")
    return payload


def merge_academic_curriculum(
    resources: Mapping[str, Any],
    *,
    curriculum: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Add one academic learning source and one actionable study plan per skill.

    Existing review records are preserved. Each new source is clearly marked
    as a learning foundation so the UI does not imply it certifies a target
    skill level or a regulated qualification.
    """
    payload = curriculum or load_academic_curriculum()
    tracks = _practice_tracks(payload)
    result = deepcopy(dict(resources))
    index = {normalize_skill(name): name for name in result if isinstance(name, str)}
    for skill, mapping in payload["skills"].items():
        normalized = normalize_skill(skill)
        group_key = index.get(normalized, skill)
        group = result.setdefault(group_key, {"skill_name": skill, "category": "technical", "resources": []})
        if not isinstance(group, dict):
            raise ValueError(f"Resource group for {skill!r} must be an object.")
        group.setdefault("resources", [])
        if not isinstance(group["resources"], list):
            raise ValueError(f"Resource group for {skill!r} must contain a resource list.")
        source = payload["sources"][mapping["source_id"]]
        plan = deepcopy(mapping["learning_plan"])
        access_check = source.get("access_check")
        practice_access_check = source.get("practice_access_check")
        # A successful HTTP response only supports link availability, not
        # educational suitability, ownership or independent expert review.
        http_ok = isinstance(access_check, Mapping) and access_check.get("http_status") == 200
        record = {
            "id": "academic_" + _slug(skill),
            "title": source["title"],
            "type": "academic_textbook",
            "provider": source["provider"],
            "url": source["url"],
            "language": "en",
            "cost": source.get("access", "check_source_access"),
            "level_from": 1,
            "level_to": 3,
            "duration_hours": None,
            "verified": http_ok,
            "last_checked": access_check.get("checked_at") if isinstance(access_check, Mapping) else None,
            "access_check": deepcopy(access_check),
            "content_review_status": "partial",
            "review_note": plan["source_scope"],
            "academic_source": True,
            "academic_label": _academic_label(source["kind"]),
            "academic_source_kind": source["kind"],
            "academic_basis": source["basis"],
            "learning_role": "academic_foundation",
            "learning_scope": plan["source_scope"],
            "learning_plan": plan,
            "jurisdiction": source.get("jurisdiction"),
            "verified_companion_url": (
                source.get("practice_url")
                if isinstance(practice_access_check, Mapping) and practice_access_check.get("http_status") == 200
                else None
            ),
            "verified_companion_title": (
                source.get("practice_title")
                if isinstance(practice_access_check, Mapping) and practice_access_check.get("http_status") == 200
                else None
            ),
            "practice_access_check": deepcopy(practice_access_check),
            "access_note": (
                "Có thể cần truy cập qua thư viện hoặc mua tài liệu; kiểm tra tại trang nhà xuất bản."
                if source.get("access") == "may_require_library_or_paid_access" else None
            ),
            "duration_issue": "not_published",
            "provenance": {
                "source_url": source["url"],
                "author_origin": source["provider"],
                "curated_by": "academic_curriculum_catalog",
                "review_tier": source["kind"],
                "reviewed_at": None,
                "rights_basis": "Link to original source; no textbook content copied into this project.",
                "license_notes": "Check the original source for its license and reuse terms.",
            },
        }
        # Keep the existing hands-on source as an optional companion when it is
        # different and has a verified public URL.
        existing = next((
            item for item in group["resources"]
            if isinstance(item, dict)
            and item.get("verified") is True
            and item.get("content_review_status") in {"reviewed", "partial"}
            and (
                not isinstance(item.get("latest_transport_check"), Mapping)
                or item["latest_transport_check"].get("status") in {"reachable", "redirect"}
            )
            and isinstance(item.get("review_note"), str)
            and item["review_note"].strip()
            and isinstance(item.get("url"), str)
            and item["url"].startswith(("https://", "http://"))
            and item["url"].rstrip("/") != source["url"].rstrip("/")
        ), None)
        if existing:
            record["practice_url"] = existing["url"]
            record["practice_title"] = existing.get("title", "Tài liệu thực hành bổ sung")
        # Replace a previous generated entry so reruns remain deterministic.
        group["resources"] = [item for item in group["resources"] if not (
            isinstance(item, dict) and item.get("id") == record["id"]
        )]
        group["resources"].append(record)
        group["learning_plan"] = plan
        track = tracks.get(mapping["source_id"])
        if track and not plan.get("user_steps"):
            # Keep the original plan intact and add a user-facing alternative.
            # The template supplies a field-specific scenario; the skill name is
            # inserted literally, without formatting arbitrary data as code.
            group.setdefault("practice_plan", {
                "title": track["title"].replace("{skill}", skill),
                "framing": track["framing"].replace("{skill}", skill),
                "steps": [step.replace("{skill}", skill) for step in track["steps"]],
                "evidence": track["evidence"].replace("{skill}", skill),
                "self_paced": True,
            })
        group["academic_source"] = {key: record[key] for key in (
            "title", "provider", "url", "academic_label", "academic_source_kind", "academic_basis", "learning_scope",
            "verified_companion_url", "verified_companion_title",
        )}
        index[normalized] = group_key
    return result

