"""Apply the three curated Step 2 drafts; default is a read-only dry run."""

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

TARGET = ROOT / "Data/interview_question/part_06_sales_customer_ecommerce.json"
MANIFEST = ROOT / "docs/reviews/sales-template-rewrite-step2.json"
BACKUPS = ROOT / "dist/data-backups/step2-sales"


def rewrite(target: Path = TARGET, *, manifest: Path = MANIFEST,
            apply: bool = False, backup_dir: Path = BACKUPS) -> dict:
    original = target.read_bytes()
    bank = json.loads(original.decode("utf-8"))
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    records = bank["roles"][spec["role_id"]]
    changed = []
    for entry in spec["records"]:
        matches = [record for record in records if record["id"] == entry["id"]]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one record: {entry['id']}")
        record = matches[0]
        updates = entry["changes"]
        if any(key in updates for key in ("id", "skill", "level", "weight")):
            raise ValueError("Step 2 must preserve question identity, skill, Level and weight")
        if all(record.get(key) == value for key, value in updates.items()):
            continue
        mismatches = [key for key, value in entry["expected"].items() if record.get(key) != value]
        if mismatches:
            raise ValueError(f"Refusing to overwrite changed record {entry['id']}: {mismatches}")
        if updates.get("quality") != "unreviewed" or updates.get("quality_reviewer") is not None or updates.get("quality_reviewed_at") is not None:
            raise ValueError("AI drafts must remain unreviewed with no human reviewer/date")
        record.update(deepcopy(updates))
        changed.append(entry["id"])

    digest = hashlib.sha256(original).hexdigest()
    result = {"mode": "apply" if apply else "dry_run", "records_changed": len(changed),
              "ids": changed, "source_sha256": digest, "backup": None}
    if not apply or not changed:
        return result
    backup = backup_dir / digest / target.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    if backup.exists() and backup.read_bytes() != original:
        raise ValueError("Existing backup differs from the source; refusing overwrite")
    if not backup.exists():
        with backup.open("xb") as output:
            output.write(original)
    if backup.read_bytes() != original:
        raise ValueError("Backup verification failed")
    if target.read_bytes() != original:
        raise ValueError("Source changed after reading; refusing overwrite")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=target.parent, suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            output.write(_format_json(bank) + "\n")
        temporary.replace(target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    result["backup"] = str(backup)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(rewrite(apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
