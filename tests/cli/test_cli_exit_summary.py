from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from cli import HermesCLI


def _make_cli():
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj.conversation_history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    cli_obj.session_start = datetime.now() - timedelta(seconds=65)
    cli_obj.session_id = "20260101_010203_deadbe"
    cli_obj._session_db = MagicMock()
    cli_obj._session_db.get_session_title.return_value = "Example Session"
    return cli_obj


def test_print_exit_summary_uses_plain_resume_commands_for_default_profile(capsys):
    cli_obj = _make_cli()

    with patch("hermes_cli.profiles.get_active_profile_name", return_value="default"):
        cli_obj._print_exit_summary()

    output = capsys.readouterr().out
    assert "Resume this session with:" in output
    assert "  hermes --resume 20260101_010203_deadbe" in output
    assert '  hermes -c "Example Session"' in output
    assert "hermes -p default" not in output


def test_print_exit_summary_includes_profile_in_resume_commands_for_named_profile(capsys):
    cli_obj = _make_cli()

    with patch("hermes_cli.profiles.get_active_profile_name", return_value="example-profile"):
        cli_obj._print_exit_summary()

    output = capsys.readouterr().out
    assert "Resume this session with:" in output
    assert "  hermes -p example-profile --resume 20260101_010203_deadbe" in output
    assert '  hermes -p example-profile -c "Example Session"' in output
