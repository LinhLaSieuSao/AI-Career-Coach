"""Gom và chuẩn hóa dữ liệu hồ sơ sinh viên từ form để các module khác sử dụng."""

from __future__ import annotations


def _clean_text(value: str | None) -> str:
    """Bỏ khoảng trắng thừa ở đầu, cuối và giữa các từ. Trả về chuỗi rỗng nếu None."""
    if not value:
        return ""
    return " ".join(value.split())


def _split_list(value: str | None) -> list[str]:
    """Tách chuỗi theo dấu phẩy, làm sạch từng phần tử, bỏ phần tử rỗng."""
    if not value:
        return []
    items = (_clean_text(part) for part in value.split(","))
    return [item for item in items if item]


def _normalize_skills(skills: list[str] | None) -> list[str]:
    """Làm sạch, loại trùng không phân biệt hoa thường, giữ dạng viết đầu tiên gặp."""
    if not skills:
        return []

    seen: dict[str, str] = {}
    for raw in skills:
        cleaned = _clean_text(raw)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen[key] = cleaned

    return sorted(seen.values(), key=str.lower)


def build_profile(form_data: dict, skills: list[str] | None = None) -> dict:
    """Gom dữ liệu từ form và danh sách kỹ năng thành một hồ sơ thống nhất.

    Tham số:
        form_data: dict có thể chứa các khóa "interests" (chuỗi, cách nhau bằng dấu phẩy)
                   và "experience" (chuỗi tự do).
        skills: danh sách kỹ năng, lấy từ người dùng nhập tay hoặc từ skill_extractor.

    Trả về:
        {
            "skills": list[str],      # đã làm sạch, không trùng, sắp xếp A-Z
            "interests": list[str],   # đã làm sạch, không rỗng
            "experience": str,        # đã làm sạch khoảng trắng, có thể là chuỗi rỗng
        }
    """
    form_data = form_data or {}

    return {
        "skills": _normalize_skills(skills),
        "interests": _split_list(form_data.get("interests")),
        "experience": _clean_text(form_data.get("experience")),
    }