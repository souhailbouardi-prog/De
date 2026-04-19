from hermes_cli.codex_limits import (
    extract_codex_limit_windows,
    format_codex_limits,
    should_show_codex_limits,
)


def test_format_codex_limits_with_primary_and_weekly_windows():
    payload = {
        "rate_limit": {
            "primary_window": {
                "used_percent": 64,
                "limit_window_seconds": 18000,
                "reset_after_seconds": 14730,
                "reset_at": 1776413408,
            },
            "secondary_window": {
                "used_percent": 15,
                "limit_window_seconds": 604800,
                "reset_after_seconds": 568655,
                "reset_at": 1776967333,
            },
        },
        "code_review_rate_limit": None,
        "additional_rate_limits": None,
    }

    result = format_codex_limits(payload)

    assert result == (
        "Limits:\n"
        "5 hours: 36% remaining.\n"
        "Resets in 4:05:30.\n"
        "\n"
        "Weekly: 85% remaining.\n"
        "Reset Apr 23 at 18:02 GMT"
    )


def test_extract_codex_limits_keeps_daily_and_named_additional_windows():
    payload = {
        "rate_limit": {
            "primary_window": {
                "used_percent": 10,
                "limit_window_seconds": 18000,
                "reset_after_seconds": 10,
            },
            "secondary_window": {
                "used_percent": 58,
                "limit_window_seconds": 86400,
                "reset_after_seconds": 66163,
                "reset_at": 1776475200,
            },
        },
        "additional_rate_limits": [
            {
                "name": "Uploads",
                "primary_window": {
                    "used_percent": 25,
                    "limit_window_seconds": 3600,
                    "reset_after_seconds": 1200,
                },
            }
        ],
    }

    windows = extract_codex_limit_windows(payload)
    labels = [window.label for window in windows]
    remaining = [window.remaining_percent for window in windows]

    assert labels == ["5 hours", "1 day", "Uploads: 1 hour"]
    assert remaining == [90, 42, 75]

    result = format_codex_limits(payload)
    assert "1 day: 42% remaining." in result
    assert "Resets in 18:22:43." in result
    assert "Uploads: 1 hour: 75% remaining." in result


def test_should_show_codex_limits_for_provider_or_base_url():
    assert should_show_codex_limits("openai-codex", None) is True
    assert should_show_codex_limits(None, "https://chatgpt.com/backend-api/codex") is True
    assert should_show_codex_limits("openrouter", "https://openrouter.ai/api/v1") is False
