from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = REPO_ROOT / "dist"
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def safe_reset(path: Path) -> None:
    resolved_dist = DIST_ROOT.resolve()
    resolved = path.resolve()
    if resolved == resolved_dist or resolved_dist not in resolved.parents:
        raise ValueError(f"Refusing to reset path outside dist: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def tracked_files(source: Path) -> list[Path]:
    relative_source = source.relative_to(REPO_ROOT).as_posix()
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{relative_source}/"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    files = [REPO_ROOT / relative for relative in completed.stdout.split("\0") if relative]
    if not files:
        raise ValueError(f"No tracked files found under {source}")
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def copy_tree(source: Path, destination: Path) -> None:
    for path in tracked_files(source):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_symlink():
            raise ValueError(f"Refusing to package symlink: {path}")
        if not path.is_file():
            raise ValueError(f"Tracked skill path is not a file: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def create_zip(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted((item for item in source.rglob("*") if item.is_file()), key=lambda item: item.relative_to(source.parent).as_posix()):
            relative = path.relative_to(source.parent).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build() -> list[Path]:
    metadata = json.loads((REPO_ROOT / "packaging" / "metadata.json").read_text(encoding="utf-8"))
    portable_root = DIST_ROOT / "portable-plugin" / metadata["name"]
    codex_root = DIST_ROOT / "codex-plugin" / metadata["name"]
    safe_reset(portable_root)
    safe_reset(codex_root)

    portable_manifest = json.loads((REPO_ROOT / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
    codex_manifest = json.loads((REPO_ROOT / "packaging" / "codex-plugin-template" / metadata["name"] / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if portable_manifest["version"] != metadata["version"] or codex_manifest["version"] != metadata["version"]:
        raise ValueError("Manifest versions must match packaging/metadata.json")
    if portable_manifest.get("license") != metadata["license"] or codex_manifest.get("license") != metadata["license"]:
        raise ValueError("Manifest licenses must match packaging/metadata.json")

    write_json(portable_root / "plugin.json", portable_manifest)
    write_json(codex_root / ".codex-plugin" / "plugin.json", codex_manifest)
    copy_tree(SKILL_ROOT, portable_root / "skills" / metadata["skill_name"])
    copy_tree(SKILL_ROOT, codex_root / "skills" / metadata["skill_name"])
    shutil.copyfile(REPO_ROOT / "LICENSE", portable_root / "LICENSE")
    shutil.copyfile(REPO_ROOT / "LICENSE", codex_root / "LICENSE")

    portable_zip = DIST_ROOT / f"{metadata['name']}-portable.zip"
    codex_zip = DIST_ROOT / f"{metadata['name']}-codex.zip"
    create_zip(portable_root, portable_zip)
    create_zip(codex_root, codex_zip)
    return [portable_root, codex_root, portable_zip, codex_zip]


def main() -> int:
    argparse.ArgumentParser(description="Stage deterministic portable and Codex plugin packages.").parse_args()
    for path in build():
        print(f"BUILT: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
