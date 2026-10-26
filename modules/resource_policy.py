"""Shared publication policy for learning-resource recommendations.

The legacy ``verified`` flag describes an earlier URL check. It is not proof
that the linked material teaches a mapped skill. Recommendation eligibility is
based on the content review status and its reviewer note instead.
"""

from collections.abc import Mapping
from collections import Counter
from datetime import date

from .skill_extractor import normalize_skill


RECOMMENDABLE_REVIEW_STATUSES = frozenset({"reviewed", "partial"})
EXCLUDED_REVIEW_STATUSES = frozenset({"blocked", "unsuitable"})
GRANULAR_LEVEL_SCOPES = frozenset({"lesson", "module", "chapter", "spec"})
SPECIALIST_EVIDENCE_MAX_AGE_DAYS = 365
RESOURCE_REVIEW_LABELS = {
    "reviewed": "Đã review nội bộ",
    "partial": "Bao phủ một phần",
    "unreviewed": "Chưa review",
    "blocked": "Đã chặn",
    "unsuitable": "Không phù hợp",
}


def resource_review_label(status: str | None) -> str:
    """Return the canonical user-facing label for a resource review status."""
    normalized = status.strip().casefold() if isinstance(status, str) else ""
    return RESOURCE_REVIEW_LABELS.get(normalized, RESOURCE_REVIEW_LABELS["unreviewed"])


def _specialty_required_for(skill: str | None) -> str | None:
    """Return the specialist evidence class required for high-risk skills."""
    if not isinstance(skill, str):
        return None
    normalized = normalize_skill(skill)
    if "thuế" in normalized or "tax" in normalized.split():
        return "vietnam_tax"
    if any(term in normalized for term in ("luật lao động", "employment law", "labor law", "labour law")):
        return "vietnam_labor_law"
    if any(term in normalized for term in (
        "an toàn điện", "chứng nhận an toàn", "chứng chỉ an toàn", "đào tạo an toàn",
        "safety certification", "fire safety certification", "pccc certification",
    )):
        return "vietnam_safety_training"
    return None


def _valid_iso_date(value, *, today: date) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    age = (today - parsed).days
    return 0 <= age <= SPECIALIST_EVIDENCE_MAX_AGE_DAYS


def has_current_specialist_evidence(
    resource: Mapping,
    skill: str,
    *,
    today: date | None = None,
) -> bool:
    """Require jurisdiction, current official source, and qualified review.

    This is a publication gate, not proof that the app has performed expert
    review. The evidence must be recorded explicitly for the mapped skill.
    """
    required = _specialty_required_for(skill)
    if required is None:
        return True
    evidence = resource.get("specialized_evidence")
    if not isinstance(evidence, Mapping):
        return False
    today = today or date.today()
    review = evidence.get("specialist_review")
    return bool(
        evidence.get("jurisdiction") == "VN"
        and evidence.get("source_authority") == "official"
        and _valid_iso_date(evidence.get("source_checked_at"), today=today)
        and isinstance(review, Mapping)
        and review.get("specialty") == required
        and review.get("approved") is True
        and review.get("qualification_verified") is True
        and isinstance(review.get("scope"), str)
        and bool(review["scope"].strip())
        and _valid_iso_date(review.get("reviewed_at"), today=today)
    )


def skill_scope_caution(skill: str | None) -> str | None:
    """Return a user-facing boundary for domains needing extra context."""
    if not isinstance(skill, str):
        return None
    normalized = normalize_skill(skill)
    if _specialty_required_for(normalized) == "vietnam_tax":
        return (
            "Chưa có học liệu thuế Việt Nam được xác minh nguồn chính thức, hiệu lực hiện hành "
            "và review bởi người có chuyên môn. Không dùng gợi ý này để kê khai, quyết toán "
            "hoặc tư vấn thuế thực tế."
        )
    if _specialty_required_for(normalized) == "vietnam_labor_law":
        return (
            "Chưa có nguồn luật lao động Việt Nam được đối chiếu hiệu lực và review chuyên môn. "
            "Không dùng nội dung này làm tư vấn pháp lý hoặc căn cứ xử lý vụ việc thật."
        )
    if _specialty_required_for(normalized) == "vietnam_safety_training":
        return (
            "Chỉ chấp nhận học liệu có phạm vi chứng nhận/huấn luyện an toàn tại Việt Nam được "
            "cơ quan có thẩm quyền và chuyên gia đủ điều kiện xác minh. Không thực hành thao tác "
            "nguy hiểm khi chưa được hướng dẫn trực tiếp."
        )
    if normalized == "an toàn lao động":
        return (
            "Tài liệu nhập môn như PAOT chỉ hỗ trợ nhận diện nguy cơ và cải tiến tại nơi làm việc; "
            "không thay thế quy chuẩn hiện hành, đánh giá rủi ro chuyên ngành hoặc khóa huấn luyện "
            "được cấp phép tại Việt Nam."
        )
    if normalized == "kiến trúc hệ thống":
        return (
            "Các nguồn hiện có chỉ bao phủ kiến trúc phần mềm hoặc một nền tảng cloud. Cần sơ đồ, "
            "quyết định kiến trúc và phản biện theo domain/hạ tầng thực tế trước khi kết luận năng lực "
            "kiến trúc hệ thống rộng hơn phần mềm."
        )
    if normalized == "bóc tách khối lượng":
        return (
            "Tài liệu phần mềm chỉ bổ trợ thao tác đo bóc. Cần bài tập bản vẽ, bộ môn, định mức "
            "và quy trình dự toán áp dụng tại Việt Nam được người có kinh nghiệm kiểm tra."
        )
    if normalized == "quản lý tồn kho":
        return (
            "Khung tổng quan cần được áp dụng vào SKU, quy trình kho và công cụ thực tế của doanh nghiệp; "
            "dùng dữ liệu mô phỏng hoặc đã ẩn danh và xin người vận hành phản hồi."
        )
    if normalized == "phân tích yêu cầu":
        return (
            "Tài liệu nền tảng chưa thay thế phỏng vấn stakeholder và domain cụ thể. Hãy dùng một "
            "case/project, xác nhận yêu cầu với người liên quan và lưu lại thay đổi sau phản hồi."
        )
    return None


def summarize_resource_reviews(resources: Mapping) -> dict:
    """Count skill-to-resource mappings, separately from interview questions."""
    counts = Counter()
    for group in resources.values() if isinstance(resources, Mapping) else ():
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            continue
        for resource in group["resources"]:
            if isinstance(resource, Mapping):
                counts[resource_review_status(resource)] += 1
    return {
        "mapping_count": sum(counts.values()),
        "by_status": dict(counts),
        "reviewed": counts.get("reviewed", 0),
        "partial": counts.get("partial", 0),
        "unsuitable": counts.get("unsuitable", 0),
        "blocked": counts.get("blocked", 0),
        "unreviewed": counts.get("unreviewed", 0),
    }


def resource_review_status(resource: Mapping) -> str:
    """Return a conservative, normalized content-review status."""
    raw_status = resource.get("content_review_status")
    status = raw_status.strip().casefold() if isinstance(raw_status, str) else ""
    note = resource.get("review_note")
    if status in RECOMMENDABLE_REVIEW_STATUSES and (not isinstance(note, str) or not note.strip()):
        return "unreviewed"
    return status or "unreviewed"


def has_granular_level_evidence(resource: Mapping) -> bool:
    """Whether a mapping names a bounded content unit and its locator.

    This is a structural prerequisite for Level evidence, not an expert
    endorsement of the mapped Level or the linked content.
    """
    if not isinstance(resource, Mapping):
        return False
    locator = resource.get("evidence_locator")
    return (
        resource.get("scope_granularity") in GRANULAR_LEVEL_SCOPES
        and isinstance(locator, str) and bool(locator.strip())
    )


def is_recommendable_resource(
    resource: Mapping,
    *,
    require_verified: bool = False,
    skill: str | None = None,
) -> bool:
    """Whether a resource may appear in the main recommendation list.

    Partial reviews remain eligible only with their scope note, which the UI
    must display. The caller may separately require the legacy link-check flag
    when building a timed plan.
    """
    if not isinstance(resource, Mapping):
        return False
    if resource_review_status(resource) not in RECOMMENDABLE_REVIEW_STATUSES:
        return False
    if skill is not None and not has_current_specialist_evidence(resource, skill):
        return False
    return not require_verified or resource.get("verified") is True


def resource_exclusion_reason(
    resource: Mapping,
    *,
    require_verified: bool = False,
    skill: str | None = None,
) -> str | None:
    """Return a stable reason code when a record must not be recommended."""
    if not isinstance(resource, Mapping):
        return "invalid_resource"
    status = resource_review_status(resource)
    if status == "blocked":
        return "blocked_resource"
    if status == "unsuitable":
        return "unsuitable_content"
    if status not in RECOMMENDABLE_REVIEW_STATUSES:
        return "unreviewed_content"
    if skill is not None and not has_current_specialist_evidence(resource, skill):
        return "specialized_source_required"
    if require_verified and resource.get("verified") is not True:
        return "unverified_link"
    return None


def resource_level_gap(resource: Mapping, target_levels: Mapping[str, int]) -> list[dict]:
    """Show where a recommendable page ends below a role's required level.

    This does not infer learner proficiency or make the resource ineligible for
    introductory use; it only prevents a Level 1 page looking sufficient for a
    Level 3 role requirement in the presence-based roadmap.
    """
    if not isinstance(resource, Mapping) or not isinstance(target_levels, Mapping):
        return []
    upper = resource.get("level_to")
    if type(upper) is not int or not 1 <= upper <= 3:
        return []
    normalized_targets = {
        normalize_skill(skill): level
        for skill, level in target_levels.items()
        if isinstance(skill, str) and type(level) is int and 1 <= level <= 3
    }
    skills = resource.get("skills", [])
    if not isinstance(skills, (list, tuple)):
        return []
    return [
        {"skill": normalize_skill(skill), "resource_level_to": upper, "required_level": normalized_targets[normalize_skill(skill)]}
        for skill in skills
        if isinstance(skill, str) and normalize_skill(skill) in normalized_targets
        and normalized_targets[normalize_skill(skill)] > upper
    ]
