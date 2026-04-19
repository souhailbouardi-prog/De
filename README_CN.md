# Hermes Agent - 自进化 AI 代理

<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

## 简介

**Hermes Agent** 是由 [Nous Research](https://nousresearch.com) 开发的自进化 AI 代理工具。它是唯一内置学习循环的代理系统——能够从经验中创建技能、在使用过程中改进技能、自主保留知识、搜索历史对话，并在多会话中建立对用户的深度理解模型。

你可以在 $5 VPS、GPU 集群或几乎无空闲成本的无服务器基础设施上运行它。它不局限于你的笔记本电脑——你可以在云端 VM 上运行它，同时通过 Telegram 与它对话。

## 核心特性

### 🔄 闭环学习系统
- **自主技能创建**：完成复杂任务后自动创建技能
- **技能自改进**：在使用过程中持续优化技能
- **智能记忆管理**：定期提示保存知识
- **跨会话搜索**：FTS5 会话搜索 + LLM 摘要，实现跨会话回忆
- **用户建模**：兼容 [Honcho](https://github.com/plastic-labs/honcho) 辩证用户建模
- **开放标准**：支持 [agentskills.io](https://agentskills.io) 开放技能标准

### 💬 多平台支持
- **CLI 交互**：完整的 TUI（终端 UI），支持多行编辑、斜杠命令自动补全、对话历史、中断重定向、流式工具输出
- **消息平台**：Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant 等——所有平台共享同一网关进程
- **语音支持**：语音备忘录转录、跨平台对话连续性

### ⏰ 定时自动化
- **内置 Cron 调度器**：支持任何平台的任务投递
- **自然语言任务**：每日报告、夜间备份、每周审计——全部用自然语言配置，无人值守运行

### 🤖 代理委派与并行
- **子代理委派**：生成独立的子代理处理并行工作流
- **RPC 脚本调用**：编写通过 RPC 调用工具的 Python 脚本，将多步骤流水线压缩为零上下文成本的轮次

### 🌍 无处不在的运行环境
- **六种终端后端**：本地、Docker、SSH、Daytona、Singularity、Modal
- **无服务器持久化**：Daytona 和 Modal 提供无服务器持久化——代理环境在空闲时休眠，按需唤醒，会话间几乎无成本
- **灵活部署**：在 $5 VPS 或 GPU 集群上运行

### 🧪 研究就绪
- **批量轨迹生成**
- **Atropos RL 环境**
- **轨迹压缩**：用于训练下一代工具调用模型

### 🔌 模型无关
支持任何你想用的模型：
- [Nous Portal](https://portal.nousresearch.com)
- [OpenRouter](https://openrouter.ai)（200+ 模型）
- [NVIDIA NIM](https://build.nvidia.com)（Nemotron）
- [小米 MiMo](https://platform.xiaomimimo.com)
- [z.ai/GLM](https://z.ai)
- [Kimi/Moonshot](https://platform.moonshot.ai)
- [MiniMax](https://www.minimax.io)
- [Hugging Face](https://huggingface.co)
- OpenAI、Anthropic
- 或你自己的端点

使用 `hermes model` 切换模型——无需代码更改，无锁定。

---

## 安装指南

### 方式一：标准安装（网络畅通）

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

支持 Linux、macOS、WSL2 和 Android（Termux）。

### 方式二：本地安装（适合中国用户或离线环境）

如果你在中国或网络环境无法访问 GitHub，可以使用以下方法：

**步骤 1：下载代码**
- 从 GitHub 下载 ZIP 或使用镜像站下载
- 或使用 Git 镜像克隆

**步骤 2：使用本地安装模式**

```bash
# 进入下载的代码目录
cd /path/to/hermes-agent

# 使用 --local 模式安装，指定已下载的目录
bash install.sh --local --dir /path/to/hermes-agent
```

**安装选项说明：**

| 选项 | 说明 |
|------|------|
| `--local` | 使用本地目录，跳过 git clone |
| `--dir PATH` | 指定安装目录路径 |
| `--no-venv` | 不创建虚拟环境 |
| `--skip-setup` | 跳过交互式设置向导 |
| `--hermes-home PATH` | 指定数据目录（默认：~/.hermes） |

**完整示例：**

```bash
# 假设你已将代码下载到 /home/user/hermes-agent
cd /home/user/hermes-agent

# 使用本地目录安装
bash install.sh --local --dir /home/user/hermes-agent

# 或者跳过设置向导（适合自动化部署）
bash install.sh --local --dir /home/user/hermes-agent --skip-setup
```

### 方式三：开发者安装（已克隆仓库）

如果你是开发者，已经克隆了仓库：

```bash
cd hermes-agent
./setup-hermes.sh
```

### Windows 用户

原生 Windows 不支持。请安装 [WSL2](https://learn.microsoft.com/zh-cn/windows/wsl/install) 然后使用上述方式。

---

## 快速入门

### 安装后步骤

```bash
# 重新加载 shell 配置
source ~/.bashrc    # 或 source ~/.zshrc

# 开始对话
hermes
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `hermes` | 启动交互式 CLI，开始对话 |
| `hermes model` | 选择 LLM 提供商和模型 |
| `hermes tools` | 配置启用哪些工具 |
| `hermes config set` | 设置单个配置值 |
| `hermes gateway` | 启动消息网关（Telegram、Discord 等） |
| `hermes setup` | 运行完整设置向导（一次配置所有） |
| `hermes update` | 更新到最新版本 |
| `hermes doctor` | 诊断任何问题 |

### 斜杠命令速查

无论是 CLI 还是消息平台，以下斜杠命令都可用：

| 命令 | 说明 |
|------|------|
| `/new` 或 `/reset` | 开始新对话 |
| `/model [provider:model]` | 切换模型 |
| `/personality [name]` | 设置个性 |
| `/retry`, `/undo` | 重试或撤销上一轮 |
| `/compress`, `/usage`, `/insights` | 压缩上下文、查看使用情况、洞察 |
| `/skills` 或 `/<skill-name>` | 浏览技能 |
| `/stop` | 中断当前工作（消息平台） |
| `/platforms` | 平台特定状态（CLI） |
| `/status`, `/sethome` | 状态、设置主目录（消息平台） |

---

## 项目架构

### 项目结构

```
hermes-agent/
├── run_agent.py              # AIAgent 类 — 核心对话循环
├── model_tools.py            # 工具编排，discover_builtin_tools(), handle_function_call()
├── toolsets.py               # 工具集定义，_HERMES_CORE_TOOLS 列表
├── cli.py                    # HermesCLI 类 — 交互式 CLI 编排器
├── hermes_state.py           # SessionDB — SQLite 会话存储（FTS5 搜索）
├── agent/                    # 代理内部模块
│   ├── prompt_builder.py     # 系统提示词构建
│   ├── context_compressor.py # 自动上下文压缩
│   ├── prompt_caching.py     # Anthropic 提示词缓存
│   ├── auxiliary_client.py   # 辅助 LLM 客户端（视觉、摘要）
│   ├── model_metadata.py     # 模型上下文长度、token 估算
│   ├── display.py            # KawaiiSpinner、工具预览格式化
│   └── skill_commands.py     # 技能斜杠命令（CLI/网关共享）
├── hermes_cli/               # CLI 子命令和设置
│   ├── main.py               # 入口点 — 所有 `hermes` 子命令
│   ├── config.py             # DEFAULT_CONFIG、OPTIONAL_ENV_VARS、迁移
│   ├── commands.py           # 斜杠命令定义 + SlashCommandCompleter
│   ├── setup.py              # 交互式设置向导
│   ├── skin_engine.py        # 皮肤/主题引擎 — CLI 视觉定制
│   ├── skills_config.py      # `hermes skills` — 按平台启用/禁用技能
│   ├── tools_config.py       # `hermes tools` — 按平台启用/禁用工具
│   └── auth.py               # 提供商凭证解析
├── tools/                    # 工具实现（每个工具一个文件）
│   ├── registry.py           # 中央工具注册表（schema、handler、dispatch）
│   ├── terminal_tool.py      # 终端编排
│   ├── file_tools.py         # 文件读写/搜索/补丁
│   ├── web_tools.py          # Web 搜索/提取（Parallel + Firecrawl）
│   ├── browser_tool.py       # 浏览器自动化
│   ├── mcp_tool.py           # MCP 客户端（约 1050 行）
│   └── environments/         # 终端后端（local、docker、ssh、modal、daytona、singularity）
├── gateway/                  # 消息平台网关
│   ├── run.py                # 主循环、斜杠命令、消息分发
│   ├── session.py            # SessionStore — 对话持久化
│   └── platforms/            # 适配器：telegram、discord、slack、whatsapp、homeassistant、signal、qqbot
├── ui-tui/                   # Ink（React）终端 UI — `hermes --tui`
│   ├── src/entry.tsx         # TTY 入口 + render()
│   ├── src/app.tsx           # 主状态机和 UI
│   └── src/components/       # Ink 组件（品牌、Markdown、提示、选择器等）
├── tui_gateway/              # TUI 的 Python JSON-RPC 后端
│   ├── entry.py              # stdio 入口点
│   ├── server.py             # RPC 处理器和会话逻辑
│   └── slash_worker.py       # 斜杠命令的持久 HermesCLI 子进程
├── acp_adapter/              # ACP 服务器（VS Code / Zed / JetBrains 集成）
├── cron/                     # 调度器（jobs.py、scheduler.py）
├── tests/                    # Pytest 测试套件（约 3000 个测试）
└── batch_runner.py           # 并行批量处理
```

### 核心架构

#### 文件依赖链

```
tools/registry.py  (无依赖 — 被所有工具文件导入)
       ↑
tools/*.py  (每个在导入时调用 registry.register())
       ↑
model_tools.py  (导入 tools/registry + 触发工具发现)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

#### AIAgent 核心循环

核心循环在 `run_conversation()` 中，完全同步：

```python
while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

消息遵循 OpenAI 格式：`{"role": "system/user/assistant/tool", ...}`。推理内容存储在 `assistant_msg["reasoning"]` 中。

#### CLI 架构

- **Rich** 用于横幅/面板，**prompt_toolkit** 用于带自动补全的输入
- **KawaiiSpinner** (`agent/display.py`) — API 调用期间的动画表情，工具结果的 `┊` 活动馈送
- `load_cli_config()` 合并硬编码默认值 + 用户配置 YAML
- **皮肤引擎** (`hermes_cli/skin_engine.py`) — 数据驱动的 CLI 主题化
- `process_command()` 根据从中央注册表 `resolve_command()` 解析的规范名称调度

---

## 学习路径

### 新手入门

1. **安装并运行**
   - 按照安装指南完成安装
   - 运行 `hermes setup` 配置 API 密钥
   - 输入 `hermes` 开始第一次对话

2. **理解基本概念**
   - 阅读 `AGENTS.md` 了解项目结构
   - 查看 `run_agent.py` 理解核心循环
   - 了解工具系统如何工作

3. **尝试常用功能**
   - 使用文件工具读取和编辑文件
   - 尝试终端工具执行命令
   - 体验技能系统

### 进阶学习

1. **工具开发**
   - 学习 `tools/registry.py` 的注册机制
   - 参考现有工具（如 `tools/file_tools.py`）
   - 理解工具集（toolsets）的概念

2. **技能系统**
   - 了解技能如何存储在 `~/.hermes/skills/`
   - 学习如何创建和使用技能
   - 理解技能与工具的区别

3. **消息网关**
   - 配置 Telegram/Discord 机器人
   - 理解网关架构
   - 学习平台适配器开发

### 高级开发

1. **核心修改**
   - 修改 `run_agent.py` 的对话循环
   - 扩展 `model_tools.py` 的工具编排
   - 自定义提示词构建器

2. **插件开发**
   - 学习内存插件系统（`plugins/memory/`）
   - 理解 MCP 集成
   - 开发自定义工具集

3. **研究与训练**
   - 使用 `environments/` 进行 RL 训练
   - 轨迹压缩与模型训练
   - 批量轨迹生成

---

## 配置说明

### 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 主配置 | `~/.hermes/config.yaml` | 所有设置 |
| API 密钥 | `~/.hermes/.env` | 环境变量和密钥 |
| 个性定义 | `~/.hermes/SOUL.md` | 代理个性和语气 |
| 技能目录 | `~/.hermes/skills/` | 用户技能存储 |

### 常用配置项

```yaml
# ~/.hermes/config.yaml 示例

model:
  provider: openrouter
  name: anthropic/claude-opus-4.6

display:
  skin: default           # default, ares, mono, slate
  tool_progress: true

tools:
  enabled:
    - terminal
    - file
    - web
```

### 环境变量

在 `~/.hermes/.env` 中配置：

```bash
# LLM 提供商
OPENROUTER_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# 消息平台
TELEGRAM_BOT_TOKEN=your-token
DISCORD_BOT_TOKEN=your-token
SLACK_BOT_TOKEN=your-token

# 其他
NOUS_PORTAL_API_KEY=your-key
```

---

## 常见问题

### Q: 在中国无法访问 GitHub 怎么办？

**A:** 使用 `--local` 安装模式：

1. 通过镜像站或其他方式下载代码
2. 运行：`bash install.sh --local --dir /path/to/downloaded/hermes-agent`

### Q: 支持哪些模型？

**A:** 支持任何兼容 OpenAI API 的模型提供商，包括：
- OpenRouter（200+ 模型）
- Anthropic
- OpenAI
- Nous Portal
- 国内模型（Kimi、智谱、MiniMax 等，通过 OpenRouter 或自定义端点）

### Q: 如何切换模型？

**A:** 使用：
```bash
hermes model                    # 交互式选择
hermes model openrouter/anthropic/claude-opus-4.6   # 直接指定
```

### Q: 如何在服务器上后台运行？

**A:** 使用网关服务：
```bash
hermes gateway install   # 安装为 systemd 服务
hermes gateway start     # 启动服务
```

或手动后台运行：
```bash
nohup hermes gateway > ~/.hermes/logs/gateway.log 2>&1 &
```

### Q: 技能和工具有什么区别？

**A:**
- **工具 (Tools)**: 由代码实现的底层能力（文件操作、终端、Web 搜索等），40+ 内置工具
- **技能 (Skills)**: 由代理从经验中学习或用户创建的高层流程，使用 Markdown 格式定义，可共享和改进

---

## 相关链接

- **官方文档**: https://hermes-agent.nousresearch.com/docs/
- **Discord 社区**: https://discord.gg/NousResearch
- **技能中心**: https://agentskills.io
- **GitHub**: https://github.com/NousResearch/hermes-agent
- **问题反馈**: https://github.com/NousResearch/hermes-agent/issues

---

## 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。

由 [Nous Research](https://nousresearch.com) 开发。
