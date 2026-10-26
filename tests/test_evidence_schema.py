"""Evidence fields must remain structurally valid without claiming full review."""

import json
from pathlib import Path
import shutil

from scripts.migrate_evidence_schema_v2 import migrate
from scripts.validate_evidence_schema import validate_schema


DATA_DIR = Path(__file__).resolve().parents[1] / "Data"


def test_migrated_records_have_valid_schema_but_open_evidence() -> None:
    report = validate_schema(DATA_DIR)
    assert report["structure_passed"]
    assert report["summary"] == {"roles": 131, "resources": 471, "questions": 766}
    assert not report["complete_evidence_passed"]
    assert report["evidence_pending"]["provenance.rights_basis"] == 1368
    assert report["evidence_pending"]["question.target_level_rubric"] == 727
    assert migrate(DATA_DIR, check=True)["files_changed"] == 0


def test_scoped_demo_gate_checks_review_and_coverage_without_claiming_completion() -> None:
    targets = {"sales_executive", "frontend_developer_react", "data_analyst", "backend_developer_java"}
    report = validate_schema(DATA_DIR, target_roles=targets)
    assert report["structure_passed"]
    assert report["summary"]["roles"] == 4
    assert report["summary"]["questions"] == 39
    assert report["evidence_pending"].get("question.role_skill_coverage", 0) == 0
    assert report["evidence_pending"]["question.content_review_status"] == 39
    assert not report["complete_evidence_passed"]


def test_scoped_gate_rejects_unknown_role() -> None:
    report = validate_schema(DATA_DIR, target_roles={"missing_role"})
    assert not report["structure_passed"]
    assert "Unknown target role: missing_role" in report["structural_errors"]


def test_validator_rejects_a_question_at_the_wrong_role_skill_level(tmp_path: Path) -> None:
    for name in ("roles.json", "resources.json", "skill_aliases.json"):
        shutil.copy2(DATA_DIR / name, tmp_path / name)
    shutil.copytree(DATA_DIR / "interview_question", tmp_path / "interview_question")
    path = tmp_path / "interview_question" / "part_01_software.json"
    bank = json.loads(path.read_text(encoding="utf-8"))
    bank["roles"]["backend_developer_java"][0]["level"] = 1
    path.write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")

    report = validate_schema(tmp_path)
    assert not report["structure_passed"]
    assert any("question Level differs from role skill Level" in error for error in report["structural_errors"])
