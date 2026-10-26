"""Read-only editorial evidence gate for the four demonstration roles.

The default command reports a backlog and exits successfully. --strict fails
while any item remains. It never opens URLs or promotes review status.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.resource_policy import is_recommendable_resource
from modules.skill_extractor import normalize_skill


DATA_DIR = ROOT / "Data"
DEMO_ROLE_IDS = (
    "sales_executive", "frontend_developer_react",
    "data_analyst", "backend_developer_java",
)
BOUNDED_SCOPES = frozenset({"lesson", "module", "chapter", "spec"})
GENERIC_PATTERNS = (
    re.compile(r"\[(?:\.{2,}|skill|kỹ năng|tình huống|placeholder)\]", re.IGNORECASE),
    re.compile(r"hãy kể theo\s+star", re.IGNORECASE),
    re.compile(r"hãy mô tả cách bạn dùng", re.IGNORECASE),
)
ISSUE_KEYS = (
    "question_missing_skill", "question_template_or_unreviewed",
    "question_generic_prompt", "question_missing_context",
    "question_missing_target_rubric", "question_missing_all_level_rubric",
    "question_missing_red_flags", "question_wrong_level",
    "resource_missing_required_level", "resource_scope_or_locator_pending", "resource_homepage_url",
    "resource_independent_access_pending", "resource_content_review_date_pending",
    "resource_rejected_records", "resource_policy_leak",
)


def _has_text(value: object) -> bool:
    return (
        isinstance(value, str) and bool(value.strip())
        and value.strip().casefold() not in {"pending", "unknown", "unverified", "n/a", "todo", "draft"}
    )


def _valid_recorded_date(value: object, *, as_of: date) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value) <= as_of
    except ValueError:
        return False


def _is_homepage_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return bool(parsed.netloc) and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment


def _read_data(data_dir: Path) -> tuple[dict, dict, dict, dict]:
    roles = {role["id"]: role for role in json.loads((data_dir / "roles.json").read_text(encoding="utf-8"))}
    resources = json.loads((data_dir / "resources.json").read_text(encoding="utf-8"))
    aliases = json.loads((data_dir / "skill_aliases.json").read_text(encoding="utf-8"))
    questions: dict[str, list[dict]] = {}
    for path in sorted((data_dir / "interview_question").glob("part_*.json")):
        bank = json.loads(path.read_text(encoding="utf-8"))
        for role_id, records in bank["roles"].items():
            if role_id in questions:
                raise ValueError(f"Question bank duplicates role {role_id}")
            questions[role_id] = records
    return roles, resources, aliases, questions


def audit_demo_roles(data_dir: Path = DATA_DIR, *, as_of: date | None = None) -> dict:
    """Report exact record locators for gates, without claiming expert review."""
    as_of = as_of or date.today()
    roles, resources, aliases, questions_by_role = _read_data(data_dir)
    report_roles: dict[str, dict] = {}
    all_resource_ids: set[str] = set()
    totals: Counter[str] = Counter()
    issue_totals: Counter[str] = Counter()

    for role_id in DEMO_ROLE_IDS:
        role = roles[role_id]
        requirements = {normalize_skill(skill["name"]): skill["level"] for skill in role["skills"]}
        questions = questions_by_role[role_id]
        issues: dict[str, list[str]] = {key: [] for key in ISSUE_KEYS}
        question_skills: set[str] = set()
        seen_resource_ids: set[str] = set()
        mapping_occurrences = 0
        excluded_by_status: Counter[str] = Counter()

        for question in questions:
            qid = question["id"]
            canonical = normalize_skill(question["skill"])
            skill = aliases.get(canonical, canonical)
            expected = requirements.get(skill)
            if expected is None or question.get("level") != expected:
                issues["question_wrong_level"].append(qid)
            else:
                question_skills.add(skill)
            if question.get("quality") in {"template", "unreviewed"}:
                issues["question_template_or_unreviewed"].append(qid)
            prompt = question.get("question", "")
            if any(pattern.search(prompt) for pattern in GENERIC_PATTERNS):
                issues["question_generic_prompt"].append(qid)
            if not _has_text(question.get("context_scenario")):
                issues["question_missing_context"].append(qid)
            rubric = question.get("evaluation_rubric") or {}
            if expected is not None and not _has_text(rubric.get(f"level_{expected}_criteria")):
                issues["question_missing_target_rubric"].append(qid)
            if any(not _has_text(rubric.get(f"level_{level}_criteria")) for level in (1, 2, 3)):
                issues["question_missing_all_level_rubric"].append(qid)
            if not (isinstance(question.get("red_flags"), list)
                    and any(_has_text(flag) for flag in question["red_flags"])):
                issues["question_missing_red_flags"].append(qid)

        for skill in requirements:
            if skill not in question_skills:
                issues["question_missing_skill"].append(skill)
            group = resources.get(skill, {})
            candidates = group.get("resources", [])
            if not any(
                is_recommendable_resource(resource, require_verified=True, skill=skill)
                and type(resource.get("level_from")) is int
                and type(resource.get("level_to")) is int
                and resource["level_from"] <= requirements[skill] <= resource["level_to"]
                for resource in candidates
            ):
                issues["resource_missing_required_level"].append(skill)
            for resource in candidates:
                mapping_occurrences += 1
                rid = resource["id"]
                if rid in seen_resource_ids:
                    continue
                seen_resource_ids.add(rid)
                all_resource_ids.add(rid)
                if resource.get("scope_granularity") not in BOUNDED_SCOPES or not _has_text(resource.get("evidence_locator")):
                    issues["resource_scope_or_locator_pending"].append(rid)
                if _is_homepage_url(resource.get("url")):
                    issues["resource_homepage_url"].append(rid)
                axes = resource.get("verification_axes") or {}
                if axes.get("access_status") != "independently_accessible" or not _valid_recorded_date(axes.get("last_live_checked"), as_of=as_of):
                    issues["resource_independent_access_pending"].append(rid)
                if not _valid_recorded_date(resource.get("content_reviewed_at"), as_of=as_of):
                    issues["resource_content_review_date_pending"].append(rid)
                status = resource.get("content_review_status", "unreviewed")
                if status in {"unsuitable", "blocked"}:
                    excluded_by_status[status] += 1
                    issues["resource_rejected_records"].append(rid)
                    if is_recommendable_resource(resource, require_verified=True, skill=skill):
                        issues["resource_policy_leak"].append(rid)

        counts = {key: len(values) for key, values in issues.items()}
        issue_totals.update(counts)
        totals.update({
            "role_skill_requirements": len(requirements),
            "questions": len(questions),
            "resource_mapping_occurrences": mapping_occurrences,
            "resource_id_occurrences_across_roles": len(seen_resource_ids),
        })
        report_roles[role_id] = {
            "role_name": role.get("name_vi") or role.get("name"),
            "counts": {
                "role_skill_requirements": len(requirements),
                "questions": len(questions),
                "resource_mapping_occurrences": mapping_occurrences,
                "unique_resource_ids": len(seen_resource_ids),
                "excluded_by_status": dict(excluded_by_status),
            },
            "issue_counts": counts,
            "issues": issues,
            "gate_passed": not any(issues.values()),
        }

    return {
        "as_of": as_of.isoformat(),
        "scope": "offline_recorded_evidence_not_independent_domain_review",
        "summary": {
            "roles": len(DEMO_ROLE_IDS),
            **dict(totals),
            "unique_resource_ids_across_demo": len(all_resource_ids),
            "issue_occurrences_by_role": dict(issue_totals),
        },
        "roles": report_roles,
        "gate_passed": all(item["gate_passed"] for item in report_roles.values()),
        "note": "Rejected mappings remain in source data for audit; policy leaks and rejected source records are separate checks. No archival schema is assumed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit_demo_roles(args.data_dir, as_of=args.as_of)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "gate_passed": report["gate_passed"]}, ensure_ascii=False, indent=2))
    return 1 if args.strict and not report["gate_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
