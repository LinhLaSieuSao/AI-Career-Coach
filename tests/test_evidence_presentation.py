"""UI labels must not imply a stronger evidence tier than source metadata."""

from copy import deepcopy

from modules.evidence_presentation import resource_evidence_badge, role_domain_notice


def test_resource_badge_uses_weakest_axis():
    record = {
        "content_review_status": "reviewed", "review_note": "Internal review",
        "scope_granularity": "lesson", "evidence_locator": "Unit 1",
        "verification_axes": {"access_status": "independently_accessible", "rights_basis": "pending"},
        "provenance": {"rights_basis": None},
    }
    assert "quyền tái sử dụng chưa xác minh" in resource_evidence_badge(record)
    without_scope = deepcopy(record)
    without_scope["scope_granularity"] = "catalog"
    assert "chưa xác định bài/chương" in resource_evidence_badge(without_scope)
    rejected = deepcopy(record)
    rejected["content_review_status"] = "unsuitable"
    assert resource_evidence_badge(rejected).startswith("Không đề xuất")


def test_role_domain_notices_are_scoped():
    assert "chứng chỉ hành nghề" in role_domain_notice("doctor")
    assert "văn bản còn hiệu lực" in role_domain_notice("legal_executive")
    assert "quy định hiện hành" in role_domain_notice("tax_accountant")
    assert "hiện trường" in role_domain_notice("safety_engineer")
    assert role_domain_notice("sales_executive") is None
