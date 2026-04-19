---
sidebar_position: 15
title: "Web 仪表板"
description: "基于浏览器的仪表板，用于管理配置、API 密钥、会话、日志、分析、定时任务和技能"
---

# Web 仪表板

Web 仪表板是一个基于浏览器的 UI，用于管理您的 Hermes Agent 安装。您无需编辑 YAML 文件或运行 CLI 命令，而是可以通过干净的 Web 界面配置设置、管理 API 密钥和监控会话。

## 快速开始

```bash
hermes dashboard
```

这会启动本地 Web 服务器并在浏览器中打开 `http://127.0.0.1:9119`。仪表板完全在您的机器上运行 — 没有数据离开 localhost。

### 选项

| 标志 | 默认值 | 描述 |
|------|---------|------|
| `--port` | `9119` | Web 服务器运行的端口 |
| `--host` | `127.0.0.1` | 绑定地址 |
| `--no-open` | — | 不自动打开浏览器 |

```bash
# 自定义端口
hermes dashboard --port 8080

# 绑定到所有接口（在共享网络上使用时要小心）
hermes dashboard --host 0.0.0.0

# 启动时不打开浏览器
hermes dashboard --no-open
```

## 前提条件

Web 仪表板需要 FastAPI 和 Uvicorn。使用以下命令安装：

```bash
pip install hermes-agent[web]
```

如果您使用 `pip install hermes-agent[all]` 安装，web 依赖项已经包含在内。

当您运行 `hermes dashboard` 而没有依赖项时，它会告诉您需要安装什么。如果前端尚未构建且 `npm` 可用，它会在首次启动时自动构建。

## 页面

### 状态

登录页面显示您安装的实时概览：

- **智能体版本**和发布日期
- **网关状态** — 运行/停止、PID、连接的平台及其状态
- **活动会话** — 过去 5 分钟内活动的会话计数
- **最近会话** — 最近 20 个会话的列表，包括模型、消息计数、令牌使用情况和对话预览

状态页面每 5 秒自动刷新一次。

### 配置

基于表单的 `config.yaml` 编辑器。所有 150+ 配置字段都是从 `DEFAULT_CONFIG` 自动发现的，并组织成选项卡式类别：

- **model** — 默认模型、提供商、基础 URL、推理设置
- **terminal** — 后端（本地/ docker/ ssh/ modal）、超时、shell 偏好
- **display** — 皮肤、工具进度、恢复显示、spinner 设置
- **agent** — 最大迭代次数、网关超时、服务层级
- **delegation** — 子智能体限制、推理努力
- **memory** — 提供商选择、上下文注入设置
- **approvals** — 危险命令批准模式（ask/yolo/deny）
- 更多 — config.yaml 的每个部分都有相应的表单字段

具有已知有效值的字段（终端后端、皮肤、批准模式等）渲染为下拉菜单。布尔值渲染为切换开关。其他所有内容都是文本输入。

**操作：**

- **保存** — 立即将更改写入 `config.yaml`
- **重置为默认值** — 将所有字段恢复为默认值（点击保存前不会保存）
- **导出** — 将当前配置下载为 JSON
- **导入** — 上传 JSON 配置文件以替换当前值

:::tip
配置更改在下次智能体会话或网关重启时生效。Web 仪表板编辑的是与 `hermes config set` 和网关读取的相同 `config.yaml` 文件。
:::

### API 密钥

管理存储 API 密钥和凭据的 `.env` 文件。密钥按类别分组：

- **LLM 提供商** — OpenRouter、Anthropic、OpenAI、DeepSeek 等
- **工具 API 密钥** — Browserbase、Firecrawl、Tavily、ElevenLabs 等
- **消息平台** — Telegram、Discord、Slack 机器人令牌等
- **智能体设置** — 非秘密环境变量，如 `API_SERVER_ENABLED`

每个密钥显示：
- 它是否当前已设置（带有值的模糊预览）
- 它的用途描述
- 指向提供商注册/密钥页面的链接
- 设置或更新值的输入字段
- 删除它的按钮

高级/很少使用的密钥默认隐藏在切换开关后面。

### 会话

浏览和检查所有智能体会话。每一行显示会话标题、源平台图标（CLI、Telegram、Discord、Slack、cron）、模型名称、消息计数、工具调用计数以及它活跃的时间。活动会话用脉冲徽章标记。

- **搜索** — 使用 FTS5 对所有消息内容进行全文搜索。结果显示突出显示的片段，展开时自动滚动到第一个匹配的消息。
- **展开** — 点击会话加载其完整消息历史。消息按角色（用户、助手、系统、工具）进行颜色编码，并渲染为带有语法高亮的 Markdown。
- **工具调用** — 带有工具调用的助手消息显示带有函数名称和 JSON 参数的可折叠块。
- **删除** — 使用垃圾桶图标删除会话及其消息历史。

### 日志

查看智能体、网关和错误日志文件，具有过滤和实时跟踪功能。

- **文件** — 在 `agent`、`errors` 和 `gateway` 日志文件之间切换
- **级别** — 按日志级别过滤：ALL、DEBUG、INFO、WARNING 或 ERROR
- **组件** — 按源组件过滤：all、gateway、agent、tools、cli 或 cron
- **行数** — 选择要显示的行数（50、100、200 或 500）
- **自动刷新** — 切换每 5 秒轮询新日志行的实时跟踪
- **颜色编码** — 日志行按严重程度着色（错误为红色，警告为黄色，调试为暗淡）

### 分析

从会话历史计算的使用和成本分析。选择时间段（7、30 或 90 天）查看：

- **摘要卡片** — 总令牌（输入/输出）、缓存命中率、总估计或实际成本，以及总会话计数和每日平均值
- **每日令牌图表** — 堆叠条形图，显示每天的输入和输出令牌使用情况，悬停工具提示显示细分和成本
- **每日细分表** — 每天的日期、会话计数、输入令牌、输出令牌、缓存命中率和成本
- **按模型细分** — 显示每个使用的模型、其会话计数、令牌使用情况和估计成本的表

### Cron

创建和管理按定期计划运行智能体提示的定时 cron 任务。

- **创建** — 填写名称（可选）、提示、cron 表达式（例如 `0 9 * * *`）和交付目标（本地、Telegram、Discord、Slack 或电子邮件）
- **任务列表** — 每个任务显示其名称、提示预览、调度表达式、状态徽章（启用/暂停/错误）、交付目标、上次运行时间和下次运行时间
- **暂停 / 恢复** — 在活动和暂停状态之间切换任务
- **立即触发** — 在正常计划之外立即执行任务
- **删除** — 永久删除 cron 任务

### 技能

浏览、搜索和切换技能和工具集。技能从 `~/.hermes/skills/` 加载并按类别分组。

- **搜索** — 按名称、描述或类别过滤技能和工具集
- **类别过滤器** — 点击类别药丸缩小列表（例如 MLOps、MCP、红队、AI）
- **切换** — 使用开关启用或禁用单个技能。更改在下次会话时生效。
- **工具集** — 单独的部分显示内置工具集（文件操作、网页浏览等）及其活动/非活动状态、设置要求和包含的工具列表

:::warning 安全
Web 仪表板读取和写入包含 API 密钥和机密的 `.env` 文件。它默认绑定到 `127.0.0.1` — 只能从您的本地机器访问。如果您绑定到 `0.0.0.0`，网络上的任何人都可以查看和修改您的凭据。仪表板本身没有身份验证。
:::

## `/reload` 斜杠命令

仪表板 PR 还在交互式 CLI 中添加了 `/reload` 斜杠命令。通过 Web 仪表板（或直接编辑 `.env`）更改 API 密钥后，在活动 CLI 会话中使用 `/reload` 来在不重启的情况下获取更改：

```
You → /reload
  Reloaded .env (3 var(s) updated)
```

这会将 `~/.hermes/.env` 重新读入运行进程的环境。当您通过仪表板添加了新的提供商密钥并想立即使用它时很有用。

## REST API

Web 仪表板公开前端使用的 REST API。您也可以直接调用这些端点进行自动化：

### GET /api/status

返回智能体版本、网关状态、平台状态和活动会话计数。

### GET /api/sessions

返回最近 20 个会话的元数据（模型、令牌计数、时间戳、预览）。

### GET /api/config

以 JSON 形式返回当前 `config.yaml` 内容。

### GET /api/config/defaults

返回默认配置值。

### GET /api/config/schema

返回描述每个配置字段的架构 — 类型、描述、类别和适用的选择选项。前端使用此架构为每个字段渲染正确的输入小部件。

### PUT /api/config

保存新配置。主体：`{"config": {...}}`。

### GET /api/env

返回所有已知环境变量，包括它们的设置/未设置状态、模糊值、描述和类别。

### PUT /api/env

设置环境变量。主体：`{"key": "VAR_NAME", "value": "secret"}`。

### DELETE /api/env

删除环境变量。主体：`{"key": "VAR_NAME"}`。

### GET /api/sessions/{session_id}

返回单个会话的元数据。

### GET /api/sessions/{session_id}/messages

返回会话的完整消息历史，包括工具调用和时间戳。

### GET /api/sessions/search

对消息内容进行全文搜索。查询参数：`q`。返回带有突出显示片段的匹配会话 ID。

### DELETE /api/sessions/{session_id}

删除会话及其消息历史。

### GET /api/logs

返回日志行。查询参数：`file`（agent/errors/gateway）、`lines`（计数）、`level`、`component`。

### GET /api/analytics/usage

返回令牌使用情况、成本和会话分析。查询参数：`days`（默认 30）。响应包括每日细分和按模型聚合。

### GET /api/cron/jobs

返回所有配置的 cron 任务及其状态、计划和运行历史。

### POST /api/cron/jobs

创建新的 cron 任务。主体：`{"prompt": "...", "schedule": "0 9 * * *", "name": "...", "deliver": "local"}`。

### POST /api/cron/jobs/{job_id}/pause

暂停 cron 任务。

### POST /api/cron/jobs/{job_id}/resume

恢复暂停的 cron 任务。

### POST /api/cron/jobs/{job_id}/trigger

在计划之外立即触发 cron 任务。

### DELETE /api/cron/jobs/{job_id}

删除 cron 任务。

### GET /api/skills

返回所有技能及其名称、描述、类别和启用状态。

### PUT /api/skills/toggle

启用或禁用技能。主体：`{"name": "skill-name", "enabled": true}`。

### GET /api/tools/toolsets

返回所有工具集及其标签、描述、工具列表和活动/已配置状态。

## CORS

Web 服务器将 CORS 限制为仅 localhost 来源：

- `http://localhost:9119` / `http://127.0.0.1:9119`（生产）
- `http://localhost:3000` / `http://127.0.0.1:3000`
- `http://localhost:5173` / `http://127.0.0.1:5173`（Vite 开发服务器）

如果您在自定义端口上运行服务器，该来源会自动添加。

## 开发

如果您正在为 Web 仪表板前端做贡献：

```bash
# 终端 1：启动后端 API
hermes dashboard --no-open

# 终端 2：启动带有 HMR 的 Vite 开发服务器
cd web/
npm install
npm run dev
```

Vite 开发服务器在 `http://localhost:5173` 上将 `/api` 请求代理到 `http://127.0.0.1:9119` 的 FastAPI 后端。

前端使用 React 19、TypeScript、Tailwind CSS v4 和 shadcn/ui 风格组件构建。生产构建输出到 `hermes_cli/web_dist/`，FastAPI 服务器将其作为静态 SPA 提供。

## 更新时自动构建

当您运行 `hermes update` 时，如果 `npm` 可用，Web 前端会自动重建。这使仪表板与代码更新保持同步。如果未安装 `npm`，更新会跳过前端构建，`hermes dashboard` 会在首次启动时构建它。

## 主题

仪表板支持更改颜色、叠加效果和整体感觉的视觉主题。从标题栏实时切换主题 — 点击语言切换器旁边的调色板图标。

### 内置主题

| 主题 | 描述 |
|------|------|
| **Hermes Teal** | 经典深青色（默认） |
| **Midnight** | 深蓝色-紫色，带有冷色调装饰 |
| **Ember** | 温暖的深红色和青铜色 |
| **Mono** | 干净的灰度，极简 |
| **Cyberpunk** | 黑色背景上的霓虹绿色 |
| **Rosé** | 柔和的粉色和温暖的象牙色 |

主题选择会持久化到 `config.yaml` 中的 `dashboard.theme`，并在页面加载时恢复。

### 自定义主题

在 `~/.hermes/dashboard-themes/` 中创建 YAML 文件：

```yaml
# ~/.hermes/dashboard-themes/ocean.yaml
name: ocean
label: Ocean
description: Deep sea blues with coral accents

colors:
  background: "#0a1628"
  foreground: "#e0f0ff"
  card: "#0f1f35"
  card-foreground: "#e0f0ff"
  primary: "#ff6b6b"
  primary-foreground: "#0a1628"
  secondary: "#152540"
  secondary-foreground: "#e0f0ff"
  muted: "#1a2d4a"
  muted-foreground: "#7899bb"
  accent: "#1f3555"
  accent-foreground: "#e0f0ff"
  destructive: "#fb2c36"
  destructive-foreground: "#fff"
  success: "#4ade80"
  warning: "#fbbf24"
  border: "color-mix(in srgb, #ff6b6b 15%, transparent)"
  input: "color-mix(in srgb, #ff6b6b 15%, transparent)"
  ring: "#ff6b6b"
  popover: "#0f1f35"
  popover-foreground: "#e0f0ff"

overlay:
  noiseOpacity: 0.08
  noiseBlendMode: color-dodge
  warmGlowOpacity: 0.15
  warmGlowColor: "rgba(255,107,107,0.2)"
```

21 个颜色令牌直接映射到仪表板中使用的 CSS 自定义属性。自定义主题需要所有字段。`overlay` 部分是可选的 — 它控制纹理和环境光效果。

创建文件后刷新仪表板。自定义主题会与内置主题一起出现在主题选择器中。

### 主题 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/dashboard/themes` | GET | 列出可用主题 + 活动名称 |
| `/api/dashboard/theme` | PUT | 设置活动主题。主体：`{"name": "midnight"}` |