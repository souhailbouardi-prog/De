# Hermes Agent v0.8.0 (v2026.4.8)

**发布日期:** 2026年4月8日

> 智能发布 — 后台任务自动通知、Nous Portal上的免费MiMo v2 Pro、跨所有平台的实时模型切换、自优化GPT/Codex指导、原生Google AI Studio、智能非活动超时、审批按钮、MCP OAuth 2.1，以及209个合并PR和82个已解决问题。

---

## ✨ 亮点

- **后台进程自动通知 (`notify_on_complete`)** — 后台任务现在可以在完成时自动通知智能体。启动长时间运行的进程（AI模型训练、测试套件、部署、构建），智能体在完成时会收到通知 — 无需轮询。智能体可以继续处理其他事情，并在结果到达时获取它们。([#5779](https://github.com/NousResearch/hermes-agent/pull/5779))

- **Nous Portal上的免费小米MiMo v2 Pro** — Nous Portal现在支持免费级别的小米MiMo v2 Pro模型用于辅助任务（压缩、视觉、摘要），在模型选择中包含免费级模型门控和定价显示。([#6018](https://github.com/NousResearch/hermes-agent/pull/6018), [#5880](https://github.com/NousResearch/hermes-agent/pull/5880))

- **实时模型切换 (`/model` 命令)** — 从CLI、Telegram、Discord、Slack或任何网关平台在会话中途切换模型和提供商。聚合器感知解析在可能的情况下保持您在OpenRouter/Nous上，在需要时自动跨提供商回退。Telegram和Discord上带有内联按钮的交互式模型选择器。([#5181](https://github.com/NousResearch/hermes-agent/pull/5181), [#5742](https://github.com/NousResearch/hermes-agent/pull/5742))

- **自优化GPT/Codex工具使用指导** — 智能体通过自动行为基准测试诊断并修补了GPT和Codex工具调用中的5种失败模式，显著提高了OpenAI模型的可靠性。包括执行纪律指导和结构化推理的仅思考预填充继续。([#6120](https://github.com/NousResearch/hermes-agent/pull/6120), [#5414](https://github.com/NousResearch/hermes-agent/pull/5414), [#5931](https://github.com/NousResearch/hermes-agent/pull/5931))

- **Google AI Studio (Gemini) 原生提供商** — 通过Google的AI Studio API直接访问Gemini模型。包括自动models.dev注册表集成，用于跨任何提供商的实时上下文长度检测。([#5577](https://github.com/NousResearch/hermes-agent/pull/5577))

- **基于非活动的智能体超时** — 网关和cron超时现在跟踪实际工具活动，而不是挂钟时间。积极工作的长时间运行任务永远不会被杀死 — 只有真正空闲的智能体会超时。([#5389](https://github.com/NousResearch/hermes-agent/pull/5389), [#5440](https://github.com/NousResearch/hermes-agent/pull/5440))

- **Slack和Telegram上的审批按钮** — 通过原生平台按钮进行危险命令审批，而不是输入`/approve`。Slack获得线程上下文保存；Telegram获得审批状态的表情反应。([#5890](https://github.com/NousResearch/hermes-agent/pull/5890), [#5975](https://github.com/NousResearch/hermes-agent/pull/5975))

- **MCP OAuth 2.1 PKCE + OSV恶意软件扫描** — 用于MCP服务器认证的完全符合标准的OAuth，以及通过OSV漏洞数据库对MCP扩展包的自动恶意软件扫描。([#5420](https://github.com/NousResearch/hermes-agent/pull/5420), [#5305](https://github.com/NousResearch/hermes-agent/pull/5305))

- **集中式日志记录和配置验证** — 结构化日志记录到`~/.hermes/logs/`（agent.log + errors.log），带有`hermes logs`命令用于跟踪和过滤。配置结构验证在启动时捕获格式错误的YAML，防止其导致神秘故障。([#5430](https://github.com/NousResearch/hermes-agent/pull/5430), [#5426](https://github.com/NousResearch/hermes-agent/pull/5426))

- **插件系统扩展** — 插件现在可以注册CLI子命令，接收带有相关ID的请求范围API钩子，在安装期间提示所需的环境变量，并挂钩到会话生命周期事件（完成/重置）。([#5295](https://github.com/NousResearch/hermes-agent/pull/5295), [#5427](https://github.com/NousResearch/hermes-agent/pull/5427), [#5470](https://github.com/NousResearch/hermes-agent/pull/5470), [#6129](https://github.com/NousResearch/hermes-agent/pull/6129))

- **Matrix Tier 1和平台加固** — Matrix获得反应、已读回执、富文本格式和房间管理。Discord添加频道控制和忽略频道。Signal获得完整的MEDIA:标签传递。Mattermost获得文件附件。所有平台的全面可靠性修复。([#5275](https://github.com/NousResearch/hermes-agent/pull/5275), [#5975](https://github.com/NousResearch/hermes-agent/pull/5975), [#5602](https://github.com/NousResearch/hermes-agent/pull/5602))

- **安全加固** — 整合SSRF保护、时序攻击缓解、tar遍历预防、凭证泄漏防护、cron路径遍历加固和跨会话隔离。所有后端的终端工作目录清理。([#5944](https://github.com/NousResearch/hermes-agent/pull/5944), [#5613](https://github.com/NousResearch/hermes-agent/pull/5613), [#5629](https://github.com/NousResearch/hermes-agent/pull/5629))

---

## 🏗️ 核心智能体与架构

### 提供商与模型支持
- **原生Google AI Studio (Gemini)提供商** 带有models.dev集成，用于自动上下文长度检测 ([#5577](https://github.com/NousResearch/hermes-agent/pull/5577))
- **`/model`命令 — 完整的提供商+模型系统改革** — 通过聚合器感知解析在CLI和所有网关平台上实时切换 ([#5181](https://github.com/NousResearch/hermes-agent/pull/5181))
- **Telegram和Discord的交互式模型选择器** — 基于内联按钮的模型选择 ([#5742](https://github.com/NousResearch/hermes-agent/pull/5742))
- **Nous Portal免费级模型门控** 在模型选择中带有定价显示 ([#5880](https://github.com/NousResearch/hermes-agent/pull/5880))
- **模型定价显示** 用于OpenRouter和Nous Portal提供商 ([#5416](https://github.com/NousResearch/hermes-agent/pull/5416))
- **xAI (Grok)提示缓存** 通过`x-grok-conv-id`标头 ([#5604](https://github.com/NousResearch/hermes-agent/pull/5604))
- **Grok添加到工具使用强制执行模型** 用于直接xAI使用 ([#5595](https://github.com/NousResearch/hermes-agent/pull/5595))
- **MiniMax TTS提供商** (speech-2.8) ([#4963](https://github.com/NousResearch/hermes-agent/pull/4963))
- **非智能体模型警告** — 当加载不是为工具使用设计的Hermes LLM模型时警告用户 ([#5378](https://github.com/NousResearch/hermes-agent/pull/5378))
- **Ollama Cloud认证、/model切换持久性** 和别名制表符补全 ([#5269](https://github.com/NousResearch/hermes-agent/pull/5269))
- **在OpenCode Go模型名称中保留点** (minimax-m2.7, glm-4.5, kimi-k2.5) ([#5597](https://github.com/NousResearch/hermes-agent/pull/5597))