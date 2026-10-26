"""Create a factual mapping-by-mapping evidence queue for demo roles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = ("sales_executive", "frontend_developer_react", "data_analyst", "backend_developer_java")


def generate(data_dir: Path = ROOT / "Data") -> str:
    roles = {item["id"]: item for item in json.loads((data_dir / "roles.json").read_text(encoding="utf-8"))}
    resources = json.loads((data_dir / "resources.json").read_text(encoding="utf-8"))
    lines = ["# Hàng đợi học liệu 4 nghề demo — 2026-10-26", "",
             "Mỗi hàng là một mapping trong nghề demo, nên một ID dùng ở nhiều nghề xuất hiện nhiều lần. `user_attested_manual` chỉ là xác nhận link của chủ dự án; `independently_accessible` chỉ nói trang đọc được, không chứng minh nội dung dạy đúng Level hoặc quyền tái sử dụng.", "",
             "`duration_hours=null` nghĩa là chưa có căn cứ thời lượng trên trang đích. Mapping unsuitable/blocked được giữ trong dữ liệu để tra cứu và bị loại khỏi lộ trình.", "",
             "| Nghề | Kỹ năng / Level đích | ID | Level tài liệu | Status | Bài/chương | Truy cập | Thời lượng | Việc còn thiếu |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for role_id in ROLES:
        for skill in roles[role_id]["skills"]:
            name, target = skill["name"], skill["level"]
            for record in resources[name]["resources"]:
                axes = record.get("verification_axes") or {}
                status = record.get("content_review_status")
                granularity = record.get("scope_granularity")
                access = axes.get("access_status")
                missing = []
                if status in {"unsuitable", "blocked"}:
                    missing.append("Thay nguồn phù hợp; giữ bản ghi bị loại")
                if granularity not in {"lesson", "module", "chapter", "spec"} or not record.get("evidence_locator"):
                    missing.append("Xác định bài/chương và locator")
                if access != "independently_accessible":
                    missing.append("Mở và đối chiếu độc lập")
                if record["level_to"] < target:
                    missing.append("Chưa phủ Level đích; cần thực hành/nguồn bổ sung")
                if not axes.get("rights_basis") or axes.get("rights_basis") == "pending":
                    missing.append("Quyền tái sử dụng chưa xác minh")
                if record.get("duration_hours") is None:
                    missing.append("Chưa có thời lượng công bố; giữ null")
                title = record["id"].replace("|", "\\|")
                lines.append(f"| `{role_id}` | {name} L{target} | [{title}]({record.get('url', '')}) | L{record['level_from']}–{record['level_to']} | {status} | {granularity} | {access} | {record.get('duration_hours') if record.get('duration_hours') is not None else 'Chưa rõ'} | {'; '.join(missing) or 'Chờ owner phê duyệt'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/verification/needs-human-resource.md")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = generate()
    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output}: {sum(line.startswith('| `') for line in content.splitlines())} mapping occurrences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
