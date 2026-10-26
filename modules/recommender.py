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
from .resource_policy import is_recommendable_resource, resource_exclusion_reason, resource_review_status
from .practice_guidance import get_practice_routes


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
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, dict[str, Any]]]:
    """Group eligible resources and retain rejected-resource reasons by skill."""
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
    eligible_by_skill: dict[str, list[tuple[str, Mapping[str, Any], list[str]]]] = {
        skill: [] for skill in skills
    }
    review_summary = {
        skill: {"candidate_count": 0, "eligible_count": 0, "excluded_statuses": set(), "reasons": set()}
        for skill in skills
    }
    for skill in skills:
        if skill not in index:
            continue
        group = index[skill]
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            raise ValueError(f"resources[{skill!r}] phải có danh sách 'resources'.")
        for resource in group["resources"]:
            if not isinstance(resource, Mapping):
                raise ValueError(f"Tài liệu của {skill!r} phải là object.")
            summary = review_summary[skill]
            summary["candidate_count"] += 1
            reason = resource_exclusion_reason(resource, require_verified=True, skill=skill)
            if not reason:
                url = resource.get("url")
                try:
                    parsed = urlsplit(url) if isinstance(url, str) else None
                except ValueError:
                    parsed = None
                if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    reason = "missing_url"
            if reason:
                summary["reasons"].add(reason)
                summary["excluded_statuses"].add(resource_review_status(resource))
                continue
            if not is_recommendable_resource(resource, require_verified=True, skill=skill):
                continue
            tokens = _resource_tokens(resource)
            if not tokens:
                summary["reasons"].add("missing_resource_identity")
                continue
            eligible_by_skill[skill].append((skill, resource, tokens))

    # A partial mapping is a fallback for the same skill only when no
    # recommendable reviewed mapping exists for that skill.
    for skill, candidates in eligible_by_skill.items():
        has_reviewed = any(resource_review_status(record) == "reviewed" for _, record, _ in candidates)
        selected = [
            candidate for candidate in candidates
            if not (has_reviewed and resource_review_status(candidate[1]) == "partial")
        ]
        for candidate in selected:
            _, resource, tokens = candidate
            review_summary[skill]["eligible_count"] += 1
            for token in tokens[1:]:
                parents[root(token)] = root(tokens[0])
            rows.append(candidate)

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
    return catalog, refs, review_summary


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

    Each week contains week, skills, eligible resources, resource_keys,
    skills_without_resources, unresolved, and partial_resources. A resource
    occurs once in the whole roadmap at its earliest related skill's week;
    resource_keys maps every skill to eligible resources, including items
    introduced earlier. Duplicate IDs/URLs are grouped.

    Only verified HTTP(S) resources whose content review is reviewed/partial
    and includes a review note may be recommended. Unknown skills and skills
    with only excluded resources remain scheduled and receive an unresolved
    reason. Inputs are not mutated. Invalid weeks, metadata, or requested
    resource groups raise an explicit TypeError or ValueError.
    """
    if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks <= 0:
        raise ValueError("weeks phải là số nguyên dương.")
    if not isinstance(resources, Mapping):
        raise TypeError("resources phải là mapping theo tên kỹ năng.")
    skills = _prioritize(_skill_list(missing), missing_details)
    if not skills:
        return []
    catalog, refs, review_summary = _resource_catalog(skills, resources)
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
        unresolved = []
        partial_resources = []
        for skill in week_skills:
            summary = review_summary[skill]
            if not refs[skill]:
                if summary["candidate_count"] == 0:
                    reason = "no_resources"
                else:
                    reason = next((candidate for candidate in (
                        "specialized_source_required",
                        "unreviewed_content", "blocked_resource", "unsuitable_content",
                        "unverified_link", "missing_url", "missing_resource_identity",
                    ) if candidate in summary["reasons"]), "unreviewed_content")
                issue = {"skill": skill, "reason": reason}
                if summary["excluded_statuses"]:
                    issue["excluded_statuses"] = sorted(summary["excluded_statuses"])
                if summary["reasons"]:
                    issue["exclusion_reasons"] = sorted(summary["reasons"])
                unresolved.append(issue)
            for key in refs[skill]:
                resource = catalog[key]
                if resource_review_status(resource) == "partial":
                    partial_resources.append({
                        "skill": skill,
                        "resource_key": key,
                        "review_note": resource.get("review_note", ""),
                    })
        roadmap.append(
            {
                "week": index + 1,
                "skills": week_skills,
                "resources": week_resources,
                "resource_keys": {skill: refs[skill] for skill in week_skills},
                "skills_without_resources": [skill for skill in week_skills if not refs[skill]],
                "unresolved": unresolved,
                "partial_resources": partial_resources,
                "practice_routes": get_practice_routes(week_skills, resources),
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
