from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_portable
import stage_plugin


class PackagingTests(unittest.TestCase):
    def test_portable_markdown_is_reproducible(self) -> None:
        first = build_portable.render()
        second = build_portable.render()
        self.assertEqual(first, second)
        self.assertIn(b"Portable Skill", first)
        self.assertNotIn(b"C:\\Users\\", first)

    def test_portable_manifest_uses_standard_schema(self) -> None:
        manifest = json.loads((REPO_ROOT / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")

    def test_staged_archives_are_reproducible(self) -> None:
        stage_plugin.build()
        metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
        archives = [
            REPO_ROOT / "dist" / f"{metadata['name']}-portable.zip",
            REPO_ROOT / "dist" / f"{metadata['name']}-codex.zip",
        ]
        first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
        stage_plugin.build()
        second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
        self.assertEqual(first, second)
        for path in archives:
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                self.assertTrue(all(info.date_time == stage_plugin.FIXED_ZIP_TIME for info in archive.infolist()))

    def test_cli_build_writes_requested_portable_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "portable.md"
            completed = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "build_portable.py"), "--output", str(output)],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(output.read_bytes(), build_portable.render())


if __name__ == "__main__":
    unittest.main()
