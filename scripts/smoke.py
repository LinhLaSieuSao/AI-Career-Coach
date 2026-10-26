"""Run a fast end-to-end check through the core, offline application modules."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.catalog import DATA_DIR, load_roles
from modules.interview import get_questions
from modules.matcher import compute_gap, suggest_roles
from modules.recommender import build_timed_roadmap
from modules.submission import prepare_submission


def main() -> int:
    started = time.perf_counter()
    submission = prepare_submission({
        "skills": ["python", "sql", "power bi"],
        "interest_activity_ids": ["analyze_data"],
        "levels": {"python": 1, "sql": 1},
    })
    if not submission.get("accepted") or not isinstance(submission.get("profile"), dict):
        raise RuntimeError(f"Hồ sơ mẫu không được chấp nhận: {submission.get('errors')}")
    profile = submission["profile"]

    suggestions = suggest_roles(profile, top_k=3)
    if not suggestions or not suggestions[0].get("role_id"):
        raise RuntimeError("Matcher không trả role hợp lệ.")
    role_id = suggestions[0]["role_id"]
    role = next((item for item in load_roles() if item["id"] == role_id), None)
    if role is None:
        raise RuntimeError(f"Role do Matcher trả về không có trong catalog: {role_id}")

    gap = compute_gap(profile.get("levels", {}), role)
    resources = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))
    roadmap = build_timed_roadmap(gap, resources)
    questions = get_questions(role_id, n=3, seed=20261025, prefer_reviewed=True)
    if "items" not in gap or "phases" not in roadmap or not isinstance(questions, list):
        raise RuntimeError("Một trong các hàm lõi trả cấu trúc không hợp lệ.")

    elapsed = time.perf_counter() - started
    if elapsed >= 2.0:
        raise RuntimeError(f"Smoke test vượt ngưỡng 2 giây: {elapsed:.3f}s")
    print(f"PASS | role={role_id} | roadmap_phases={len(roadmap['phases'])} "
          f"| questions={len(questions)} | elapsed={elapsed:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
