"""Generate a reproducible editorial queue from the data-readiness inventory.

This prioritizes coverage work; it does not change content-review states or
assert that a course, practice route, or interview answer is expert-approved.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_data_readiness import build_inventory


DEMO_ROLES = ("data_analyst", "frontend_developer_react", "backend_developer_java", "sales_executive")


def render_priority(report: dict) -> str:
    roles = report["roles"]
    requirements = report["role_skill_requirements"]
    by_skill: dict[str, list[dict]] = defaultdict(list)
    for row in requirements:
        by_skill[row["skill"]].append(row)
    roles_by_id = {row["id"]: row for row in roles}
    ordered_roles = [roles_by_id[key] for key in DEMO_ROLES if key in roles_by_id]
    ordered_roles.extend(sorted(
        (row for row in roles if row["id"] not in DEMO_ROLES),
        key=lambda row: (-row["high_weight_skills_without_required_level_material"],
                         -row["high_weight_skills_without_question"], row["id"]),
    ))
    lines = [
        f"# Danh sách ưu tiên review dữ liệu — {report['as_of']}", "",
        "Danh sách này được sinh lại từ [inventory JSON](data-readiness-2026-10-26.json), không phải phán quyết chuyên môn. Bốn role demo đứng đầu; các role còn lại xếp theo số kỹ năng weight ≥ 2 thiếu học liệu **đúng Level yêu cầu**, rồi số kỹ năng ưu tiên thiếu câu hỏi. Một tài liệu Level 1 không làm đầy yêu cầu Level 3.", "",
        f"Dấu vân tay dataset: `{report['dataset_fingerprint']['sha256']}`. Xác nhận URL do người dùng báo: `{report['scope']['link_attestation']['status']}`; điều này không nâng review nội dung hoặc quyền sử dụng.", "",
        "## Toàn bộ 131 nghề", "",
        "| Role ID | Tên | Học liệu đúng Level / skill | Skill có câu hỏi / skill | Câu chưa review + template | Thiếu học liệu ưu tiên | Thiếu câu hỏi ưu tiên |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ordered_roles:
        counts = row["question_review_counts"]
        pending = counts["unreviewed"] + counts["template"]
        lines.append(
            f"| `{row['id']}` | {row['name']} | "
            f"{row['skills_with_material_at_required_level']}/{row['required_skills']} | "
            f"{row['skills_with_question']}/{row['required_skills']} | {pending} | "
            f"{row['high_weight_skills_without_required_level_material']} | "
            f"{row['high_weight_skills_without_question']} |"
        )

    missing_by_skill = []
    for skill, rows in by_skill.items():
        no_material = [row for row in rows if row["required_level_resource_status"] == "none"]
        no_question = [row for row in rows if not row["question_ids"]]
        important = sum(row["weight"] >= 2 for row in no_material)
        if no_material or no_question:
            missing_by_skill.append((skill, len(rows), len(no_material), len(no_question), important,
                                     sum(row["practice_route_available"] for row in no_material)))
    missing_by_skill.sort(key=lambda row: (-row[4], -row[2], -row[3], -row[1], row[0]))
    lines.extend(["", "## 40 kỹ năng cần biên tập trước", "",
                  "Số đếm theo **cặp nghề–kỹ năng**, nên một skill dùng ở nhiều nghề được tính nhiều lần. Với kỹ năng mềm, route thực hành có giám sát là một giải pháp hợp lệ và không bị đánh đồng với khóa học. Danh sách đủ 1.192 cặp, Level đích, câu hỏi và mapping ID nằm trong inventory JSON.", "",
                  "| Kỹ năng | Số nghề dùng | Cặp thiếu tài liệu đúng Level | Cặp thiếu câu hỏi | Thiếu tài liệu ưu tiên | Cặp có route thực hành |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for skill, role_count, no_material, no_question, important, practice in missing_by_skill[:40]:
        lines.append(f"| {skill.replace('|', '&#124;')} | {role_count} | {no_material} | {no_question} | {important} | {practice} |")

    generic_by_role = Counter(row["role_id"] for row in report["questions"] if row["editorial_flags"])
    broad = [row for row in report["resource_mappings"]
             if row["review_status"] == "reviewed" and row["level_from"] == 1 and row["level_to"] == 3]
    lines.extend(["", "## Hàng đợi biên tập nội dung", "",
                  f"- {sum(generic_by_role.values())} câu có mẫu lời hỏi chung ‘hãy mô tả cách bạn dùng…’; kiểm tra bối cảnh, tình huống và đáp án trước khi nâng trạng thái. Role có nhiều nhất: "
                  + ", ".join(f"`{role}` ({count})" for role, count in generic_by_role.most_common(12)) + ".",
                  f"- {len(broad)} mapping `reviewed` đang gắn cả Level 1–3. Đây là danh sách **cần đối chiếu**, không tự động là sai: "
                  + ", ".join(f"`{row['id']}`" for row in broad) + ".",
                  "- Các nội dung thuế, luật lao động và huấn luyện an toàn cần nguồn thẩm quyền hiện hành cùng người có chuyên môn. Link mở được không đóng cổng này.", "",
                  "## Quy trình đóng từng hàng", "",
                  "1. Mở locator của cặp nghề–skill, câu hỏi và resource trong inventory JSON; đối chiếu Level đích, weight và nhu cầu thực tế của vị trí.",
                  "2. Với câu hỏi, sửa tình huống và đáp án tham khảo theo nguồn chuyên ngành; ghi người/ngày review, phạm vi và quyền dùng. Không tự đổi `unreviewed` thành review chuyên gia.",
                  "3. Với học liệu, kiểm tra trang gốc, mục/bài cụ thể và Level thực sự được dạy. Giữ `partial` nếu phạm vi hẹp; bổ sung bài tập/portfolio hoặc role-play có người giám sát cho phần còn thiếu.",
                  "4. Chạy inventory, validator ngân hàng, module sweep và test trình duyệt cho role vừa sửa; so sánh độ phủ theo Level và câu hỏi. Giữ bằng chứng cùng commit.", "",
                  "```powershell", f"python scripts/generate_priority_review.py --as-of {report['as_of']}", "```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, default=ROOT / "docs/verification/priority-review-2026-10-26.md")
    args = parser.parse_args()
    report = build_inventory(as_of=args.as_of)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_priority(report), encoding="utf-8")
    print(f"{len(report['roles'])} roles; {len(report['role_skill_requirements'])} role-skill requirements; {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
