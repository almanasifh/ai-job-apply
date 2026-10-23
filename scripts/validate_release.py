from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
ASSETS = SKILL_ROOT / "assets" / "fictional-profile-pack"
DIST_ROOT = REPO_ROOT / "dist"
BLOCKED_SUFFIXES = {".doc", ".docx", ".pdf", ".pem", ".key", ".p12", ".sqlite", ".sqlite3", ".db"}
BLOCKED_PARTS = {"private", "credentials", "cookies", "sessions", "auth"}
SECRET_PATTERNS = {
    "absolute Windows user path": re.compile(rb"[A-Za-z]:\\Users\\[^\\\s]+\\"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style secret": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "Google OAuth token": re.compile(rb"\bya29\.[A-Za-z0-9_-]+"),
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_manifest(path: Path, *, portable: bool, expected_license: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"name", "version", "description", "author"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path} is missing {sorted(missing)}")
    if portable and data.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError(f"{path} has the wrong portable schema")
    if data.get("license") != expected_license:
        raise ValueError(f"{path} does not declare {expected_license}")
    if not portable and "interface" not in data:
        raise ValueError(f"{path} is missing interface metadata")
    if "TODO" in path.read_text(encoding="utf-8"):
        raise ValueError(f"{path} contains TODO metadata")


def scan_tree(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Release contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        lower_parts = {part.lower() for part in relative.parts}
        if lower_parts & BLOCKED_PARTS:
            raise ValueError(f"Release contains a blocked path: {relative}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            raise ValueError(f"Release contains a blocked file type: {relative}")
        content = path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                raise ValueError(f"Release contains {label}: {relative}")


def validate_zip(path: Path, expected_prefix: str) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != sorted(names):
            raise ValueError(f"Archive entries are not sorted: {path}")
        if not names or any(not name.startswith(expected_prefix + "/") for name in names):
            raise ValueError(f"Archive has an unexpected root: {path}")
        if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in archive.infolist()):
            raise ValueError(f"Archive timestamps are not normalized: {path}")


def validate_license(path: Path, expected: bytes) -> None:
    content = path.read_bytes()
    if content != expected:
        raise ValueError(f"{path} does not match the repository license")
    if not content.splitlines() or content.splitlines()[0] != b"MIT License":
        raise ValueError(f"{path} is not an MIT license")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate staged public release artifacts.")
    parser.add_argument("--dist", type=Path, default=DIST_ROOT)
    args = parser.parse_args()
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
    common = load_module("skill_common", SKILL_ROOT / "scripts" / "common.py")
    profile_validator = load_module("profile_validator", SKILL_ROOT / "scripts" / "validate_profile.py")
    application_validator = load_module("application_validator", SKILL_ROOT / "scripts" / "validate_application.py")
    checkpoint_validator = load_module("checkpoint_validator", SKILL_ROOT / "scripts" / "validate_checkpoint.py")
    evaluation_validator = load_module("evaluation_validator", REPO_ROOT / "scripts" / "validate_evals.py")

    metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("license") != "MIT":
        raise ValueError("packaging/metadata.json must declare MIT")
    portable = args.dist / "portable-plugin" / metadata["name"]
    codex = args.dist / "codex-plugin" / metadata["name"]
    validate_manifest(portable / "plugin.json", portable=True, expected_license=metadata["license"])
    validate_manifest(codex / ".codex-plugin" / "plugin.json", portable=False, expected_license=metadata["license"])
    license_content = (REPO_ROOT / "LICENSE").read_bytes()
    validate_license(portable / "LICENSE", license_content)
    validate_license(codex / "LICENSE", license_content)
    scan_tree(portable)
    scan_tree(codex)
    validate_zip(args.dist / f"{metadata['name']}-portable.zip", metadata["name"])
    validate_zip(args.dist / f"{metadata['name']}-codex.zip", metadata["name"])

    profile_validator.validate_profile(common.load_json(ASSETS / "profile.json"))
    validated = application_validator.validate_application(common.load_json(ASSETS / "application.json"), ASSETS)
    application_validator.validate_authorization(
        common.load_json(ASSETS / "authorization.json"),
        validated,
        common.parse_datetime("2099-01-01T00:05:00Z", "fixture time"),
    )
    checkpoint_validator.validate_checkpoint(checkpoint_validator.load_events(ASSETS / "checkpoint.jsonl"))
    evaluation_validator.validate_catalog(
        evaluation_validator.load_catalog(REPO_ROOT / "evals" / "behavioral-scenarios.json"),
        repo_root=REPO_ROOT,
    )
    print("VALID: staged release, manifests, archives, fixtures, hash chains, and evaluation catalog")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
