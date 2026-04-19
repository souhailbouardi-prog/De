#!/usr/bin/env python3
"""Cron pre-run script: prints whether morning checkin was responded to.
Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_log import check_morning_response
print("RESPONDED" if check_morning_response() else "NO_RESPONSE")
