"""A local candidate must be reproducible and omit private or generated files."""

import hashlib
import tarfile
import zipfile

from scripts.build_release import build


def test_candidate_archives_are_versioned_deterministic_and_private_data_free(tmp_path):
    first = build(output=tmp_path)
    second = build(output=tmp_path)
    assert first["sha256"] == second["sha256"]
    assert first["root_directory"].startswith("ai-career-coach-0.4.0-candidate")

    zip_path = tmp_path / f"{first['root_directory']}.zip"
    tar_path = tmp_path / f"{first['root_directory']}.tar.gz"
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = set(archive.namelist())
        manifest = archive.read(f"{first['root_directory']}/MANIFEST.sha256").decode()
        assert f"{first['root_directory']}/app.py" in zip_names
        assert f"{first['root_directory']}/Data/roles.json" in zip_names
        assert f"{first['root_directory']}/requirements.lock" in zip_names
        assert f"{first['root_directory']}/.github/workflows/ci.yml" in zip_names
        assert all(name.startswith(first["root_directory"] + "/") for name in zip_names)
        assert not any("cv_data_engineering" in name or "secrets.toml" in name or ".venv" in name for name in zip_names)
        for line in manifest.splitlines():
            digest, name = line.split("  ", 1)
            assert hashlib.sha256(archive.read(f"{first['root_directory']}/{name}")).hexdigest() == digest
    with tarfile.open(tar_path, "r:gz") as archive:
        assert set(archive.getnames()) == zip_names
