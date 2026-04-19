---
sidebar_position: 8
title: "扩展 CLI"
description: "构建包装 CLI，通过自定义小部件、按键绑定和布局更改扩展 Hermes TUI"
---

# 扩展 CLI

Hermes 在 `HermesCLI` 上公开受保护的扩展钩子，以便包装 CLI 可以添加小部件、按键绑定和布局自定义，而无需覆盖 1000+ 行的 `run()` 方法。这使你的扩展与内部更改解耦。

## 扩展点

有五个可用的扩展接缝：

| 钩子 | 目的 | 何时覆盖... |
|------|---------|------------------|
| `_get_extra_tui_widgets()` | 将小部件注入布局 | 你需要一个持久的 UI 元素（面板、状态栏、迷你播放器） |
| `_register_extra_tui_keybindings(kb, *, input_area)` | 添加键盘快捷键 | 你需要热键（切换面板、传输控制、模态快捷键） |
| `_build_tui_layout_children(**widgets)` | 完全控制小部件排序 | 你需要重新排序或包装现有小部件（罕见） |
| `process_command()` | 添加自定义斜杠命令 | 你需要 `/mycommand` 处理（预先存在的钩子） |
| `_build_tui_style_dict()` | 自定义 prompt_toolkit 样式 | 你需要自定义颜色或样式（预先存在的钩子） |

前三个是新的受保护钩子。后两个已经存在。

## 快速开始：包装 CLI

```python
#!/usr/bin/env python3
"""my_cli.py — 扩展 Hermes 的示例包装 CLI。"""

from cli import HermesCLI
from prompt_toolkit.layout import FormattedTextControl, Window
from prompt_toolkit.filters import Condition


class MyCLI(HermesCLI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._panel_visible = False

    def _get_extra_tui_widgets(self):
        """在状态栏上方添加一个可切换的信息面板。"""
        cli_ref = self
        return [
            Window(
                FormattedTextControl(lambda: "📊 我的自定义面板内容"),
                height=1,
                filter=Condition(lambda: cli_ref._panel_visible),
            ),
        ]

    def _register_extra_tui_keybindings(self, kb, *, input_area):
        """F2 切换自定义面板。"""
        cli_ref = self

        @kb.add("f2")
        def _toggle_panel(event):
            cli_ref._panel_visible = not cli_ref._panel_visible

    def process_command(self, cmd: str) -> bool:
        """添加 /panel 斜杠命令。"""
        if cmd.strip().lower() == "/panel":
            self._panel_visible = not self._panel_visible
            state = "可见" if self._panel_visible else "隐藏"
            print(f"面板现在{state}")
            return True
        return super().process_command(cmd)


if __name__ == "__main__":
    cli = MyCLI()
    cli.run()
```

运行它：

```bash
cd ~/.hermes/hermes-agent
source .venv/bin/activate
python my_cli.py
```

## 钩子参考

### `_get_extra_tui_widgets()`

返回要插入到 TUI 布局中的 prompt_toolkit 小部件列表。小部件出现在**间隔符和状态栏之间** — 在输入区域上方但在主输出下方。

```python
def _get_extra_tui_widgets(self) -> list:
    return []  # 默认：无额外小部件
```

每个小部件应该是一个 prompt_toolkit 容器（例如，`Window`、`ConditionalContainer`、`HSplit`）。使用 `ConditionalContainer` 或 `filter=Condition(...)` 使小部件可切换。

```python
from prompt_toolkit.layout import ConditionalContainer, Window, FormattedTextControl
from prompt_toolkit.filters import Condition

def _get_extra_tui_widgets(self):
    return [
        ConditionalContainer(
            Window(FormattedTextControl("状态: 已连接"), height=1),
            filter=Condition(lambda: self._show_status),
        ),
    ]
```

### `_register_extra_tui_keybindings(kb, *, input_area)`

在 Hermes 注册自己的按键绑定后且在构建布局前调用。将你的按键绑定添加到 `kb`。

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    pass  # 默认：无额外按键绑定
```

参数：
- **`kb`** — prompt_toolkit 应用程序的 `KeyBindings` 实例
- **`input_area`** — 主 `TextArea` 小部件，如果你需要读取或操作用户输入

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

**避免与内置按键绑定冲突**：`Enter`（提交）、`Escape Enter`（换行）、`Ctrl-C`（中断）、`Ctrl-D`（退出）、`Tab`（自动建议接受）。功能键 F2+ 和 Ctrl 组合键通常是安全的。

### `_build_tui_layout_children(**widgets)`

仅在你需要完全控制小部件排序时覆盖此方法。大多数扩展应该使用 `_get_extra_tui_widgets()` 代替。

```python
def _build_tui_layout_children(self, *, sudo_widget, secret_widget,
    approval_widget, clarify_widget, spinner_widget, spacer,
    status_bar, input_rule_top, image_bar, input_area,
    input_rule_bot, voice_status_bar, completions_menu) -> list:
```

默认实现返回：

```python
[
    Window(height=0),       # 锚点
    sudo_widget,            # sudo 密码提示（条件）
    secret_widget,          # 秘密输入提示（条件）
    approval_widget,        # 危险命令批准（条件）
    clarify_widget,         # 澄清问题 UI（条件）
    spinner_widget,         # 思考旋转器（条件）
    spacer,                 # 填充剩余垂直空间
    *self._get_extra_tui_widgets(),  # 你的小部件在这里
    status_bar,             # 模型/令牌/上下文状态栏
    input_rule_top,         # 输入上方的 ─── 边框
    image_bar,              # 附加图像指示器
    input_area,             # 用户文本输入
    input_rule_bot,         # 输入下方的 ─── 边框
    voice_status_bar,       # 语音模式状态（条件）
    completions_menu,       # 自动完成下拉菜单
]
```

## 布局图

默认布局从上到下：

1. **输出区域** — 滚动对话历史
2. **间隔符**
3. **额外小部件** — 来自 `_get_extra_tui_widgets()`
4. **状态栏** — 模型、上下文 %、经过时间
5. **图像栏** — 附加图像计数
6. **输入区域** — 用户提示
7. **语音状态** — 录制指示器
8. **完成菜单** — 自动完成建议

## 提示

- **在状态更改后使显示无效**：调用 `self._invalidate()` 触发 prompt_toolkit 重绘。
- **访问代理状态**：`self.agent`、`self.model`、`self.conversation_history` 都可用。
- **自定义样式**：覆盖 `_build_tui_style_dict()` 并为你的自定义样式类添加条目。
- **斜杠命令**：覆盖 `process_command()`，处理你的命令，并为其他所有内容调用 `super().process_command(cmd)`。
- **不要覆盖 `run()`**，除非绝对必要 — 扩展钩子的存在就是为了避免这种耦合。