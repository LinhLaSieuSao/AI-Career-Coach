"""Apply only independently opened demo source pages; default is dry run."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.migrate_evidence_schema_v2 import _format_json

TARGET = ROOT / "Data/resources.json"
MANIFEST = ROOT / "docs/reviews/demo-resource-page-checks-2026-10-26.json"
BACKUPS = ROOT / "dist/data-backups/step4-demo-resources"
PREVIOUS_URLS = {
    "typescript_handbook": "https://www.typescriptlang.org/docs/handbook/",
    "git_001": "https://git-scm.com/doc",
    "docker_001": "https://docs.docker.com/get-started/",
    "tableau_001": "https://www.tableau.com/learn/training",
    "openstax_introductory_statistics_2e": "https://openstax.org/books/introductory-statistics-2e/pages/1-introduction",
    "ban_hang_dot03_en": "https://learn.microsoft.com/vi-vn/training/modules/manage-opportunities-dynamics-365-sales/",
    "css_dot03_vi": "https://learn.microsoft.com/vi-vn/training/modules/use-css-styles/",
}


def apply_checks(target: Path = TARGET, *, manifest: Path = MANIFEST,
                 apply: bool = False, backup_dir: Path = BACKUPS) -> dict:
    original = target.read_bytes()
    data = json.loads(original.decode("utf-8"))
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    indexed = {}
    for skill, group in data.items():
        for record in group["resources"]:
            if record["id"] in indexed:
                raise ValueError(f"Duplicate resource ID: {record['id']}")
            indexed[record["id"]] = (skill, record)
    changed = []
    for entry in spec["records"]:
        rid = entry["id"]
        if rid not in indexed:
            raise ValueError(f"Unknown resource ID: {rid}")
        _, record = indexed[rid]
        old_url = PREVIOUS_URLS.get(rid, entry["source_url"])
        if record.get("url") not in {old_url, entry["source_url"]}:
            raise ValueError(f"Refusing unexpected URL for {rid}")
        expected = deepcopy(record)
        expected["url"] = entry["source_url"]
        expected["scope_granularity"] = entry["scope"]
        expected["evidence_locator"] = entry["locator"]
        expected["last_checked"] = spec["checked_at"]
        expected["verification_origin"] = "independent_public_page_read_2026-10-26"
        expected["verification_axes"]["access_status"] = "independently_accessible"
        expected["verification_axes"]["last_live_checked"] = spec["checked_at"]
        expected["provenance"]["source_url"] = entry["source_url"]
        if "language" in entry:
            expected["language"] = entry["language"]
        if "title" in entry:
            expected["title"] = entry["title"]
        if "level_to" in entry:
            if type(record.get("level_to")) is not int or entry["level_to"] > record["level_to"]:
                raise ValueError(f"Step 4 cannot broaden level range for {rid}")
            expected["level_to"] = entry["level_to"]
        if "duration_hours" in entry:
            expected["duration_hours"] = entry["duration_hours"]
            expected["duration_source"] = entry["source_url"]
            expected["duration_basis"] = "Thời lượng tutorial được nguồn công bố (15 phút)."
            expected["duration_checked_at"] = spec["checked_at"]
        if record == expected:
            continue
        # On reruns, only the exact generated state is accepted. For the
        # initial run, a preexisting granular record may already be present.
        if record.get("verification_origin") == "independent_public_page_read_2026-10-26":
            legacy_duration = deepcopy(expected)
            legacy_duration.pop("duration_checked_at", None)
            legacy_locale = deepcopy(expected)
            if rid == "css_dot03_vi":
                legacy_locale["language"] = "vi"
                legacy_locale["title"] = "Sử dụng kiểu CSS trong trang web"
            if record not in (legacy_duration, legacy_locale):
                raise ValueError(f"Refusing to overwrite edited check: {rid}")
        record.clear()
        record.update(expected)
        changed.append(rid)
    result = {"mode": "apply" if apply else "dry_run", "records_changed": len(changed),
              "ids": changed, "source_sha256": hashlib.sha256(original).hexdigest()}
    if not apply or not changed:
        return result
    backup = backup_dir / result["source_sha256"] / target.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    if backup.exists() and backup.read_bytes() != original:
        raise ValueError("Existing backup differs from current source")
    if not backup.exists():
        backup.write_bytes(original)
    if backup.read_bytes() != original or target.read_bytes() != original:
        raise ValueError("Source changed or backup failed")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            output.write(_format_json(data).encode("utf-8") + b"\n")
        temporary.replace(target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    result["backup"] = str(backup)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply_checks(apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
