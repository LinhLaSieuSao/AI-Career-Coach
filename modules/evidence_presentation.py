"""Conservative learner-facing evidence labels independent of visual layout."""

from __future__ import annotations

from collections.abc import Mapping

from .resource_policy import has_granular_level_evidence, resource_review_status


def resource_evidence_badge(record: Mapping) -> str:
    """Describe the weakest recorded axis without implying expert approval."""
    status = resource_review_status(record)
    if status in {"blocked", "unsuitable"}:
        return "Không đề xuất · nguồn bị loại khỏi lộ trình"
    if status not in {"reviewed", "partial"}:
        return "Tham khảo · nội dung chưa rà soát"
    if not has_granular_level_evidence(record):
        return "Tham khảo · chưa xác định bài/chương đúng Level"
    axes = record.get("verification_axes") or {}
    if axes.get("access_status") != "independently_accessible":
        return "Tham khảo · link chưa kiểm tra độc lập"
    if axes.get("rights_basis") == "pending" or not (record.get("provenance") or {}).get("rights_basis"):
        return "Tham khảo · quyền tái sử dụng chưa xác minh"
    if status == "partial":
        return "Đã rà soát nội bộ · chỉ bao phủ một phần"
    return "Đã rà soát nội bộ · phạm vi bài đã ghi nhận"


MEDICAL_ROLES = frozenset({"doctor", "registered_nurse", "pharmacist"})
LEGAL_ROLES = frozenset({"legal_executive", "compliance_officer"})
ACCOUNTING_ROLES = frozenset({"accountant", "general_accountant", "chief_accountant", "tax_accountant", "auditor", "internal_auditor"})
SAFETY_ROLES = frozenset({"safety_engineer", "electrical_engineer", "civil_engineer", "site_engineer", "architect"})


def role_domain_notice(role_id: str) -> str | None:
    if role_id in MEDICAL_ROLES:
        return "Nội dung y tế chỉ để định hướng học và luyện phỏng vấn; không thay tư vấn lâm sàng, giám sát nghề hay chứng chỉ hành nghề."
    if role_id in LEGAL_ROLES:
        return "Nội dung pháp lý chỉ để định hướng học; cần đối chiếu văn bản còn hiệu lực và người có chuyên môn trước khi áp dụng vụ việc thật."
    if role_id in ACCOUNTING_ROLES:
        return "Nội dung kế toán, thuế chỉ để định hướng học; không thay quy định hiện hành, người kiểm tra nghiệp vụ hoặc chứng chỉ cần thiết."
    if role_id in SAFETY_ROLES:
        return "Nội dung kỹ thuật và an toàn chỉ để định hướng học; không thay quy chuẩn, huấn luyện, giám sát tại hiện trường hoặc chứng chỉ bắt buộc."
    return None
