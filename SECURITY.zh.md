# Hermes Agent 安全策略

本文档概述了 **Hermes Agent** 项目的安全协议、信任模型和部署加固指南。

## 1. 漏洞报告

Hermes Agent **不** 运行漏洞赏金计划。安全问题应通过 [GitHub Security Advisories (GHSA)](https://github.com/NousResearch/hermes-agent/security/advisories/new) 或发送电子邮件至 **security@nousresearch.com** 进行报告。不要为安全漏洞打开公共问题。

### 所需提交详情
- **标题和严重性：** 简明描述和 CVSS 评分/评级。
- **受影响组件：** 精确的文件路径和行范围（例如，`tools/approval.py:120-145`）。
- **环境：** `hermes version` 的输出、提交 SHA、操作系统和 Python 版本。
- **重现：** 针对 `main` 或最新版本的分步概念证明 (PoC)。
- **影响：** 解释跨越了什么信任边界。

---

## 2. 信任模型

核心假设是 Hermes 是一个 **个人代理**，有一个受信任的操作员。

### 操作员和会话信任
- **单租户：** 系统保护操作员免受 LLM 操作的影响，而不是免受恶意共同租户的影响。多用户隔离必须在 OS/主机级别发生。
- **网关安全：** 授权调用者（Telegram、Discord、Slack 等）获得同等信任。会话密钥用于路由，而不是作为授权边界。
- **执行：** 默认为 `terminal.backend: local`（直接主机执行）。容器隔离（Docker、Modal、Daytona）是用于沙箱的可选功能。

### 危险命令批准
批准系统（`tools/approval.py`）是核心安全边界。终端命令、文件操作和其他潜在破坏性操作在执行前需要明确的用户确认。批准模式可通过 `config.yaml` 中的 `approvals.mode` 配置：
- `"on"`（默认）— 提示用户批准危险命令。
- `"auto"` — 在可配置的延迟后自动批准。
- `"off"` — 完全禁用门控（紧急情况下；见第 3 节）。

### 输出编辑
`agent/redact.py` 从所有显示输出中剥离类似秘密的模式（API 密钥、令牌、凭据），然后才到达终端或网关平台。这防止了在聊天日志、工具预览和响应文本中意外泄露凭据。编辑仅在显示层操作 — 底层值对内部代理操作保持不变。

### 技能与 MCP 服务器
- **已安装技能：** 高信任度。相当于本地主机代码；技能可以读取环境变量并运行任意命令。
- **MCP 服务器：** 较低信任度。MCP 子进程接收过滤后的环境（`tools/mcp_tool.py` 中的 `_build_safe_env()`）— 只传递安全的基线变量（`PATH`、`HOME`、`XDG_*`）以及在服务器的 `env` 配置块中明确声明的变量。默认情况下，主机凭据被剥离。此外，通过 `npx`/`uvx` 调用的包在生成之前会对照 OSV 恶意软件数据库进行检查。

### 代码执行沙箱
`execute_code` 工具（`tools/code_execution_tool.py`）在子进程中运行 LLM 生成的 Python 脚本，从环境中剥离 API 密钥和令牌以防止凭据窃取。只有由加载的技能明确声明的环境变量（通过 `env_passthrough`）或用户在 `config.yaml` 中声明的环境变量（`terminal.env_passthrough`）才会被传递。子进程通过 RPC 访问 Hermes 工具，而不是直接 API 调用。

### 子代理
- **无递归委托：** `delegate_task` 工具对子代理禁用。
- **深度限制：** `MAX_DEPTH = 2` — 父级（深度 0）可以生成子级（深度 1）；孙级被拒绝。
- **内存隔离：** 子代理以 `skip_memory=True` 运行，无法访问父级的持久内存提供程序。父级只收到任务提示和最终响应作为观察结果。

---

## 3. 超出范围（非漏洞）

以下场景 **不** 被视为安全漏洞：
- **提示注入：** 除非它导致批准系统、工具集限制或容器沙箱的具体绕过。
- **公共暴露：** 在没有外部身份验证或网络保护的情况下将网关部署到公共互联网。
- **受信任状态访问：** 需要预先存在对 `~/.hermes/`、`.env` 或 `config.yaml` 的写入访问权限的报告（这些是操作员拥有的文件）。
- **默认行为：** 当 `terminal.backend` 设置为 `local` 时的主机级命令执行 — 这是文档化的默认设置，不是漏洞。
- **配置权衡：** 有意的紧急设置，如生产环境中的 `approvals.mode: "off"` 或 `terminal.backend: local`。
- **工具级读取/访问限制：** 代理通过 `terminal` 工具设计上具有无限制的 shell 访问。如果通过 `terminal` 也可以进行相同的访问，则特定工具（例如，`read_file`）可以访问资源的报告不是漏洞。工具级拒绝列表只有在与终端侧的等效限制配对时才构成有意义的安全边界（如写操作，其中 `WRITE_DENIED_PATHS` 与危险命令批准系统配对）。

---

## 4. 部署加固和最佳实践

### 文件系统和网络
- **生产沙箱：** 对不受信任的工作负载使用容器后端（`docker`、`modal`、`daytona`）而不是 `local`。
- **文件权限：** 以非 root 用户运行（Docker 镜像使用 UID 10000）；在本地安装时使用 `chmod 600 ~/.hermes/.env` 保护凭据。
- **网络暴露：** 不要在没有 VPN、Tailscale 或防火墙保护的情况下将网关或 API 服务器暴露给公共互联网。所有网关平台适配器（Telegram、Discord、Slack、Matrix、Mattermost 等）默认启用 SSRF 保护，并进行重定向验证。注意：本地终端后端不应用 SSRF 过滤，因为它在受信任操作员的环境中运行。

### 技能和供应链
- **技能安装：** 在安装第三方技能之前查看技能保护报告（`tools/skills_guard.py`）。`~/.hermes/skills/.hub/audit.log` 处的审计日志跟踪每次安装和卸载。
- **MCP 安全：** 在 MCP 服务器进程生成之前，会自动对 `npx`/`uvx` 包运行 OSV 恶意软件检查。
- **CI/CD：** GitHub Actions 固定到完整的提交 SHA。`supply-chain-audit.yml` 工作流阻止包含 `.pth` 文件或可疑 `base64`+`exec` 模式的 PR。

### 凭据存储
- API 密钥和令牌应完全存储在 `~/.hermes/.env` 中 — 永远不要在 `config.yaml` 中或签入版本控制。
- 凭据池系统（`agent/credential_pool.py`）处理密钥轮换和回退。凭据从环境变量解析，而不是存储在明文数据库中。

---

## 5. 披露流程

- **协调披露：** 90 天窗口或直到发布修复，以先到者为准。
- **沟通：** 所有更新通过 GHSA 线程或与 security@nousresearch.com 的电子邮件通信进行。
- **功劳：** 除非要求匿名，否则报告者会在发行说明中获得功劳。