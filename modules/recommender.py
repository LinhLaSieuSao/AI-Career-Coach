"""Build weekly learning roadmaps from Matcher gaps and skill-indexed resources."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from decimal import Decimal
import math
from collections.abc import Iterable, Mapping
from copy import deepcopy
from numbers import Real
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .skill_extractor import canonical_skill, normalize_skill


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _skill_list(missing: Iterable[str] | str | None) -> list[str]:
    if missing is None:
        return []
    values = [missing] if isinstance(missing, str) else missing
    result: list[str] = []
    seen: set[str] = set()
    for name in values:
        if not isinstance(name, str):
            raise TypeError("Mỗi kỹ năng thiếu phải là chuỗi.")
        normalized = normalize_skill(name)
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _prioritize(skills: list[str], missing_details: Iterable[Mapping[str, Any]] | None) -> list[str]:
    if missing_details is None:
        return skills
    weights: dict[str, float] = {}
    allowed = set(skills)
    for detail in missing_details:
        if not isinstance(detail, Mapping) or not isinstance(detail.get("name"), str):
            raise ValueError("missing_details phải chứa object có tên kỹ năng hợp lệ.")
        name = normalize_skill(detail["name"])
        if name not in allowed or name in weights:
            raise ValueError("Tên trong missing_details phải thuộc missing và không trùng nhau.")
        weight = detail.get("weight", 1)
        if (
            isinstance(weight, bool)
            or not isinstance(weight, Real)
            or not math.isfinite(float(weight))
            or weight <= 0
        ):
            raise ValueError("missing_details.weight phải là số dương hữu hạn.")
        weights[name] = float(weight)
    # Python's stable sort keeps the incoming order when weights are equal.
    return sorted(skills, key=lambda name: -weights.get(name, 1.0))


def _resource_tokens(resource: Mapping[str, Any]) -> list[str]:
    """Identify duplicates by ID or URL without changing path/query casing."""
    tokens: list[str] = []
    raw_url = resource.get("url")
    if isinstance(raw_url, str) and raw_url.strip():
        url = urlsplit(raw_url.strip())
        if url.scheme.lower() in {"http", "https"} and url.netloc:
            normalized_url = urlunsplit(
                (url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), url.query, "")
            )
            tokens.append("url:" + normalized_url)
    resource_id = resource.get("id")
    if isinstance(resource_id, str) and resource_id.strip():
        tokens.append("id:" + resource_id.strip())
    return tokens


def _resource_catalog(
    skills: list[str], resources: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, dict[str, Any]]]:
    """Group eligible resources and retain rejected-resource reasons by skill."""
    index: dict[str, Any] = {}
    for name, entry in resources.items():
        if not isinstance(name, str):
            raise ValueError("Khóa của resources phải là tên kỹ năng dạng chuỗi.")
        normalized = normalize_skill(name)
        if normalized in index:
            raise ValueError(f"resources chứa tên kỹ năng trùng sau chuẩn hóa: {name!r}.")
        index[normalized] = entry

    # Union identities before producing output: duplicates may connect through
    # both an ID and a URL across more than two resource records.
    parents: dict[str, str] = {}

    def root(token: str) -> str:
        parents.setdefault(token, token)
        while parents[token] != token:
            parents[token] = parents[parents[token]]
            token = parents[token]
        return token

    rows: list[tuple[str, Mapping[str, Any], list[str]]] = []
    eligible_by_skill: dict[str, list[tuple[str, Mapping[str, Any], list[str]]]] = {
        skill: [] for skill in skills
    }
    review_summary = {
        skill: {"candidate_count": 0, "eligible_count": 0, "excluded_statuses": set(), "reasons": set()}
        for skill in skills
    }
    for skill in skills:
        if skill not in index:
            continue
        group = index[skill]
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            raise ValueError(f"resources[{skill!r}] phải có danh sách 'resources'.")
        for resource in group["resources"]:
            if not isinstance(resource, Mapping):
                raise ValueError(f"Tài liệu của {skill!r} phải là object.")
            summary = review_summary[skill]
            summary["candidate_count"] += 1
            reason = resource_exclusion_reason(resource, require_verified=True, skill=skill)
            if not reason:
                url = resource.get("url")
                try:
                    parsed = urlsplit(url) if isinstance(url, str) else None
                except ValueError:
                    parsed = None
                if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    reason = "missing_url"
            if reason:
                summary["reasons"].add(reason)
                summary["excluded_statuses"].add(resource_review_status(resource))
                continue
            if not is_recommendable_resource(resource, require_verified=True, skill=skill):
                continue
            tokens = _resource_tokens(resource)
            if not tokens:
                summary["reasons"].add("missing_resource_identity")
                continue
            eligible_by_skill[skill].append((skill, resource, tokens))

    # A partial mapping is a fallback for the same skill only when no
    # recommendable reviewed mapping exists for that skill.
    for skill, candidates in eligible_by_skill.items():
        has_reviewed = any(resource_review_status(record) == "reviewed" for _, record, _ in candidates)
        selected = [
            candidate for candidate in candidates
            if not (has_reviewed and resource_review_status(candidate[1]) == "partial")
        ]
        for candidate in selected:
            _, resource, tokens = candidate
            review_summary[skill]["eligible_count"] += 1
            for token in tokens[1:]:
                parents[root(token)] = root(tokens[0])
            rows.append(candidate)

    catalog: dict[str, dict[str, Any]] = {}
    refs: dict[str, list[str]] = {skill: [] for skill in skills}
    group_keys: dict[str, str] = {}
    for skill, resource, tokens in rows:
        identity = root(tokens[0])
        if identity not in group_keys:
            key = tokens[0]
            group_keys[identity] = key
            catalog[key] = {**deepcopy(dict(resource)), "key": key, "skills": []}
        key = group_keys[identity]
        if key not in refs[skill]:
            refs[skill].append(key)
            catalog[key]["skills"].append(skill)
    return catalog, refs, review_summary


def build_roadmap(
    missing: Iterable[str] | str | None,
    resources: Mapping[str, Any],
    weeks: int = 4,
    *,
    missing_details: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Split missing skills into balanced, consecutive weekly study groups.

    Return [] for no skills, otherwise min(weeks, unique skill count) weeks.
    Metadata optionally sorts skills by descending role weight, stably for
    ties; missing metadata weights default to 1. Required level is not used
    to infer study time or resource suitability. Names use the shared skill
    normalizer; aliases should already have been resolved by Matcher.

    Each week contains week, skills, eligible resources, resource_keys,
    skills_without_resources, unresolved, and partial_resources. A resource
    occurs once in the whole roadmap at its earliest related skill's week;
    resource_keys maps every skill to eligible resources, including items
    introduced earlier. Duplicate IDs/URLs are grouped.

    Only verified HTTP(S) resources whose content review is reviewed/partial
    and includes a review note may be recommended. Unknown skills and skills
    with only excluded resources remain scheduled and receive an unresolved
    reason. Inputs are not mutated. Invalid weeks, metadata, or requested
    resource groups raise an explicit TypeError or ValueError.
    """
    if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks <= 0:
        raise ValueError("weeks phải là số nguyên dương.")
    if not isinstance(resources, Mapping):
        raise TypeError("resources phải là mapping theo tên kỹ năng.")
    skills = _prioritize(_skill_list(missing), missing_details)
    if not skills:
        return []
    catalog, refs, review_summary = _resource_catalog(skills, resources)
    week_count = min(weeks, len(skills))
    base_size, remainder = divmod(len(skills), week_count)
    roadmap: list[dict[str, Any]] = []
    assigned: set[str] = set()
    offset = 0
    for index in range(week_count):
        count = base_size + (1 if index < remainder else 0)
        week_skills = skills[offset : offset + count]
        offset += count
        week_resources = []
        for skill in week_skills:
            for key in refs[skill]:
                if key not in assigned:
                    week_resources.append(catalog[key])
                    assigned.add(key)
        unresolved = []
        partial_resources = []
        for skill in week_skills:
            summary = review_summary[skill]
            if not refs[skill]:
                if summary["candidate_count"] == 0:
                    reason = "no_resources"
                else:
                    reason = next((candidate for candidate in (
                        "specialized_source_required",
                        "unreviewed_content", "blocked_resource", "unsuitable_content",
                        "unverified_link", "missing_url", "missing_resource_identity",
                    ) if candidate in summary["reasons"]), "unreviewed_content")
                issue = {"skill": skill, "reason": reason}
                if summary["excluded_statuses"]:
                    issue["excluded_statuses"] = sorted(summary["excluded_statuses"])
                if summary["reasons"]:
                    issue["exclusion_reasons"] = sorted(summary["reasons"])
                unresolved.append(issue)
            for key in refs[skill]:
                resource = catalog[key]
                if resource_review_status(resource) == "partial":
                    partial_resources.append({
                        "skill": skill,
                        "resource_key": key,
                        "review_note": resource.get("review_note", ""),
                    })
        roadmap.append(
            {
                "week": index + 1,
                "skills": week_skills,
                "resources": week_resources,
                "resource_keys": {skill: refs[skill] for skill in week_skills},
                "skills_without_resources": [skill for skill in week_skills if not refs[skill]],
                "unresolved": unresolved,
                "partial_resources": partial_resources,
                "practice_routes": get_practice_routes(week_skills, resources),
            }
        )
    return roadmap


def get_course_recommendations(missing_skills: Iterable[str]) -> list[dict[str, Any]]:
    """Adapt the current resource catalog to the existing app's flat cards."""
    skills = _skill_list(missing_skills)
    if not skills:
        return []
    with (_DATA_DIR / "resources.json").open(encoding="utf-8") as source:
        resources = json.load(source)
    roadmap = build_roadmap(skills, resources, weeks=1)
    return [
        {
            **resource,
            "course_name": resource.get("title", "Tài liệu học tập"),
            "link": resource.get("url", ""),
            "resource_id": resource.get("id", ""),
            "skills_achieved": list(resource["skills"]),
        }
        for resource in roadmap[0]["resources"]
    ]


def build_timed_roadmap(gap, resources, hours_per_week=8) -> dict:
    """Schedule reviewed level ranges with sourced hours; keep incomplete work explicit."""
    return plan(gap, resources, hours_per_week)


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


_SALES_SKILLS = {
    "bán hàng",
    "bán hàng b2b",
    "bán hàng bất động sản",
    "bán hàng kỹ thuật",
    "tìm kiếm khách hàng",
    "tư vấn bán hàng",
    "thuyết phục",
    "chăm sóc khách hàng",
    "đàm phán",
    "thương lượng",
    "xây dựng mối quan hệ",
}
_COMMUNICATION_SKILLS = {"giao tiếp", "lắng nghe", "giao tiếp khách hàng", "thuyết trình"}
_TEAMWORK_SKILLS = {"làm việc nhóm", "phối hợp nhóm", "cộng tác"}
_PROBLEM_SKILLS = {"giải quyết vấn đề", "xử lý tình huống", "xử lý sự cố"}
_LEADERSHIP_SKILLS = {"quản lý đội ngũ", "quản lý công nhân", "quản lý nhân sự"}
_EVENT_SKILLS = {"tổ chức sự kiện", "điều phối sự kiện"}
_TRANSVERSAL_SKILLS = {
    "giải quyết vấn đề", "tiếng anh chuyên ngành", "excel", "cẩn thận",
    "đọc bản vẽ kỹ thuật", "chăm sóc khách hàng",
}
_OBSERVATION_CHECKLISTS = {
    "giải quyết vấn đề": [
        "Tách dữ kiện đã kiểm chứng khỏi giả định và ghi điều còn thiếu.",
        "Nêu ít nhất hai lựa chọn, rủi ro và lý do chọn cách thử.",
        "Kiểm tra kết quả, tác dụng phụ và ghi phản hồi của người quan sát.",
    ],
    "cẩn thận": [
        "Xác định trường/chi tiết trọng yếu trước khi bàn giao.",
        "Đối chiếu với nguồn đầu vào độc lập hoặc checklist, không chỉ đọc lại bằng mắt.",
        "Ghi sai lệch, sửa có dấu vết và xin người phụ trách xác nhận khi vượt thẩm quyền.",
    ],
    "chăm sóc khách hàng": [
        "Hỏi và nhắc lại nhu cầu hoặc sự cố bằng lời trung tính.",
        "Nêu bước tiếp theo, thời điểm cập nhật và giới hạn điều mình có thể cam kết.",
        "Không ghi dữ liệu nhận dạng khách hàng vào portfolio; xin phản hồi sau khi xử lý.",
    ],
    "excel": [
        "Công thức, phạm vi dữ liệu và đơn vị được kiểm tra bằng bộ dữ liệu giả lập.",
        "Đối chiếu tổng số bằng phép tính hoặc cách lọc độc lập; kiểm tra dữ liệu thiếu/trùng.",
        "Lưu file, giả định, bước tái lập và một nhận xét của người rà soát.",
    ],
    "đọc bản vẽ kỹ thuật": [
        "Xác nhận mã bản vẽ, phiên bản, đơn vị, tỷ lệ và ghi chú trước khi đọc kích thước.",
        "Đánh dấu kích thước/dung sai chưa rõ, không tự suy từ hình minh họa.",
        "Nhờ kỹ sư/người hướng dẫn kiểm tra diễn giải trước khi gia công hoặc thi công.",
    ],
    "tiếng anh chuyên ngành": [
        "Chỉ ra câu hoặc đoạn nguồn chứa thuật ngữ, phiên bản và bối cảnh sử dụng.",
        "Viết lại ý chính bằng tiếng Việt rồi diễn đạt lại bằng tiếng Anh, tách phần chưa chắc nghĩa.",
        "Nhờ người am hiểu chuyên ngành rà thuật ngữ; không dùng bản dịch để tự ra quyết định chuyên môn.",
    ],
}
_ENGLISH_TRACKS = [
    {
        "name": "IT/phần mềm", "terms": "issue, endpoint, rollback, changelog, pull request",
        "exercise": "Đọc một đoạn tài liệu API hoặc Git; viết ticket lỗi 5 câu gồm tái hiện, kỳ vọng và kết quả thực tế.",
        "reference_url": "https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging",
    },
    {
        "name": "Kinh doanh/tài chính", "terms": "revenue, expense, cash flow, variance, disclosure",
        "exercise": "Đọc một đoạn bảng thuật ngữ IFRS và viết ghi chú song ngữ về một chênh lệch giả lập; không dùng làm kết luận kế toán/thuế.",
        "reference_url": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/glossary.pdf?bypass=on",
    },
    {
        "name": "Logistics/chuỗi cung ứng", "terms": "shipment, bill of lading, carrier, delivery, risk transfer",
        "exercise": "Đọc phần giới thiệu Incoterms của ICC; viết email giả lập hỏi rõ địa điểm giao và chứng từ, không tự diễn giải nghĩa vụ hợp đồng.",
        "reference_url": "https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/",
    },
    {
        "name": "Kỹ thuật/bản vẽ", "terms": "dimension, tolerance, revision, datum, drawing note",
        "exercise": "Đọc phần giới thiệu GD&T, ghi chú song ngữ năm chi tiết cần hỏi lại trên bản vẽ giả lập; xin kỹ sư rà trước khi áp dụng.",
        "reference_url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=936463",
    },
    {
        "name": "Y tế/dược và thử nghiệm", "terms": "protocol, informed consent, adverse event, deviation, essential record",
        "exercise": "Đọc một đoạn tài liệu ICH GCP, tóm tắt thuật ngữ và câu hỏi cần xác minh; không dùng để hướng dẫn điều trị hay vận hành thử nghiệm.",
        "reference_url": "https://admin.ich.org/sites/default/files/elearning-contents/27d6f78b-c8aa-4d50-ab13-9ce13a220b19/ICH%20E6%28R3%29%20Module%204.1%20Publication/story.html",
    },
]


def _route(skill: str, category: str) -> dict:
    normalized = normalize_skill(skill)
    if normalized == "tiếng anh chuyên ngành":
        return {
            "skill": skill, "category": "practice", "title": "Đọc và viết tiếng Anh theo nhóm nghề",
            "framing": "Năm bộ từ khóa là bài tập do dự án biên soạn từ trang nguồn, chưa được chuyên gia ngôn ngữ/ngành xác nhận. Chọn một nhóm phù hợp, không xem đây là học liệu Level 2–3 đã review.",
            "steps": [
                "Chọn một trong năm nhóm nghề và mở phần nguồn được dẫn; đọc một đoạn ngắn thay vì học thuộc danh sách từ.",
                "Ghi bối cảnh của năm thuật ngữ, viết lại ý chính và làm bài tập của nhóm đã chọn.",
                "Xin người am hiểu ngành sửa cách dùng thuật ngữ, lưu bản trước/sau và ghi điểm còn chưa chắc chắn.",
            ],
            "evidence": "đoạn nguồn, ghi chú từ trong ngữ cảnh, sản phẩm viết song ngữ và phản hồi đã ẩn danh.",
            "tracks": _ENGLISH_TRACKS,
        }
    if normalized == "excel":
        return {
            "skill": skill, "category": "practice", "title": "Kiểm tra một bảng tính có dữ liệu giả lập",
            "framing": "Bài thực hành tự tạo không chứng nhận Excel Level 3; cần người dùng và người rà soát kiểm tra file, công thức và diễn giải.",
            "steps": [
                "Tạo bảng 30–50 dòng dữ liệu bán hàng giả lập có bản ghi trùng, giá trị trống và một giá trị ngoại lệ.",
                "Làm sạch có ghi quy tắc, tính tổng theo nhóm và tạo biểu đồ; không xóa dữ liệu bất thường khi chưa giải thích.",
                "Đối chiếu một tổng bằng cách tính độc lập, kiểm tra khi thêm một dòng mới và xin người khác rà công thức.",
            ],
            "evidence": "file bảng tính không chứa dữ liệu thật, README giải thích công thức, phép đối chiếu và nhận xét của người rà soát.",
        }
    if normalized == "đọc bản vẽ kỹ thuật":
        return {
            "skill": skill, "category": "practice", "title": "Diễn giải bản vẽ mẫu có người giám sát",
            "framing": "Chỉ dùng bản vẽ mẫu được phép chia sẻ. Bài tập không thay cho chứng nhận thiết kế, kiểm tra bản vẽ thi công hoặc hướng dẫn an toàn tại nơi làm việc.",
            "steps": [
                "Chọn bản vẽ mẫu, ghi mã phiên bản, đơn vị, tỷ lệ, ghi chú và các hình chiếu trước khi suy kích thước.",
                "Đánh dấu ba kích thước/dung sai quan trọng và những điểm chưa rõ; không tự điền thông số thiếu.",
                "Nhờ kỹ sư hoặc người hướng dẫn rà diễn giải, ghi lại một sai khác và cách sửa.",
            ],
            "evidence": "bản ghi chú trên bản vẽ mẫu, câu hỏi làm rõ và phản hồi có tên vai trò người rà soát.",
        }
    if normalized in _COMMUNICATION_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện giao tiếp bằng mô phỏng và phản hồi",
            "framing": "Tài liệu giúp chuẩn bị; năng lực giao tiếp cần được luyện trong tình huống và điều chỉnh theo phản hồi quan sát được.",
            "steps": [
                "Chọn một tình huống gần công việc như nhận yêu cầu, báo tiến độ hoặc giải thích một quyết định.",
                "Role-play theo cặp: một người trình bày, người kia hỏi làm rõ; người nghe tóm tắt lại điều đã hiểu trước khi trả lời.",
                "Nhờ người quan sát ghi ví dụ cụ thể về sự rõ ràng, lắng nghe và xác nhận thông tin; tránh nhận xét chung về tính cách.",
                "Thử lại sau khi nhận phản hồi, rồi lưu điểm đã sửa và câu hỏi còn cần làm rõ.",
            ],
            "evidence": "kịch bản role-play đã ẩn danh, checklist của người quan sát, phản hồi mentor/đồng nghiệp và bản thực hành đã chỉnh sửa.",
        }
    if normalized in _TEAMWORK_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện phối hợp qua nhiệm vụ nhóm có giám sát",
            "framing": "Đọc tài liệu chỉ là bước chuẩn bị; phối hợp cần được thực hiện trong một nhiệm vụ có vai trò, phụ thuộc và phản hồi thật.",
            "steps": [
                "Chọn nhiệm vụ nhỏ có người hướng dẫn, mục tiêu và thời hạn rõ; thống nhất vai trò và cách báo trở ngại.",
                "Thực hiện một lần bàn giao công việc có tiêu chí hoàn thành và xác nhận người nhận đã hiểu.",
                "Nhờ đồng nghiệp/mentor quan sát cách chia sẻ thông tin, xử lý bất đồng và xin hỗ trợ; ghi lại ví dụ cụ thể.",
                "Debrief cùng nhóm, chọn một cách phối hợp cần thay đổi và thử lại ở nhiệm vụ kế tiếp.",
            ],
            "evidence": "mục tiêu nhiệm vụ đã ẩn danh, checklist bàn giao, phản hồi thành viên/mentor và một thay đổi đã thử.",
        }
    if normalized in _SALES_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Thực hành tư vấn và phản hồi khách hàng",
            "framing": "Ưu tiên luyện với khách hàng giả lập, quan sát người có kinh nghiệm và nhận phản hồi cụ thể. Khóa học sản phẩm có thể hỗ trợ, nhưng không thay cho luyện tình huống.",
            "steps": [
                "Chọn một sản phẩm/dịch vụ và chân dung khách hàng giả lập; không đưa thông tin nhận dạng khách hàng thật vào ghi chép.",
                "Luyện một cuộc trao đổi ngắn: hỏi nhu cầu, ngân sách và ràng buộc; tóm tắt lại để xác nhận trước khi đề xuất.",
                "Nhờ đồng nghiệp đóng vai khách hàng nêu 2–3 phản đối; trả lời bằng câu hỏi làm rõ và thông tin đã kiểm chứng, không gây áp lực hoặc hứa quá mức.",
                "Xin người quan sát góp ý bằng ví dụ cụ thể, sửa một điểm trong kịch bản rồi diễn tập lại; nếu đang đi làm, xin shadow một ca và phản tư cùng quản lý.",
            ],
            "evidence": "kịch bản đã ẩn danh, ghi chú phản hồi của người quan sát và một phiên bản đã sửa; theo dõi chất lượng hỏi/lắng nghe/xác nhận bước tiếp theo, không chỉ đếm tỷ lệ chốt.",
        }
    if normalized in _PROBLEM_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện xử lý tình huống bằng ca thực tế",
            "framing": "Năng lực này tiến bộ qua nhiều lần xử lý, xem lại hệ quả và nhận góp ý; một khóa học không thay thế được trải nghiệm theo bối cảnh.",
            "steps": [
                "Chọn một vấn đề thật đã ẩn thông tin nhạy cảm hoặc một tình huống mô phỏng gần với công việc.",
                "Viết rõ mục tiêu, dữ kiện đã biết, điều còn chưa rõ và người cần tham vấn trước khi chọn cách xử lý.",
                "Thử một hành động có thể đảo ngược khi phù hợp, theo dõi kết quả và ghi lại tác dụng phụ hoặc rủi ro.",
                "Nhờ đồng nghiệp/mentor phản biện giả định, sau đó ghi một điều sẽ làm khác ở lần sau.",
            ],
            "evidence": "bản tóm tắt ca đã ẩn danh gồm dữ kiện, lựa chọn, kết quả quan sát được và góp ý nhận được.",
        }
    if normalized in _LEADERSHIP_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện điều phối nhóm qua một nhiệm vụ nhỏ",
            "framing": "Kỹ năng quản lý cần được luyện với con người và bối cảnh thật. Dùng phạm vi có giám sát; không suy ra năng lực lãnh đạo từ một bài học hay một chỉ số duy nhất.",
            "steps": [
                "Nhận điều phối một nhiệm vụ nhỏ có mục tiêu, thời hạn và quyền quyết định rõ ràng.",
                "Cùng nhóm thống nhất vai trò, phụ thuộc, cách báo trở ngại và tiêu chí hoàn thành trước khi bắt đầu.",
                "Trong quá trình làm, hỏi từng người về trở ngại và hỗ trợ cần thiết; ghi nhận quyết định thay vì chỉ nhắc tiến độ.",
                "Sau khi kết thúc, xin phản hồi riêng từ thành viên/mentor, xác định một hành vi cần điều chỉnh và thử lại ở nhiệm vụ kế tiếp.",
            ],
            "evidence": "mục tiêu nhiệm vụ, quyết định điều phối đã ẩn danh, phản hồi của thành viên và một thay đổi bạn đã thử.",
        }
    if normalized in _EVENT_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Tập điều phối sự kiện có người hướng dẫn",
            "framing": "Tổ chức sự kiện được củng cố khi thực hiện từng phần việc, phối hợp nhà cung cấp và tổng kết sự cố; lý thuyết chỉ hỗ trợ bước chuẩn bị.",
            "steps": [
                "Shadow một sự kiện nhỏ hoặc nhận một hạng mục có phạm vi rõ như đăng ký, hậu cần hay lịch trình.",
                "Dùng checklist, người phụ trách, thời điểm bàn giao và phương án dự phòng; xác nhận thay đổi với người có thẩm quyền.",
                "Trong lúc diễn ra, ghi nhận tình huống và quyết định xử lý; bảo vệ dữ liệu người tham dự.",
                "Debrief với người hướng dẫn về điều diễn ra đúng/sai và sửa checklist trước lần tiếp theo.",
            ],
            "evidence": "checklist đã ẩn danh, một ví dụ xử lý thay đổi/sự cố và cập nhật rút ra sau debrief.",
        }
    if normalized == "viết nội dung":
        return {
            "skill": skill,
            "category": category,
            "title": "Xây portfolio nội dung và nhận biên tập",
            "framing": "Khóa học kỹ thuật viết chỉ phù hợp với một số loại nội dung; năng lực viết nội dung nói chung cần sản phẩm thật, phản hồi của biên tập viên và chỉnh sửa nhiều vòng.",
            "steps": [
                "Chọn một nhóm độc giả và mục tiêu rõ cho một bài ngắn, trang sản phẩm hoặc email.",
                "Viết bản đầu dựa trên thông tin có nguồn; đánh dấu riêng dữ kiện cần xác nhận.",
                "Nhờ biên tập viên/đồng nghiệp thuộc nhóm độc giả đọc thử và chỉ ra chỗ khó hiểu, thiếu bằng chứng hoặc không đúng giọng.",
                "Sửa bài, lưu trước/sau cùng ghi chú quyết định biên tập; tạo thêm mẫu khác cho một kênh hoặc đối tượng khác.",
            ],
            "evidence": "2–3 mẫu nội dung, góp ý đã nhận và bản sửa có ghi rõ nguồn cho các dữ kiện.",
        }
    if category == "trait":
        return {
            "skill": skill,
            "category": category,
            "title": "Biến phẩm chất thành hành vi có thể quan sát",
            "framing": "Không gắn nhãn hay chấm tính cách. Chọn hành vi liên quan đến công việc, luyện trong nhiệm vụ nhỏ và kiểm tra bằng bằng chứng cùng phản hồi.",
            "steps": [
                "Viết một hành vi cụ thể thể hiện kỹ năng này trong vị trí đang nhắm tới.",
                "Chọn nhiệm vụ sắp tới để thử hành vi đó; ghi lại bối cảnh và quyết định của bạn.",
                "Nhờ người làm cùng phản hồi điều họ quan sát được, không yêu cầu nhận xét chung về tính cách.",
                "Lặp lại trong một tình huống khác và so sánh điều kiện nào giúp hành vi hiệu quả hơn.",
            ],
            "evidence": "ghi chú ngắn về bối cảnh, hành vi, kết quả và nhận xét quan sát được; không xem đây là điểm năng lực.",
        }
    return {
        "skill": skill,
        "category": category,
        "title": "Luyện qua nhiệm vụ và phản hồi",
        "framing": "Ưu tiên cơ hội thực hành trong công việc hoặc mô phỏng có người quan sát. Tài liệu có thể giúp biết cách làm, còn năng lực cần được củng cố bằng áp dụng và phản hồi.",
        "steps": [
            "Chọn một tình huống sắp tới cần dùng kỹ năng này và xác định một hành vi cụ thể muốn thử.",
            "Thực hành trong nhiệm vụ thật có giám sát hoặc diễn tập với đồng nghiệp; xin phép trước nếu ghi âm/ghi hình.",
            "Xin phản hồi gắn với hành động cụ thể: điều gì hiệu quả, lúc nào, và có thể thử gì khác.",
            "Thử lại ở tình huống tiếp theo và ghi nhận kết quả quan sát được để tự điều chỉnh.",
        ],
            "evidence": "một ví dụ công việc đã ẩn danh, ghi chú của người quan sát, phản hồi mentor/đồng nghiệp và điều chỉnh đã thử lần tiếp theo.",
    }


def get_practice_routes(skills, resources: Mapping) -> list[dict]:
    """Build non-course practice plans for soft skills and observable traits."""
    categories = {}
    for name, group in resources.items():
        if isinstance(name, str) and isinstance(group, Mapping):
            categories[normalize_skill(name)] = group.get("category")
    routes = []
    for skill in skills:
        normalized = normalize_skill(skill)
        category = categories.get(normalized)
        if normalized in _SALES_SKILLS:
            route = _route(skill, "soft_skill")
        elif normalized in _COMMUNICATION_SKILLS | _TEAMWORK_SKILLS | _LEADERSHIP_SKILLS | _EVENT_SKILLS | {"viết nội dung"}:
            route = _route(skill, "soft_skill")
        elif normalized in _TRANSVERSAL_SKILLS:
            route = _route(skill, category or "practice")
        elif category in {"soft_skill", "trait"}:
            route = _route(skill, category)
        else:
            continue
        if normalized in _OBSERVATION_CHECKLISTS:
            route["observation_checklist"] = _OBSERVATION_CHECKLISTS[normalized]
        routes.append(route)
    return routes


def get_partial_resource_assignment(
    skill: str,
    resource: Mapping,
    resources: Mapping,
    *,
    role_context: str | None = None,
) -> dict | None:
    """Turn a partial learning resource into a bounded, reviewable work sample."""
    if not isinstance(resource, Mapping) or resource_review_status(resource) != "partial":
        return None
    normalized = normalize_skill(skill)
    context = f" cho vị trí {role_context}" if role_context else " trong bối cảnh nghề bạn đang nhắm tới"
    scope = resource.get("review_note", "")

    routes = get_practice_routes([skill], resources)
    if routes:
        route = routes[0]
        return {
            "skill": skill,
            "title": "Bài thực hành có phản hồi sau phần tài liệu",
            "scope": scope,
            "steps": [
                f"Chọn một ý trong tài liệu và dùng nó để chuẩn bị một tình huống mô phỏng{context}.",
                *route["steps"],
            ],
            "evidence": route["evidence"],
            "caution": skill_scope_caution(skill),
        }

    if normalized == "sql":
        artifact = "một file truy vấn SQL, dữ liệu giả lập nhỏ, kết quả mong đợi và README nêu giả định/giới hạn."
        steps = [
            f"Tạo dữ liệu giả lập cho một câu hỏi nghiệp vụ{context}; không dùng dữ liệu cá nhân hoặc dữ liệu công ty chưa được phép.",
            "Viết truy vấn chỉ cho chủ đề mà ghi chú phạm vi nguồn xác nhận; lưu truy vấn và kết quả mẫu.",
            "Kiểm tra trường hợp thiếu dữ liệu, trùng bản ghi và đối chiếu một kết quả bằng cách độc lập.",
            "Nhờ đồng nghiệp/mentor review tính đúng, cách đặt tên và giới hạn của truy vấn; ghi lại phần đã sửa.",
        ]
    elif normalized in {"python", "pandas", "phân tích dữ liệu", "thống kê", "power bi", "tableau", "trực quan hóa dữ liệu"}:
        artifact = "notebook hoặc dashboard chạy lại được, bộ dữ liệu tổng hợp, mô tả trường dữ liệu, 2–3 kết quả và giới hạn phân tích."
        steps = [
            f"Chọn một câu hỏi nghiệp vụ cụ thể{context} và tạo hoặc tìm dữ liệu tổng hợp phù hợp.",
            "Thực hiện phần kỹ thuật được nguồn partial hỗ trợ; ghi rõ thao tác và phiên bản công cụ.",
            "Kiểm tra đầu vào, cách tính và một kết quả mẫu; không diễn giải tương quan thành quan hệ nhân quả.",
            "Xin mentor/đồng nghiệp phản biện tính hữu ích của đầu ra; lưu nhận xét và bản chỉnh sửa.",
        ]
    elif normalized == "kiến trúc hệ thống":
        artifact = "sơ đồ ranh giới hệ thống và một ADR ngắn gồm bối cảnh, lựa chọn, trade-off, rủi ro vận hành và câu hỏi còn mở."
        steps = [
            f"Chọn một case mô phỏng gần domain của vị trí{context}; ghi rõ các giả định và thành phần nằm ngoài phạm vi.",
            "Chỉ áp dụng phần nguồn hỗ trợ (kiến trúc phần mềm hoặc nền tảng cụ thể); không suy rộng thành kiến trúc toàn hệ thống.",
            "Nêu ít nhất hai lựa chọn, yêu cầu chất lượng liên quan và trade-off về bảo mật, độ tin cậy, chi phí hoặc vận hành.",
            "Nhờ kiến trúc sư/mentor có kinh nghiệm trong domain phản biện sơ đồ và ADR; cập nhật ranh giới và quyết định.",
        ]
    else:
        artifact = "một sản phẩm nhỏ có thể xem lại (bản phân tích, checklist, demo hoặc tài liệu quyết định) cùng nguồn và giả định."
        steps = [
            f"Chọn một nhiệm vụ gần vị trí mục tiêu{context}, xác định đầu ra và tiêu chí hoàn thành trước khi làm.",
            "Dùng tài liệu partial cho đúng phần được ghi trong phạm vi review; nêu riêng các phần tài liệu không bao quát.",
            "Tạo đầu ra có thể kiểm tra, dùng dữ liệu tổng hợp/đã được phép và ghi lại các giả định.",
            "Nhờ người có kinh nghiệm hoặc đồng nghiệp review bằng tiêu chí cụ thể; chỉnh sửa và lưu minh chứng trước/sau.",
        ]
    return {
        "skill": skill,
        "title": "Bài tập/portfolio theo bối cảnh",
        "scope": scope,
        "steps": steps,
        "evidence": artifact,
        "caution": skill_scope_caution(skill),
    }


def _positive(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _url(value):
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        return parsed is not None and parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


def _duration(record):
    hours = record.get("duration_hours")
    if hours is not None:
        if not _positive(hours):
            raise ValueError("duration_hours phải là số dương hữu hạn hoặc null.")
        if _url(record.get("duration_source")) and record.get("duration_basis"):
            return float(hours), "published", None
        return None, "unknown", "unverified_duration"
    estimate = record.get("estimated_duration_hours")
    if estimate is not None:
        if not _positive(estimate):
            raise ValueError("estimated_duration_hours phải là số dương hữu hạn.")
        if record.get("estimated_duration_basis") or record.get("duration_basis"):
            return float(estimate), "estimated", None
        return None, "unknown", "estimate_without_basis"
    return None, "unknown", "unknown_duration"


def _items(gap):
    if not isinstance(gap, Mapping) or not isinstance(gap.get("items"), list):
        raise ValueError("gap phải có items từ compute_gap.")
    items, seen = [], set()
    for raw in gap["items"]:
        if not isinstance(raw, Mapping):
            raise ValueError("gap.items phải chứa object.")
        skill = canonical_skill(raw.get("skill"))
        if skill in seen:
            raise ValueError("gap có kỹ năng trùng sau canonical.")
        seen.add(skill)
        current, required = raw.get("current"), raw.get("required")
        if any(type(v) is not int or not 0 <= v <= 3 for v in (current, required)):
            raise ValueError("current/required phải là int 0–3.")
        if type(raw.get("gap")) is not int or raw["gap"] != max(0, required-current):
            raise ValueError("gap không nhất quán với current/required.")
        if isinstance(raw.get("priority"), bool) or (not _positive(raw.get("priority")) and not (raw["gap"] == 0 and raw.get("priority") == 0)):
            raise ValueError("priority không hợp lệ.")
        if raw["gap"]:
            items.append({**raw, "skill": skill})
    return sorted(items, key=lambda item: -item["priority"])


def plan(gap, resources, hours_per_week=8):
    if not _positive(hours_per_week):
        raise ValueError("hours_per_week phải là số dương hữu hạn, không nhận bool.")
    if not isinstance(resources, Mapping):
        raise TypeError("resources phải là mapping.")
    items = _items(gap)
    index = {}
    for name, group in resources.items():
        name = canonical_skill(name)
        if name in index:
            raise ValueError("resources có khóa trùng sau canonical/alias.")
        index[name] = group

    # Union IDs and normalized URLs before selection. Metadata remains per mapping.
    parents, rows = {}, []
    excluded_without_url = {item["skill"]: [] for item in items}
    def root(token):
        parents.setdefault(token, token)
        while parents[token] != token:
            parents[token] = parents[parents[token]]
            token = parents[token]
        return token
    for item in items:
        group = index.get(item["skill"], {"resources": []})
        if not isinstance(group, Mapping) or not isinstance(group.get("resources"), list):
            raise ValueError("Nhóm tài nguyên phải có resources:list.")
        for record in group["resources"]:
            if not isinstance(record, Mapping):
                raise ValueError("Resource phải là object.")
            tokens = _resource_tokens(record)
            if not tokens or not _url(record.get("url")):
                excluded_without_url[item["skill"]].append((record, "missing_url" if tokens else "missing_resource_identity"))
                continue
            for token in tokens[1:]:
                parents[root(token)] = root(tokens[0])
            rows.append((item["skill"], record, tokens))
    identities = {}
    candidates = {item["skill"]: [] for item in items}
    for skill, record, tokens in rows:
        key = identities.setdefault(root(tokens[0]), tokens[0])
        eligible = is_recommendable_resource(record, require_verified=True, skill=skill)
        if eligible:
            start, end = record.get("level_from"), record.get("level_to")
            if any(type(v) is not int or not 1 <= v <= 3 for v in (start, end)) or start > end:
                raise ValueError(f"Khoảng level resource của {skill} không hợp lệ.")
            duration = _duration(record)
        else:
            duration = None
        candidates[skill].append((key, record, duration))

    catalog, refs, unresolved, coverage = {}, {}, [], []
    for item in items:
        skill = item["skill"]
        refs[skill] = []
        needed = set(range(item["current"]+1, item["required"]+1))
        all_candidates = candidates[skill]
        eligible = [(key, r, duration) for key, r, duration in all_candidates
                    if is_recommendable_resource(r, require_verified=True, skill=skill)]
        while needed:
            level = min(needed)
            choices = [(k, r, d) for k, r, d in eligible if r["level_from"] <= level <= r["level_to"]]
            reviewed_choices = [choice for choice in choices if resource_review_status(choice[1]) == "reviewed"]
            if reviewed_choices:
                choices = reviewed_choices
            if not choices:
                excluded = excluded_without_url[skill]
                exclusion_reasons = {
                    resource_exclusion_reason(record, require_verified=True, skill=skill)
                    for _, record, _ in all_candidates
                }
                exclusion_reasons.update(reason_code for _, reason_code in excluded)
                exclusion_reasons.discard(None)
                if not all_candidates and not excluded:
                    reason = "no_resources"
                elif not eligible:
                    reason = next((candidate for candidate in (
                        "specialized_source_required",
                        "unreviewed_content", "blocked_resource", "unsuitable_content",
                        "unverified_link", "missing_url", "missing_resource_identity",
                    ) if candidate in exclusion_reasons), "unreviewed_content")
                else:
                    reason = "level_mismatch"
                issue = {"skill": skill, "reason": reason, "levels": sorted(needed)}
                status_records = [record for _, record, _ in all_candidates] + [record for record, _ in excluded]
                statuses = sorted({resource_review_status(record) for record in status_records})
                if statuses:
                    issue["resource_statuses"] = statuses
                if exclusion_reasons:
                    issue["exclusion_reasons"] = sorted(exclusion_reasons)
                unresolved.append(issue)
                break
            # Prefer reviewed, sourced duration, then broader coverage; stable data order.
            key, record, duration = min(choices, key=lambda choice: (
                choice[1]["content_review_status"] != "reviewed",
                {"published": 0, "estimated": 1, "unknown": 2}[choice[2][1]],
                -len(needed & set(range(choice[1]["level_from"], choice[1]["level_to"]+1))),
            ))
            covered = sorted(needed & set(range(record["level_from"], record["level_to"]+1)))
            needed.difference_update(covered)
            if key not in refs[skill]:
                refs[skill].append(key)
            coverage.append({"skill": skill, "resource_key": key, "levels": covered,
                             "content_review_status": record["content_review_status"],
                             "review_note": record.get("review_note", ""),
                             "level_evidence": (
                                 "bounded_unit_recorded" if has_granular_level_evidence(record)
                                 else "scope_pending" if "scope_granularity" in record
                                 else "legacy_metadata_unavailable"
                             )})
            if "scope_granularity" in record and not has_granular_level_evidence(record):
                unresolved.append({
                    "skill": skill, "resource_key": key,
                    "reason": "scope_evidence_pending", "levels": covered,
                })
            if record["content_review_status"] == "partial":
                unresolved.append({"skill": skill, "resource_key": key, "reason": "partial_content", "levels": covered})
            if key not in catalog:
                catalog[key] = {**deepcopy(dict(record)), "key": key, "skills": [],
                                "planned_hours": duration[0], "duration_kind": duration[1],
                                "duration_issue": duration[2], "duration_evidence": {}}
            selected = catalog[key]
            old_hours, old_kind = selected["planned_hours"], selected["duration_kind"]
            rank = {"published": 0, "estimated": 1, "unknown": 2}
            if selected["duration_issue"] != "conflicting_duration":
                if duration[0] is not None and old_hours is not None and old_kind == duration[1] and old_hours != duration[0]:
                    selected.update(planned_hours=None, duration_kind="unknown", duration_issue="conflicting_duration", duration_evidence={})
                elif rank[duration[1]] < rank[old_kind] or (duration[0], duration[1]) == (old_hours, old_kind):
                    selected.update(planned_hours=duration[0], duration_kind=duration[1], duration_issue=duration[2])
                    if duration[0] is not None:
                        selected["duration_evidence"] = {
                            "source": record.get("duration_source") if duration[1] == "published" else None,
                            "basis": record.get("estimated_duration_basis") or record.get("duration_basis"),
                            "hours": duration[0], "kind": duration[1],
                        }
            if skill not in selected["skills"]:
                selected["skills"].append(skill)

    unknown = []
    published = estimated = Decimal(0)
    phases = []
    budget = Decimal(str(hours_per_week))
    used = Decimal(0)
    for key, record in catalog.items():
        hours = record["planned_hours"]
        if hours is None:
            issue = {"resource_key": key, "skills": list(record["skills"]), "reason": record["duration_issue"]}
            unknown.append(issue)
            unresolved.append(dict(issue))
            continue
        remaining = Decimal(str(hours))
        if record["duration_kind"] == "estimated":
            estimated += remaining
        else:
            published += remaining
        part = 0
        while remaining > 0:
            if not phases or used >= budget:
                phases.append({"week": len(phases)+1, "hours": 0, "segments": []})
                used = Decimal(0)
            phase = phases[-1]
            allocation = min(remaining, budget-used)
            part += 1
            phase["segments"].append({"resource_key": key, "hours": float(allocation), "part": part,
                                      "duration_kind": record["duration_kind"]})
            used += allocation
            phase["hours"] = float(used)
            remaining -= allocation
    return {"role_id": gap.get("role_id"), "hours_per_week": hours_per_week,
            "phases": phases, "resources": catalog, "resource_keys": refs, "level_coverage": coverage,
            "total_weeks": None if unresolved else len(phases), "known_weeks": len(phases),
            "total_known_hours": float(published), "total_estimated_hours": float(estimated),
            "total_planned_hours": float(published+estimated), "is_estimated": bool(estimated),
            "unresolved": unresolved, "unknown_duration": unknown,
            "practice_routes": get_practice_routes([item["skill"] for item in items], resources),
            "completion_basis": "resource_metadata_not_skill_attainment"}


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
