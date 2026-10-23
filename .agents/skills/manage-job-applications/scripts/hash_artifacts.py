from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import ValidationError, file_digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash final artifact bytes with SHA-256.")
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for path in args.artifacts:
            byte_count, digest = file_digest(path)
            print(json.dumps({"path": str(path), "byte_count": byte_count, "sha256": digest}, sort_keys=True))
    except (OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
