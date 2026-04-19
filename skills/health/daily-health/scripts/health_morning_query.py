#!/usr/bin/env python3
"""Cron pre-run script: prints last user interaction timestamp.
Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_log import last_user_interaction
ts = last_user_interaction()
print(ts or "NEVER")
