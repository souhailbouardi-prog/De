from cli import HermesCLI


class _FakeBuffer:
    def __init__(self, text="", cursor_position=0):
        self.text = text
        self.cursor_position = cursor_position

    def delete(self, count=1):
        if count <= 0:
            return ""
        if self.cursor_position >= len(self.text):
            return ""
        deleted = self.text[self.cursor_position : self.cursor_position + count]
        self.text = self.text[: self.cursor_position] + self.text[self.cursor_position + count :]
        return deleted


class _FakeApp:
    def __init__(self, text="", cursor_position=0, is_running=True):
        self.current_buffer = _FakeBuffer(text=text, cursor_position=cursor_position)
        self.invalidated = False
        self.exited = False
        self.is_running = is_running

    def invalidate(self):
        self.invalidated = True

    def exit(self):
        self.exited = True


def _make_cli_stub():
    cli = HermesCLI.__new__(HermesCLI)
    cli._should_exit = False
    return cli


def test_ctrl_d_deletes_character_under_cursor_instead_of_exiting():
    cli = _make_cli_stub()
    app = _FakeApp(text="abc", cursor_position=1)

    cli._handle_ctrl_d_keypress(app)

    assert app.current_buffer.text == "ac"
    assert app.invalidated is True
    assert app.exited is False
    assert cli._should_exit is False


def test_ctrl_d_at_end_of_non_empty_line_does_not_exit():
    cli = _make_cli_stub()
    app = _FakeApp(text="abc", cursor_position=3)

    cli._handle_ctrl_d_keypress(app)

    assert app.current_buffer.text == "abc"
    assert app.invalidated is True
    assert app.exited is False
    assert cli._should_exit is False


def test_ctrl_d_on_empty_buffer_exits_like_eof():
    cli = _make_cli_stub()
    app = _FakeApp(text="", cursor_position=0)

    cli._handle_ctrl_d_keypress(app)

    assert app.exited is True
    assert cli._should_exit is True
