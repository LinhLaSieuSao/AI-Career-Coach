"""Structural checks for the bundled catalogs used by the web app."""

import json

from modules.catalog import DATA_DIR, load_roles, load_skill_vocabulary
from modules.interview import question_bank_quality_summary
from modules.matcher import load_interest_activities, load_role_family_vectors
from modules.schemas import RoleRequirement
from modules.skill_extractor import load_aliases, normalize_skill


def test_role_and_interest_catalogs_cover_every_role():
    roles = load_roles()
    assert len(roles) == 131
    assert len({role["id"] for role in roles}) == len(roles)
    for role in roles:
        RoleRequirement.model_validate(role)
    families = json.loads((DATA_DIR / "role_families_riasec.json").read_text(encoding="utf-8"))["families"]
    assert len(families) == 15
    assert len(load_role_family_vectors()) == len(roles)
    assert load_interest_activities()


def test_aliases_and_resources_use_recognized_skills():
    vocabulary = load_skill_vocabulary()
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    assert aliases and all(target in vocabulary for target in aliases.values())
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    assert isinstance(resources, dict) and resources
    for skill, group in resources.items():
        assert normalize_skill(skill) in vocabulary
        assert isinstance(group.get("resources"), list)
        for record in group["resources"]:
            assert isinstance(record.get("url"), str) and record["url"].startswith(("http://", "https://"))


def test_question_banks_have_unique_ids_and_known_roles():
    role_ids = {role["id"] for role in load_roles()}
    files = sorted((DATA_DIR / "interview_questions").glob("*.json"))
    assert len(files) == 10
    seen = set()
    count = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for role_id, questions in payload["roles"].items():
            assert role_id in role_ids
            for question in questions:
                assert question["id"] not in seen
                seen.add(question["id"])
                assert question.get("question")
                count += 1
    assert count == question_bank_quality_summary()["total"] == 766
