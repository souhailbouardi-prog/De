from hermes_cli.pairing import _cmd_list


class _FakePairingStore:
    def list_pending(self):
        return [
            {
                "platform": "telegram",
                "code": "ABCD1234",
                "user_id": "user-1",
                "user_name": None,
                "age_minutes": 5,
            }
        ]

    def list_approved(self):
        return [
            {
                "platform": "telegram",
                "user_id": "user-2",
                "user_name": None,
            }
        ]


def test_cmd_list_handles_null_user_names(capsys):
    _cmd_list(_FakePairingStore())

    output = capsys.readouterr().out
    assert "Pending Pairing Requests (1)" in output
    assert "Approved Users (1)" in output
    assert "telegram" in output
    assert "ABCD1234" in output
    assert "user-1" in output
    assert "user-2" in output
