"""Read-only inventory of excluded mappings and their recorded reasons."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Data/resources.json"


def classify(status: str, note: str) -> str:
    text = note.casefold()
    if status == "blocked":
        if any(term in text for term in ("403", "404", "429", "lỗi truy cập")):
            return "access_error_recorded"
        if any(term in text for term in ("đăng nhập", "login", "trả phí", "paywall")):
            return "access_requirement_recorded"
        if any(term in text for term in ("javascript", "tải động", "không đọc được")):
            return "content_not_inspectable_recorded"
        return "blocked_reason_needs_manual_classification"
    if any(term in text for term in ("thuế việt nam", "luật việt nam", "chứng chỉ", "quy chuẩn")):
        return "specialist_or_jurisdiction_evidence_missing"
    if any(term in text for term in ("trang chủ", "danh mục", "cổng tổng hợp", "portal", "trang /learn")):
        return "catalog_or_homepage_instead_of_lesson"
    if any(term in text for term in ("không dạy", "không phải", "không được nội dung", "không có nội dung", "chỉ tập trung")):
        return "recorded_skill_content_mismatch"
    return "unsuitable_reason_needs_manual_classification"


def inventory(source: Path = SOURCE) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    records = []
    for skill, group in data.items():
        for record in group["resources"]:
            status = record.get("content_review_status")
            if status not in {"blocked", "unsuitable"}:
                continue
            note = record.get("review_note") or ""
            records.append({"skill": skill, "id": record["id"], "status": status,
                            "reason_code": classify(status, note),
                            "recorded_note": note, "url": record.get("url")})
    status_counts = Counter(item["status"] for item in records)
    reason_counts = Counter(item["reason_code"] for item in records)
    return {"scope": "recorded_status_and_machine_triage_not_new_content_review",
            "total": len(records), "by_status": dict(status_counts),
            "by_reason": dict(reason_counts), "records": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    result = inventory()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        lines = ["# Hàng đợi mapping không được đề xuất — 2026-10-26", "",
                 "Phân loại dưới đây dựa trên ghi chú review đã có. Mã `needs_manual_classification` cần người biên tập xem lại; không có mapping nào được tự động nâng trạng thái.", "",
                 f"Tổng {result['total']} mapping; unsuitable {result['by_status'].get('unsuitable', 0)}, blocked {result['by_status'].get('blocked', 0)}.", "",
                 "| Mã lý do | Số mapping |", "| --- | ---: |"]
        lines.extend(f"| `{code}` | {count} |" for code, count in sorted(result["by_reason"].items()))
        lines.extend(["", "| Kỹ năng | ID | Trạng thái | Lý do máy phân loại | Ghi chú đã lưu |", "| --- | --- | --- | --- | --- |"])
        for item in result["records"]:
            note = item["recorded_note"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {item['skill']} | `{item['id']}` | {item['status']} | `{item['reason_code']}` | {note} |")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("total", "by_status", "by_reason")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
