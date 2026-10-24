"""Export a compact career assessment without reproducing the source CV."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from typing import Any


CSV_FIELDS = (
    "section", "role_id", "skill", "required", "current", "gap", "priority",
    "status", "score", "week", "hours", "resource_key", "title", "url", "duration_kind",
    "duration_hours", "source", "note",
)


def _cell(value: Any) -> Any:
    """Protect spreadsheet cells that could be interpreted as a formula."""
    if not isinstance(value, str):
        return value
    probe = value.lstrip(" \t\r\n\x00")
    return "'" + value if probe.startswith(("=", "+", "-", "@")) else value


def _rows(profile: Mapping[str, Any], gap: Mapping[str, Any] | None, roadmap: Any) -> list[dict[str, Any]]:
    role_id = profile.get("role_id") or (gap or {}).get("role_id")
    rows: list[dict[str, Any]] = []
    for key, value in (
        ("skills", ", ".join(map(str, profile.get("skills", [])))),
        ("interests", ", ".join(map(str, profile.get("interests", [])))),
        ("experience", profile.get("experience", "")),
        ("levels", ", ".join(f"{name}: {level}" for name, level in profile.get("levels", {}).items())),
    ):
        if value:
            rows.append({"section": "profile", "role_id": role_id, "skill": key, "note": value})

    if gap:
        for item in gap.get("items", []):
            rows.append({
                "section": "gap", "role_id": role_id, "skill": item.get("skill"),
                "required": item.get("required"), "current": item.get("current"),
                "gap": item.get("gap"), "priority": item.get("priority"),
                "status": item.get("status"),
            })
        if not gap.get("items") and ("percent" in gap or "matched" in gap or "missing" in gap):
            rows.append({
                "section": "presence", "role_id": role_id,
                "score": gap.get("percent"),
                "status": "presence_percent; không đánh giá level",
                "note": "Matched: " + ", ".join(map(str, gap.get("matched", [])))
                        + "; missing: " + ", ".join(map(str, gap.get("missing", []))),
            })

    resource_index: dict[str, Mapping[str, Any]] = {}
    if isinstance(roadmap, Mapping):
        raw_resources = roadmap.get("resources", {})
        if isinstance(raw_resources, Mapping):
            resource_index = {str(key): value for key, value in raw_resources.items() if isinstance(value, Mapping)}
        for phase in roadmap.get("phases", []):
            for segment in phase.get("segments", []):
                key = str(segment.get("resource_key", ""))
                resource = resource_index.get(key, {})
                evidence = resource.get("duration_evidence", {})
                rows.append({
                    "section": "roadmap", "role_id": role_id,
                    "skill": ", ".join(resource.get("skills", [])), "week": phase.get("week"),
                    "hours": segment.get("hours"), "resource_key": key,
                    "title": resource.get("title"), "url": resource.get("url"),
                    "duration_kind": segment.get("duration_kind"),
                    "duration_hours": resource.get("planned_hours"),
                    "source": evidence.get("source"), "note": evidence.get("basis"),
                })
        for item in roadmap.get("unresolved", []):
            rows.append({
                "section": "unresolved", "role_id": role_id,
                "skill": item.get("skill") or ", ".join(item.get("skills", [])),
                "status": item.get("reason"), "note": item.get("detail", item.get("reason")),
            })
        for item in roadmap.get("unknown_duration", []):
            key = str(item.get("resource_key", ""))
            resource = resource_index.get(key, {})
            evidence = resource.get("duration_evidence", {})
            rows.append({
                "section": "unknown_duration", "role_id": role_id,
                "skill": ", ".join(resource.get("skills", [])), "resource_key": key,
                "title": resource.get("title"), "url": resource.get("url"),
                "status": resource.get("duration_issue", "unknown_duration"),
                "source": evidence.get("source"), "note": evidence.get("basis"),
            })
    elif isinstance(roadmap, list):
        catalog = {resource.get("key"): resource for week in roadmap for resource in week.get("resources", [])}
        introduced: set[str] = set()
        for week in roadmap:
            for skill, keys in week.get("resource_keys", {}).items():
                for key in keys:
                    resource = catalog.get(key, {})
                    if key in introduced:
                        continue
                    rows.append({
                        "section": "roadmap", "role_id": role_id,
                        "skill": ", ".join(resource.get("skills", [])) or skill,
                        "week": week.get("week"), "resource_key": key,
                        "title": resource.get("title"), "url": resource.get("url"),
                        "status": "new_resource",
                        "note": "Tài liệu được khử trùng theo resource key.",
                    })
                    introduced.add(key)
        for week in roadmap:
            for skill in week.get("skills_without_resources", []):
                rows.append({"section": "unresolved", "role_id": role_id, "skill": skill,
                             "status": "no_resources", "week": week.get("week")})
    return rows


def export_report(profile, gap, roadmap, format="markdown") -> str:
    """Return a Markdown or spreadsheet-safe CSV snapshot of the current result."""
    if not isinstance(profile, Mapping):
        raise TypeError("profile phải là mapping.")
    rows = _rows(profile, gap, roadmap)
    if format == "csv":
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key, "")) for key in CSV_FIELDS})
        return output.getvalue()
    if format != "markdown":
        raise ValueError("format phải là 'markdown' hoặc 'csv'.")

    def md(value: Any) -> str:
        return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")

    lines = ["# Báo cáo hồ sơ nghề nghiệp", "", f"- Role ID: {md(profile.get('role_id') or (gap or {}).get('role_id'))}",
             f"- Kỹ năng: {md(', '.join(map(str, profile.get('skills', []))))}",
             f"- Sở thích: {md(', '.join(map(str, profile.get('interests', []))))}",
             f"- Level tự khai báo: {md(', '.join(f'{name}: {level}' for name, level in profile.get('levels', {}).items()))}",
             "- Kinh nghiệm: không xuất toàn văn CV; chỉ xuất phần mô tả đã nhập trong hồ sơ.", ""]
    if gap:
        if gap.get("items"):
            lines += ["## Khoảng cách kỹ năng", "", f"Mức đáp ứng theo level: {md(gap.get('match_percent'))}%", "",
                      "| Kỹ năng | Yêu cầu | Hiện tại | Gap | Ưu tiên | Trạng thái |",
                      "| --- | ---: | ---: | ---: | ---: | --- |"]
            for item in gap.get("items", []):
                lines.append("| " + " | ".join(md(item.get(key)) for key in ("skill", "required", "current", "gap", "priority", "status")) + " |")
        elif "percent" in gap:
            lines += ["## Đối chiếu kỹ năng hiện có", "", f"Presence score: {md(gap.get('percent'))}% (theo trọng số role; không đánh giá level).",
                      f"Matched: {md(', '.join(map(str, gap.get('matched', []))))}.",
                      f"Missing: {md(', '.join(map(str, gap.get('missing', []))))}.", ""]
        lines.append("")
    if isinstance(roadmap, Mapping):
        lines += ["## Lộ trình theo giờ", "", f"Giờ công bố đã chọn: {md(roadmap.get('total_known_hours'))}; giờ ước lượng: {md(roadmap.get('total_estimated_hours'))}; tổng tuần: {md(roadmap.get('total_weeks') if roadmap.get('total_weeks') is not None else 'chưa xác định')}", ""]
        for phase in roadmap.get("phases", []):
            for segment in phase.get("segments", []):
                key = str(segment.get("resource_key", ""))
                resource = roadmap.get("resources", {}).get(key, {})
                lines.append(f"- Tuần {md(phase.get('week'))}: [{md(resource.get('title'))}]({md(resource.get('url'))}) · {md(segment.get('hours'))} giờ · {md(segment.get('duration_kind'))} · {md(key)}")
                evidence = resource.get("duration_evidence", {})
                if evidence.get("source"):
                    lines.append(f"  - Nguồn thời lượng: {md(evidence['source'])}")
                if segment.get("duration_kind") == "estimated":
                    lines.append(f"  - Cơ sở ước lượng: {md(evidence.get('basis'))}")
        for item in roadmap.get("unresolved", []):
            lines.append(f"- Chưa giải quyết: {md(item.get('skill') or item.get('skills'))} · {md(item.get('reason'))}")
        for item in roadmap.get("unknown_duration", []):
            resource = roadmap.get("resources", {}).get(item.get("resource_key"), {})
            lines.append(f"- Chưa rõ thời lượng: [{md(resource.get('title'))}]({md(resource.get('url'))}) · {md(item.get('resource_key'))}")
        lines += ["", "Tổng tuần là chưa xác định khi còn phần gap/tài liệu/thời lượng chưa giải quyết. Giờ ước lượng được ghi riêng; tài liệu hoàn thành không chứng nhận đạt kỹ năng hay level.", ""]
    else:
        lines += ["## Tài liệu", "", "| Tuần | Kỹ năng | Tài liệu | Trạng thái |", "| ---: | --- | --- | --- |"]
        for row in rows:
            if row["section"] == "roadmap":
                lines.append(f"| {md(row.get('week'))} | {md(row.get('skill'))} | [{md(row.get('title'))}]({md(row.get('url'))}) | {md(row.get('status'))} |")
        lines.append("")
    lines += ["## Giới hạn", "", "Điểm presence phản ánh kỹ năng nhận diện hiện có; điểm level dùng riêng các level khai báo. Gợi ý role là heuristic, không phải xác suất tuyển dụng. Thời lượng/tuần chưa biết được giữ là chưa xác định; resource chung chỉ được tính một lần.", ""]
    return "\n".join(lines)
