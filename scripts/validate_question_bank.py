"""Validate interview-bank integrity without treating checks as expert review."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.skill_extractor import load_aliases, normalize_skill


def _load_banks(data_dir: Path) -> dict[str, list[dict[str, Any]]]:
    directories = (data_dir / "interview_questions", data_dir / "interview_question")
    paths = [path for directory in directories if directory.is_dir() for path in sorted(directory.glob("*.json"))]
    if not paths and (data_dir / "interview_questions.json").is_file():
        paths = [data_dir / "interview_questions.json"]
    merged: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        role_map = payload.get("roles", payload) if isinstance(payload, dict) else None
        if not isinstance(role_map, dict):
            continue
        for role_id, questions in role_map.items():
            if isinstance(questions, list):
                merged.setdefault(str(role_id), []).extend(
                    question for question in questions if isinstance(question, dict)
                )
    return merged


def _canonical(value: str, aliases: dict[str, str]) -> str:
    result = normalize_skill(value)
    visited: set[str] = set()
    while result in aliases and result not in visited:
        visited.add(result)
        result = normalize_skill(aliases[result])
    return result


def _normalized_question(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", text).strip()


def validate_question_records(
    records: Iterable[tuple[str, dict[str, Any]]],
    *,
    role_ids: set[str],
    skill_vocabulary: set[str],
    aliases: dict[str, str] | None = None,
) -> list[str]:
    """Return stable integrity errors for question rows and catalog references."""
    aliases = aliases or {}
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_questions: dict[str, str] = {}
    for role_id, question in records:
        question_id = question.get("id")
        text = question.get("question")
        skill = question.get("skill")
        question_type = question.get("type")
        label = question_id if isinstance(question_id, str) and question_id else f"<ID trống>/{role_id}"
        if role_id not in role_ids:
            errors.append(f"{label}: role_id {role_id!r} không tồn tại trong catalog.")
        if not isinstance(question_id, str) or not question_id.strip():
            errors.append(f"{label}: thiếu id.")
        elif question_id in seen_ids:
            errors.append(f"{label}: id câu hỏi bị trùng.")
        else:
            seen_ids.add(question_id)
        if not isinstance(text, str) or len(text.strip()) < 20:
            errors.append(f"{label}: câu hỏi thiếu nội dung hoặc ngắn hơn 20 ký tự.")
        else:
            normalized = _normalized_question(text)
            previous = seen_questions.get(normalized)
            if previous:
                errors.append(f"{label}: câu hỏi trùng nội dung với {previous}.")
            else:
                seen_questions[normalized] = label
        if not isinstance(question_type, str) or not question_type.strip():
            errors.append(f"{label}: thiếu type.")
        elif question_type not in {"technical", "scenario"}:
            errors.append(f"{label}: type {question_type!r} không thuộc technical/scenario.")
        if not isinstance(skill, str) or not skill.strip():
            errors.append(f"{label}: thiếu skill.")
        elif _canonical(skill, aliases) not in skill_vocabulary:
            errors.append(f"{label}: skill {skill!r} không tồn tại trong catalog.")
        if not (isinstance(question.get("reference_answer"), str) and question["reference_answer"].strip()) and not (
            isinstance(question.get("good_answer_points"), list)
            and any(isinstance(point, str) and point.strip() for point in question["good_answer_points"])
        ):
            errors.append(f"{label}: thiếu hướng dẫn trả lời/reference_answer hoặc good_answer_points.")
        quality = question.get("quality", "unreviewed")
        if quality not in {"reviewed", "ai_reviewed_internal", "template", "unreviewed"}:
            errors.append(f"{label}: quality {quality!r} không hợp lệ.")
        if quality in {"reviewed", "ai_reviewed_internal"}:
            try:
                from datetime import date

                date.fromisoformat(question.get("quality_reviewed_at", ""))
            except (TypeError, ValueError):
                errors.append(f"{label}: reviewed thiếu quality_reviewed_at dạng YYYY-MM-DD.")
            if not isinstance(question.get("quality_review_note"), str) or not question["quality_review_note"].strip():
                errors.append(f"{label}: reviewed thiếu quality_review_note.")
            sources = question.get("quality_sources")
            if not isinstance(sources, list) or not sources:
                errors.append(f"{label}: reviewed thiếu quality_sources.")
            else:
                for source in sources:
                    try:
                        parsed = urlsplit(source) if isinstance(source, str) else None
                    except ValueError:
                        parsed = None
                    if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                        errors.append(f"{label}: quality_sources chứa URL không hợp lệ.")
                        break
            if quality == "ai_reviewed_internal":
                reviewer = question.get("quality_reviewer")
                note = question.get("quality_review_note", "")
                if not isinstance(reviewer, str) or "AI" not in reviewer:
                    errors.append(f"{label}: AI review phải ghi rõ reviewer có nhãn AI.")
                if not isinstance(note, str) or "not an independent" not in note.casefold():
                    errors.append(f"{label}: AI review phải ghi rõ chưa thẩm định độc lập.")
    return errors


def validate_question_bank(data_dir: str | Path = DATA_DIR) -> dict[str, Any]:
    """Validate the whole bundled bank; automated integrity is not expert review."""
    directory = Path(data_dir)
    roles = load_roles(directory / "roles.json")
    vocabulary = load_skill_vocabulary(roles, data_dir=directory)
    alias_path = directory / "skill_aliases.json"
    aliases = load_aliases(alias_path) if alias_path.is_file() else {}
    banks = _load_banks(directory)
    records = [(role_id, question) for role_id, questions in banks.items() for question in questions]
    errors = validate_question_records(
        records,
        role_ids={role["id"] for role in roles},
        skill_vocabulary=vocabulary,
        aliases=aliases,
    )
    statuses = Counter()
    for _, question in records:
        status = question.get("quality", "unreviewed")
        if status == "reviewed":
            statuses["reviewed_internal"] += 1
        elif status == "ai_reviewed_internal":
            statuses["ai_reviewed_internal"] += 1
        else:
            statuses[status] += 1
    return {
        "role_count": len(banks),
        "question_count": len(records),
        "integrity_errors": errors,
        "review_status_counts": dict(sorted(statuses.items())),
        "note": "Kiểm tra tự động tính toàn vẹn; không xác nhận tính đúng chuyên môn hay thẩm định độc lập.",
    }


def main() -> int:
    # Windows PowerShell may attach a legacy cp1252 stream; the report includes
    # Vietnamese labels and should remain usable in terminals and redirected logs.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--json", action="store_true", help="In báo cáo JSON thay vì bảng ngắn.")
    args = parser.parse_args()
    report = validate_question_bank(args.data_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['question_count']} câu / {report['role_count']} vị trí; lỗi toàn vẹn: {len(report['integrity_errors'])}.")
        print(report["note"])
        for error in report["integrity_errors"]:
            print(f"- {error}")
    return 1 if report["integrity_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
