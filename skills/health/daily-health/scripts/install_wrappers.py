#!/usr/bin/env python3
"""Install cron wrapper scripts to ~/.hermes/scripts/.
Creates symlinks from ~/.hermes/scripts/ pointing to the skill's script files.
Run once after cloning or updating the skill.
Usage: python install_wrappers.py
"""
import os
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
SCRIPTS_DIR = HERMES_HOME / "scripts"
SKILL_SCRIPTS = Path(__file__).resolve().parent

WRAPPERS = [
    "health_morning_query.py",
    "health_noon_query.py",
    "health_log_cli.py",
    "health_weekly_query.py",
    "health_bloodwork_query.py",
    "health_insights_cli.py",
]

def install():
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for name in WRAPPERS:
        src = SKILL_SCRIPTS / name
        dst = SCRIPTS_DIR / name
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        dst.symlink_to(src)
        print(f"  {dst} -> {src}")
    print(f"Installed {len(WRAPPERS)} wrapper scripts to {SCRIPTS_DIR}")

if __name__ == "__main__":
    install()
