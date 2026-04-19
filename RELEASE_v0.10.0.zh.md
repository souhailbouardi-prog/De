# Hermes Agent v0.10.0 (v2026.4.16)

**发布日期:** 2026年4月16日

> 工具网关发布 — 付费Nous Portal订阅者现在可以通过其现有订阅使用网络搜索、图像生成、文本转语音和浏览器自动化，无需额外的API密钥。

---

## ✨ 亮点

- **Nous工具网关** — 付费[Nous Portal](https://portal.nousresearch.com)订阅者现在可以通过其现有订阅自动访问**网络搜索**（Firecrawl）、**图像生成**（FAL / FLUX 2 Pro）、**文本转语音**（OpenAI TTS）和**浏览器自动化**（Browser Use）。无需单独的API密钥 — 只需运行`hermes model`，选择Nous Portal，然后选择要启用的工具。通过`use_gateway`配置进行每工具选择加入，与`hermes tools`和`hermes status`完全集成，即使存在直接API密钥，运行时也会正确优先使用网关。用干净的基于订阅的检测替换旧的隐藏`HERMES_ENABLE_NOUS_MANAGED_TOOLS`环境变量。([#11206](https://github.com/NousResearch/hermes-agent/pull/11206), 基于@jquesnelle的工作; 文档: [#11208](https://github.com/NousResearch/hermes-agent/pull/11208))

---

## 🐛 错误修复与改进

此版本包含180+个提交，其中包含智能体核心、网关、CLI和工具系统的众多错误修复、平台改进和可靠性增强。完整详情将在v0.11.0变更日志中发布。

---

## 👥 贡献者

- **@jquesnelle** (emozilla) — 原始工具网关实现 ([#10799](https://github.com/NousResearch/hermes-agent/pull/10799))，在此版本中被挽救并发布

---

**完整变更日志**: [v2026.4.13...v2026.4.16](https://github.com/NousResearch/hermes-agent/compare/v2026.4.13...v2026.4.16)