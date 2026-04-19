#!/usr/bin/env python3
"""Cron pre-run script: prints bloodwork status for Wednesday reminder.
Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_log import bloodwork_status

result = bloodwork_status()
if result["status"] == "not_scheduled":
    print("NOT_SCHEDULED")
elif result["status"] == "scheduled":
    print(f"SCHEDULED: {result['date']}")
elif result["status"] == "completed":
    print("COMPLETED")
