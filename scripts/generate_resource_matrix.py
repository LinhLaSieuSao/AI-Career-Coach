"""Generate a skill-by-level audit of eligible reviewed learning resources."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.resource_policy import is_recommendable_resource, resource_review_status
from modules.skill_extractor import normalize_skill


def _valid_link(resource: dict) -> bool:
    try:
        parsed = urlsplit(resource.get("url", ""))
    except (TypeError, ValueError):
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and resource.get("verified") is True


def build_resource_matrix(data_dir: str | Path = DATA_DIR) -> tuple[list[dict], dict[str, int]]:
    directory = Path(data_dir)
    roles = load_roles(directory / "roles.json")
    resources = json.loads((directory / "resources.json").read_text(encoding="utf-8"))
    # Include recognition-only skills too, so this matrix covers the full
    # canonical vocabulary rather than only skills currently attached to roles.
    skill_names = sorted(load_skill_vocabulary(roles, data_dir=directory))
    resource_index = {normalize_skill(name): group for name, group in resources.items()}
    rows: list[dict] = []
    counts: Counter[str] = Counter()
    for skill in skill_names:
        group = resource_index.get(skill, {})
        records = group.get("resources", []) if isinstance(group, dict) else []
        for level in (1, 2, 3):
            applicable = [
                resource for resource in records
                if isinstance(resource, dict)
                and type(resource.get("level_from")) is int
                and type(resource.get("level_to")) is int
                and resource["level_from"] <= level <= resource["level_to"]
                and _valid_link(resource)
                and is_recommendable_resource(resource, require_verified=True, skill=skill)
            ]
            reviewed = [resource for resource in applicable if resource_review_status(resource) == "reviewed"]
            partial = [resource for resource in applicable if resource_review_status(resource) == "partial"]
            if reviewed:
                status = "reviewed"
                note = "Ưu tiên nguồn reviewed cho level này; partial cùng phạm vi không được ưu tiên."
                candidates = reviewed
            elif partial:
                status = "partial"
                note = "; ".join(sorted({resource.get("review_note", "").strip() for resource in partial if resource.get("review_note", "").strip()}))
                candidates = partial
            else:
                status = "none"
                rejected = [resource_review_status(resource) for resource in records if isinstance(resource, dict)]
                note = "Chưa có tài liệu được xác minh cho kỹ năng/level này."
                if rejected:
                    note += " Bản ghi khác trạng thái: " + ", ".join(sorted(set(rejected))) + "."
                candidates = []
            counts[status] += 1
            rows.append({
                "skill": skill,
                "level": level,
                "status": status,
                "resource_count": len(candidates),
                "titles": [resource.get("title", "Tài liệu") for resource in candidates],
                "note": note,
            })
    summary = {"skills": len(skill_names), "skill_level_rows": len(rows), **dict(counts)}
    return rows, summary


def render_markdown(rows: list[dict], summary: dict[str, int]) -> str:
    lines = [
        "# Ma trận bao phủ tài liệu theo kỹ năng và level",
        "",
        f"Tổng {summary['skills']} kỹ năng × 3 level = {summary['skill_level_rows']} dòng; "
        f"reviewed: {summary.get('reviewed', 0)}, partial: {summary.get('partial', 0)}, "
        f"chưa có nguồn đủ điều kiện: {summary.get('none', 0)}.",
        "",
        "Bảng chỉ kiểm tra trạng thái mapping, link và khoảng level theo dữ liệu hiện có; không phải thẩm định độc lập của chuyên gia nghề nghiệp.",
        "Partial chỉ được dùng cho level chưa có nguồn reviewed phù hợp và phải đi kèm review note.",
        "",
        "| Kỹ năng | Level | Trạng thái planner | Số tài liệu | Tên tài liệu / ghi chú |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        content = ", ".join(row["titles"]) if row["titles"] else row["note"]
        content = content.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {row['skill']} | {row['level']} | {row['status']} | {row['resource_count']} | {content} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path, default=Path("docs/resource-coverage-matrix.md"))
    args = parser.parse_args()
    rows, summary = build_resource_matrix(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(rows, summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"Đã ghi {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
