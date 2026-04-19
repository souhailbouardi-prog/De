---
title: 浏览器自动化
description: 使用多个提供商、通过 CDP 的本地 Chrome 或云浏览器进行网络交互、表单填写、抓取等操作。
sidebar_label: 浏览器
sidebar_position: 5
---

# 浏览器自动化

Hermes Agent 包含完整的浏览器自动化工具集，具有多个后端选项：

- **Browserbase 云模式** 通过 [Browserbase](https://browserbase.com) 提供托管云浏览器和反机器人工具
- **Browser Use 云模式** 通过 [Browser Use](https://browser-use.com) 作为替代云浏览器提供商
- **Firecrawl 云模式** 通过 [Firecrawl](https://firecrawl.dev) 提供带有内置抓取功能的云浏览器
- **Camofox 本地模式** 通过 [Camofox](https://github.com/jo-inc/camofox-browser) 提供本地反检测浏览（基于 Firefox 的指纹欺骗）
- **通过 CDP 的本地 Chrome** — 使用 `/browser connect` 将浏览器工具连接到您自己的 Chrome 实例
- **本地浏览器模式** 通过 `agent-browser` CLI 和本地 Chromium 安装

在所有模式下，智能体都可以导航网站、与页面元素交互、填写表单和提取信息。

## 概述

页面被表示为**可访问性树**（基于文本的快照），使其成为 LLM 智能体的理想选择。交互式元素获得引用 ID（如 `@e1`、`@e2`），智能体使用这些 ID 进行点击和输入。

关键功能：

- **多提供商云执行** — Browserbase、Browser Use 或 Firecrawl — 无需本地浏览器
- **本地 Chrome 集成** — 通过 CDP 连接到您运行的 Chrome 进行实际浏览
- **内置隐身** — 随机指纹、CAPTCHA 解决、住宅代理（Browserbase）
- **会话隔离** — 每个任务获得自己的浏览器会话
- **自动清理** — 非活动会话在超时后关闭
- **视觉分析** — 截图 + AI 分析用于视觉理解

## 设置

### Browserbase 云模式

要使用 Browserbase 托管的云浏览器，请添加：

```bash
# 添加到 ~/.hermes/.env
BROWSERBASE_API_KEY=***
BROWSERBASE_PROJECT_ID=your-project-id-here
```

在 [browserbase.com](https://browserbase.com) 获取您的凭证。

### Browser Use 云模式

要使用 Browser Use 作为您的云浏览器提供商，请添加：

```bash
# 添加到 ~/.hermes/.env
BROWSER_USE_API_KEY=***
```

在 [browser-use.com](https://browser-use.com) 获取您的 API 密钥。Browser Use 通过其 REST API 提供云浏览器。如果同时设置了 Browserbase 和 Browser Use 凭证，Browserbase 优先。

### Firecrawl 云模式

要使用 Firecrawl 作为您的云浏览器提供商，请添加：

```bash
# 添加到 ~/.hermes/.env
FIRECRAWL_API_KEY=fc-***
```

在 [firecrawl.dev](https://firecrawl.dev) 获取您的 API 密钥。然后选择 Firecrawl 作为您的浏览器提供商：

```bash
hermes setup tools
# → 浏览器自动化 → Firecrawl
```

可选设置：

```bash
# 自托管 Firecrawl 实例（默认：https://api.firecrawl.dev）
FIRECRAWL_API_URL=http://localhost:3002

# 会话 TTL（默认：300 秒）
FIRECRAWL_BROWSER_TTL=600
```

### Camofox 本地模式

[Camofox](https://github.com/jo-inc/camofox-browser) 是一个自托管的 Node.js 服务器，包装了 Camoufox（一个带有 C++ 指纹欺骗的 Firefox 分支）。它提供本地反检测浏览，无需云依赖。

```bash
# 安装和运行
git clone https://github.com/jo-inc/camofox-browser && cd camofox-browser
npm install && npm start   # 首次运行时下载 Camoufox (~300MB)

# 或通过 Docker
docker run -d --network host -e CAMOFOX_PORT=9377 jo-inc/camofox-browser
```

然后在 `~/.hermes/.env` 中设置：

```bash
CAMOFOX_URL=http://localhost:9377
```

或通过 `hermes tools` → 浏览器自动化 → Camofox 进行配置。

当设置了 `CAMOFOX_URL` 时，所有浏览器工具会自动通过 Camofox 路由，而不是 Browserbase 或 agent-browser。

#### 持久浏览器会话

默认情况下，每个 Camofox 会话获得一个随机身份 — cookies 和登录状态不会在智能体重启后保留。要启用持久浏览器会话：

```yaml
# 在 ~/.hermes/config.yaml 中
browser:
  camofox:
    managed_persistence: true
```

启用后，Hermes 向 Camofox 发送稳定的配置文件范围身份。Camofox 服务器将此身份映射到持久浏览器配置文件目录，因此 cookies、登录状态和 localStorage 在重启后仍然保留。不同的 Hermes 配置文件获得不同的浏览器配置文件（配置文件隔离）。

:::note
Camofox 服务器还必须在服务器端配置 `CAMOFOX_PROFILE_DIR` 才能使持久化工作。
:::

#### VNC 实时查看

当 Camofox 在有头模式（带有可见浏览器窗口）下运行时，它会在健康检查响应中暴露 VNC 端口。Hermes 自动发现这一点并在导航响应中包含 VNC URL，因此智能体可以共享链接让您实时观看浏览器。

### 通过 CDP 的本地 Chrome（`/browser connect`）

您可以通过 Chrome DevTools 协议（CDP）将 Hermes 浏览器工具连接到您自己运行的 Chrome 实例，而不是使用云提供商。这在您希望实时查看智能体正在做什么、与需要您自己的 cookies/会话的页面交互或避免云浏览器成本时非常有用。

在 CLI 中使用：

```
/browser connect              # 连接到 ws://localhost:9222 上的 Chrome
/browser connect ws://host:port  # 连接到特定的 CDP 端点
/browser status               # 检查当前连接
/browser disconnect            # 断开连接并返回云/本地模式
```

如果 Chrome 尚未以远程调试模式运行，Hermes 将尝试使用 `--remote-debugging-port=9222` 自动启动它。

:::tip
要手动启动启用了 CDP 的 Chrome：
```bash
# Linux
google-chrome --remote-debugging-port=9222

# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
```
:::

通过 CDP 连接时，所有浏览器工具（`browser_navigate`、`browser_click` 等）在您的实时 Chrome 实例上操作，而不是启动云会话。

### 本地浏览器模式

如果您**不**设置任何云凭证且不使用 `/browser connect`，Hermes 仍然可以通过由 `agent-browser` 驱动的本地 Chromium 安装使用浏览器工具。

### 可选环境变量

```bash
# 用于更好地解决 CAPTCHA 的住宅代理（默认："true"）
BROWSERBASE_PROXIES=true

# 带有自定义 Chromium 的高级隐身 — 需要 Scale Plan（默认："false"）
BROWSERBASE_ADVANCED_STEALTH=false

# 断开后会话重连 — 需要付费计划（默认："true"）
BROWSERBASE_KEEP_ALIVE=true

# 自定义会话超时（毫秒，默认：项目默认值）
# 示例：600000（10分钟），1800000（30分钟）
BROWSERBASE_SESSION_TIMEOUT=600000

# 自动清理前的非活动超时（秒，默认：120）
BROWSER_INACTIVITY_TIMEOUT=120
```

### 安装 agent-browser CLI

```bash
npm install -g agent-browser
# 或在仓库中本地安装：
npm install
```

:::info
`browser` 工具集必须包含在您的配置的 `toolsets` 列表中，或通过 `hermes config set toolsets '["hermes-cli", "browser"]'` 启用。
:::

## 可用工具

### `browser_navigate`

导航到 URL。必须在任何其他浏览器工具之前调用。初始化 Browserbase 会话。

```
Navigate to https://github.com/NousResearch
```

:::tip
对于简单的信息检索，首选 `web_search` 或 `web_extract` — 它们更快更便宜。当您需要**与页面交互**时（点击按钮、填写表单、处理动态内容），使用浏览器工具。
:::

### `browser_snapshot`

获取当前页面可访问性树的基于文本的快照。返回带有引用 ID（如 `@e1`、`@e2`）的交互式元素，用于 `browser_click` 和 `browser_type`。

- **`full=false`**（默认）：紧凑视图，仅显示交互式元素
- **`full=true`**：完整页面内容

超过 8000 个字符的快照会由 LLM 自动总结。

### `browser_click`

点击由快照中的引用 ID 标识的元素。

```
Click @e5 to press the "Sign In" button
```

### `browser_type`

在输入字段中输入文本。首先清除字段，然后输入新文本。

```
Type "hermes agent" into the search field @e3
```

### `browser_scroll`

向上或向下滚动页面以显示更多内容。

```
Scroll down to see more results
```

### `browser_press`

按下键盘按键。用于提交表单或导航。

```
Press Enter to submit the form
```

支持的按键：`Enter`、`Tab`、`Escape`、`ArrowDown`、`ArrowUp` 等。

### `browser_back`

导航回浏览器历史记录中的上一页。

### `browser_get_images`

列出当前页面上的所有图像及其 URL 和替代文本。用于查找要分析的图像。

### `browser_vision`

拍摄屏幕截图并使用视觉 AI 进行分析。当文本快照无法捕获重要的视觉信息时使用此工具 — 对于 CAPTCHA、复杂布局或视觉验证挑战特别有用。

屏幕截图被持久保存，文件路径与 AI 分析一起返回。在消息平台（Telegram、Discord、Slack、WhatsApp）上，您可以要求智能体分享屏幕截图 — 它将通过 `MEDIA:` 机制作为原生照片附件发送。

```
What does the chart on this page show?
```

屏幕截图存储在 `~/.hermes/cache/screenshots/` 中，并在 24 小时后自动清理。

### `browser_console`

获取当前页面的浏览器控制台输出（日志/警告/错误消息）和未捕获的 JavaScript 异常。对于检测不出现在可访问性树中的静默 JS 错误至关重要。

```
Check the browser console for any JavaScript errors
```

使用 `clear=True` 在读取后清除控制台，以便后续调用只显示新消息。

## 实用示例

### 填写 Web 表单

```
User: Sign up for an account on example.com with my email john@example.com

Agent workflow:
1. browser_navigate("https://example.com/signup")
2. browser_snapshot()  → sees form fields with refs
3. browser_type(ref="@e3", text="john@example.com")
4. browser_type(ref="@e5", text="SecurePass123")
5. browser_click(ref="@e8")  → clicks "Create Account"
6. browser_snapshot()  → confirms success
```

### 研究动态内容

```
User: What are the top trending repos on GitHub right now?

Agent workflow:
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → reads trending repo list
3. Returns formatted results
```

## 会话录制

自动将会话录制为 WebM 视频文件：

```yaml
browser:
  record_sessions: true  # 默认：false
```

启用后，录制会在第一次 `browser_navigate` 时自动开始，并在会话关闭时保存到 `~/.hermes/browser_recordings/`。在本地和云（Browserbase）模式下都有效。超过 72 小时的录制会自动清理。

## 隐身功能

Browserbase 提供自动隐身功能：

| 功能 | 默认 | 说明 |
|---------|---------|-------|
| 基本隐身 | 始终开启 | 随机指纹、视口随机化、CAPTCHA 解决 |
| 住宅代理 | 开启 | 通过住宅 IP 路由以获得更好的访问 |
| 高级隐身 | 关闭 | 自定义 Chromium 构建，需要 Scale Plan |
| 保持活跃 | 开启 | 网络中断后会话重连 |

:::note
如果您的计划中没有付费功能，Hermes 会自动回退 — 首先禁用 `keepAlive`，然后禁用代理 — 这样在免费计划中浏览仍然可以工作。
:::

## 会话管理

- 每个任务通过 Browserbase 获得一个隔离的浏览器会话
- 会话在非活动后自动清理（默认：2 分钟）
- 后台线程每 30 秒检查一次过期会话
- 进程退出时运行紧急清理以防止会话孤儿
- 会话通过 Browserbase API 释放（`REQUEST_RELEASE` 状态）

## 限制

- **基于文本的交互** — 依赖可访问性树，而非像素坐标
- **快照大小** — 大页面可能在 8000 字符处被截断或由 LLM 总结
- **会话超时** — 云会话根据您提供商的计划设置过期
- **成本** — 云会话消耗提供商信用额度；会话在对话结束或非活动后自动清理。使用 `/browser connect` 进行免费本地浏览。
- **无文件下载** — 无法从浏览器下载文件
