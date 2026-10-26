"""Inventory data readiness without equating review metadata with reuse permission.

The report is reproducible for fixed input bytes and --as-of. It performs no
network requests and never changes catalog records. A successful default exit
means the inventory's consistency checks passed, not that the data are ready
for an unrestricted release. Optional gates make those separate requirements
explicit in CI or a release review.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.practice_guidance import get_practice_routes
from modules.resource_policy import has_current_specialist_evidence, resource_review_status
from modules.skill_extractor import load_aliases, normalize_skill
from scripts.validate_question_bank import validate_question_records


PROVENANCE_FIELDS = ("source_url", "author_origin", "curated_by", "review_tier", "reviewed_at", "rights_basis", "license_notes")
QUESTION_STATUSES = ("reviewed_internal", "ai_reviewed_internal", "template", "unreviewed")
RESOURCE_STATUSES = ("reviewed", "partial", "unsuitable", "blocked", "unreviewed")


def resource_url_set_digest(urls: set[str]) -> str:
    """Bind a manual URL attestation to the exact current URL set."""
    payload = json.dumps(sorted(urls), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _link_attestation(record: Any, urls: set[str], as_of: date) -> dict:
    """Read a user's link statement separately from content and rights review."""
    valid = isinstance(record, dict) and (
        record.get("schema_version") == 1
        and record.get("scope") == "all_distinct_resource_urls"
        and record.get("method") == "user_reported_manual_browser_check"
        and record.get("url_count") == len(urls)
        and record.get("url_set_sha256") == resource_url_set_digest(urls)
        and _recorded_date(record.get("attested_at"), as_of) is not None
    )
    return {
        "status": "user_attested_current_url_set" if valid else "stale_or_invalid",
        "url_count": len(urls),
        "attested_at": record.get("attested_at") if isinstance(record, dict) else None,
        "evidence_kind": "user_statement_not_independent_recheck",
        "content_fit": "not_established_by_link_attestation",
        "reuse_permission": "not_established_by_link_attestation",
    }


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _http_url(value: Any) -> bool:
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        return bool(parsed and parsed.scheme in {"https", "http"} and parsed.netloc)
    except ValueError:
        return False


def _recorded_date(value: Any, as_of: date) -> date | None:
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else None
        return parsed if parsed is not None and parsed <= as_of else None
    except ValueError:
        return None


def _provenance(record: dict, as_of: date) -> dict:
    """Report evidence fields only; no license or legal approval is inferred."""
    raw = record.get("provenance")
    evidence = raw if isinstance(raw, dict) else {}
    def recorded(value: Any) -> bool:
        return _nonempty(value) and value.strip().casefold() not in {"pending", "unknown", "n/a"}

    missing = [field for field in PROVENANCE_FIELDS if not recorded(evidence.get(field))]
    if "reviewed_at" not in missing and _recorded_date(evidence["reviewed_at"], as_of) is None:
        missing.append("reviewed_at")
    return {
        "metadata_present": any(recorded(evidence.get(field)) for field in PROVENANCE_FIELDS),
        "evidence_fields_complete": not missing,
        "missing_fields": sorted(missing),
        "legal_permission": "not_determined_by_this_inventory",
    }


def _question_review(question: dict, as_of: date) -> tuple[str, list[str]]:
    declared = question.get("quality", "unreviewed")
    if declared == "template":
        return "template", []
    if declared not in {"reviewed", "ai_reviewed_internal"}:
        return "unreviewed", []
    missing = []
    sources = question.get("quality_sources")
    if not isinstance(sources, list) or not sources or not all(_http_url(source) for source in sources):
        missing.append("quality_sources")
    if not _nonempty(question.get("quality_review_note")):
        missing.append("quality_review_note")
    if _recorded_date(question.get("quality_reviewed_at"), as_of) is None:
        missing.append("quality_reviewed_at")
    if declared == "ai_reviewed_internal":
        if not _nonempty(question.get("quality_reviewer")) or "AI" not in question["quality_reviewer"]:
            missing.append("quality_reviewer")
        if "not an independent" not in str(question.get("quality_review_note", "")).casefold():
            missing.append("independent_review_disclaimer")
    status = "reviewed_internal" if declared == "reviewed" else "ai_reviewed_internal"
    return ("unreviewed" if missing else status), missing


def _resource_reason(resource: dict, skill: str, as_of: date) -> str | None:
    """Mirror planner eligibility while making specialist evidence's date explicit."""
    status = resource_review_status(resource)
    if status == "blocked":
        return "blocked_resource"
    if status == "unsuitable":
        return "unsuitable_content"
    if status not in {"reviewed", "partial"}:
        return "unreviewed_content"
    if not has_current_specialist_evidence(resource, skill, today=as_of):
        return "specialized_source_required"
    if resource.get("verified") is not True:
        return "unverified_link"
    if not _http_url(resource.get("url")):
        return "invalid_url"
    return None


def build_inventory(data_dir: str | Path = DATA_DIR, *, as_of: date | None = None) -> dict:
    """Return stable aggregate metrics plus actionable per-record inventories."""
    directory = Path(data_dir)
    as_of = as_of or date.today()
    source_paths: set[Path] = set()
    errors: list[str] = []

    def read(path: Path):
        source_paths.add(path)
        return json.loads(path.read_text(encoding="utf-8"))

    roles = load_roles(directory / "roles.json")
    source_paths.add(directory / "roles.json")
    vocabulary = load_skill_vocabulary(roles, data_dir=directory)
    if (directory / "skill_catalog.json").is_file():
        source_paths.add(directory / "skill_catalog.json")
    alias_path = directory / "skill_aliases.json"
    aliases = load_aliases(alias_path) if alias_path.is_file() else {}
    if alias_path.is_file():
        source_paths.add(alias_path)
    resources = read(directory / "resources.json")
    if not isinstance(resources, dict):
        raise ValueError("resources.json must contain a skill-keyed object")
    role_skills = {
        role["id"]: {normalize_skill(skill["name"]) for skill in role["skills"]}
        for role in roles
    }
    for alias, target in sorted(aliases.items()):
        if target not in vocabulary or target in aliases or alias in vocabulary:
            errors.append(f"alias.{alias}: target must be a canonical catalog skill without a chain/shadow")

    resource_rows = []
    grouped_resources: dict[str, list[dict]] = defaultdict(list)
    resource_ids: set[str] = set()
    for skill, group in sorted(resources.items()):
        if normalize_skill(skill) != skill or skill not in vocabulary:
            errors.append(f"resources.{skill}: noncanonical or unknown skill")
        if not isinstance(group, dict) or not isinstance(group.get("resources"), list):
            errors.append(f"resources.{skill}: expected resources list")
            continue
        for index, record in enumerate(group["resources"]):
            locator = f"resources.json#/{skill}/resources/{index}"
            if not isinstance(record, dict):
                errors.append(f"{locator}: expected object")
                continue
            record_id = record.get("id")
            if not _nonempty(record_id) or record_id in resource_ids:
                errors.append(f"{locator}: missing or duplicate resource id")
            resource_ids.add(str(record_id))
            status = resource_review_status(record)
            if status not in RESOURCE_STATUSES:
                errors.append(f"{locator}: invalid review status {status!r}")
            if record.get("content_review_status") in {"reviewed", "partial"}:
                if not _nonempty(record.get("review_note")) or _recorded_date(record.get("content_reviewed_at"), as_of) is None:
                    errors.append(f"{locator}: reviewed/partial needs a note and nonfuture review date")
            start, end = record.get("level_from"), record.get("level_to")
            level_range_valid = type(start) is int and type(end) is int and 1 <= start <= end <= 3
            if not level_range_valid:
                errors.append(f"{locator}: invalid level range")
            reason = _resource_reason(record, skill, as_of)
            checked = _recorded_date(record.get("last_checked"), as_of)
            row = {
                "id": record_id, "skill": skill, "locator": locator,
                "declared_review_status": record.get("content_review_status", "unreviewed"),
                "review_status": status, "eligible": reason is None and level_range_valid,
                "exclusion_reason": reason or (None if level_range_valid else "invalid_level_range"),
                "level_from": start, "level_to": end,
                "url": record.get("url"), "link_checked_at": record.get("last_checked"),
                "link_check_age_days": (as_of - checked).days if checked else None,
                "duration_hours": record.get("duration_hours"),
                "provenance": _provenance(record, as_of),
            }
            resource_rows.append(row)
            grouped_resources[skill].append(row)

    current_urls = {row["url"] for row in resource_rows if _http_url(row["url"])}
    attestation_path = directory / "link_review_attestation.json"
    if attestation_path.is_file():
        link_attestation = _link_attestation(read(attestation_path), current_urls, as_of)
    else:
        link_attestation = {
            "status": "not_recorded", "url_count": len(current_urls),
            "attested_at": None, "evidence_kind": None,
            "content_fit": "not_established_by_link_attestation",
            "reuse_permission": "not_established_by_link_attestation",
        }

    banks = sorted(path for folder in ("interview_question", "interview_questions")
                   for path in (directory / folder).glob("*.json"))
    if not banks and (directory / "interview_questions.json").is_file():
        banks = [directory / "interview_questions.json"]
    raw_questions: list[tuple[str, dict]] = []
    question_rows = []
    seen_bank_roles = set()
    for path in banks:
        payload = read(path)
        mapping = payload.get("roles", payload) if isinstance(payload, dict) else None
        if not isinstance(mapping, dict):
            errors.append(f"{path.name}: expected role mapping")
            continue
        for role_id, questions in sorted(mapping.items()):
            if role_id in seen_bank_roles:
                errors.append(f"questions.{role_id}: role appears in more than one bank")
            seen_bank_roles.add(role_id)
            if not isinstance(questions, list) or not questions:
                errors.append(f"questions.{role_id}: expected nonempty question list")
                continue
            for index, question in enumerate(questions):
                locator = f"{path.relative_to(directory).as_posix()}#/roles/{role_id}/{index}"
                if not isinstance(question, dict):
                    errors.append(f"{locator}: expected question object")
                    continue
                raw_questions.append((role_id, question))
                skill = normalize_skill(question.get("skill", ""))
                skill = aliases.get(skill, skill)
                if skill not in role_skills.get(role_id, set()):
                    errors.append(f"{locator}: question skill is not required by its role")
                status, missing = _question_review(question, as_of)
                if missing:
                    errors.append(f"{locator}: incomplete claimed review: {', '.join(missing)}")
                question_rows.append({
                    "id": question.get("id"), "role_id": role_id, "skill": skill,
                    "locator": locator, "declared_review_status": question.get("quality", "unreviewed"),
                    "review_status": status, "missing_review_fields": missing,
                    "review_sources": question.get("quality_sources", []),
                    "reviewer_recorded": question.get("quality_reviewer"),
                    "editorial_flags": (["generic_how_used_prompt"] if "hãy mô tả cách bạn dùng" in str(question.get("question", "")).casefold() else []),
                    "provenance": _provenance(question, as_of),
                })
    errors.extend(validate_question_records(
        raw_questions, role_ids=set(role_skills), skill_vocabulary=vocabulary, aliases=aliases,
    ))
    for role_id in sorted(set(role_skills) - seen_bank_roles):
        errors.append(f"questions.{role_id}: role has no question bank")

    matrix = []
    for skill in sorted(vocabulary):
        practice_available = bool(get_practice_routes([skill], resources))
        for level in (1, 2, 3):
            candidates = [row for row in grouped_resources[skill]
                          if row["eligible"] and row["level_from"] <= level <= row["level_to"]]
            reviewed = [row for row in candidates if row["review_status"] == "reviewed"]
            status = "reviewed" if reviewed else "partial" if candidates else "none"
            matrix.append({
                "skill": skill, "level": level, "resource_status": status,
                "resource_ids": [row["id"] for row in reviewed or candidates],
                "practice_route_available": practice_available,
            })

    matrix_index = {(row["skill"], row["level"]): row for row in matrix}
    questions_by_role: dict[str, list[dict]] = defaultdict(list)
    questions_by_role_skill: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in question_rows:
        questions_by_role[row["role_id"]].append(row)
        questions_by_role_skill[row["role_id"], row["skill"]].append(row)
    role_rows = []
    role_skill_requirements = []
    for role in sorted(roles, key=lambda value: value["id"]):
        role_id = role["id"]
        question_counts = Counter(row["review_status"] for row in questions_by_role[role_id])
        requirement_rows = []
        for requirement in role["skills"]:
            skill = normalize_skill(requirement["name"])
            level = requirement["level"]
            material = matrix_index.get((skill, level))
            questions_for_skill = questions_by_role_skill[role_id, skill]
            requirement_rows.append({
                "role_id": role_id, "skill": skill, "required_level": level,
                "weight": requirement["weight"],
                "required_level_resource_status": material["resource_status"] if material else "none",
                "required_level_resource_ids": material["resource_ids"] if material else [],
                "practice_route_available": bool(material and material["practice_route_available"]),
                "question_ids": [row["id"] for row in questions_for_skill],
                "question_review_statuses": [row["review_status"] for row in questions_for_skill],
            })
        role_skill_requirements.extend(requirement_rows)
        role_rows.append({
            "id": role_id, "name": role.get("name_vi", role["name"]),
            "required_skills": len(role_skills[role_id]),
            "skills_with_eligible_material": sum(any(row["eligible"] for row in grouped_resources[skill]) for skill in role_skills[role_id]),
            "skills_with_material_at_required_level": sum(row["required_level_resource_status"] != "none" for row in requirement_rows),
            "skills_with_question": sum(bool(row["question_ids"]) for row in requirement_rows),
            "high_weight_skills_without_question": sum(row["weight"] >= 2 and not row["question_ids"] for row in requirement_rows),
            "high_weight_skills_without_required_level_material": sum(row["weight"] >= 2 and row["required_level_resource_status"] == "none" for row in requirement_rows),
            "skills_with_practice_route": len(get_practice_routes(sorted(role_skills[role_id]), resources)),
            "question_count": len(questions_by_role[role_id]),
            "question_review_counts": {key: question_counts[key] for key in QUESTION_STATUSES},
            "provenance": _provenance(role, as_of),
        })

    review_counts = Counter(row["review_status"] for row in question_rows)
    resource_counts = Counter(row["review_status"] for row in resource_rows)
    matrix_counts = Counter(row["resource_status"] for row in matrix)
    high_weight_requirements = [row for row in role_skill_requirements if row["weight"] >= 2]
    provenance_counts = {
        kind: {"total": len(rows), "metadata_present": sum(row["provenance"]["metadata_present"] for row in rows),
               "evidence_fields_complete": sum(row["provenance"]["evidence_fields_complete"] for row in rows)}
        for kind, rows in (("roles", role_rows), ("questions", question_rows), ("resource_mappings", resource_rows))
    }
    fingerprints = [
        {"path": path.relative_to(directory).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(source_paths, key=lambda value: value.relative_to(directory).as_posix())
    ]
    digest = hashlib.sha256(json.dumps(fingerprints, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    errors = sorted(set(errors))
    questions_pending = review_counts["unreviewed"] + review_counts["template"]
    provenance_pending = sum(value["total"] - value["evidence_fields_complete"] for value in provenance_counts.values())
    return {
        "schema_version": 1, "as_of": as_of.isoformat(),
        "dataset_fingerprint": {"sha256": digest, "files": fingerprints},
        "scope": {
            "network_checked": False,
            "expert_validation": "not_established_by_this_inventory",
            "legal_permission": "not_determined_by_this_inventory",
            "provenance_required_fields": list(PROVENANCE_FIELDS),
            "note": "Review sources support content checking; they do not grant redistribution rights. Missing record-level metadata does not establish infringement or absence of evidence elsewhere.",
            "link_attestation": link_attestation,
        },
        "summary": {
            "roles": len(role_rows), "role_skills": len(set().union(*role_skills.values())) if role_skills else 0,
            "recognition_skills": len(vocabulary),
            "resources": {"mappings": len(resource_rows), "unique_urls": len({row["url"] for row in resource_rows if _http_url(row["url"])}),
                          "by_review_status": {key: resource_counts[key] for key in RESOURCE_STATUSES},
                          "eligible_mappings": sum(row["eligible"] for row in resource_rows),
                          "skills_with_eligible_material": len({row["skill"] for row in resource_rows if row["eligible"]}),
                          "published_duration_mappings": sum(row["duration_hours"] is not None for row in resource_rows),
                          "reviewed_three_level_mappings_to_recheck": sum(row["review_status"] == "reviewed" and row["level_from"] == 1 and row["level_to"] == 3 for row in resource_rows)},
            "questions": {"total": len(question_rows), "by_review_status": {key: review_counts[key] for key in QUESTION_STATUSES},
                          "roles_with_any_internal_review": sum(any(row["question_review_counts"][key] for key in QUESTION_STATUSES[:2]) for row in role_rows)},
            "skill_level_coverage": {"cells": len(matrix), **{key: matrix_counts[key] for key in ("reviewed", "partial", "none")},
                                     "no_material_but_practice_route": sum(row["resource_status"] == "none" and row["practice_route_available"] for row in matrix)},
            "role_skill_readiness": {
                "requirements": len(role_skill_requirements),
                "with_question": sum(bool(row["question_ids"]) for row in role_skill_requirements),
                "with_material_at_required_level": sum(row["required_level_resource_status"] != "none" for row in role_skill_requirements),
                "high_weight_requirements": len(high_weight_requirements),
                "high_weight_with_question": sum(bool(row["question_ids"]) for row in high_weight_requirements),
                "high_weight_with_material_at_required_level": sum(row["required_level_resource_status"] != "none" for row in high_weight_requirements),
                "material_missing_but_practice_route": sum(row["required_level_resource_status"] == "none" and row["practice_route_available"] for row in role_skill_requirements),
                "generic_how_used_questions_for_editorial_review": sum(bool(row["editorial_flags"]) for row in question_rows),
            },
            "recorded_provenance": provenance_counts,
        },
        "gates": {
            "inventory_consistency": {"passed": not errors, "errors": errors},
            "current_link_attestation": {
                "passed": link_attestation["status"] == "user_attested_current_url_set",
                "status": link_attestation["status"],
                "note": "Only checks that the user's recorded URL-set statement still matches the current catalog; it does not re-open URLs or review content.",
            },
            "complete_question_review_metadata": {"passed": questions_pending == 0, "pending": questions_pending,
                                                   "note": "Passing this gate still does not establish expert validation."},
            "complete_recorded_provenance": {"passed": provenance_pending == 0, "pending": provenance_pending,
                                            "note": "Passing this gate means metadata are present, not legal approval."},
        },
        "roles": role_rows, "role_skill_requirements": role_skill_requirements, "questions": question_rows,
        "resource_mappings": resource_rows, "skill_level_coverage": matrix,
    }


def gate_failures(report: dict, *, require_complete_review: bool = False, require_provenance: bool = False,
                  require_current_link_attestation: bool = False) -> list[str]:
    required = ["inventory_consistency"]
    if require_current_link_attestation:
        required.append("current_link_attestation")
    if require_complete_review:
        required.append("complete_question_review_metadata")
    if require_provenance:
        required.append("complete_recorded_provenance")
    return [key for key in required if not report["gates"][key]["passed"]]


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    resources = summary["resources"]
    questions = summary["questions"]
    coverage = summary["skill_level_coverage"]
    readiness = summary["role_skill_readiness"]
    link_attestation = report["scope"]["link_attestation"]
    lines = [
        "# Kiểm kê mức sẵn sàng dữ liệu", "",
        f"Ngày đối chiếu: **{report['as_of']}**. Dấu vân tay dữ liệu: `{report['dataset_fingerprint']['sha256']}`.", "",
        "Báo cáo đọc dữ liệu hiện có, không sửa record và không truy cập mạng. Review nội dung, khả năng truy cập link và quyền phân phối là ba loại bằng chứng riêng. Thiếu metadata không chứng minh vi phạm quyền hoặc chưa từng có review ở nơi khác.", "",
        "| Nhóm | Kết quả |", "| --- | --- |",
        f"| Catalog | {summary['roles']} role; {summary['role_skills']} skill của role; {summary['recognition_skills']} skill nhận diện |",
        f"| Resource mapping | {resources['mappings']} record; {resources['unique_urls']} URL; {resources['eligible_mappings']} mapping đủ điều kiện qua chính sách hiện hành trên {resources['skills_with_eligible_material']} skill |",
        f"| Trạng thái học liệu | " + "; ".join(f"{key}: {value}" for key, value in resources["by_review_status"].items()) + " |",
        f"| Ngân hàng phỏng vấn | {questions['total']} câu; " + "; ".join(f"{key}: {value}" for key, value in questions["by_review_status"].items()) + " |",
        f"| Role có ít nhất một câu review nội bộ/AI hỗ trợ | {questions['roles_with_any_internal_review']}/{summary['roles']} |",
        f"| Skill × level | {coverage['cells']} ô: {coverage['reviewed']} reviewed; {coverage['partial']} partial; {coverage['none']} chưa có tài liệu đủ điều kiện |",
        f"| Thực hành cho ô chưa có tài liệu | {coverage['no_material_but_practice_route']} ô có lộ trình thực hành; không coi đây là chứng nhận bao phủ chuyên môn |",
        f"| Nghề × kỹ năng yêu cầu | {readiness['requirements']} cặp; {readiness['with_question']} có ít nhất một câu hỏi; {readiness['with_material_at_required_level']} có học liệu đúng Level yêu cầu |",
        f"| Cặp ưu tiên (weight ≥ 2) | {readiness['high_weight_requirements']} cặp; {readiness['high_weight_with_question']} có câu hỏi; {readiness['high_weight_with_material_at_required_level']} có học liệu đúng Level |",
        f"| Cần biên tập thêm | {readiness['generic_how_used_questions_for_editorial_review']} câu dùng mẫu lời hỏi chung; {resources['reviewed_three_level_mappings_to_recheck']} mapping reviewed phủ cả Level 1–3 cần đối chiếu phạm vi |",
        f"| Xác nhận link do người dùng báo | {link_attestation['status']}: {link_attestation['url_count']} URL; ngày {link_attestation['attested_at'] or 'chưa ghi'} |",
        "", "Xác nhận link chỉ ghi nhận lời kiểm tra thủ công của người dùng trên đúng tập URL hiện tại; không nâng mức review nội dung, Level hay quyền sử dụng. Bất cứ URL nào đổi sẽ làm dấu vân tay xác nhận này hết hiệu lực.",
        "", "## Cổng kiểm tra", "",
        "| Cổng | Trạng thái | Phạm vi |", "| --- | --- | --- |",
        f"| Nhất quán của inventory | {'PASS' if report['gates']['inventory_consistency']['passed'] else 'FAIL'} | {len(report['gates']['inventory_consistency']['errors'])} lỗi; cần chạy thêm bộ test/validator dự án |",
        f"| Dấu vân tay xác nhận link | {'PASS' if report['gates']['current_link_attestation']['passed'] else 'PENDING'} | So khớp {link_attestation['url_count']} URL với lời kiểm tra thủ công của người dùng; không phải tái kiểm tra mạng |",
        f"| Metadata review toàn ngân hàng | {'PASS' if report['gates']['complete_question_review_metadata']['passed'] else 'PENDING'} | {report['gates']['complete_question_review_metadata']['pending']} câu unreviewed/template; không thay thế chuyên gia |",
        f"| Metadata provenance theo record | {'PASS' if report['gates']['complete_recorded_provenance']['passed'] else 'PENDING'} | {report['gates']['complete_recorded_provenance']['pending']} record chưa đủ trường bằng chứng; không phải kết luận pháp lý |",
        "", "## Khung khắc phục", "",
        "1. **Review câu hỏi theo role và mức độ rủi ro:** ưu tiên các role trình diễn và role dùng thực tế, rồi chia backlog theo chuyên ngành. Mỗi câu cần tình huống riêng, hướng dẫn có bối cảnh, nguồn phù hợp, ngày và người review; AI hỗ trợ vẫn giữ nhãn riêng. Chỉ người có chuyên môn/owner mới có thể cung cấp xác nhận độc lập.",
        "2. **Bổ sung học liệu theo ô skill–level đang thiếu:** không tăng level_from/level_to chỉ để làm đầy ma trận. Partial phải có bài tập phù hợp và ghi phạm vi. Kỹ năng mềm dùng thực hành, người quan sát và phản hồi; các ô thực hành không tự biến thành tài liệu chuyên môn đã review.",
        "3. **Đối chiếu nguồn gốc trước phát hành dữ liệu:** owner ghi tác giả/nguồn gốc, cơ sở sử dụng, giấy phép/điều khoản và người xác nhận. quality_sources, verified=true và HTTP 200 không phải quyền sao chép. Có thể dẫn chứng manifest cấp tệp khi cùng nguồn/phạm vi, nhưng cần ánh xạ rõ tới record.",
        "4. **Catalog nghề:** ghi cơ sở của skill/level/weight và review của người hiểu nghề; regression synthetic không chứng minh độ phù hợp tuyển dụng ngoài đời.",
        "5. **Không nâng điểm bằng đổi nhãn:** report cho phép CI chặn claim review thiếu bằng chứng, giữ pending ngoài phạm vi đã xác minh. Website cần nói rõ câu hỏi tham khảo và metadata nội bộ.",
        "", "## Ghi metadata provenance", "",
        "Schema 2.0 ghi `provenance` với bảy trường: `source_url`, `author_origin`, `curated_by`, `review_tier`, `reviewed_at`, `rights_basis`, `license_notes`. `null`/`pending` không được tính là bằng chứng. URL nguồn của học liệu không tự xác nhận tác giả mapping, quyền sao chép hoặc license dữ liệu; không mặc định MIT cho dữ liệu. Cổng đầy đủ vẫn pending cho đến khi owner/chuyên gia cung cấp căn cứ thật.", "",
        "| Nhóm record | Tổng | Có metadata | Đủ trường bằng chứng |",
        "| --- | ---: | ---: | ---: |",
    ]
    for kind, counts in summary["recorded_provenance"].items():
        lines.append(f"| {kind} | {counts['total']} | {counts['metadata_present']} | {counts['evidence_fields_complete']} |")
    lines.extend(["", "## Role có review nội bộ hoặc AI hỗ trợ", "", "| Role | Tổng câu | Review nội bộ | AI hỗ trợ | Template | Chưa review |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for row in report["roles"]:
        counts = row["question_review_counts"]
        if counts["reviewed_internal"] or counts["ai_reviewed_internal"]:
            lines.append(f"| {row['id']} | {row['question_count']} | {counts['reviewed_internal']} | {counts['ai_reviewed_internal']} | {counts['template']} | {counts['unreviewed']} |")
    lines.extend(["", "## Những nghề cần ưu tiên bổ sung theo Level và câu hỏi", "",
                  "Bảng xếp theo số kỹ năng weight ≥ 2 chưa có tài liệu đúng Level và số kỹ năng chưa có câu hỏi. Một URL nhập môn ở Level 1 không được tính là bao phủ yêu cầu Level 3.", "",
                  "| Role | Học liệu đúng Level / skill | Skill có câu hỏi / skill | Thiếu học liệu ưu tiên | Thiếu câu hỏi ưu tiên |",
                  "| --- | ---: | ---: | ---: | ---: |"])
    priority_roles = sorted(report["roles"], key=lambda row: (
        -row["high_weight_skills_without_required_level_material"],
        -row["high_weight_skills_without_question"], row["id"],
    ))[:25]
    for row in priority_roles:
        lines.append(
            f"| `{row['id']}` | {row['skills_with_material_at_required_level']}/{row['required_skills']} | "
            f"{row['skills_with_question']}/{row['required_skills']} | "
            f"{row['high_weight_skills_without_required_level_material']} | {row['high_weight_skills_without_question']} |"
        )
    lines.extend(["", "## Tái lập", "", "```powershell",
                  f"python scripts/audit_data_readiness.py --as-of {report['as_of']} --json-output docs/verification/data-readiness-{report['as_of']}.json --markdown-output docs/verification/data-readiness-{report['as_of']}.md",
                  "```", "", "CLI mặc định trả lỗi khi inventory không nhất quán. Thêm `--require-current-link-attestation` để CI phát hiện tập URL đã đổi sau lời kiểm tra của người dùng; tùy chọn `--require-complete-review` hoặc `--require-provenance` dành cho cổng phát hành. Không bật rồi đổi nhãn giả để làm test xanh. JSON chứa locator, trạng thái và thiếu hụt của từng record để chia việc review.", ""])
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--require-complete-review", action="store_true")
    parser.add_argument("--require-provenance", action="store_true")
    parser.add_argument("--require-current-link-attestation", action="store_true")
    args = parser.parse_args()
    report = build_inventory(args.data_dir, as_of=args.as_of)
    for path, content in (
        (args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
        (args.markdown_output, render_markdown(report)),
    ):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    failures = gate_failures(report, require_complete_review=args.require_complete_review,
                             require_provenance=args.require_provenance,
                             require_current_link_attestation=args.require_current_link_attestation)
    print(json.dumps({"summary": report["summary"], "failed_required_gates": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
