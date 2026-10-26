"""Add explicit evidence fields without fabricating review or reuse rights.

Idempotent: existing nonempty evidence is preserved. Unknown facts remain null
or pending. Run --check to detect records that have not been migrated yet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_data_readiness import resource_url_set_digest


DATA_DIR = ROOT / "Data"
PROVENANCE_KEYS = (
    "source_url", "author_origin", "curated_by", "review_tier",
    "reviewed_at", "rights_basis", "license_notes",
)
SCOPE_BY_RESOURCE_ID = {
    "csharp_mslearn_first_path": "learning_path",
    "reactjs_react_quick_start": "lesson",
    "kubernetes_official_tutorials": "module",
    "agile_scrum_001": "spec",
    "budget_openstax_operating_budgets": "chapter",
    "ml_google_crash_course": "course",
    "cisco_networking_basics": "course",
    "google_analytics_001": "catalog",
    "typescript_handbook": "catalog",
    "javascript_mdn_guide": "catalog",
    "pytorch_official_tutorials": "catalog",
}
INTERNALLY_BOUNDED_IDS = {
    "csharp_mslearn_first_path", "reactjs_react_quick_start",
    "kubernetes_official_tutorials", "agile_scrum_001",
    "budget_openstax_operating_budgets", "ml_google_crash_course",
    "cisco_networking_basics", "google_analytics_001", "typescript_handbook",
}
CONTENT_FIT_BY_STATUS = {
    "reviewed": "internally_reviewed_relevant_scope",
    "partial": "internally_reviewed_partial",
    "unsuitable": "not_fit",
    "blocked": "not_assessed",
    "unreviewed": "pending",
}


def write_compact_roles(path: Path, roles: list[dict]) -> None:
    """Keep the catalog's compact per-skill layout so role changes stay reviewable."""
    lines = ["["]
    for index, role in enumerate(roles):
        lines.append("{")
        for key in ("id", "name", "name_vi", "difficulty", "learning_time_months"):
            lines.append(f"{json.dumps(key)}: {json.dumps(role[key], ensure_ascii=False)},")
        lines.append('"skills": [')
        for skill_index, skill in enumerate(role["skills"]):
            suffix = "," if skill_index + 1 < len(role["skills"]) else ""
            lines.append(json.dumps(skill, ensure_ascii=False) + suffix)
        lines.append("],")
        lines.append('"provenance": ' + json.dumps(role["provenance"], ensure_ascii=False))
        lines.append("}," if index + 1 < len(roles) else "}")
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_json(value, depth: int = 0, *, field: str | None = None) -> str:
    """Use regular JSON indentation, with small evidence objects on one line."""
    if field in {"verification_axes", "evaluation_rubric", "provenance"}:
        return json.dumps(value, ensure_ascii=False)
    pad = "  " * depth
    child_pad = "  " * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        rows = [child_pad + json.dumps(key, ensure_ascii=False) + ": "
                + _format_json(item, depth + 1, field=key)
                for key, item in value.items()]
        return "{\n" + ",\n".join(rows) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        rows = [child_pad + _format_json(item, depth + 1) for item in value]
        return "[\n" + ",\n".join(rows) + "\n" + pad + "]"
    return json.dumps(value, ensure_ascii=False)


def write_compact_evidence(path: Path, value: dict) -> None:
    path.write_text(_format_json(value) + "\n", encoding="utf-8")


def _fill_provenance(record: dict, *, source_url=None, review_tier=None, reviewed_at=None) -> None:
    provenance = record.setdefault("provenance", {})
    for key in PROVENANCE_KEYS:
        provenance.setdefault(key, None)
    if source_url is not None and provenance["source_url"] is None:
        provenance["source_url"] = source_url
    if review_tier is not None and provenance["review_tier"] is None:
        provenance["review_tier"] = review_tier
    if reviewed_at is not None and provenance["reviewed_at"] is None:
        provenance["reviewed_at"] = reviewed_at


def migrate(data_dir: Path, *, check: bool = False) -> dict[str, int]:
    resources_path = data_dir / "resources.json"
    roles_path = data_dir / "roles.json"
    resources = json.loads(resources_path.read_text(encoding="utf-8"))
    roles = json.loads(roles_path.read_text(encoding="utf-8"))
    urls = {record["url"] for group in resources.values() for record in group["resources"]}
    attestation = json.loads((data_dir / "link_review_attestation.json").read_text(encoding="utf-8"))
    attested = (attestation.get("url_count") == len(urls)
                and attestation.get("url_set_sha256") == resource_url_set_digest(urls))

    changed = 0
    counts = {"roles": len(roles), "resources": 0, "questions": 0, "files_changed": 0}
    for role in roles:
        before = json.dumps(role, ensure_ascii=False, sort_keys=True)
        _fill_provenance(role)
        changed += before != json.dumps(role, ensure_ascii=False, sort_keys=True)
    if changed:
        counts["files_changed"] += 1
        if not check:
            write_compact_roles(roles_path, roles)

    changed = 0
    for group in resources.values():
        for record in group["resources"]:
            counts["resources"] += 1
            before = json.dumps(record, ensure_ascii=False, sort_keys=True)
            rid = record["id"]
            status = record.get("content_review_status", "unreviewed")
            record.setdefault("scope_granularity", SCOPE_BY_RESOURCE_ID.get(rid, "unknown"))
            record.setdefault("evidence_locator", None)
            axes = record.setdefault("verification_axes", {})
            defaults = {
                "access_status": "user_attested_manual" if attested else "pending",
                "content_fit": CONTENT_FIT_BY_STATUS.get(status, "pending"),
                "level_fit": "internally_bounded" if rid in INTERNALLY_BOUNDED_IDS else "mapped_unconfirmed",
                "rights_basis": "pending", "practice_type": "unknown", "last_live_checked": None,
            }
            for key, value in defaults.items():
                axes.setdefault(key, value)
            tier = (f"internal_{status}_unattributed" if record.get("content_reviewed_at")
                    and status in {"reviewed", "partial", "unsuitable"} else None)
            _fill_provenance(record, source_url=record.get("url"),
                             review_tier=tier, reviewed_at=record.get("content_reviewed_at"))
            changed += before != json.dumps(record, ensure_ascii=False, sort_keys=True)
    if changed:
        counts["files_changed"] += 1
        if not check:
            write_compact_evidence(resources_path, resources)

    for path in sorted((data_dir / "interview_question").glob("*.json")):
        bank = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for questions in bank["roles"].values():
            for question in questions:
                counts["questions"] += 1
                before = json.dumps(question, ensure_ascii=False, sort_keys=True)
                question.setdefault("context_scenario", None)
                rubric = question.setdefault("evaluation_rubric", {})
                for key in ("level_1_criteria", "level_2_criteria", "level_3_criteria"):
                    rubric.setdefault(key, None)
                quality = question.get("quality", "unreviewed")
                tier = ("reviewed_internal" if quality == "reviewed" else
                        "ai_reviewed_internal" if quality == "ai_reviewed_internal" else None)
                _fill_provenance(question, review_tier=tier,
                                 reviewed_at=question.get("quality_reviewed_at"))
                changed += before != json.dumps(question, ensure_ascii=False, sort_keys=True)
        if changed:
            counts["files_changed"] += 1
            if not check:
                write_compact_evidence(path, bank)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = migrate(args.data_dir, check=args.check)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if args.check and result["files_changed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
