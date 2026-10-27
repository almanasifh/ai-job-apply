from __future__ import annotations

import errno
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_portable
import validate_release
import stage_plugin


class PackagingTests(unittest.TestCase):
    EXPECTED_ROLES = {"scout.md", "matcher.md", "drafter.md", "verifier.md", "tracker.md"}

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
        self.assertIn(b"roles/scout.md", first)
        for role in self.EXPECTED_ROLES:
            self.assertIn(f"roles/{role}".encode(), first)
        self.assertIn(b"claim-ledger.schema.json", first)
        self.assertNotIn(b"C:\\Users\\", first)
        self.assertNotIn(b"](references/", first)
        self.assertIn(b"](#source-references-policy-md)", first)
        self.assertIn(b"](#source-references-roles-scout-md)", first)
        self.assertNotIn(b"](roles/scout.md)", first)
        self.assertIn(b"standalone portable Markdown edition", first)

    def test_portable_source_anchors_must_be_unique(self) -> None:
        first = build_portable.SKILL_ROOT / "references" / "a-b.md"
        second = build_portable.SKILL_ROOT / "references" / "a_b.md"
        with self.assertRaisesRegex(ValueError, "duplicate anchors"):
            build_portable.source_anchors([
                build_portable.SKILL_ROOT / "SKILL.md", first, second
            ])

    def test_portable_builder_excludes_untracked_reference_markdown(self) -> None:
        references = build_portable.SKILL_ROOT / "references"
        with tempfile.NamedTemporaryFile(
            dir=references, suffix=".md", delete=False
        ) as handle:
            path = Path(handle.name)
            handle.write(b"private untracked content\n")
        try:
            self.assertNotIn(path, build_portable.source_files())
            self.assertNotIn(b"private untracked content", build_portable.render())
        finally:
            path.unlink(missing_ok=True)

    def test_codex_agent_adapter_is_valid_and_points_to_canonical_roles(self) -> None:
        agents_root = REPO_ROOT / ".codex" / "agents"
        files = sorted(agents_root.glob("*.toml"))
        self.assertEqual(len(files), 5)
        observed_roles = set()
        for path in files:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                {"name", "description", "developer_instructions", "features"},
                set(data),
            )
            self.assertTrue(data["name"].startswith("job_"))
            self.assertFalse(data["features"]["apps"])
            self.assertFalse(data["features"]["memories"])
            self.assertFalse(data["features"]["request_permissions_tool"])
            role = path.name.removeprefix("job-").removesuffix(".toml") + ".md"
            observed_roles.add(role)
            canonical = (
                REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
                / "references" / "roles" / role
            )
            self.assertTrue(canonical.is_file(), canonical)
            self.assertIn(canonical.relative_to(REPO_ROOT).as_posix(), data["developer_instructions"])
        self.assertEqual(observed_roles, self.EXPECTED_ROLES)
        config = tomllib.loads((REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
        self.assertTrue(config["agents"]["enabled"])
        self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 5)

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

    def test_privacy_scan_rejects_certificate_and_environment_files(self) -> None:
        for filename, expected in (("identity.pfx", "blocked file type"), (".env", "blocked environment file"), (".env.staging", "blocked environment file"), (".envrc", "blocked environment file")):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / filename).write_text("fictional-sensitive-value", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, expected):
                    validate_release.scan_tree(Path(directory))

    def test_ignore_policy_allows_fictional_fixture_locations(self) -> None:
        cases = {
            "data/private.json": True,
            "tests/data/fictional.json": False,
            "tests/fixtures/fictional.pdf": False,
            "evals/fixtures/fictional.csv": False,
            "tests/fixtures/credentials-fixture.json": False,
        }
        for relative_path, expected_ignored in cases.items():
            with self.subTest(relative_path=relative_path):
                completed = subprocess.run(
                    ["git", "check-ignore", "-q", "--no-index", "--", relative_path],
                    cwd=REPO_ROOT,
                    check=False,
                )
                self.assertEqual(completed.returncode == 0, expected_ignored)

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
        with tempfile.TemporaryDirectory() as directory:
            dist_root = Path(directory) / "dist"
            stage_plugin.build(dist_root=dist_root)
            metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
            license_content = (REPO_ROOT / "LICENSE").read_bytes()
            self.assertEqual((dist_root / "portable-plugin" / metadata["name"] / "LICENSE").read_bytes(), license_content)
            self.assertEqual((dist_root / "codex-plugin" / metadata["name"] / "LICENSE").read_bytes(), license_content)
            portable_markdown = dist_root / "portable-plugin" / metadata["name"] / f"{metadata['skill_name']}.md"
            self.assertEqual(portable_markdown.read_bytes(), build_portable.render())
            for package_type in ("portable-plugin", "codex-plugin"):
                staged_skill = dist_root / package_type / metadata["name"] / "skills" / metadata["skill_name"]
                pack = staged_skill / "assets" / "fictional-profile-pack"
                for name in (
                    "answers.json",
                    "claim-ledger.json",
                    "minimized-facts.json",
                    "delegation.json",
                    "delegation-scout.json",
                    "delegation-drafter.json",
                    "delegation-verifier.json",
                    "delegation-tracker.json",
                    "checkpoint-reference.json",
                ):
                    self.assertTrue((pack / name).is_file(), name)
                self.assertEqual(
                    {path.name for path in (staged_skill / "references" / "roles").glob("*.md")},
                    self.EXPECTED_ROLES,
                )
            archives = [
                dist_root / f"{metadata['name']}-portable.zip",
                dist_root / f"{metadata['name']}-codex.zip",
            ]
            first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
            stage_plugin.build(dist_root=dist_root)
            second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in archives]
            self.assertEqual(first, second)
            for index, path in enumerate(archives):
                with zipfile.ZipFile(path) as archive:
                    self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                    self.assertTrue(all(info.date_time == stage_plugin.FIXED_ZIP_TIME for info in archive.infolist()))
                    portable_name = f"{metadata['name']}/{metadata['skill_name']}.md"
                    self.assertEqual(portable_name in archive.namelist(), index == 0)

    def test_staging_excludes_untracked_skill_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            source = repo_root / "skill"
            destination = repo_root / "output"
            source.mkdir()
            tracked = source / "tracked.txt"
            untracked = source / "untracked.txt"
            tracked.write_text("public\n", encoding="utf-8")
            untracked.write_text("private\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
            subprocess.run(["git", "add", "skill/tracked.txt"], cwd=repo_root, check=True)
            stage_plugin.copy_tree(source, destination, repo_root=repo_root)
            self.assertEqual((destination / tracked.name).read_text(encoding="utf-8"), "public\n")
            self.assertFalse((destination / untracked.name).exists())

    def test_staging_rejects_unstaged_tracked_skill_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            source = repo_root / "skill"
            source.mkdir()
            tracked = source / "tracked.txt"
            tracked.write_text("public\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
            subprocess.run(["git", "add", "skill/tracked.txt"], cwd=repo_root, check=True)
            tracked.write_text("private change\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unstaged changes"):
                stage_plugin.tracked_files(source, repo_root=repo_root)

    def test_safe_reset_retries_directory_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dist"
            target = root / "staging"
            target.mkdir(parents=True)
            (target / "old.txt").write_text("old", encoding="utf-8")
            real_rmtree = stage_plugin.shutil.rmtree
            calls = 0

            def flaky_rmtree(path: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise OSError(errno.ENOTEMPTY, "Directory not empty")
                real_rmtree(path)

            with mock.patch.object(stage_plugin.shutil, "rmtree", side_effect=flaky_rmtree):
                stage_plugin.safe_reset(target, root=root, retry_delay=0)
            self.assertEqual(calls, 2)
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

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
