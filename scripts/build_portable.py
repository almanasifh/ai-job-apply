from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "portable" / "manage-job-applications.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip() + "\n"


def skill_body(text: str) -> str:
    match = re.match(r"\A---\n.*?\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")
    return text[match.end():].strip()


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


def source_files() -> list[Path]:
    tracked = set(tracked_files(SKILL_ROOT))
    files = [SKILL_ROOT / "SKILL.md"]
    files.extend(sorted((path for path in (SKILL_ROOT / "references").glob("*.md") if path in tracked), key=lambda path: path.name))
    files.extend(sorted((path for path in (SKILL_ROOT / "references").glob("*.schema.json") if path in tracked), key=lambda path: path.name))
    files.extend(sorted((path for path in (SKILL_ROOT / "assets" / "fictional-profile-pack").glob("*.json*") if path in tracked), key=lambda path: path.name))
    files.extend(sorted((path for path in (SKILL_ROOT / "assets" / "fictional-profile-pack").glob("*.txt") if path in tracked), key=lambda path: path.name))
    files.extend(
        sorted(
            (path for path in (SKILL_ROOT / "assets" / "templates").rglob("*") if path.is_file() and path in tracked),
            key=lambda path: path.relative_to(SKILL_ROOT).as_posix(),
        )
    )
    if files[0] not in tracked:
        raise ValueError("Canonical SKILL.md is not tracked")
    return files


def render() -> bytes:
    metadata = json.loads(read_text(REPO_ROOT / "packaging" / "metadata.json"))
    files = source_files()
    source_digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        source_digest.update(relative.encode("utf-8") + b"\0")
        source_digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")

    sections = [
        "# Job Application Manager — Portable Skill",
        "",
        f"Version: `{metadata['version']}`  ",
        f"License: `{metadata['license']}`  ",
        f"Source digest: `{source_digest.hexdigest()}`",
        "",
        "This generated file is a self-contained, non-executable edition of the canonical repository skill. It uses fictional examples only. Keep private profiles and credentials outside this file.",
        "",
        skill_body(read_text(SKILL_ROOT / "SKILL.md")),
    ]

    for path in files[1:]:
        relative = path.relative_to(SKILL_ROOT).as_posix()
        content = read_text(path).strip()
        sections.extend(["", "---", "", f"## Embedded Source: `{relative}`", ""])
        if path.suffix == ".md":
            sections.append(content)
        else:
            language = "json" if ".json" in path.name else "text"
            sections.extend([f"```{language}", content, "```"])

    return ("\n".join(sections).rstrip() + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic portable Markdown skill.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render())
    print(f"BUILT: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
