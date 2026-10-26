"""Golden regression benchmark for transparent local role suggestions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.catalog import load_roles
from modules.matcher import suggest_roles


FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "golden_profiles.json"


def benchmark_metrics() -> dict[str, float | int]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise AssertionError("Golden benchmark phải có ít nhất một hồ sơ.")
    valid_role_ids = {role["id"] for role in load_roles()}
    ids = [profile.get("id") for profile in profiles]
    if len(ids) != len(set(ids)) or any(not isinstance(value, str) or not value for value in ids):
        raise AssertionError("Golden benchmark có ID hồ sơ bị thiếu hoặc trùng.")

    reciprocal_ranks: list[float] = []
    hits = 0
    forbidden = 0
    details = []
    for profile in profiles:
        skills = profile.get("skills")
        activities = profile.get("interests", [])
        expected = set(profile.get("expected_top_roles", []))
        disallowed = set(profile.get("forbidden_top_roles", []))
        if not isinstance(skills, list) or not skills:
            raise AssertionError(f"{profile.get('id')}: cần có danh sách kỹ năng.")
        if not expected:
            raise AssertionError(f"{profile.get('id')}: thiếu expected_top_roles.")
        unknown = (expected | disallowed) - valid_role_ids
        if unknown:
            raise AssertionError(f"{profile.get('id')}: role ID không tồn tại: {sorted(unknown)}")
        top = suggest_roles({"skills": skills, "interest_activity_ids": activities}, top_k=3)
        top_ids = [entry["role_id"] for entry in top]
        ranks = [index + 1 for index, role_id in enumerate(top_ids) if role_id in expected]
        if ranks:
            hits += 1
            reciprocal_ranks.append(1.0 / min(ranks))
        else:
            reciprocal_ranks.append(0.0)
        bad = sorted(set(top_ids) & disallowed)
        forbidden += len(bad)
        details.append({"id": profile["id"], "top3": top_ids, "expected_rank": min(ranks) if ranks else None,
                        "forbidden": bad})

    count = len(profiles)
    return {
        "profiles": count,
        "hit_at_3": hits / count,
        "mrr_at_3": sum(reciprocal_ranks) / count,
        "forbidden_rate_at_3": forbidden / count,
        "details": details,
    }


def test_golden_role_recommendations_meet_quality_thresholds():
    metrics = benchmark_metrics()
    assert metrics["hit_at_3"] >= 0.90, metrics
    assert metrics["mrr_at_3"] >= 0.75, metrics
    assert metrics["forbidden_rate_at_3"] == 0, metrics


if __name__ == "__main__":
    results = benchmark_metrics()
    print(f"Profiles: {results['profiles']}")
    print(f"Hit@3: {results['hit_at_3']:.1%}")
    print(f"MRR@3: {results['mrr_at_3']:.3f}")
    print(f"Forbidden@3: {results['forbidden_rate_at_3']:.1%}")
    if (results["hit_at_3"] < 0.90 or results["mrr_at_3"] < 0.75
            or results["forbidden_rate_at_3"] != 0):
        for row in results["details"]:
            print(f"{row['id']}: top3={row['top3']}, expected_rank={row['expected_rank']}, forbidden={row['forbidden']}")
        raise SystemExit(1)
