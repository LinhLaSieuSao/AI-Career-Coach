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
            "verified": True,
            "last_checked": "2026-10-27",
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
            "verified_companion_url": source.get("practice_url"),
            "verified_companion_title": source.get("practice_title"),
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
                "reviewed_at": "2026-10-27",
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
        group["academic_source"] = {key: record[key] for key in (
            "title", "provider", "url", "academic_label", "academic_source_kind", "academic_basis", "learning_scope",
            "verified_companion_url", "verified_companion_title",
        )}
        index[normalized] = group_key
    return result

