"""Separate, intentionally pending content gate for the four demo roles.

Normal test runs show these as xfail. Run this file with --runxfail for the
strict editorial gate, which must currently report the actual failures.
"""

import json

import pytest

from modules.resource_policy import is_recommendable_resource
from scripts.audit_demo_role_quality import DATA_DIR, DEMO_ROLE_IDS, audit_demo_roles


@pytest.fixture(scope="module")
def report() -> dict:
    return audit_demo_roles(DATA_DIR)


@pytest.mark.parametrize("role_id", DEMO_ROLE_IDS)
@pytest.mark.xfail(
    strict=True, raises=AssertionError,
    reason="Demo content and independent evidence gate is an explicit remediation backlog",
)
def test_demo_role_content_and_evidence_gate(role_id: str, report: dict) -> None:
    role = report["roles"][role_id]
    active_counts = {key: count for key, count in role["issue_counts"].items() if count}
    assert role["gate_passed"], json.dumps(
        {"role": role_id, "counts": active_counts,
         "examples": {key: values[:3] for key, values in role["issues"].items() if values}},
        ensure_ascii=False,
    )


def test_rejected_demo_resources_are_not_recommended() -> None:
    """The known raw-data backlog must not leak into learner suggestions."""
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    roles = {role["id"]: role for role in json.loads((DATA_DIR / "roles.json").read_text(encoding="utf-8"))}
    for role_id in DEMO_ROLE_IDS:
        for skill in roles[role_id]["skills"]:
            name = skill["name"]
            for resource in resources[name]["resources"]:
                if resource.get("content_review_status") in {"unsuitable", "blocked"}:
                    assert not is_recommendable_resource(resource, require_verified=True, skill=name)
