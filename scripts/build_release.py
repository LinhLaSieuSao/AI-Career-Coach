"""Build deterministic local source candidates without publishing them.

The allowlist deliberately omits personal CV directories, logs, secrets and
build caches. A candidate is not a cleared public release: data rights and
content review require an owner decision before publication.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    ".dockerignore", ".gitignore", "CHANGELOG.md", "CONTRIBUTING.md",
    "Dockerfile", "LICENSE", "LICENSES.md", "README.md", "app.py",
    "pyproject.toml", "requirements.txt", "requirements.lock",
    "requirements-dev.txt", "requirements-dev.lock",
}
ALLOWED_DIR_EXTENSIONS = {
    "modules": {".py"},
    "scripts": {".py"},
    "tests": {".py", ".json"},
    "browser_tests": {".py"},
    "Data": {".json"},
    "docs": {".md", ".json"},
    "assets": {".css", ".svg"},
    ".streamlit": {".toml"},
    ".github": {".yml", ".yaml"},
}
EXCLUDED_PARTS = {
    "__pycache__", "cv_data_engineering", "dist", "build", ".pytest_cache",
    ".uv-cache", ".playwright-browsers", ".venv", "venv", "secrets.toml",
}
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_SOURCE_BYTES = 100 * 1024 * 1024


def selected_sources(root: Path = ROOT) -> dict[str, bytes]:
    """Select only reviewed source locations; reject symlinks and large files."""
    selected: dict[str, bytes] = {}
    candidates = [root / name for name in ROOT_FILES]
    for directory in ALLOWED_DIR_EXTENSIONS:
        if (root / directory).is_dir():
            candidates.extend((root / directory).rglob("*"))
    for path in sorted(candidates):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        parts = rel.parts
        if any(part in EXCLUDED_PARTS for part in parts) or path.is_symlink():
            continue
        if len(parts) == 1:
            permitted = parts[0] in ROOT_FILES
        else:
            permitted = parts[0] in ALLOWED_DIR_EXTENSIONS and path.suffix in ALLOWED_DIR_EXTENSIONS[parts[0]]
            if parts[0] == ".streamlit":
                permitted = permitted and rel.as_posix() == ".streamlit/config.toml"
            if parts[0] == ".github":
                permitted = permitted and len(parts) == 3 and parts[1] == "workflows"
        if not permitted:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Source file too large for candidate: {rel}")
        selected[rel.as_posix()] = path.read_bytes()
    missing = sorted(ROOT_FILES - selected.keys())
    if missing:
        raise ValueError(f"Required source files missing: {missing}")
    if sum(map(len, selected.values())) > MAX_SOURCE_BYTES:
        raise ValueError("Selected source exceeds 100 MiB")
    return selected


def bundle_files(root: Path = ROOT, *, suffix: str = "candidate") -> tuple[str, dict[str, bytes]]:
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if not version or any(char not in "0123456789." for char in version):
        raise ValueError("Expected a numeric dotted project version")
    if suffix and (not suffix.isascii() or not suffix.replace("-", "").isalnum()):
        raise ValueError("Suffix must contain only ASCII letters, digits and hyphens")
    folder = f"ai-career-coach-{version}" + (f"-{suffix}" if suffix else "")
    sources = selected_sources(root)
    manifest = "".join(
        f"{hashlib.sha256(content).hexdigest()}  {name}\n"
        for name, content in sorted(sources.items())
    ).encode("utf-8")
    return folder, {**sources, "MANIFEST.sha256": manifest}


def build(root: Path = ROOT, output: Path | None = None, *, suffix: str = "candidate") -> dict:
    folder, files = bundle_files(root, suffix=suffix)
    target = output or root / "dist"
    target.mkdir(parents=True, exist_ok=True)
    zip_path = target / f"{folder}.zip"
    tar_path = target / f"{folder}.tar.gz"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            item = zipfile.ZipInfo(f"{folder}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o644 << 16
            archive.writestr(item, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with tar_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name, content in sorted(files.items()):
                    item = tarfile.TarInfo(f"{folder}/{name}")
                    item.size = len(content)
                    item.mode = 0o644
                    item.mtime = item.uid = item.gid = 0
                    archive.addfile(item, io.BytesIO(content))
    checksums = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (zip_path, tar_path)
    }
    (target / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checksums.items())),
        encoding="utf-8",
    )
    return {"root_directory": folder, "files": len(files), "archive_bytes": {
        path.name: path.stat().st_size for path in (zip_path, tar_path)
    }, "sha256": checksums, "output": str(target)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--suffix", default="candidate")
    args = parser.parse_args()
    print(json.dumps(build(output=args.output, suffix=args.suffix), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
