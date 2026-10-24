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
import validate_release
import stage_plugin


class PackagingTests(unittest.TestCase):
    def test_packaged_text_uses_lf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.yaml"
            path.write_bytes(b"first\r\nsecond\r\n")
            self.assertEqual(stage_plugin.package_bytes(path), b"first\nsecond\n")

    def test_mit_license_validation_accepts_windows_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            license_path = Path(directory) / "LICENSE"
            content = b"MIT License\r\n\r\nPermission is hereby granted\r\n"
            license_path.write_bytes(content)
            validate_release.validate_license(license_path, content)

    def test_portable_markdown_is_reproducible(self) -> None:
        first = build_portable.render()
        second = build_portable.render()
        self.assertEqual(first, second)
        self.assertIn(b"Portable Skill", first)
        self.assertIn(b"application-review.template.md", first)
        self.assertIn(b"manual-handoff.template.md", first)
        self.assertNotIn(b"C:\\Users\\", first)
        self.assertNotIn(b"](references/", first)
        self.assertIn(b"](#source-references-policy-md)", first)
        self.assertIn(b"standalone portable Markdown edition", first)

    def test_portable_manifest_uses_standard_schema(self) -> None:
        manifest = json.loads((REPO_ROOT / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")

    def test_portable_manifest_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            manifest = json.loads((REPO_ROOT / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
            manifest["unknown"] = True
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported portable fields"):
                validate_release.validate_manifest(path, portable=True, expected_license="MIT")

    def test_manifest_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text('{"name":"first","name":"second"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                validate_release.load_json_object(path)

    def test_manifest_rejects_nonfinite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text('{"unsupported":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported numeric constant"):
                validate_release.load_json_object(path)

    def test_privacy_scan_rejects_email_and_unix_user_path(self) -> None:
        for content, expected in (
            ("person@example.com", "email address"),
            ("/home/private-user/profile.json", "absolute Unix user path"),
        ):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "leak.txt"
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, expected):
                    validate_release.scan_tree(Path(directory))

    def test_release_metadata_uses_mit_license(self) -> None:
        metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
        portable_manifest = json.loads((REPO_ROOT / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
        codex_manifest = json.loads((REPO_ROOT / "packaging" / "codex-plugin-template" / metadata["name"] / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        license_content = (REPO_ROOT / "LICENSE").read_bytes()
        self.assertEqual(metadata["license"], "MIT")
        self.assertEqual(portable_manifest["license"], metadata["license"])
        self.assertEqual(codex_manifest["license"], metadata["license"])
        self.assertEqual(license_content.splitlines()[0], b"MIT License")

    def test_staged_archives_are_reproducible(self) -> None:
        stage_plugin.build()
        metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
        license_content = (REPO_ROOT / "LICENSE").read_bytes()
        self.assertEqual((REPO_ROOT / "dist" / "portable-plugin" / metadata["name"] / "LICENSE").read_bytes(), license_content)
        self.assertEqual((REPO_ROOT / "dist" / "codex-plugin" / metadata["name"] / "LICENSE").read_bytes(), license_content)
        portable_markdown = REPO_ROOT / "dist" / "portable-plugin" / metadata["name"] / f"{metadata['skill_name']}.md"
        self.assertEqual(portable_markdown.read_bytes(), build_portable.render())
        for package_type in ("portable-plugin", "codex-plugin"):
            staged_skill = REPO_ROOT / "dist" / package_type / metadata["name"] / "skills" / metadata["skill_name"]
            self.assertTrue((staged_skill / "assets" / "fictional-profile-pack" / "answers.json").is_file())
        archives = [
            REPO_ROOT / "dist" / f"{metadata['name']}-portable.zip",
            REPO_ROOT / "dist" / f"{metadata['name']}-codex.zip",
        ]
        first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
        stage_plugin.build()
        second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
        self.assertEqual(first, second)
        for index, path in enumerate(archives):
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                self.assertTrue(all(info.date_time == stage_plugin.FIXED_ZIP_TIME for info in archive.infolist()))
                portable_name = f"{metadata['name']}/{metadata['skill_name']}.md"
                self.assertEqual(portable_name in archive.namelist(), index == 0)

    def test_staging_excludes_untracked_skill_files(self) -> None:
        metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
        local_file = stage_plugin.SKILL_ROOT / "assets" / "fictional-profile-pack" / "untracked-local-test.json"
        self.assertFalse(local_file.exists())
        try:
            local_file.write_text('{"private": "must not be packaged"}\n', encoding="utf-8")
            self.assertNotIn(b"must not be packaged", build_portable.render())
            stage_plugin.build()
            for package_type in ("portable-plugin", "codex-plugin"):
                staged_skill = REPO_ROOT / "dist" / package_type / metadata["name"] / "skills" / metadata["skill_name"]
                self.assertFalse((staged_skill / "assets" / "fictional-profile-pack" / local_file.name).exists())
        finally:
            local_file.unlink(missing_ok=True)

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
