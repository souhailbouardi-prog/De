---
sidebar_position: 2
title: "TUI"
description: "启动 Hermes 的现代终端 UI —— 鼠标友好、丰富的覆盖层和非阻塞输入。"
---

# TUI

TUI 是 Hermes 的现代前端 —— 一个由与 [经典 CLI](cli.md) 相同的 Python 运行时支持的终端 UI。相同的代理、相同的会话、相同的斜杠命令；一个更干净、响应更快的界面来与它们交互。

这是交互式运行 Hermes 的推荐方式。

## 启动

```bash
# 启动 TUI
hermes --tui

# 恢复最新的 TUI 会话（回退到最新的经典会话）
hermes --tui -c
hermes --tui --continue

# 通过 ID 或标题恢复特定会话
hermes --tui -r 20260409_000000_aa11bb
hermes --tui --resume "my t0p session"

# 直接运行源代码 —— 跳过预构建步骤（适用于 TUI 贡献者）
hermes --tui --dev
```

你也可以通过环境变量启用它：

```bash
export HERMES_TUI=1
hermes          # 现在使用 TUI
hermes chat     # 相同
```

经典 CLI 仍然作为默认值可用。[CLI 界面](cli.md) 中记录的任何内容 —— 斜杠命令、快速命令、技能预加载、个性、多行输入、中断 —— 在 TUI 中的工作方式完全相同。

## 为什么选择 TUI

- **即时第一帧** —— 横幅在应用程序完成加载之前绘制，因此当 Hermes 启动时，终端永远不会感觉冻结。
- **非阻塞输入** —— 在会话准备好之前键入和排队消息。你的第一个提示会在代理上线的那一刻发送。
- **丰富的覆盖层** —— 模型选择器、会话选择器、审批和澄清提示都渲染为模态面板，而不是内联流程。
- **实时会话面板** —— 工具和技能在初始化时逐步填充。
- **鼠标友好的选择** —— 拖动以使用统一的背景而不是 SGR 反转来突出显示。使用终端的正常复制手势复制。
- **备用屏幕渲染** —— 差异更新意味着流式传输时没有闪烁，退出后没有回滚混乱。
- **编辑器辅助功能** —— 长片段的内联粘贴折叠、从剪贴板粘贴图像（`Alt+V`）、括号粘贴安全性。

相同的 [外观](features/skins.md) 和 [个性](features/personality.md) 适用。使用 `/skin ares`、`/personality pirate` 在会话中途切换，UI 会实时重新绘制。外观键在 [`example-skin.yaml`](https://github.com/NousResearch/hermes-agent/blob/main/docs/skins/example-skin.yaml) 中标记为 `(both)`、`(classic)` 或 `(tui)`，因此你可以一目了然地看到什么适用在哪里 —— TUI 支持横幅调色板、UI 颜色、提示字形/颜色、会话显示、完成菜单、选择背景、`tool_prefix` 和 `help_header`。

## 要求

- **Node.js** ≥ 20 —— TUI 作为从 Python CLI 启动的子进程运行。`hermes doctor` 会验证这一点。
- **TTY** —— 与经典 CLI 一样，管道标准输入或在非交互环境中运行会回退到单查询模式。

首次启动时，Hermes 会将 TUI 的 Node 依赖安装到 `ui-tui/node_modules`（一次性，几秒钟）。后续启动很快。如果你拉取新的 Hermes 版本，当源比 dist 更新时，TUI 捆绑包会自动重建。

### 外部预构建

提供预构建捆绑包的发行版（Nix、系统包）可以将 Hermes 指向它：

```bash
export HERMES_TUI_DIR=/path/to/prebuilt/ui-tui
hermes --tui
```

该目录必须包含 `dist/entry.js` 和最新的 `node_modules`。

## 键绑定

键绑定与 [经典 CLI](cli.md#keybindings) 完全匹配。唯一的行为差异：

- **鼠标拖动** 使用统一的选择背景突出显示文本。
- **`Ctrl+V`** 将剪贴板中的文本直接粘贴到编辑器中；多行粘贴保持在一行，直到你展开它们。
- **斜杠自动补全** 作为带有描述的浮动面板打开，而不是内联下拉列表。

## 斜杠命令

所有斜杠命令都可以正常工作。有几个是 TUI 专有的 —— 它们产生更丰富的输出或渲染为覆盖层，而不是内联面板：

| 命令 | TUI 行为 |
|---------|--------------|
| `/help` | 带有分类命令的覆盖层，可通过箭头键导航 |
| `/sessions` | 模态会话选择器 —— 预览、标题、令牌总数、内联恢复 |
| `/model` | 按提供程序分组的模态模型选择器，带有成本提示 |
| `/skin` | 实时预览 —— 浏览时应用主题更改 |
| `/details` | 在转录中切换详细的工具调用详细信息 |
| `/usage` | 丰富的令牌 / 成本 / 上下文面板 |

每个其他斜杠命令（包括已安装的技能、快速命令和个性切换）的工作方式都与经典 CLI 完全相同。请参阅 [斜杠命令参考](../reference/slash-commands.md)。

## 状态行

TUI 的状态行实时跟踪代理状态：

| 状态 | 含义 |
|--------|---------|
| `starting agent…` | 会话 ID 是活动的；工具和技能仍在上线。你可以键入 —— 消息在准备好时排队并发送。 |
| `ready` | 代理空闲，接受输入。 |
| `thinking…` / `running…` | 代理正在推理或运行工具。 |
| `interrupted` | 当前回合被取消；按 Enter 再次发送。 |
| `forging session…` / `resuming…` | 初始连接或 `--resume` 握手。 |

每个外观的状态栏颜色和阈值都与经典 CLI 共享 —— 有关自定义，请参阅 [外观](features/skins.md)。

## 配置

TUI 尊重所有标准 Hermes 配置：`~/.hermes/config.yaml`、配置文件、个性、外观、快速命令、凭据池、记忆提供程序、工具/技能启用。不存在特定于 TUI 的配置文件。

有几个键专门调整 TUI 界面：

```yaml
display:
  skin: default          # 任何内置或自定义外观
  personality: helpful
  details_mode: compact  # 或 "verbose" —— 默认工具调用详细级别
  mouse_tracking: true   # 如果你的终端与鼠标报告冲突，则禁用
```

`/details on` / `/details off` / `/details cycle` 在运行时切换这一点。

## 会话

会话在 TUI 和经典 CLI 之间共享 —— 两者都写入相同的 `~/.hermes/state.db`。你可以在一个中启动会话，在另一个中恢复。会话选择器显示来自两个来源的会话，并带有来源标签。

有关生命周期、搜索、压缩和导出，请参阅 [会话](sessions.md)。

## 恢复到经典 CLI

启动 `hermes`（不带 `--tui`）会停留在经典 CLI 上。要使机器偏好 TUI，请在你的 shell 配置文件中设置 `HERMES_TUI=1`。要回去，请取消设置它。

如果 TUI 无法启动（没有 Node、缺失捆绑包、TTY 问题），Hermes 会打印诊断并回退 —— 而不是让你卡住。

## 另请参阅

- [CLI 界面](cli.md) —— 完整的斜杠命令和键绑定参考（共享）
- [会话](sessions.md) —— 恢复、分支和历史记录
- [外观与主题](features/skins.md) —— 主题横幅、状态栏和覆盖层
- [语音模式](features/voice-mode.md) —— 在两个界面中都有效
- [配置](configuration.md) —— 所有配置键
