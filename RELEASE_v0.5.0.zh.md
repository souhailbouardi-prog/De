# Hermes Agent v0.5.0 (v2026.3.28)

**发布日期:** 2026年3月28日

> 加固发布 — Hugging Face提供商、/model命令全面改革、Telegram私人聊天主题、原生Modal SDK、插件生命周期钩子、GPT模型的工具使用强制执行、Nix flake、50+安全和可靠性修复，以及全面的供应链审计。

---

## ✨ 亮点

- **Nous Portal现在支持400+模型** — Nous Research推理门户已大幅扩展，让Hermes Agent用户通过单个提供商端点访问超过400个模型

- **Hugging Face作为一流推理提供商** — 与HF Inference API的完整集成，包括映射到OpenRouter类似物的精选智能体模型选择器、实时`/models`端点探测和设置向导流程 ([#3419](https://github.com/NousResearch/hermes-agent/pull/3419), [#3440](https://github.com/NousResearch/hermes-agent/pull/3440))

- **Telegram私人聊天主题** — 基于项目的对话，每个主题都有功能技能绑定，在单个Telegram聊天中启用隔离的工作流程 ([#3163](https://github.com/NousResearch/hermes-agent/pull/3163))

- **原生Modal SDK后端** — 用原生Modal SDK (`Sandbox.create.aio` + `exec.aio`) 替换swe-rex依赖，消除隧道并简化Modal终端后端 ([#3538](https://github.com/NousResearch/hermes-agent/pull/3538))

- **插件生命周期钩子激活** — `pre_llm_call`、`post_llm_call`、`on_session_start`和`on_session_end`钩子现在在智能体循环和CLI/网关中触发，完成插件钩子系统 ([#3542](https://github.com/NousResearch/hermes-agent/pull/3542))

- **改进的OpenAI模型可靠性** — 添加了`GPT_TOOL_USE_GUIDANCE`以防止GPT模型描述预期操作而不是进行工具调用，以及自动从对话历史中剥离导致模型在回合间避免使用工具的过时预算警告 ([#3528](https://github.com/NousResearch/hermes-agent/pull/3528))

- **Nix flake** — 完整的uv2nix构建、带有持久容器模式的NixOS模块、从Python源代码自动生成的配置键，以及对智能体友好的后缀PATHs ([#20](https://github.com/NousResearch/hermes-agent/pull/20), [#3274](https://github.com/NousResearch/hermes-agent/pull/3274), [#3061](https://github.com/NousResearch/hermes-agent/pull/3061)) 由@alt-glitch提供

- **供应链加固** — 移除了被入侵的`litellm`依赖，固定了所有依赖版本范围，使用哈希重新生成`uv.lock`，添加了扫描PR中供应链攻击模式的CI工作流，并更新了依赖以修复CVE ([#2796](https://github.com/NousResearch/hermes-agent/pull/2796), [#2810](https://github.com/NousResearch/hermes-agent/pull/2810), [#2812](https://github.com/NousResearch/hermes-agent/pull/2812), [#2816](https://github.com/NousResearch/hermes-agent/pull/2816), [#3073](https://github.com/NousResearch/hermes-agent/pull/3073))

- **Anthropic输出限制修复** — 用每个模型的原生输出限制（Opus 4.6为128K，Sonnet 4.6为64K）替换硬编码的16K `max_tokens`，修复了直接Anthropic API上的"响应被截断"和思考预算耗尽问题 ([#3426](https://github.com/NousResearch/hermes-agent/pull/3426), [#3444](https://github.com/NousResearch/hermes-agent/pull/3444))

---

## 🏗️ 核心智能体与架构

### 新提供商：Hugging Face
- 一流的Hugging Face Inference API集成，带有认证、设置向导和模型选择器 ([#3419](https://github.com/NousResearch/hermes-agent/pull/3419))
- 精选模型列表，将OpenRouter智能体默认值映射到HF等效项 — 具有8+精选模型的提供商跳过实时`/models`探测以提高速度 ([#3440](https://github.com/NousResearch/hermes-agent/pull/3440))
- 将glm-5-turbo添加到Z.AI提供商模型列表 ([#3095](https://github.com/NousResearch/hermes-agent/pull/3095))

### 提供商与模型改进
- `/model`命令全面改革 — 提取了CLI和网关的共享`switch_model()`管道、自定义端点支持、提供商感知路由 ([#2795](https://github.com/NousResearch/hermes-agent/pull/2795), [#2799](https://github.com/NousResearch/hermes-agent/pull/2799))
- 移除CLI和网关中的`/model`斜杠命令，改用`hermes model`子命令 ([#3080](https://github.com/NousResearch/hermes-agent/pull/3080))
- 保留`custom`提供商，而不是静默重新映射到`openrouter` ([#2792](https://github.com/NousResearch/hermes-agent/pull/2792))
- 从config.yaml读取根级别的`provider`和`base_url`到模型配置 ([#3112](https://github.com/NousResearch/hermes-agent/pull/3112))
- 使Nous Portal模型slug与OpenRouter命名对齐 ([#3253](https://github.com/NousResearch/hermes-agent/pull/3253))
- 修复阿里巴巴提供商默认端点和模型列表 ([#3484](https://github.com/NousResearch/hermes-agent/pull/3484))
- 允许MiniMax用户覆盖`/v1` → `/anthropic`自动更正 ([#3553](https://github.com/NousResearch/hermes-agent/pull/3553))
- 将OAuth令牌刷新迁移到`platform.claude.com`并带有回退 ([#3246](https://github.com/NousResearch/hermes-agent/pull/3246))

### 智能体循环与对话
- **改进的OpenAI模型可靠性** — `GPT_TOOL_USE_GUIDANCE`防止GPT模型描述操作而不是调用工具 + 自动从历史中剥离预算警告 ([#3528](https://github.com/NousResearch/hermes-agent/pull/3528))
- **表面生命周期事件** — 所有重试、回退和压缩事件现在以格式化消息的形式呈现给用户 ([#3153](https://github.com/NousResearch/hermes-agent/pull/3153))