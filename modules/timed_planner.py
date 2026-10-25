"""Level metadata coverage and conservative scheduling, separate from presence API."""

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
import math
from numbers import Real
from urllib.parse import urlsplit

from .levels import canonical_skill
from .recommender import _resource_tokens


def _positive(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _url(value):
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        return parsed is not None and parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


def _duration(record):
    hours = record.get("duration_hours")
    if hours is not None:
        if not _positive(hours):
            raise ValueError("duration_hours phải là số dương hữu hạn hoặc null.")
        if _url(record.get("duration_source")) and record.get("duration_basis"):
            return float(hours), "published", None
        return None, "unknown", "unverified_duration"
    estimate = record.get("estimated_duration_hours")
    if estimate is not None:
        if not _positive(estimate):
            raise ValueError("estimated_duration_hours phải là số dương hữu hạn.")
        if record.get("estimated_duration_basis") or record.get("duration_basis"):
            return float(estimate), "estimated", None
        return None, "unknown", "estimate_without_basis"
    return None, "unknown", "unknown_duration"


def _items(gap):
    if not isinstance(gap, Mapping) or not isinstance(gap.get("items"), list):
        raise ValueError("gap phải có items từ compute_gap.")
    items, seen = [], set()
    for raw in gap["items"]:
        if not isinstance(raw, Mapping):
            raise ValueError("gap.items phải chứa object.")
        skill = canonical_skill(raw.get("skill"))
        if skill in seen:
            raise ValueError("gap có kỹ năng trùng sau canonical.")
        seen.add(skill)
        current, required = raw.get("current"), raw.get("required")
        if any(type(v) is not int or not 0 <= v <= 3 for v in (current, required)):
            raise ValueError("current/required phải là int 0–3.")
        if type(raw.get("gap")) is not int or raw["gap"] != max(0, required-current):
            raise ValueError("gap không nhất quán với current/required.")
        if isinstance(raw.get("priority"), bool) or (not _positive(raw.get("priority")) and not (raw["gap"] == 0 and raw.get("priority") == 0)):
            raise ValueError("priority không hợp lệ.")
        if raw["gap"]:
            items.append({**raw, "skill": skill})
    return sorted(items, key=lambda item: -item["priority"])


def plan(gap, resources, hours_per_week=8):
    if not _positive(hours_per_week):
        raise ValueError("hours_per_week phải là số dương hữu hạn, không nhận bool.")
    if not isinstance(resources, Mapping):
        raise TypeError("resources phải là mapping.")
    items = _items(gap)
    index = {}
    for name, group in resources.items():
        name = canonical_skill(name)
        if name in index:
            raise ValueError("resources có khóa trùng sau canonical/alias.")
        index[name] = group

    # Union IDs and normalized URLs before selection. Metadata remains per mapping.
    parents, rows = {}, []
    def root(token):
        parents.setdefault(token, token)
        while parents[token] != token:
            parents[token] = parents[parents[token]]
            token = parents[token]
        return token
    for item in items:
        group = index.get(item["skill"], {"resources": []})
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            raise ValueError("Nhóm tài nguyên phải có resources:list.")
        for record in group["resources"]:
            if not isinstance(record, Mapping):
                raise ValueError("Resource phải là object.")
            tokens = _resource_tokens(record)
            if not tokens or not _url(record.get("url")):
                continue
            for token in tokens[1:]:
                parents[root(token)] = root(tokens[0])
            rows.append((item["skill"], record, tokens))
    identities = {}
    candidates = {item["skill"]: [] for item in items}
    for skill, record, tokens in rows:
        key = identities.setdefault(root(tokens[0]), tokens[0])
        start, end = record.get("level_from"), record.get("level_to")
        if any(type(v) is not int or not 1 <= v <= 3 for v in (start, end)) or start > end:
            raise ValueError(f"Khoảng level resource của {skill} không hợp lệ.")
        duration = _duration(record)
        candidates[skill].append((key, record, duration))

    catalog, refs, unresolved, coverage = {}, {}, [], []
    for item in items:
        skill = item["skill"]
        refs[skill] = []
        needed = set(range(item["current"]+1, item["required"]+1))
        all_candidates = candidates[skill]
        eligible = [(key, r, duration) for key, r, duration in all_candidates
                    if r.get("verified") is True and r.get("content_review_status") in ("reviewed", "partial")]
        while needed:
            level = min(needed)
            choices = [(k, r, d) for k, r, d in eligible if r["level_from"] <= level <= r["level_to"]]
            if not choices:
                reason = "no_resources" if not all_candidates else "unreviewed_content" if not eligible else "level_mismatch"
                unresolved.append({"skill": skill, "reason": reason, "levels": sorted(needed)})
                break
            # Prefer reviewed, sourced duration, then broader coverage; stable data order.
            key, record, duration = min(choices, key=lambda choice: (
                choice[1]["content_review_status"] != "reviewed",
                {"published": 0, "estimated": 1, "unknown": 2}[choice[2][1]],
                -len(needed & set(range(choice[1]["level_from"], choice[1]["level_to"]+1))),
            ))
            covered = sorted(needed & set(range(record["level_from"], record["level_to"]+1)))
            needed.difference_update(covered)
            if key not in refs[skill]:
                refs[skill].append(key)
            coverage.append({"skill": skill, "resource_key": key, "levels": covered,
                             "content_review_status": record["content_review_status"],
                             "review_note": record.get("review_note", "")})
            if record["content_review_status"] == "partial":
                unresolved.append({"skill": skill, "resource_key": key, "reason": "partial_content", "levels": covered})
            if key not in catalog:
                catalog[key] = {**deepcopy(dict(record)), "key": key, "skills": [],
                                "planned_hours": duration[0], "duration_kind": duration[1],
                                "duration_issue": duration[2], "duration_evidence": {}}
            selected = catalog[key]
            old_hours, old_kind = selected["planned_hours"], selected["duration_kind"]
            rank = {"published": 0, "estimated": 1, "unknown": 2}
            if selected["duration_issue"] != "conflicting_duration":
                if duration[0] is not None and old_hours is not None and old_kind == duration[1] and old_hours != duration[0]:
                    selected.update(planned_hours=None, duration_kind="unknown", duration_issue="conflicting_duration", duration_evidence={})
                elif rank[duration[1]] < rank[old_kind] or (duration[0], duration[1]) == (old_hours, old_kind):
                    selected.update(planned_hours=duration[0], duration_kind=duration[1], duration_issue=duration[2])
                    if duration[0] is not None:
                        selected["duration_evidence"] = {
                            "source": record.get("duration_source") if duration[1] == "published" else None,
                            "basis": record.get("estimated_duration_basis") or record.get("duration_basis"),
                            "hours": duration[0], "kind": duration[1],
                        }
            if skill not in selected["skills"]:
                selected["skills"].append(skill)

    unknown = []
    published = estimated = Decimal(0)
    phases = []
    budget = Decimal(str(hours_per_week))
    used = Decimal(0)
    for key, record in catalog.items():
        hours = record["planned_hours"]
        if hours is None:
            issue = {"resource_key": key, "skills": list(record["skills"]), "reason": record["duration_issue"]}
            unknown.append(issue)
            unresolved.append(dict(issue))
            continue
        remaining = Decimal(str(hours))
        if record["duration_kind"] == "estimated":
            estimated += remaining
        else:
            published += remaining
        part = 0
        while remaining > 0:
            if not phases or used >= budget:
                phases.append({"week": len(phases)+1, "hours": 0, "segments": []})
                used = Decimal(0)
            phase = phases[-1]
            allocation = min(remaining, budget-used)
            part += 1
            phase["segments"].append({"resource_key": key, "hours": float(allocation), "part": part,
                                      "duration_kind": record["duration_kind"]})
            used += allocation
            phase["hours"] = float(used)
            remaining -= allocation
    return {"role_id": gap.get("role_id"), "hours_per_week": hours_per_week,
            "phases": phases, "resources": catalog, "resource_keys": refs, "level_coverage": coverage,
            "total_weeks": None if unresolved else len(phases), "known_weeks": len(phases),
            "total_known_hours": float(published), "total_estimated_hours": float(estimated),
            "total_planned_hours": float(published+estimated), "is_estimated": bool(estimated),
            "unresolved": unresolved, "unknown_duration": unknown,
            "completion_basis": "resource_metadata_not_skill_attainment"}
