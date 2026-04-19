#!/usr/bin/env python3
"""Quick validation script for a single Hermes skill directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.skills_validation import validate_skill_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single Hermes skill directory.")
    parser.add_argument("skill_directory", help="Path to a skill directory containing SKILL.md")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print machine-readable JSON output")
    args = parser.parse_args()

    result = validate_skill_dir(args.skill_directory)
    payload = {
        "path": str(Path(args.skill_directory).expanduser()),
        "valid": result.valid,
        "message": result.message,
    }

    if args.json_output:
        print(json.dumps(payload, indent=2))
    else:
        print(("VALID: " if result.valid else "INVALID: ") + result.message)
    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
