#!/usr/bin/env python3
"""Smart health insights and phase transition detection.

Pure Python analysis on top of health_log's SQLite store.
No external dependencies beyond the stdlib.
"""
import json
from datetime import datetime, timezone, timedelta

from health_log import events_range, weight_trend, bloodwork_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_checkin_data(event: dict) -> dict | None:
    """Extract WHOOP metrics from a checkin event's data JSON. Returns None on failure."""
    raw = event.get("data")
    if not raw:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return None


def _checkins_with_metrics(days: int) -> list[dict]:
    """Return checkin events with parsed WHOOP metrics, sorted oldest-first."""
    events = events_range(days)
    results = []
    for e in events:
        if e.get("type") != "checkin" or e.get("source") != "system":
            continue
        metrics = _parse_checkin_data(e)
        if metrics is None:
            continue
        results.append({"ts": e["ts"], **metrics})
    return results


# ---------------------------------------------------------------------------
# a) Sleep / recovery correlation
# ---------------------------------------------------------------------------

def sleep_recovery_correlation(days: int = 30) -> dict:
    """Compare avg recovery on nights above vs below a sleep-hours threshold."""
    threshold = 7.5
    checkins = _checkins_with_metrics(days)

    above_recoveries: list[float] = []
    below_recoveries: list[float] = []

    for c in checkins:
        recovery = c.get("recovery")
        sleep = c.get("sleep_hours")
        if recovery is None or sleep is None:
            continue
        (above_recoveries if sleep >= threshold else below_recoveries).append(recovery)

    above_avg = sum(above_recoveries) / len(above_recoveries) if above_recoveries else 0
    below_avg = sum(below_recoveries) / len(below_recoveries) if below_recoveries else 0

    if below_avg > 0 and above_avg > 0:
        pct = round((above_avg - below_avg) / below_avg * 100, 1)
        insight = f"You recover {pct}% better on nights with {threshold}+ hours sleep"
    elif above_avg > 0:
        insight = f"All recorded nights are {threshold}+ hours — not enough contrast to compare"
    elif below_avg > 0:
        insight = f"All recorded nights are below {threshold} hours — prioritise sleep"
    else:
        insight = "No sleep/recovery data yet"

    return {
        "above_threshold": {
            "count": len(above_recoveries),
            "avg_recovery": round(above_avg, 1),
        },
        "below_threshold": {
            "count": len(below_recoveries),
            "avg_recovery": round(below_avg, 1),
        },
        "threshold_hours": threshold,
        "insight": insight,
    }


# ---------------------------------------------------------------------------
# b) HRV trend analysis
# ---------------------------------------------------------------------------

def hrv_trend_analysis(days: int = 30) -> dict:
    """Compute 7-day rolling average of HRV and determine trend direction."""
    checkins = _checkins_with_metrics(days)

    hrv_series: list[dict] = []  # {ts, hrv}
    for c in checkins:
        hrv = c.get("hrv")
        if hrv is not None:
            hrv_series.append({"ts": c["ts"], "hrv": hrv})

    # Compute 7-day rolling average for each point
    values: list[dict] = []
    for i, point in enumerate(hrv_series):
        dt_current = datetime.strptime(point["ts"], "%Y-%m-%dT%H:%M:%SZ")
        window_start = dt_current - timedelta(days=7)
        window_vals = [
            hrv_series[j]["hrv"]
            for j in range(i + 1)
            if datetime.strptime(hrv_series[j]["ts"], "%Y-%m-%dT%H:%M:%SZ") > window_start
        ]
        rolling_avg = sum(window_vals) / len(window_vals) if window_vals else 0
        values.append({
            "ts": point["ts"],
            "hrv": point["hrv"],
            "rolling_avg": round(rolling_avg, 2),
        })

    # Determine direction: compare last 7-day avg to previous 7-day avg
    if len(values) < 2:
        return {
            "current_7day_avg": values[-1]["rolling_avg"] if values else 0,
            "previous_7day_avg": 0,
            "direction": "stable",
            "values": values,
        }

    current_avg = values[-1]["rolling_avg"]
    # Find the rolling avg at the midpoint (or the earliest point whose window is fully 7+ days back)
    mid = len(values) // 2
    previous_avg = values[mid]["rolling_avg"] if mid < len(values) else values[0]["rolling_avg"]

    if previous_avg == 0:
        direction = "stable"
    else:
        pct_change = (current_avg - previous_avg) / previous_avg * 100
        if pct_change > 5:
            direction = "up"
        elif pct_change < -5:
            direction = "down"
        else:
            direction = "stable"

    return {
        "current_7day_avg": current_avg,
        "previous_7day_avg": previous_avg,
        "direction": direction,
        "values": values,
    }


# ---------------------------------------------------------------------------
# c) Illness signal detection
# ---------------------------------------------------------------------------

def detect_illness_signals(days: int = 3) -> dict:
    """Check last N days for illness-indicating biometric changes."""
    # Get a wider window for baseline: look-back days + 7 day baseline
    all_checkins = _checkins_with_metrics(days + 10)

    now = datetime.now(timezone.utc)
    cutoff_recent = now - timedelta(days=days)
    cutoff_baseline_start = cutoff_recent - timedelta(days=7)

    baseline_rhr: list[float] = []
    baseline_hrv: list[float] = []
    recent_rhr: list[float] = []
    recent_hrv: list[float] = []
    recent_spo2: list[float] = []

    for c in all_checkins:
        dt = datetime.strptime(c["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        rhr = c.get("rhr")
        hrv = c.get("hrv")
        spo2 = c.get("spo2")

        if cutoff_baseline_start <= dt < cutoff_recent:
            if rhr is not None:
                baseline_rhr.append(rhr)
            if hrv is not None:
                baseline_hrv.append(hrv)
        elif dt >= cutoff_recent:
            if rhr is not None:
                recent_rhr.append(rhr)
            if hrv is not None:
                recent_hrv.append(hrv)
            if spo2 is not None:
                recent_spo2.append(spo2)

    signals: list[str] = []
    details: dict = {}

    # RHR spike > 10%
    if baseline_rhr and recent_rhr:
        baseline_avg_rhr = sum(baseline_rhr) / len(baseline_rhr)
        recent_avg_rhr = sum(recent_rhr) / len(recent_rhr)
        if baseline_avg_rhr > 0 and (recent_avg_rhr - baseline_avg_rhr) / baseline_avg_rhr > 0.10:
            signals.append("rhr_spike")
            details["rhr_baseline"] = round(baseline_avg_rhr, 1)
            details["rhr_recent"] = round(recent_avg_rhr, 1)

    # HRV drop > 20%
    if baseline_hrv and recent_hrv:
        baseline_avg_hrv = sum(baseline_hrv) / len(baseline_hrv)
        recent_avg_hrv = sum(recent_hrv) / len(recent_hrv)
        if baseline_avg_hrv > 0 and (baseline_avg_hrv - recent_avg_hrv) / baseline_avg_hrv > 0.20:
            signals.append("hrv_drop")
            details["hrv_baseline"] = round(baseline_avg_hrv, 1)
            details["hrv_recent"] = round(recent_avg_hrv, 1)

    # SpO2 < 95%
    if recent_spo2:
        avg_spo2 = sum(recent_spo2) / len(recent_spo2)
        if avg_spo2 < 95:
            signals.append("spo2_low")
            details["spo2_avg"] = round(avg_spo2, 1)

    return {
        "alert": len(signals) > 0,
        "signals": signals,
        "details": details,
    }


# ---------------------------------------------------------------------------
# d) Habit / recovery correlation
# ---------------------------------------------------------------------------

def habit_recovery_correlation(days: int = 30) -> dict:
    """Compare avg recovery on days with/without each tracked habit."""
    all_events = events_range(days)
    target_habits = {"walk", "supplement", "sighing", "nebulize"}

    # Build per-day maps
    day_recovery: dict[str, float] = {}   # date -> recovery
    day_habits: dict[str, set] = {}       # date -> set of habit subtypes

    for e in all_events:
        day = e["ts"][:10]  # YYYY-MM-DD
        if e["type"] == "checkin" and e["source"] == "system":
            metrics = _parse_checkin_data(e)
            if metrics and metrics.get("recovery") is not None:
                day_recovery[day] = metrics["recovery"]
        if e["type"] == "habit" and e.get("subtype") in target_habits:
            day_habits.setdefault(day, set()).add(e["subtype"])

    # Only consider days that have a checkin (recovery data)
    days_with_recovery = set(day_recovery.keys())

    correlations: dict = {}
    for habit in sorted(target_habits):
        with_vals: list[float] = []
        without_vals: list[float] = []
        for day in days_with_recovery:
            rec = day_recovery[day]
            if habit in day_habits.get(day, set()):
                with_vals.append(rec)
            else:
                without_vals.append(rec)

        avg_with = sum(with_vals) / len(with_vals) if with_vals else 0
        avg_without = sum(without_vals) / len(without_vals) if without_vals else 0

        correlations[habit] = {
            "with": round(avg_with, 1),
            "without": round(avg_without, 1),
            "delta": round(avg_with - avg_without, 1),
            "with_count": len(with_vals),
            "without_count": len(without_vals),
        }

    return {"correlations": correlations}


# ---------------------------------------------------------------------------
# e) Phase transition check
# ---------------------------------------------------------------------------

def check_phase_transition(current_phase: int = 1) -> dict:
    """Evaluate whether criteria for the next phase transition are met."""
    if current_phase == 1:
        return _check_phase_1_to_2()
    elif current_phase == 2:
        return _check_phase_2_to_3()
    else:
        return {"ready": False, "phase": f"{current_phase}->?", "criteria": {}, "blockers": ["unknown_phase"]}


def _check_phase_1_to_2() -> dict:
    criteria: dict[str, bool] = {}
    blockers: list[str] = []

    checkins = _checkins_with_metrics(14)
    all_events = events_range(7)

    # sleep_consistent: avg sleep >= 7.5h for last 7 days
    now = datetime.now(timezone.utc)
    cutoff_7 = now - timedelta(days=7)
    recent_sleep: list[float] = []
    for c in checkins:
        dt = datetime.strptime(c["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if dt >= cutoff_7 and c.get("sleep_hours") is not None:
            recent_sleep.append(c["sleep_hours"])
    avg_sleep = sum(recent_sleep) / len(recent_sleep) if recent_sleep else 0
    criteria["sleep_consistent"] = avg_sleep >= 7.5
    if not criteria["sleep_consistent"]:
        blockers.append("sleep_consistent")

    # recovery_trending_up: HRV trend direction is "up" or "stable"
    hrv = hrv_trend_analysis(days=30)
    criteria["recovery_trending_up"] = hrv["direction"] in ("up", "stable")
    if not criteria["recovery_trending_up"]:
        blockers.append("recovery_trending_up")

    # walking_regular: walk logged >= 5 of last 7 days
    walk_days = set()
    for e in all_events:
        if e["type"] == "habit" and e.get("subtype") == "walk":
            walk_days.add(e["ts"][:10])
    criteria["walking_regular"] = len(walk_days) >= 5
    if not criteria["walking_regular"]:
        blockers.append("walking_regular")

    # supplements_regular: supplement logged >= 5 of last 7 days
    supp_days = set()
    for e in all_events:
        if e["type"] == "habit" and e.get("subtype") == "supplement":
            supp_days.add(e["ts"][:10])
    criteria["supplements_regular"] = len(supp_days) >= 5
    if not criteria["supplements_regular"]:
        blockers.append("supplements_regular")

    # bloodwork_scheduled: status is "scheduled" or "completed"
    bw = bloodwork_status()
    criteria["bloodwork_scheduled"] = bw["status"] in ("scheduled", "completed")
    if not criteria["bloodwork_scheduled"]:
        blockers.append("bloodwork_scheduled")

    ready = len(blockers) == 0
    return {
        "ready": ready,
        "phase": "1->2",
        "criteria": criteria,
        "blockers": blockers,
    }


def _check_phase_2_to_3() -> dict:
    criteria: dict[str, bool] = {}
    blockers: list[str] = []

    # weight_trending_up: 0.25-0.5 kg/week gain
    wt = weight_trend(days=30)
    weekly_avgs = wt.get("weekly_averages", [])
    if len(weekly_avgs) >= 2:
        first_avg = weekly_avgs[0]["avg"]
        last_avg = weekly_avgs[-1]["avg"]
        weeks = max(len(weekly_avgs) - 1, 1)
        gain_per_week = (last_avg - first_avg) / weeks
        criteria["weight_trending_up"] = 0.25 <= gain_per_week <= 0.5
    else:
        criteria["weight_trending_up"] = False
    if not criteria["weight_trending_up"]:
        blockers.append("weight_trending_up")

    # recovery_consistent: avg recovery > 50% for last 14 days
    checkins = _checkins_with_metrics(14)
    recoveries = [c["recovery"] for c in checkins if c.get("recovery") is not None]
    avg_recovery = sum(recoveries) / len(recoveries) if recoveries else 0
    criteria["recovery_consistent"] = avg_recovery > 50
    if not criteria["recovery_consistent"]:
        blockers.append("recovery_consistent")

    # labs_completed: bloodwork status is "completed"
    bw = bloodwork_status()
    criteria["labs_completed"] = bw["status"] == "completed"
    if not criteria["labs_completed"]:
        blockers.append("labs_completed")

    ready = len(blockers) == 0
    return {
        "ready": ready,
        "phase": "2->3",
        "criteria": criteria,
        "blockers": blockers,
    }
