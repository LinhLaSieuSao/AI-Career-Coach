"""Publication eligibility and exclusion reasons for learning resources."""

import pytest
from datetime import date, timedelta

from modules.resource_policy import (
    is_recommendable_resource,
    resource_exclusion_reason,
    resource_review_status,
    has_current_specialist_evidence,
    skill_scope_caution,
    summarize_resource_reviews,
    resource_review_label,
    resource_level_gap,
)


def _resource(**overrides):
    return {
        "content_review_status": "reviewed",
        "review_note": "Reviewed for the mapped learning outcome.",
        "verified": True,
        **overrides,
    }


@pytest.mark.parametrize("status", ["reviewed", "partial", "REVIEWED"])
def test_reviewed_resource_with_note_is_recommendable(status):
    resource = _resource(content_review_status=status)

    assert is_recommendable_resource(resource)
    assert is_recommendable_resource(resource, require_verified=True)
    assert resource_exclusion_reason(resource, require_verified=True) is None


@pytest.mark.parametrize(
    "resource,reason",
    [
        (_resource(content_review_status="blocked"), "blocked_resource"),
        (_resource(content_review_status="unsuitable"), "unsuitable_content"),
        (_resource(content_review_status="unreviewed"), "unreviewed_content"),
        (_resource(content_review_status="reviewed", review_note=" "), "unreviewed_content"),
        (_resource(content_review_status="pending"), "unreviewed_content"),
        (_resource(verified=False), "unverified_link"),
        (None, "invalid_resource"),
    ],
)
def test_ineligible_resources_explain_why_they_are_excluded(resource, reason):
    assert not is_recommendable_resource(resource, require_verified=True)
    assert resource_exclusion_reason(resource, require_verified=True) == reason


def test_legacy_url_verification_alone_does_not_establish_content_review():
    resource = {"verified": True}

    assert resource_review_status(resource) == "unreviewed"
    assert not is_recommendable_resource(resource)
    assert resource_exclusion_reason(resource) == "unreviewed_content"


def _specialist_evidence(specialty="vietnam_tax", *, checked_at=None, reviewed_at=None):
    today = date.today()
    return {
        "jurisdiction": "VN",
        "source_authority": "official",
        "source_checked_at": checked_at or today.isoformat(),
        "specialist_review": {
            "specialty": specialty,
            "approved": True,
            "qualification_verified": True,
            "scope": "Current Vietnamese tax filing rules for the covered scenario.",
            "reviewed_at": reviewed_at or today.isoformat(),
        },
    }


def test_tax_and_labor_resources_need_current_jurisdiction_and_specialist_evidence():
    resource = _resource()
    assert not is_recommendable_resource(resource, require_verified=True, skill="kế toán thuế")
    assert resource_exclusion_reason(resource, require_verified=True, skill="kế toán thuế") == "specialized_source_required"

    resource["specialized_evidence"] = _specialist_evidence()
    assert has_current_specialist_evidence(resource, "kế toán thuế")
    assert is_recommendable_resource(resource, require_verified=True, skill="kế toán thuế")

    resource["specialized_evidence"] = _specialist_evidence(specialty="vietnam_tax")
    assert not has_current_specialist_evidence(resource, "luật lao động")


def test_specialist_source_checks_expire_and_safety_certification_is_gated():
    old = (date.today() - timedelta(days=366)).isoformat()
    resource = _resource(specialized_evidence=_specialist_evidence(checked_at=old, reviewed_at=old))
    assert not has_current_specialist_evidence(resource, "kế toán thuế")

    safety = _resource()
    assert resource_exclusion_reason(
        safety, require_verified=True, skill="chứng chỉ an toàn điện"
    ) == "specialized_source_required"
    assert "không thực hành thao tác nguy hiểm" in skill_scope_caution("an toàn điện").casefold()


def test_scope_cautions_preserve_limits_for_partial_domains():
    assert "kiến trúc phần mềm" in skill_scope_caution("kiến trúc hệ thống")
    assert "định mức" in skill_scope_caution("bóc tách khối lượng")
    assert "không thay thế" in skill_scope_caution("an toàn lao động")


def test_resource_review_summary_counts_mappings_separately():
    summary = summarize_resource_reviews({
        "sql": {"resources": [_resource(content_review_status="partial"), _resource(content_review_status="blocked")]},
        "python": {"resources": [_resource(content_review_status="reviewed")]},
    })
    assert summary["mapping_count"] == 3
    assert summary["partial"] == 1
    assert summary["blocked"] == 1
    assert summary["reviewed"] == 1
    assert summary["unreviewed"] == 0


def test_resource_review_labels_have_one_shared_mapping():
    assert resource_review_label("reviewed") == "Đã review nội bộ"
    assert resource_review_label("partial") == "Bao phủ một phần"
    assert resource_review_label("blocked") == "Đã chặn"
    assert resource_review_label("unknown") == resource_review_label(None) == "Chưa review"


def test_resource_level_gap_does_not_treat_intro_as_full_role_coverage():
    resource = {"level_from": 1, "level_to": 1, "skills": ["c#", "reactjs"]}
    assert resource_level_gap(resource, {"c#": 3, "reactjs": 1}) == [
        {"skill": "c#", "resource_level_to": 1, "required_level": 3}
    ]
    assert resource_level_gap(resource, {"c#": 1}) == []
