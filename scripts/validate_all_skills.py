#!/usr/bin/env python3
"""Batch validator for Hermes skills."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.skills_validation import find_skill_dirs, validate_skill_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all Hermes skills under a root directory.")
    parser.add_argument("skills_root", help="Root directory to scan recursively for SKILL.md files")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print machine-readable JSON output")
    args = parser.parse_args()

    skills_root = Path(args.skills_root).expanduser()

    try:
        skill_dirs = find_skill_dirs(skills_root)
    except Exception as exc:
        if args.json_output:
            print(json.dumps({"root": str(skills_root), "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 1

    if not skill_dirs:
        message = f"No skills found under {skills_root}"
        if args.json_output:
            print(json.dumps({"root": str(skills_root), "error": message}, indent=2))
        else:
            print(f"ERROR: {message}")
        return 1

    valid_count = 0
    invalid_count = 0
    results = []

    for skill_dir in skill_dirs:
        result = validate_skill_dir(skill_dir)
        rel = str(skill_dir.relative_to(skills_root))
        results.append({"path": rel, "valid": result.valid, "message": result.message})
        if result.valid:
            valid_count += 1
        else:
            invalid_count += 1

    if args.json_output:
        print(json.dumps({
            "root": str(skills_root),
            "valid": invalid_count == 0,
            "summary": {
                "valid": valid_count,
                "invalid": invalid_count,
                "total": len(skill_dirs),
            },
            "results": results,
        }, indent=2))
        return 0 if invalid_count == 0 else 1

    print(f"Found {len(skill_dirs)} skill(s) under {skills_root}")
    print()

    for item in results:
        status = "VALID" if item["valid"] else "INVALID"
        print(f"[{status}] {item['path']} - {item['message']}")

    print()
    print("Summary:")
    print(f"  Valid:   {valid_count}")
    print(f"  Invalid: {invalid_count}")
    print(f"  Total:   {len(skill_dirs)}")

    if invalid_count:
        print()
        print("Failures:")
        for item in results:
            if not item["valid"]:
                print(f"  - {item['path']}: {item['message']}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
