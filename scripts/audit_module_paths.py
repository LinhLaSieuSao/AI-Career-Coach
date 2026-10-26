"""Exercise every bundled role through core recommendation and interview APIs.

Uses synthetic profile skills only. A successful run establishes that current
catalog records can traverse the modules without exceptions; it is not an
expert judgement of occupational fit or a full browser usability audit.
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

from modules.catalog import DATA_DIR, load_roles
from modules.interview import get_question_feedback, get_questions
from modules.matcher import compute_gap, match_role
from modules.recommender import build_roadmap, build_timed_roadmap
from scripts.audit_data_readiness import build_inventory


def audit_paths(*, as_of: date | None = None) -> dict:
    inventory = build_inventory(as_of=as_of)
    roles = load_roles()
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    checks = Counter()
    rows = []
    for role in roles:
        role_id = role["id"]
        skills = [item["name"] for item in role["skills"]]
        sample = skills[:2]
        row = {"role_id": role_id, "errors": [], "questions_sampled": 0}

        def check(name: str, action):
            try:
                result = action()
                checks[name] += 1
                return result
            except Exception as exc:  # The report must keep testing other roles.
                row["errors"].append(f"{name}: {type(exc).__name__}: {exc}")
                return None

        check("presence_match", lambda: match_role(sample, role))
        gap = check("level_gap", lambda: compute_gap({skill: 1 for skill in sample}, role))
        roadmap = check("presence_roadmap", lambda: build_roadmap(skills, resources, weeks=4))
        if roadmap is not None and {skill for phase in roadmap for skill in phase["skills"]} != set(skills):
            row["errors"].append("presence_roadmap: role skills lost")
        if gap is not None:
            check("timed_roadmap", lambda: build_timed_roadmap(gap, resources, hours_per_week=8))
        questions = check("interview_selection", lambda: get_questions(role_id, n=3, seed=0))
        if questions is not None:
            row["questions_sampled"] = len(questions)
            if len(questions) != 3 or any(item.get("role_id") != role_id for item in questions):
                row["errors"].append("interview_selection: wrong count or role")
            for question in questions:
                guidance = check("answer_guidance", lambda qid=question["id"]: get_question_feedback(qid))
                if guidance is not None and not guidance.get("reference_answer"):
                    row["errors"].append(f"answer_guidance: empty reference for {question['id']}")
        rows.append(row)
    failed = [row for row in rows if row["errors"]]
    return {
        "schema_version": 1, "as_of": inventory["as_of"],
        "dataset_fingerprint": inventory["dataset_fingerprint"]["sha256"],
        "scope": "synthetic_core_module_paths_not_expert_or_browser_review",
        "summary": {"roles": len(rows), "roles_passed": len(rows) - len(failed),
                    "roles_failed": len(failed), "checks_passed": dict(sorted(checks.items()))},
        "roles": rows,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = ["# Kiểm tra đường đi dữ liệu qua module", "",
             f"Ngày: {report['as_of']}; dataset `{report['dataset_fingerprint']}`.", "",
             f"{summary['roles_passed']}/{summary['roles']} role qua các API lõi; "
             f"{summary['roles_failed']} role có lỗi. Hồ sơ đầu vào là hai kỹ năng đầu của mỗi role với Level 1 tổng hợp.", "",
             "Kiểm tra gồm presence match, level gap, lộ trình presence, lộ trình theo giờ, lấy 3 câu phỏng vấn và hướng dẫn sau gửi. PASS chỉ nói các module đọc và nối dữ liệu không exception/sai role; không chứng minh độ phù hợp nghề, nội dung đúng hoặc giao diện trình duyệt.", "",
             "| API | Số lượt đạt |", "| --- | ---: |"]
    lines.extend(f"| {name} | {count} |" for name, count in summary["checks_passed"].items())
    lines.extend(["", "## Lỗi theo role", ""])
    failed = [row for row in report["roles"] if row["errors"]]
    if failed:
        for row in failed:
            lines.append(f"- `{row['role_id']}`: " + "; ".join(row["errors"]))
    else:
        lines.append("Không có lỗi trong phạm vi kiểm tra này.")
    lines.extend(["", "```powershell", "python scripts/audit_module_paths.py --as-of 2026-10-26", "```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json-output", type=Path, default=ROOT / "docs/verification/module-paths-2026-10-26.json")
    parser.add_argument("--markdown-output", type=Path, default=ROOT / "docs/verification/module-paths-2026-10-26.md")
    args = parser.parse_args()
    report = audit_paths(as_of=args.as_of)
    for path, content in ((args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
                          (args.markdown_output, render_markdown(report))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 1 if report["summary"]["roles_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
