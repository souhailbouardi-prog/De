#!/usr/bin/env python3
"""CLI wrapper for health_insights — cron/agent-friendly, env-var driven.

Usage:
    HEALTH_LOG_CMD=insights python health_insights_cli.py
    HEALTH_LOG_CMD=phase_check HEALTH_LOG_ARGS='{"current_phase":1}' python health_insights_cli.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_insights import (
    sleep_recovery_correlation,
    hrv_trend_analysis,
    detect_illness_signals,
    habit_recovery_correlation,
    check_phase_transition,
)

cmd = os.environ.get("HEALTH_LOG_CMD", "")
args = json.loads(os.environ.get("HEALTH_LOG_ARGS", "{}"))

if cmd == "insights":
    result = {
        "sleep_recovery": sleep_recovery_correlation(args.get("days", 30)),
        "hrv_trend": hrv_trend_analysis(args.get("days", 30)),
        "illness_signals": detect_illness_signals(args.get("days", 3)),
        "habit_correlations": habit_recovery_correlation(args.get("days", 30)),
    }
    print(json.dumps(result, indent=2))
elif cmd == "phase_check":
    result = check_phase_transition(args.get("current_phase", 1))
    print(json.dumps(result, indent=2))
else:
    print(f"Unknown command: {cmd}", file=sys.stderr)
    sys.exit(1)
