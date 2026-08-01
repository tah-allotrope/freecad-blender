#!/usr/bin/env python3
"""Keep the two homedesign skill copies in sync.

The authoritative skill lives at `.claude/skills/homedesign/SKILL.md`; the
`.agents/skills/homedesign/SKILL.md` copy exists for agents that look there.
This script copies one to the other, or with `--check` verifies they match
and exits non-zero when they differ (used in CI).
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY = REPO_ROOT / ".claude" / "skills" / "homedesign" / "SKILL.md"
MIRROR = REPO_ROOT / ".agents" / "skills" / "homedesign" / "SKILL.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the copies match; exit 1 if they differ")
    args = parser.parse_args()

    if not PRIMARY.exists():
        print(f"error: primary skill not found: {PRIMARY}", file=sys.stderr)
        return 1

    if args.check:
        if not MIRROR.exists():
            print(f"error: mirror skill missing: {MIRROR}", file=sys.stderr)
            return 1
        a = PRIMARY.read_text(encoding="utf-8")
        b = MIRROR.read_text(encoding="utf-8")
        if a == b:
            print("ok: skill copies match")
            return 0
        diff = "\n".join(difflib.unified_diff(
            b.splitlines(), a.splitlines(),
            fromfile=str(MIRROR), tofile=str(PRIMARY), lineterm=""))
        print(f"error: skill copies differ:\n{diff}", file=sys.stderr)
        return 1

    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    MIRROR.write_text(PRIMARY.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"copied {PRIMARY.name} -> {MIRROR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
