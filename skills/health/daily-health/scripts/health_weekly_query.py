#!/usr/bin/env python3
"""Cron pre-run script: prints weekly summary JSON for Sunday review.
Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_log import weekly_summary, weight_trend, mood_trend

output = {
    "weekly_summary": weekly_summary(7),
    "weight_trend": weight_trend(7),
    "mood_trend": mood_trend(7),
}
print(json.dumps(output, indent=2))
