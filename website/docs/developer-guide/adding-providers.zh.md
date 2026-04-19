---
sidebar_position: 5
title: "添加提供商"
description: "如何向 Hermes Agent 添加新的推理提供商 — 认证、运行时解析、CLI 流程、适配器、测试和文档"
---

# 添加提供商

Hermes 已经可以通过自定义提供商路径与任何 OpenAI 兼容的端点通信。除非您希望为该服务提供一级 UX，否则不要添加内置提供商：

- 提供商特定的认证或令牌刷新
- 精选模型目录
- 设置 / `hermes model` 菜单项
- `provider:model` 语法的提供商别名
- 需要适配器的非 OpenAI API 形状

如果提供商只是"另一个 OpenAI 兼容的基本 URL 和 API 密钥"，那么命名自定义提供商可能就足够了。

## 心理模型

内置提供商必须在几个层中对齐：

1. `hermes_cli/auth.py` 决定如何找到凭证。
2. `hermes_cli/runtime_provider.py` 将其转换为运行时数据：
   - `provider`
   - `api_mode`
   - `base_url`
   - `api_key`
   - `source`
3. `run_agent.py` 使用 `api_mode` 来决定如何构建和发送请求。
4. `hermes_cli/models.py` 和 `hermes_cli/main.py` 使提供商在 CLI 中显示。（`hermes_cli/setup.py` 自动委托给 `main.py` — 那里不需要更改。）
5. `agent/auxiliary_client.py` 和 `agent/model_metadata.py` 保持辅助任务和令牌预算正常工作。

重要的抽象是 `api_mode`。

- 大多数提供商使用 `chat_completions`。
- Codex 使用 `codex_responses`。
- Anthropic 使用 `anthropic_messages`。
- 新的非 OpenAI 协议通常意味着添加新的适配器和新的 `api_mode` 分支。

## 首先选择实现路径

### 路径 A — OpenAI 兼容提供商

当提供商接受标准聊天完成风格的请求时使用。

典型工作：

- 添加认证元数据
- 添加模型目录 / 别名
- 添加运行时解析
- 添加 CLI 菜单连接
- 添加辅助模型默认值
- 添加测试和用户文档

通常不需要新的适配器或新的 `api_mode`。

### 路径 B — 原生提供商

当提供商的行为不像 OpenAI 聊天完成时使用。

今天树中的例子：

- `codex_responses`
- `anthropic_messages`

此路径包括路径 A 的所有内容加上：

- `agent/` 中的提供商适配器
- `run_agent.py` 分支，用于请求构建、调度、使用提取、中断处理和响应标准化
- 适配器测试

## 文件清单

### 每个内置提供商都需要

1. `hermes_cli/auth.py`
2. `hermes_cli/models.py`
3. `hermes_cli/runtime_provider.py`
4. `hermes_cli/main.py`
5. `agent/auxiliary_client.py`
6. `agent/model_metadata.py`
7. 测试
8. `website/docs/` 下的用户文档

:::tip
`hermes_cli/setup.py` **不需要**更改。设置向导将提供商/模型选择委托给 `main.py` 中的 `select_provider_and_model()` — 添加到那里的任何提供商都会自动在 `hermes setup` 中可用。
:::

### 原生 / 非 OpenAI 提供商的附加内容

10. `agent/<provider>_adapter.py`
11. `run_agent.py`
12. 如果需要提供商 SDK，则需要 `pyproject.toml`

## 步骤 1：选择一个规范的提供商 ID

选择一个提供商 ID 并在所有地方使用它。

来自仓库的例子：

- `openai-codex`
- `kimi-coding`
- `minimax-cn`

同一个 ID 应该出现在：

- `hermes_cli/auth.py` 中的 `PROVIDER_REGISTRY`
- `hermes_cli/models.py` 中的 `_PROVIDER_LABELS`
- `hermes_cli/auth.py` 和 `hermes_cli/models.py` 中的 `_PROVIDER_ALIASES`
- `hermes_cli/main.py` 中的 CLI `--provider` 选项
- 设置 / 模型选择分支
- 辅助模型默认值
- 测试

如果这些文件之间的 ID 不同，提供商将感觉像是半连接的：认证可能正常工作，而 `/model`、设置或运行时解析会静默错过它。

## 步骤 2：在 `hermes_cli/auth.py` 中添加认证元数据

对于 API 密钥提供商，向 `PROVIDER_REGISTRY` 添加 `ProviderConfig` 条目，包含：

- `id`
- `name`
- `auth_type="api_key"`
- `inference_base_url`
- `api_key_env_vars`
- 可选的 `base_url_env_var`

还要向 `_PROVIDER_ALIASES` 添加别名。

使用现有提供商作为模板：

- 简单 API 密钥路径：Z.AI、MiniMax
- 带端点检测的 API 密钥路径：Kimi、Z.AI
- 原生令牌解析：Anthropic
- OAuth / 认证存储路径：Nous、OpenAI Codex

这里要回答的问题：

- Hermes 应该检查哪些环境变量，以什么优先级顺序？
- 提供商是否需要基本 URL 覆盖？
- 是否需要端点探测或令牌刷新？
- 当凭证缺失时，认证错误应该说什么？

如果提供商需要的不仅仅是"查找 API 密钥"，请添加专用的凭证解析器，而不是将逻辑推入不相关的分支。

## 步骤 3：在 `hermes_cli/models.py` 中添加模型目录和别名

更新提供商目录，使提供商在菜单和 `provider:model` 语法中工作。

典型编辑：

- `_PROVIDER_MODELS`
- `_PROVIDER_LABELS`
- `_PROVIDER_ALIASES`
- `list_available_providers()` 中的提供商显示顺序
- 如果提供商支持实时 `/models` 获取，则添加 `provider_model_ids()`

如果提供商公开实时模型列表，优先使用它，并将 `_PROVIDER_MODELS` 作为静态回退。

此文件还使以下输入工作：

```text
anthropic:claude-sonnet-4-6
kimi:model-name
```

如果这里缺少别名，提供商可能会正确认证，但在 `/model` 解析中仍然失败。

## 步骤 4：在 `hermes_cli/runtime_provider.py` 中解析运行时数据

`resolve_runtime_provider()` 是 CLI、网关、cron、ACP 和辅助客户端使用的共享路径。

添加一个分支，返回至少包含以下内容的字典：

```python
{
    "provider": "your-provider",
    "api_mode": "chat_completions",  # 或您的原生模式
    "base_url": "https://...",
    "api_key": "...",
    "source": "env|portal|auth-store|explicit",
    "requested_provider": requested_provider,
}
```

如果提供商与 OpenAI 兼容，`api_mode` 通常应该保持为 `chat_completions`。

注意 API 密钥优先级。Hermes 已经包含逻辑，避免将 OpenRouter 密钥泄露到不相关的端点。新提供商应该同样明确哪个密钥对应哪个基本 URL。

## 步骤 5：在 `hermes_cli/main.py` 中连接 CLI

提供商在交互式 `hermes model` 流程中显示之前是不可发现的。

在 `hermes_cli/main.py` 中更新这些：

- `provider_labels` 字典
- `select_provider_and_model()` 中的 `providers` 列表
- 提供商调度 (`if selected_provider == ...`)
- `--provider` 参数选项
- 如果提供商支持这些流程，则登录/注销选项
- `_model_flow_<provider>()` 函数，或如果适合则重用 `_model_flow_api_key_provider()`

:::tip
`hermes_cli/setup.py` 不需要更改 — 它调用 `main.py` 中的 `select_provider_and_model()`，因此您的新提供商会自动出现在 `hermes model` 和 `hermes setup` 中。
:::

## 步骤 6：保持辅助调用正常工作

这里有两个重要文件：

### `agent/auxiliary_client.py`

如果这是直接的 API 密钥提供商，向 `_API_KEY_PROVIDER_AUX_MODELS` 添加一个廉价/快速的默认辅助模型。

辅助任务包括：

- 视觉摘要
- Web 提取摘要
- 上下文压缩摘要
- 会话搜索摘要
- 记忆刷新

如果提供商没有合理的辅助默认值，辅助任务可能会严重回退或意外使用昂贵的主模型。

### `agent/model_metadata.py`

为提供商的模型添加上下文长度，以便令牌预算、压缩阈值和限制保持合理。

## 步骤 7：如果提供商是原生的，添加适配器和 `run_agent.py` 支持

如果提供商不是普通的聊天完成，将提供商特定的逻辑隔离在 `agent/<provider>_adapter.py` 中。

保持 `run_agent.py` 专注于编排。它应该调用适配器助手，而不是在文件中内联手工构建提供商有效负载。

原生提供商通常需要在这些地方工作：

### 新适配器文件

典型职责：

- 构建 SDK / HTTP 客户端
- 解析令牌
- 将 OpenAI 风格的对话消息转换为提供商的请求格式
- 必要时转换工具架构
- 将提供商响应规范化回 `run_agent.py` 期望的内容
- 提取使用和完成原因数据

### `run_agent.py`

搜索 `api_mode` 并审计每个切换点。至少验证：

- `__init__` 选择新的 `api_mode`
- 客户端构建对提供商有效
- `_build_api_kwargs()` 知道如何格式化请求
- `_api_call_with_interrupt()` 调度到正确的客户端调用
- 中断 / 客户端重建路径工作
- 响应验证接受提供商的形状
- 完成原因提取正确
- 令牌使用提取正确
- 回退模型激活可以干净地切换到新提供商
- 摘要生成和记忆刷新路径仍然工作

还要在 `run_agent.py` 中搜索 `self.client.`。任何假设标准 OpenAI 客户端存在的代码路径在原生提供商使用不同的客户端对象或 `self.client = None` 时都可能中断。

### 提示缓存和提供商特定的请求字段

提示缓存和提供商特定的旋钮很容易回归。

树中已有的例子：

- Anthropic 有原生提示缓存路径
- OpenRouter 获取提供商路由字段
- 并非每个提供商都应该接收每个请求端选项

添加原生提供商时，仔细检查 Hermes 只发送提供商实际理解的字段。

## 步骤 8：测试

至少触摸保护提供商连接的测试。

常见位置：

- `tests/test_runtime_provider_resolution.py`
- `tests/test_cli_provider_resolution.py`
- `tests/test_cli_model_command.py`
- `tests/test_setup_model_selection.py`
- `tests/test_provider_parity.py`
- `tests/test_run_agent.py`
- 对于原生提供商，`tests/test_<provider>_adapter.py`

对于仅文档示例，确切的文件集可能不同。重点是覆盖：

- 认证解析
- CLI 菜单 / 提供商选择
- 运行时提供商解析
- 代理执行路径
- provider:model 解析
- 任何适配器特定的消息转换

禁用 xdist 运行测试：

```bash
source venv/bin/activate
python -m pytest tests/test_runtime_provider_resolution.py tests/test_cli_provider_resolution.py tests/test_cli_model_command.py tests/test_setup_model_selection.py -n0 -q
```

对于更深层次的更改，在推送前运行完整套件：

```bash
source venv/bin/activate
python -m pytest tests/ -n0 -q
```

## 步骤 9：实时验证

测试后，运行真实的冒烟测试。

```bash
source venv/bin/activate
python -m hermes_cli.main chat -q "Say hello" --provider your-provider --model your-model
```

如果您更改了菜单，还测试交互式流程：

```bash
source venv/bin/activate
python -m hermes_cli.main model
python -m hermes_cli.main setup
```

对于原生提供商，至少验证一个工具调用，而不仅仅是纯文本响应。

## 步骤 10：更新用户文档

如果提供商打算作为一级选项发布，也更新用户文档：

- `website/docs/getting-started/quickstart.md`
- `website/docs/user-guide/configuration.md`
- `website/docs/reference/environment-variables.md`

开发者可以完美连接提供商，但仍然让用户无法发现所需的环境变量或设置流程。

## OpenAI 兼容提供商清单

当提供商是标准聊天完成时使用。

- [ ] 在 `hermes_cli/auth.py` 中添加 `ProviderConfig`
- [ ] 在 `hermes_cli/auth.py` 和 `hermes_cli/models.py` 中添加别名
- [ ] 在 `hermes_cli/models.py` 中添加模型目录
- [ ] 在 `hermes_cli/runtime_provider.py` 中添加运行时分支
- [ ] 在 `hermes_cli/main.py` 中添加 CLI 连接（setup.py 自动继承）
- [ ] 在 `agent/auxiliary_client.py` 中添加辅助模型
- [ ] 在 `agent/model_metadata.py` 中添加上下文长度
- [ ] 更新运行时 / CLI 测试
- [ ] 更新用户文档

## 原生提供商清单

当提供商需要新的协议路径时使用。

- [ ] OpenAI 兼容清单中的所有内容
- [ ] 在 `agent/<provider>_adapter.py` 中添加适配器
- [ ] 在 `run_agent.py` 中支持新的 `api_mode`
- [ ] 中断 / 重建路径工作
- [ ] 使用和完成原因提取工作
- [ ] 回退路径工作
- [ ] 添加适配器测试
- [ ] 实时冒烟测试通过

## 常见陷阱

### 1. 将提供商添加到认证但未添加到模型解析

这会使凭证正确解析，而 `/model` 和 `provider:model` 输入失败。

### 2. 忘记 `config["model"]` 可以是字符串或字典

许多提供商选择代码必须规范化两种形式。

### 3. 假设需要内置提供商

如果服务只是 OpenAI 兼容的，自定义提供商可能已经以较少的维护解决了用户问题。

### 4. 忘记辅助路径

主聊天路径可以工作，而摘要、记忆刷新或视觉助手可能失败，因为辅助路由从未更新。

### 5. `run_agent.py` 中隐藏的原生提供商分支

搜索 `api_mode` 和 `self.client.`。不要假设明显的请求路径是唯一的。

### 6. 向其他提供商发送仅 OpenRouter 的旋钮

像提供商路由这样的字段只属于支持它们的提供商。

### 7. 更新 `hermes model` 但不更新 `hermes setup`

两个流程都需要了解提供商。

## 实现时的良好搜索目标

如果您正在寻找提供商触及的所有地方，搜索这些符号：

- `PROVIDER_REGISTRY`
- `_PROVIDER_ALIASES`
- `_PROVIDER_MODELS`
- `resolve_runtime_provider`
- `_model_flow_`
- `select_provider_and_model`
- `api_mode`
- `_API_KEY_PROVIDER_AUX_MODELS`
- `self.client.`

## 相关文档

- [提供商运行时解析](./provider-runtime.md)
- [架构](./architecture.md)
- [贡献](./contributing.md)
