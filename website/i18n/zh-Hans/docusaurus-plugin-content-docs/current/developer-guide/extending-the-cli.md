---
sidebar_position: 8
title: "扩展 CLI"
description: "构建包装器 CLI，使用自定义小部件、键绑定和布局更改扩展 Hermes TUI"
---

# 扩展 CLI

Hermes 在 `HermesCLI` 上暴露受保护的扩展钩子，以便包装器 CLI 可以添加小部件、键绑定和布局自定义，而无需覆盖 1000+ 行的 `run()` 方法。这使您的扩展与内部更改解耦。

## 扩展点

有五个可用的扩展接缝：

| 钩子 | 用途 | 何时重写... |
|------|---------|------------------|
| `_get_extra_tui_widgets()` | 将小部件注入布局 | 您需要持久性 UI 元素（面板、状态行、迷你播放器） |
| `_register_extra_tui_keybindings(kb, *, input_area)` | 添加键盘快捷键 | 您需要热键（切换面板、传输控制、模态快捷键） |
| `_build_tui_layout_children(**widgets)` | 完全控制小部件排序 | 您需要重新排序或包装现有小部件（罕见） |
| `process_command()` | 添加自定义斜杠命令 | 您需要 `/mycommand` 处理（预先存在的钩子） |
| `_build_tui_style_dict()` | 自定义 prompt_toolkit 样式 | 您需要自定义颜色或样式（预先存在的钩子） |

前三个是新的受保护钩子。后两个已经存在。

## 快速开始：包装器 CLI

```python
#!/usr/bin/env python3
"""my_cli.py — 扩展 Hermes 的示例包装器 CLI。"""

from cli import HermesCLI
from prompt_toolkit.layout import FormattedTextControl, Window
from prompt_toolkit.filters import Condition


class MyCLI(HermesCLI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._panel_visible = False

    def _get_extra_tui_widgets(self):
        """在状态栏上方添加可切换的信息面板。"""
        cli_ref = self
        return [
            Window(
                FormattedTextControl(lambda: "📊 我的自定义面板内容"),
                height=1,
                filter=Condition(lambda: cli_ref._panel_visible),
            ),
        ]

    def _register_extra_tui_keybindings(self, kb, *, input_area):
        """F2 toggles the custom panel."""
        cli_ref = self

        @kb.add("f2")
        def _toggle_panel(event):
            cli_ref._panel_visible = not cli_ref._panel_visible

    def process_command(self, cmd: str) -> bool:
        """Add a /panel slash command."""
        if cmd.strip().lower() == "/panel":
            self._panel_visible = not self._panel_visible
            state = "visible" if self._panel_visible else "hidden"
            print(f"Panel is now {state}")
            return True
        return super().process_command(cmd)


if __name__ == "__main__":
    cli = MyCLI()
    cli.run()
```

Run it:

```bash
cd ~/.hermes/hermes-agent
source .venv/bin/activate
python my_cli.py
```

## Hook reference

### `_get_extra_tui_widgets()`

Returns a list of prompt_toolkit widgets to insert into the TUI layout. Widgets appear **between the spacer and the status bar** — above the input area but below the main output.

```python
def _get_extra_tui_widgets(self) -> list:
    return []  # default: no extra widgets
```

Each widget should be a prompt_toolkit container (e.g., `Window`, `ConditionalContainer`, `HSplit`). Use `ConditionalContainer` or `filter=Condition(...)` to make widgets toggleable.

```python
from prompt_toolkit.layout import ConditionalContainer, Window, FormattedTextControl
from prompt_toolkit.filters import Condition

def _get_extra_tui_widgets(self):
    return [
        ConditionalContainer(
            Window(FormattedTextControl("Status: connected"), height=1),
            filter=Condition(lambda: self._show_status),
        ),
    ]
```

### `_register_extra_tui_keybindings(kb, *, input_area)`

Called after Hermes registers its own keybindings and before the layout is built. Add your keybindings to `kb`.

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    pass  # default: no extra keybindings
```

Parameters:
- **`kb`** — The `KeyBindings` instance for the prompt_toolkit application
- **`input_area`** — The main `TextArea` widget, if you need to read or manipulate user input

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    cli_ref = self

    @kb.add("f3")
    def _clear_input(event):
        input_area.text = ""

    @kb.add("f4")
    def _insert_template(event):
        input_area.text = "/search "
```

**Avoid conflicts** with built-in keybindings: `Enter` (submit), `Escape Enter` (newline), `Ctrl-C` (interrupt), `Ctrl-D` (exit), `Tab` (auto-suggest accept). Function keys F2+ and Ctrl-combinations are generally safe.

### `_build_tui_layout_children(**widgets)`

Override this only when you need full control over widget ordering. Most extensions should use `_get_extra_tui_widgets()` instead.

```python
def _build_tui_layout_children(self, *, sudo_widget, secret_widget,
    approval_widget, clarify_widget, spinner_widget, spacer,
    status_bar, input_rule_top, image_bar, input_area,
    input_rule_bot, voice_status_bar, completions_menu) -> list:
```

The default implementation returns:

```python
[
    Window(height=0),       # anchor
    sudo_widget,            # sudo password prompt (conditional)
    secret_widget,          # secret input prompt (conditional)
    approval_widget,        # dangerous command approval (conditional)
    clarify_widget,         # clarify question UI (conditional)
    spinner_widget,         # thinking spinner (conditional)
    spacer,                 # fills remaining vertical space
    *self._get_extra_tui_widgets(),  # YOUR WIDGETS GO HERE
    status_bar,             # model/token/context status line
    input_rule_top,         # ─── border above input
    image_bar,              # attached images indicator
    input_area,             # user text input
    input_rule_bot,         # ─── border below input
    voice_status_bar,       # voice mode status (conditional)
    completions_menu,       # autocomplete dropdown
]
```

## Layout diagram

The default layout from top to bottom:

1. **Output area** — scrolling conversation history
2. **Spacer**
3. **Extra widgets** — from `_get_extra_tui_widgets()`
4. **Status bar** — model, context %, elapsed time
5. **Image bar** — attached image count
6. **Input area** — user prompt
7. **Voice status** — recording indicator
8. **Completions menu** — autocomplete suggestions

## Tips

- **Invalidate the display** after state changes: call `self._invalidate()` to trigger a prompt_toolkit redraw.
- **Access agent state**: `self.agent`, `self.model`, `self.conversation_history` are all available.
- **Custom styles**: Override `_build_tui_style_dict()` and add entries for your custom style classes.
- **Slash commands**: Override `process_command()`, handle your commands, and call `super().process_command(cmd)` for everything else.
- **Don't override `run()`** unless absolutely necessary — the extension hooks exist specifically to avoid that coupling.