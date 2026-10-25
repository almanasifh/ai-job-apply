from __future__ import annotations

import argparse
import errno
import json
import shutil
import stat
import subprocess
import time
import zipfile
from pathlib import Path

import build_portable


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = REPO_ROOT / "dist"
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}


def safe_reset(path: Path, *, root: Path = DIST_ROOT, attempts: int = 5, retry_delay: float = 0.05) -> None:
    resolved_dist = root.resolve()
    resolved = path.resolve()
    if resolved == resolved_dist or resolved_dist not in resolved.parents:
        raise ValueError(f"Refusing to reset path outside dist: {resolved}")
    for attempt in range(attempts):
        if not resolved.exists():
            break
        try:
            shutil.rmtree(resolved)
            break
        except OSError as exc:
            if exc.errno != errno.ENOTEMPTY or attempt == attempts - 1:
                raise
            time.sleep(retry_delay * (attempt + 1))
    resolved.mkdir(parents=True, exist_ok=True)


def tracked_files(source: Path, *, repo_root: Path = REPO_ROOT) -> list[Path]:
    relative_source = source.resolve().relative_to(repo_root.resolve()).as_posix()
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{relative_source}/"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    files = [repo_root / relative for relative in completed.stdout.split("\0") if relative]
    if not files:
        raise ValueError(f"No tracked files found under {source}")
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def package_bytes(path: Path) -> bytes:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8").encode("utf-8")
    return path.read_bytes()


def copy_tree(source: Path, destination: Path, *, repo_root: Path = REPO_ROOT) -> None:
    for path in tracked_files(source, repo_root=repo_root):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_symlink():
            raise ValueError(f"Refusing to package symlink: {path}")
        if not path.is_file():
            raise ValueError(f"Tracked skill path is not a file: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package_bytes(path))


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


def build(*, dist_root: Path = DIST_ROOT, repo_root: Path = REPO_ROOT, skill_root: Path = SKILL_ROOT) -> list[Path]:
    metadata = json.loads((repo_root / "packaging" / "metadata.json").read_text(encoding="utf-8"))
    portable_root = dist_root / "portable-plugin" / metadata["name"]
    codex_root = dist_root / "codex-plugin" / metadata["name"]
    safe_reset(portable_root, root=dist_root)
    safe_reset(codex_root, root=dist_root)

    portable_manifest = json.loads((repo_root / "packaging" / "portable" / "plugin.json").read_text(encoding="utf-8"))
    codex_manifest = json.loads((repo_root / "packaging" / "codex-plugin-template" / metadata["name"] / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if portable_manifest["version"] != metadata["version"] or codex_manifest["version"] != metadata["version"]:
        raise ValueError("Manifest versions must match packaging/metadata.json")
    if portable_manifest.get("license") != metadata["license"] or codex_manifest.get("license") != metadata["license"]:
        raise ValueError("Manifest licenses must match packaging/metadata.json")

    write_json(portable_root / "plugin.json", portable_manifest)
    write_json(codex_root / ".codex-plugin" / "plugin.json", codex_manifest)
    (portable_root / f"{metadata['skill_name']}.md").write_bytes(build_portable.render())
    copy_tree(skill_root, portable_root / "skills" / metadata["skill_name"], repo_root=repo_root)
    copy_tree(skill_root, codex_root / "skills" / metadata["skill_name"], repo_root=repo_root)
    shutil.copyfile(repo_root / "LICENSE", portable_root / "LICENSE")
    shutil.copyfile(repo_root / "LICENSE", codex_root / "LICENSE")

    portable_zip = dist_root / f"{metadata['name']}-portable.zip"
    codex_zip = dist_root / f"{metadata['name']}-codex.zip"
    create_zip(portable_root, portable_zip)
    create_zip(codex_root, codex_zip)
    return [portable_root, codex_root, portable_zip, codex_zip]


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage deterministic portable and Codex plugin packages.")
    parser.add_argument("--dist", type=Path, default=DIST_ROOT)
    args = parser.parse_args()
    for path in build(dist_root=args.dist):
        print(f"BUILT: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
