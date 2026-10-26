"""Validate evidence schema 2.0 and report unmet publication evidence.

Default success means structurally valid data only. --require-complete-evidence
also fails on missing human/domain/rights evidence; it is intentionally pending
for the current catalog. No network request or review-status promotion occurs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.skill_extractor import normalize_skill
from scripts.migrate_evidence_schema_v2 import PROVENANCE_KEYS


DATA_DIR = ROOT / "Data"
GRANULARITIES = {"lesson", "module", "chapter", "spec", "course", "learning_path", "catalog", "unknown"}
ACCESS_STATUSES = {"user_attested_manual", "independently_accessible", "blocked", "pending"}
CONTENT_FITS = {"internally_reviewed_relevant_scope", "internally_reviewed_partial", "not_fit", "not_assessed", "pending"}
LEVEL_FITS = {"internally_bounded", "mapped_unconfirmed", "pending"}
RIGHTS_BASES = {"pending", "external_referral_only", "licensed_reuse"}
PRACTICE_TYPES = {"unknown", "reference", "guided_lab", "case_study", "supervised_practice"}
AXIS_ENUMS = {
    "access_status": ACCESS_STATUSES, "content_fit": CONTENT_FITS,
    "level_fit": LEVEL_FITS, "rights_basis": RIGHTS_BASES,
    "practice_type": PRACTICE_TYPES,
}
RUBRIC_KEYS = ("level_1_criteria", "level_2_criteria", "level_3_criteria")


def _date_or_none(value, as_of: date) -> bool:
    if value is None:
        return True
    try:
        return isinstance(value, str) and date.fromisoformat(value) <= as_of
    except ValueError:
        return False


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().casefold() not in {"pending", "unknown", "unverified", "n/a", "draft"}


def _provenance(record: dict, locator: str, errors: list[str], pending: Counter, *, as_of: date) -> None:
    value = record.get("provenance")
    if not isinstance(value, dict):
        errors.append(f"{locator}.provenance: object required")
        return
    for key in PROVENANCE_KEYS:
        if key not in value or not (value[key] is None or isinstance(value[key], str)):
            errors.append(f"{locator}.provenance.{key}: string|null required")
        elif not _text(value[key]):
            pending[f"provenance.{key}"] += 1
    if not _date_or_none(value.get("reviewed_at"), as_of):
        errors.append(f"{locator}.provenance.reviewed_at: invalid/future date")


def validate_schema(data_dir: Path = DATA_DIR, *, as_of: date | None = None,
                    target_roles: set[str] | None = None) -> dict:
    as_of = as_of or date.today()
    errors: list[str] = []
    pending: Counter = Counter()
    roles = json.loads((data_dir / "roles.json").read_text(encoding="utf-8"))
    resources = json.loads((data_dir / "resources.json").read_text(encoding="utf-8"))
    aliases = json.loads((data_dir / "skill_aliases.json").read_text(encoding="utf-8"))
    all_role_ids = {role.get("id") for role in roles}
    if target_roles is not None:
        errors.extend(f"Unknown target role: {role_id}" for role_id in sorted(target_roles - all_role_ids))
    role_levels = {}
    covered_skills: dict[str, set[str]] = {}
    counts = Counter()

    for role in roles:
        rid = role.get("id")
        if target_roles is not None and rid not in target_roles:
            continue
        counts["roles"] += 1
        _provenance(role, f"roles.{rid}", errors, pending, as_of=as_of)
        role_levels[rid] = {normalize_skill(skill["name"]): skill["level"] for skill in role["skills"]}
        covered_skills[rid] = set()

    target_skills = {skill for levels in role_levels.values() for skill in levels}

    seen_resource_ids = set()
    for skill, group in resources.items():
        if target_roles is not None and normalize_skill(skill) not in target_skills:
            continue
        for resource in group["resources"]:
            counts["resources"] += 1
            rid = resource.get("id")
            locator = f"resources.{skill}.{rid}"
            if rid in seen_resource_ids:
                errors.append(f"{locator}: duplicate ID")
            seen_resource_ids.add(rid)
            start, end = resource.get("level_from"), resource.get("level_to")
            if not (type(start) is type(end) is int and 1 <= start <= end <= 3):
                errors.append(f"{locator}: invalid Level range")
            granularity = resource.get("scope_granularity")
            if granularity not in GRANULARITIES:
                errors.append(f"{locator}.scope_granularity: invalid/missing")
            elif granularity in {"catalog", "unknown"}:
                pending["resource.granular_scope"] += 1
            evidence_locator = resource.get("evidence_locator")
            if not (evidence_locator is None or isinstance(evidence_locator, str)):
                errors.append(f"{locator}.evidence_locator: string|null required")
            if not _text(evidence_locator):
                pending["resource.evidence_locator"] += 1
            axes = resource.get("verification_axes")
            if not isinstance(axes, dict):
                errors.append(f"{locator}.verification_axes: object required")
            else:
                for key, allowed in AXIS_ENUMS.items():
                    if axes.get(key) not in allowed:
                        errors.append(f"{locator}.verification_axes.{key}: invalid/missing")
                if not _date_or_none(axes.get("last_live_checked"), as_of):
                    errors.append(f"{locator}.verification_axes.last_live_checked: invalid/future date")
                for key, unresolved in (
                    ("access_status", {"pending"}), ("content_fit", {"pending", "not_assessed"}),
                    ("level_fit", {"pending", "mapped_unconfirmed"}),
                    ("rights_basis", {"pending"}), ("practice_type", {"unknown"}),
                ):
                    if axes.get(key) in unresolved:
                        pending[f"resource.{key}"] += 1
                if axes.get("access_status") == "user_attested_manual":
                    pending["resource.independent_access_check"] += 1
            if granularity == "catalog" and type(end) is int and end > 1:
                pending["resource.catalog_claims_level_above_1"] += 1
            _provenance(resource, locator, errors, pending, as_of=as_of)
            if resource.get("content_review_status") in {"unsuitable", "blocked"}:
                pending["resource.rejected_mapping"] += 1

    seen_question_ids = set()
    for path in sorted((data_dir / "interview_question").glob("*.json")):
        bank = json.loads(path.read_text(encoding="utf-8"))
        for role_id, questions in bank["roles"].items():
            if target_roles is not None and role_id not in target_roles:
                continue
            if role_id not in role_levels:
                errors.append(f"{path.name}.{role_id}: unknown role")
            for question in questions:
                counts["questions"] += 1
                qid = question.get("id")
                locator = f"{path.name}.{role_id}.{qid}"
                if qid in seen_question_ids:
                    errors.append(f"{locator}: duplicate ID")
                seen_question_ids.add(qid)
                raw_skill = question.get("skill")
                skill = aliases.get(normalize_skill(raw_skill), normalize_skill(raw_skill)) if isinstance(raw_skill, str) else None
                target_level = role_levels.get(role_id, {}).get(skill)
                if target_level is None:
                    errors.append(f"{locator}: skill not required by role")
                elif question.get("level") != target_level:
                    errors.append(f"{locator}: question Level differs from role skill Level")
                elif role_id in covered_skills:
                    covered_skills[role_id].add(skill)
                if question.get("quality") in {"template", "unreviewed", None}:
                    pending["question.content_review_status"] += 1
                context = question.get("context_scenario")
                if not (context is None or isinstance(context, str)):
                    errors.append(f"{locator}.context_scenario: string|null required")
                if not _text(context):
                    pending["question.context_scenario"] += 1
                rubric = question.get("evaluation_rubric")
                if not isinstance(rubric, dict):
                    errors.append(f"{locator}.evaluation_rubric: object required")
                else:
                    for key in RUBRIC_KEYS:
                        if key not in rubric or not (rubric[key] is None or isinstance(rubric[key], str)):
                            errors.append(f"{locator}.evaluation_rubric.{key}: string|null required")
                    key = f"level_{question.get('level')}_criteria"
                    if not _text(rubric.get(key)):
                        pending["question.target_level_rubric"] += 1
                red_flags = question.get("red_flags")
                if not (isinstance(red_flags, list) and red_flags and all(_text(flag) for flag in red_flags)):
                    errors.append(f"{locator}.red_flags: nonempty text list required")
                _provenance(question, locator, errors, pending, as_of=as_of)

    for role_id, required in role_levels.items():
        pending["question.role_skill_coverage"] += len(set(required) - covered_skills[role_id])

    return {
        "schema_version": 2, "as_of": as_of.isoformat(),
        "target_roles": sorted(target_roles) if target_roles is not None else None,
        "scope": "offline_structure_and_recorded_evidence_only",
        "summary": dict(counts), "structure_passed": not errors,
        "structural_errors": errors,
        "evidence_pending": dict(sorted(pending.items())),
        "complete_evidence_passed": not errors and not pending,
        "note": "Schema PASS is not expert review, independent URL verification, or legal clearance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--require-complete-evidence", action="store_true")
    parser.add_argument("--target-roles", help="Comma-separated role IDs; default checks the whole catalog")
    args = parser.parse_args()
    target_roles = set(filter(None, (item.strip() for item in args.target_roles.split(",")))) if args.target_roles else None
    report = validate_schema(args.data_dir, as_of=args.as_of, target_roles=target_roles)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("summary", "structure_passed", "evidence_pending", "complete_evidence_passed")}, ensure_ascii=False, indent=2))
    return 1 if not report["structure_passed"] or (args.require_complete_evidence and not report["complete_evidence_passed"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
