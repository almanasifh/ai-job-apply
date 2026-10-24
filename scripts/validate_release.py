from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import build_portable
import stage_plugin


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
DIST_ROOT = REPO_ROOT / "dist"
BLOCKED_SUFFIXES = {".doc", ".docx", ".pdf", ".pem", ".key", ".p12", ".sqlite", ".sqlite3", ".db"}
BLOCKED_PARTS = {".git", "private", "credentials", "cookies", "sessions", "auth", "secrets"}
SECRET_PATTERNS = {
    "email address": re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "absolute Windows user path": re.compile(rb"[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]"),
    "absolute Unix user path": re.compile(rb"(?:/Users/|/home/)[^/\s]+/"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style secret": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    "Google OAuth token": re.compile(rb"\bya29\.[A-Za-z0-9_-]+"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
}
PORTABLE_MANIFEST_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
PLUGIN_NAME_PATTERN = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def load_json_object(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path} contains duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_nonfinite(value: str) -> None:
        raise ValueError(f"{path} contains unsupported numeric constant: {value}")

    data = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_nonfinite,
    )
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_manifest(path: Path, *, portable: bool, expected_license: str) -> None:
    data = load_json_object(path)
    required = {"name", "version", "description", "author"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path} is missing {sorted(missing)}")
    if portable and data.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError(f"{path} has the wrong portable schema")
    if portable:
        extra = sorted(data.keys() - PORTABLE_MANIFEST_FIELDS)
        if extra:
            raise ValueError(f"{path} has unsupported portable fields: {', '.join(extra)}")
        name = data.get("name")
        if not isinstance(name, str) or not 1 <= len(name) <= 64 or not PLUGIN_NAME_PATTERN.fullmatch(name):
            raise ValueError(f"{path} has an invalid portable plugin name")
        if not isinstance(data.get("version"), str) or not SEMVER_PATTERN.fullmatch(data["version"]):
            raise ValueError(f"{path} version must use semantic versioning")
        author = data.get("author")
        if not isinstance(author, dict) or set(author) - {"name", "email", "url"}:
            raise ValueError(f"{path} has invalid portable author metadata")
        if any(not isinstance(value, str) for value in author.values()):
            raise ValueError(f"{path} portable author fields must be strings")
        keywords = data.get("keywords", [])
        if not isinstance(keywords, list) or any(not isinstance(item, str) for item in keywords):
            raise ValueError(f"{path} keywords must be a string array")
        extensions = data.get("extensions", {})
        if not isinstance(extensions, dict) or any(not isinstance(value, dict) for value in extensions.values()):
            raise ValueError(f"{path} extensions must map namespaces to objects")
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


def validate_zip(path: Path, staged_root: Path) -> None:
    expected_files = {
        f"{staged_root.name}/{source.relative_to(staged_root).as_posix()}": source
        for source in staged_root.rglob("*")
        if source.is_file()
    }
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != sorted(names):
            raise ValueError(f"Archive entries are not sorted: {path}")
        if names != sorted(expected_files):
            missing = sorted(set(expected_files) - set(names))
            unexpected = sorted(set(names) - set(expected_files))
            raise ValueError(f"Archive file set mismatch: {path}; missing={missing}, unexpected={unexpected}")
        if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in archive.infolist()):
            raise ValueError(f"Archive timestamps are not normalized: {path}")
        for name, source in expected_files.items():
            if archive.read(name) != source.read_bytes():
                raise ValueError(f"Archive entry does not match staged content: {path}!{name}")


def validate_license(path: Path, expected: bytes) -> None:
    content = path.read_bytes()
    if content != expected:
        raise ValueError(f"{path} does not match the repository license")
    if not content.splitlines() or content.splitlines()[0] != b"MIT License":
        raise ValueError(f"{path} is not an MIT license")


def validate_staged_skill(path: Path) -> None:
    expected_files = {
        source.relative_to(SKILL_ROOT): source
        for source in stage_plugin.tracked_files(SKILL_ROOT)
    }
    actual_files = {
        source.relative_to(path): source
        for source in path.rglob("*")
        if source.is_file()
    }
    if actual_files.keys() != expected_files.keys():
        missing = sorted(item.as_posix() for item in expected_files.keys() - actual_files.keys())
        unexpected = sorted(item.as_posix() for item in actual_files.keys() - expected_files.keys())
        raise ValueError(f"{path} file set mismatch; missing={missing}, unexpected={unexpected}")
    for relative, source in expected_files.items():
        if actual_files[relative].read_bytes() != source.read_bytes():
            raise ValueError(f"{path / relative} does not match the tracked skill source")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate staged public release artifacts.")
    parser.add_argument("--dist", type=Path, default=DIST_ROOT)
    args = parser.parse_args()
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
    common = load_module("skill_common", SKILL_ROOT / "scripts" / "common.py")
    profile_validator = load_module("profile_validator", SKILL_ROOT / "scripts" / "validate_profile.py")
    answers_validator = load_module("answers_validator", SKILL_ROOT / "scripts" / "validate_answers.py")
    job_validator = load_module("job_validator", SKILL_ROOT / "scripts" / "validate_job.py")
    match_validator = load_module("match_validator", SKILL_ROOT / "scripts" / "validate_match.py")
    application_validator = load_module("application_validator", SKILL_ROOT / "scripts" / "validate_application.py")
    checkpoint_validator = load_module("checkpoint_validator", SKILL_ROOT / "scripts" / "validate_checkpoint.py")
    evaluation_validator = load_module("evaluation_validator", REPO_ROOT / "scripts" / "validate_evals.py")

    metadata = load_json_object(REPO_ROOT / "packaging" / "metadata.json")
    if metadata.get("license") != "MIT":
        raise ValueError("packaging/metadata.json must declare MIT")
    portable = args.dist / "portable-plugin" / metadata["name"]
    codex = args.dist / "codex-plugin" / metadata["name"]
    validate_manifest(portable / "plugin.json", portable=True, expected_license=metadata["license"])
    validate_manifest(codex / ".codex-plugin" / "plugin.json", portable=False, expected_license=metadata["license"])
    portable_manifest = load_json_object(portable / "plugin.json")
    codex_manifest = load_json_object(codex / ".codex-plugin" / "plugin.json")
    for manifest_path, manifest in (
        (portable / "plugin.json", portable_manifest),
        (codex / ".codex-plugin" / "plugin.json", codex_manifest),
    ):
        for field in ("name", "version", "description", "license"):
            if manifest.get(field) != metadata[field]:
                raise ValueError(f"{manifest_path} {field} does not match packaging/metadata.json")
        if manifest.get("author", {}).get("name") != metadata["author"]:
            raise ValueError(f"{manifest_path} author does not match packaging/metadata.json")
    license_content = (REPO_ROOT / "LICENSE").read_bytes()
    validate_license(portable / "LICENSE", license_content)
    validate_license(codex / "LICENSE", license_content)
    portable_markdown = portable / f"{metadata['skill_name']}.md"
    if portable_markdown.read_bytes() != build_portable.render():
        raise ValueError(f"{portable_markdown} does not match the canonical portable Markdown build")
    portable_skill = portable / "skills" / metadata["skill_name"]
    codex_skill = codex / "skills" / metadata["skill_name"]
    validate_staged_skill(portable_skill)
    validate_staged_skill(codex_skill)
    scan_tree(portable)
    scan_tree(codex)
    validate_zip(args.dist / f"{metadata['name']}-portable.zip", portable)
    validate_zip(args.dist / f"{metadata['name']}-codex.zip", codex)

    for skill in (portable_skill, codex_skill):
        assets = skill / "assets" / "fictional-profile-pack"
        profile = common.load_json(assets / "profile.json")
        job = common.load_json(assets / "job.json")
        profile_validator.validate_profile(profile)
        answers_validator.validate_answers(common.load_json(assets / "answers.json"))
        job_validator.validate_job(job)
        match_validator.validate_match(common.load_json(assets / "match.json"), job, profile)
        validated = application_validator.validate_application(common.load_json(assets / "application.json"), assets)
        application_validator.validate_authorization(
            common.load_json(assets / "authorization.json"),
            validated,
            common.parse_datetime("2099-01-01T00:05:00Z", "fixture time"),
        )
        checkpoint_validator.validate_checkpoint(checkpoint_validator.load_events(assets / "checkpoint.jsonl"))
    evaluation_validator.validate_catalog(
        evaluation_validator.load_catalog(REPO_ROOT / "evals" / "behavioral-scenarios.json"),
        repo_root=REPO_ROOT,
    )
    print("VALID: staged release, manifests, archives, all fixtures, hash chains, and evaluation catalog")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
