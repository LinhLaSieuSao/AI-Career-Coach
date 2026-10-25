"""Build weekly learning roadmaps from Matcher gaps and skill-indexed resources."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from copy import deepcopy
from numbers import Real
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .skill_extractor import normalize_skill


_DATA_DIR = Path(__file__).resolve().parent.parent / "Data"


def _skill_list(missing: Iterable[str] | str | None) -> list[str]:
    if missing is None:
        return []
    values = [missing] if isinstance(missing, str) else missing
    result: list[str] = []
    seen: set[str] = set()
    for name in values:
        if not isinstance(name, str):
            raise TypeError("Mỗi kỹ năng thiếu phải là chuỗi.")
        normalized = normalize_skill(name)
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _prioritize(skills: list[str], missing_details: Iterable[Mapping[str, Any]] | None) -> list[str]:
    if missing_details is None:
        return skills
    weights: dict[str, float] = {}
    allowed = set(skills)
    for detail in missing_details:
        if not isinstance(detail, Mapping) or not isinstance(detail.get("name"), str):
            raise ValueError("missing_details phải chứa object có tên kỹ năng hợp lệ.")
        name = normalize_skill(detail["name"])
        if name not in allowed or name in weights:
            raise ValueError("Tên trong missing_details phải thuộc missing và không trùng nhau.")
        weight = detail.get("weight", 1)
        if (
            isinstance(weight, bool)
            or not isinstance(weight, Real)
            or not math.isfinite(float(weight))
            or weight <= 0
        ):
            raise ValueError("missing_details.weight phải là số dương hữu hạn.")
        weights[name] = float(weight)
    # Python's stable sort keeps the incoming order when weights are equal.
    return sorted(skills, key=lambda name: -weights.get(name, 1.0))


def _resource_tokens(resource: Mapping[str, Any]) -> list[str]:
    """Identify duplicates by ID or URL without changing path/query casing."""
    tokens: list[str] = []
    raw_url = resource.get("url")
    if isinstance(raw_url, str) and raw_url.strip():
        url = urlsplit(raw_url.strip())
        if url.scheme.lower() in {"http", "https"} and url.netloc:
            normalized_url = urlunsplit(
                (url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), url.query, "")
            )
            tokens.append("url:" + normalized_url)
    resource_id = resource.get("id")
    if isinstance(resource_id, str) and resource_id.strip():
        tokens.append("id:" + resource_id.strip())
    return tokens


def _resource_catalog(
    skills: list[str], resources: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    """Group shared resources and retain every skill's references to them."""
    index: dict[str, Any] = {}
    for name, entry in resources.items():
        if not isinstance(name, str):
            raise ValueError("Khóa của resources phải là tên kỹ năng dạng chuỗi.")
        normalized = normalize_skill(name)
        if normalized in index:
            raise ValueError(f"resources chứa tên kỹ năng trùng sau chuẩn hóa: {name!r}.")
        index[normalized] = entry

    # Union identities before producing output: duplicates may connect through
    # both an ID and a URL across more than two resource records.
    parents: dict[str, str] = {}

    def root(token: str) -> str:
        parents.setdefault(token, token)
        while parents[token] != token:
            parents[token] = parents[parents[token]]
            token = parents[token]
        return token

    rows: list[tuple[str, Mapping[str, Any], list[str]]] = []
    for skill in skills:
        if skill not in index:
            continue
        group = index[skill]
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            raise ValueError(f"resources[{skill!r}] phải có danh sách 'resources'.")
        for resource in group["resources"]:
            if not isinstance(resource, Mapping):
                raise ValueError(f"Tài liệu của {skill!r} phải là object.")
            tokens = _resource_tokens(resource)
            if not tokens:
                continue
            for token in tokens[1:]:
                parents[root(token)] = root(tokens[0])
            rows.append((skill, resource, tokens))

    catalog: dict[str, dict[str, Any]] = {}
    refs: dict[str, list[str]] = {skill: [] for skill in skills}
    group_keys: dict[str, str] = {}
    for skill, resource, tokens in rows:
        identity = root(tokens[0])
        if identity not in group_keys:
            key = tokens[0]
            group_keys[identity] = key
            catalog[key] = {**deepcopy(dict(resource)), "key": key, "skills": []}
        key = group_keys[identity]
        if key not in refs[skill]:
            refs[skill].append(key)
            catalog[key]["skills"].append(skill)
    return catalog, refs


def build_roadmap(
    missing: Iterable[str] | str | None,
    resources: Mapping[str, Any],
    weeks: int = 4,
    *,
    missing_details: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Split missing skills into balanced, consecutive weekly study groups.

    Return [] for no skills, otherwise min(weeks, unique skill count) weeks.
    Metadata optionally sorts skills by descending role weight, stably for
    ties; missing metadata weights default to 1. Required level is not used
    to infer study time or resource suitability. Names use the shared skill
    normalizer; aliases should already have been resolved by Matcher.

    Each week contains week, skills, resources, resource_keys, and
    skills_without_resources. A resource occurs once in the whole roadmap,
    at its earliest related skill's week. resource_keys maps each skill to
    those resources' keys, including resources introduced in earlier weeks.
    Duplicates sharing an ID or normalized URL are grouped. Original fields
    are preserved from the first record and augmented with key and skills.

    Unknown skills remain scheduled and are listed in skills_without_resources.
    Resources without an ID or usable HTTP(S) URL are ignored. Inputs are not
    mutated. Invalid weeks, metadata, or requested resource groups raise an
    explicit TypeError or ValueError.
    """
    if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks <= 0:
        raise ValueError("weeks phải là số nguyên dương.")
    if not isinstance(resources, Mapping):
        raise TypeError("resources phải là mapping theo tên kỹ năng.")
    skills = _prioritize(_skill_list(missing), missing_details)
    if not skills:
        return []
    catalog, refs = _resource_catalog(skills, resources)
    week_count = min(weeks, len(skills))
    base_size, remainder = divmod(len(skills), week_count)
    roadmap: list[dict[str, Any]] = []
    assigned: set[str] = set()
    offset = 0
    for index in range(week_count):
        count = base_size + (1 if index < remainder else 0)
        week_skills = skills[offset : offset + count]
        offset += count
        week_resources = []
        for skill in week_skills:
            for key in refs[skill]:
                if key not in assigned:
                    week_resources.append(catalog[key])
                    assigned.add(key)
        roadmap.append(
            {
                "week": index + 1,
                "skills": week_skills,
                "resources": week_resources,
                "resource_keys": {skill: refs[skill] for skill in week_skills},
                "skills_without_resources": [skill for skill in week_skills if not refs[skill]],
            }
        )
    return roadmap


def get_course_recommendations(missing_skills: Iterable[str]) -> list[dict[str, Any]]:
    """Adapt the current resource catalog to the existing app's flat cards."""
    skills = _skill_list(missing_skills)
    if not skills:
        return []
    with (_DATA_DIR / "resources.json").open(encoding="utf-8") as source:
        resources = json.load(source)
    roadmap = build_roadmap(skills, resources, weeks=1)
    return [
        {
            **resource,
            "course_name": resource.get("title", "Tài liệu học tập"),
            "link": resource.get("url", ""),
            "resource_id": resource.get("id", ""),
            "skills_achieved": list(resource["skills"]),
        }
        for resource in roadmap[0]["resources"]
    ]


def build_timed_roadmap(gap, resources, hours_per_week=8) -> dict:
    """Schedule reviewed level ranges with sourced hours; keep incomplete work explicit."""
    from .timed_planner import plan
    return plan(gap, resources, hours_per_week)
