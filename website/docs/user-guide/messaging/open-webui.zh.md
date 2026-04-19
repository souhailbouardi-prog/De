---
sidebar_position: 8
title: "Open WebUI"
description: "通过OpenAI兼容的API服务器将Open WebUI连接到Hermes Agent"
---

# Open WebUI 集成

[Open WebUI](https://github.com/open-webui/open-webui) (126k★) 是最流行的自托管AI聊天界面。通过Hermes Agent内置的API服务器，您可以将Open WebUI用作代理的抛光Web前端 — 完整的对话管理、用户账户和现代聊天界面。

## 架构

```mermaid
flowchart LR
    A["Open WebUI<br/>浏览器UI<br/>端口 3000"]
    B["hermes-agent<br/>网关API服务器<br/>端口 8642"]
    A -->|POST /v1/chat/completions| B
    B -->|SSE 流式响应| A
```

Open WebUI连接到Hermes Agent的API服务器，就像它连接到OpenAI一样。您的代理使用其完整工具集处理请求 — 终端、文件操作、网络搜索、内存、技能 — 并返回最终响应。

Open WebUI与Hermes服务器对服务器通信，因此您不需要为此集成设置 `API_SERVER_CORS_ORIGINS`。

## 快速设置

### 1. 启用API服务器

添加到 `~/.hermes/.env`：

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=your-secret-key
```

### 2. 启动Hermes Agent网关

```bash
hermes gateway
```

您应该看到：

```
[API Server] API server listening on http://127.0.0.1:8642
```

### 3. 启动Open WebUI

```bash
docker run -d -p 3000:8080 \
  -e OPENAI_API_BASE_URL=http://host.docker.internal:8642/v1 \
  -e OPENAI_API_KEY=your-secret-key \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

### 4. 打开UI

前往 **http://localhost:3000**。创建您的管理员账户（第一个用户成为管理员）。您应该在模型下拉菜单中看到您的代理（以您的配置文件命名，或默认为 **hermes-agent**）。开始聊天！

## Docker Compose 设置

对于更永久的设置，创建一个 `docker-compose.yml`：

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OPENAI_API_BASE_URL=http://host.docker.internal:8642/v1
      - OPENAI_API_KEY=your-secret-key
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: always

volumes:
  open-webui:
```

然后：

```bash
docker compose up -d
```

## 通过管理UI配置

如果您更喜欢通过UI而不是环境变量配置连接：

1. 登录Open WebUI，地址为 **http://localhost:3000**
2. 点击您的 **个人资料头像** → **管理设置**
3. 前往 **连接**
4. 在 **OpenAI API** 下，点击 **扳手图标**（管理）
5. 点击 **+ 添加新连接**
6. 输入：
   - **URL**：`http://host.docker.internal:8642/v1`
   - **API Key**：您的密钥或任何非空值（例如 `not-needed`）
7. 点击 **勾选** 验证连接
8. **保存**

您的代理模型现在应该出现在模型下拉菜单中（以您的配置文件命名，或默认为 **hermes-agent**）。

:::warning
环境变量仅在Open WebUI的**首次启动**时生效。之后，连接设置存储在其内部数据库中。要稍后更改它们，请使用管理UI或删除Docker卷并重新开始。
:::

## API类型：聊天完成 vs 响应

Open WebUI在连接到后端时支持两种API模式：

| 模式 | 格式 | 何时使用 |
|------|--------|-------------|
| **聊天完成**（默认） | `/v1/chat/completions` | 推荐。开箱即用。 |
| **响应**（实验性） | `/v1/responses` | 用于通过 `previous_response_id` 进行服务器端对话状态。 |

### 使用聊天完成（推荐）

这是默认设置，不需要额外配置。Open WebUI发送标准OpenAI格式的请求，Hermes Agent相应地响应。每个请求都包含完整的对话历史。

### 使用响应API

要使用响应API模式：

1. 前往 **管理设置** → **连接** → **OpenAI** → **管理**
2. 编辑您的hermes-agent连接
3. 将 **API类型** 从 "聊天完成" 更改为 **"响应（实验性）"**
4. 保存

使用响应API时，Open WebUI以响应格式发送请求（`input` 数组 + `instructions`），Hermes Agent可以通过 `previous_response_id` 跨轮次保留完整的工具调用历史。当 `stream: true` 时，Hermes还会流式传输规范原生的 `function_call` 和 `function_call_output` 项，这使得渲染响应事件的客户端能够实现自定义结构化工具调用UI。

:::note
Open WebUI目前即使在响应模式下也在客户端管理对话历史 — 它在每个请求中发送完整的消息历史，而不是使用 `previous_response_id`。今天响应模式的主要优势是结构化事件流：文本增量、`function_call` 和 `function_call_output` 项作为OpenAI响应SSE事件而不是聊天完成块到达。
:::

## 工作原理

当您在Open WebUI中发送消息时：

1. Open WebUI发送 `POST /v1/chat/completions` 请求，包含您的消息和对话历史
2. Hermes Agent创建一个具有完整工具集的AIAgent实例
3. 代理处理您的请求 — 它可能调用工具（终端、文件操作、网络搜索等）
4. 工具执行时，**内联进度消息流式传输到UI**，这样您可以看到代理正在做什么（例如 `` `💻 ls -la` ``, `` `🔍 Python 3.12 release` ``）
5. 代理的最终文本响应流式传输回Open WebUI
6. Open WebUI在其聊天界面中显示响应

您的代理可以访问与使用CLI或Telegram时相同的所有工具和功能 — 唯一的区别是前端。

:::tip 工具进度
启用流式传输（默认）时，您会看到工具运行时的简短内联指示器 — 工具表情符号及其关键参数。这些在代理最终答案之前出现在响应流中，让您了解幕后发生的事情。
:::

## 配置参考

### Hermes Agent（API服务器）

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `API_SERVER_ENABLED` | `false` | 启用API服务器 |
| `API_SERVER_PORT` | `8642` | HTTP服务器端口 |
| `API_SERVER_HOST` | `127.0.0.1` | 绑定地址 |
| `API_SERVER_KEY` | _(必需)_ | 用于认证的Bearer令牌。与 `OPENAI_API_KEY` 匹配。 |

### Open WebUI

| 变量 | 描述 |
|----------|-------------|
| `OPENAI_API_BASE_URL` | Hermes Agent的API URL（包括 `/v1`） |
| `OPENAI_API_KEY` | 必须非空。与您的 `API_SERVER_KEY` 匹配。 |

## 故障排除

### 下拉菜单中没有显示模型

- **检查URL是否有 `/v1` 后缀**：`http://host.docker.internal:8642/v1`（不仅仅是 `:8642`）
- **验证网关是否运行**：`curl http://localhost:8642/health` 应该返回 `{"status": "ok"}`
- **检查模型列表**：`curl http://localhost:8642/v1/models` 应该返回包含 `hermes-agent` 的列表
- **Docker网络**：在Docker内部，`localhost` 指容器，不是您的主机。使用 `host.docker.internal` 或 `--network=host`。

### 连接测试通过但没有加载模型

这几乎总是缺少 `/v1` 后缀。Open WebUI的连接测试是基本的连接性检查 — 它不验证模型列表是否有效。

### 响应需要很长时间

Hermes Agent可能在生成最终响应之前执行多个工具调用（读取文件、运行命令、搜索网络）。对于复杂查询，这是正常的。当代理完成时，响应会一次性出现。

### "无效API密钥" 错误

确保Open WebUI中的 `OPENAI_API_KEY` 与Hermes Agent中的 `API_SERVER_KEY` 匹配。

## 使用配置文件的多用户设置

要为每个用户运行单独的Hermes实例 — 每个实例都有自己的配置、内存和技能 — 请使用[配置文件](/docs/user-guide/features/profiles)。每个配置文件在不同端口上运行自己的API服务器，并自动将配置文件名称作为模型在Open WebUI中公布。

### 1. 创建配置文件并配置API服务器

```bash
hermes profile create alice
hermes -p alice config set API_SERVER_ENABLED true
hermes -p alice config set API_SERVER_PORT 8643
hermes -p alice config set API_SERVER_KEY alice-secret

hermes profile create bob
hermes -p bob config set API_SERVER_ENABLED true
hermes -p bob config set API_SERVER_PORT 8644
hermes -p bob config set API_SERVER_KEY bob-secret
```

### 2. 启动每个网关

```bash
hermes -p alice gateway &
hermes -p bob gateway &
```

### 3. 在Open WebUI中添加连接

在 **管理设置** → **连接** → **OpenAI API** → **管理** 中，为每个配置文件添加一个连接：

| 连接 | URL | API密钥 |
|-----------|-----|---------|
| Alice | `http://host.docker.internal:8643/v1` | `alice-secret` |
| Bob | `http://host.docker.internal:8644/v1` | `bob-secret` |

模型下拉菜单将显示 `alice` 和 `bob` 作为不同的模型。您可以通过管理面板将模型分配给Open WebUI用户，为每个用户提供自己隔离的Hermes代理。

:::tip 自定义模型名称
模型名称默认为配置文件名称。要覆盖它，请在配置文件的 `.env` 中设置 `API_SERVER_MODEL_NAME`：
```bash
hermes -p alice config set API_SERVER_MODEL_NAME "Alice's Agent"
```
:::

## Linux Docker（无Docker Desktop）

在没有Docker Desktop的Linux上，`host.docker.internal` 默认不解析。选项：

```bash
# 选项1：添加主机映射
docker run --add-host=host.docker.internal:host-gateway ...

# 选项2：使用主机网络
docker run --network=host -e OPENAI_API_BASE_URL=http://localhost:8642/v1 ...

# 选项3：使用Docker桥接IP
docker run -e OPENAI_API_BASE_URL=http://172.17.0.1:8642/v1 ...
```