"""The data inventory must keep structural checks separate from release claims."""

from datetime import date

from scripts.audit_data_readiness import (
    _link_attestation, build_inventory, gate_failures, resource_url_set_digest,
)


def test_inventory_passes_consistency_without_claiming_review_or_rights() -> None:
    report = build_inventory(as_of=date(2026, 10, 26))

    assert report["gates"]["inventory_consistency"]["passed"]
    assert gate_failures(report) == []
    # Five source URLs were changed after the user's manual URL-set attestation.
    # The old digest must not be silently promoted to the new URL set.
    assert report["scope"]["link_attestation"]["status"] == "stale_or_invalid"
    assert gate_failures(report, require_current_link_attestation=True) == ["current_link_attestation"]
    assert "complete_question_review_metadata" in gate_failures(
        report, require_complete_review=True
    )
    assert "complete_recorded_provenance" in gate_failures(
        report, require_provenance=True
    )
    assert report["scope"]["legal_permission"] == "not_determined_by_this_inventory"
    assert report["summary"]["questions"]["total"] == len(report["questions"])
    assert report["summary"]["resources"]["mappings"] == len(report["resource_mappings"])
    assert report["scope"]["link_attestation"]["content_fit"] == "not_established_by_link_attestation"


def test_role_skill_requirements_measure_exact_level_and_question_coverage() -> None:
    report = build_inventory(as_of=date(2026, 10, 26))
    readiness = report["summary"]["role_skill_readiness"]
    assert readiness["requirements"] == len(report["role_skill_requirements"])
    assert readiness["with_question"] == sum(bool(row["question_ids"]) for row in report["role_skill_requirements"])
    assert readiness["with_material_at_required_level"] == sum(
        row["required_level_resource_status"] != "none" for row in report["role_skill_requirements"]
    )
    sales = next(row for row in report["roles"] if row["id"] == "sales_executive")
    assert sales["skills_with_material_at_required_level"] < sales["skills_with_eligible_material"]
    assert sales["skills_with_question"] <= sales["required_skills"]


def test_user_link_statement_expires_when_url_set_changes() -> None:
    urls = {"https://example.org/a", "https://example.org/b"}
    attestation = {
        "schema_version": 1, "scope": "all_distinct_resource_urls",
        "method": "user_reported_manual_browser_check", "url_count": 2,
        "url_set_sha256": resource_url_set_digest(urls), "attested_at": "2026-10-26",
    }
    assert _link_attestation(attestation, urls, date(2026, 10, 26))["status"] == "user_attested_current_url_set"
    assert _link_attestation(attestation, urls | {"https://example.org/c"}, date(2026, 10, 26))["status"] == "stale_or_invalid"
    report = {"gates": {"inventory_consistency": {"passed": True},
                        "current_link_attestation": {"passed": False}}}
    assert gate_failures(report, require_current_link_attestation=True) == ["current_link_attestation"]


def test_inventory_fingerprint_is_stable_for_identical_input() -> None:
    first = build_inventory(as_of=date(2026, 10, 26))
    second = build_inventory(as_of=date(2026, 10, 26))
    assert first["dataset_fingerprint"] == second["dataset_fingerprint"]
