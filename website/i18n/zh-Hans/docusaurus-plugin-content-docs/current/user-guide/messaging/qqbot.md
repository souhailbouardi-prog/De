# QQ 机器人

通过 **官方 QQ 机器人 API (v2)** 将 Hermes 连接到 QQ — 支持私聊（C2C）、群聊 @ 提及、频道消息和带语音转录的直接消息。

## 概述

QQ 机器人适配器使用 [官方 QQ 机器人 API](https://bot.q.qq.com/wiki/develop/api-v2/) 实现：

- 通过与 QQ 网关的持久 **WebSocket** 连接接收消息
- 通过 **REST API** 发送文本和 Markdown 回复
- 下载和处理图片、语音消息和文件附件
- 使用腾讯内置的 ASR 或可配置的 STT 提供商转录语音消息

## 先决条件

1. **QQ 机器人应用** — 在 [q.qq.com](https://q.qq.com) 注册：
   - 创建新应用并记录您的 **App ID** 和 **App Secret**
   - 启用所需的权限：C2C 消息、群聊 @ 消息、频道消息
   - 在沙盒模式下配置您的机器人进行测试，或发布到生产环境

2. **依赖项** — 适配器需要 `aiohttp` 和 `httpx`：
   ```bash
   pip install aiohttp httpx
   ```

## 配置

### 交互式设置

```bash
hermes setup gateway
```

从平台列表中选择 **QQ 机器人** 并按照提示操作。

### 手动配置

在 `~/.hermes/.env` 中设置所需的环境变量：

```bash
QQ_APP_ID=your-app-id
QQ_CLIENT_SECRET=your-app-secret
```

## 环境变量

| 变量 | 描述 | 默认值 |
|---|---|---|
| `QQ_APP_ID` | QQ 机器人 App ID（必需） | — |
| `QQ_CLIENT_SECRET` | QQ 机器人 App Secret（必需） | — |
| `QQ_HOME_CHANNEL` | 用于定时任务/通知传递的 OpenID | — |
| `QQ_HOME_CHANNEL_NAME` | 主频道的显示名称 | `Home` |
| `QQ_ALLOWED_USERS` | 用于 DM 访问的逗号分隔用户 OpenID | 开放（所有用户） |
| `QQ_ALLOW_ALL_USERS` | 设置为 `true` 以允许所有 DM | `false` |
| `QQ_MARKDOWN_SUPPORT` | 启用 QQ Markdown（msg_type 2） | `true` |
| `QQ_STT_API_KEY` | 语音转文本提供商的 API 密钥 | — |
| `QQ_STT_BASE_URL` | STT 提供商的基础 URL | `https://open.bigmodel.cn/api/coding/paas/v4` |
| `QQ_STT_MODEL` | STT 模型名称 | `glm-asr` |

## 高级配置

对于细粒度控制，将平台设置添加到 `~/.hermes/config.yaml`：

```yaml
platforms:
  qq:
    enabled: true
    extra:
      app_id: "your-app-id"
      client_secret: "your-secret"
      markdown_support: true
      dm_policy: "open"          # open | allowlist | disabled
      allow_from:
        - "user_openid_1"
      group_policy: "open"       # open | allowlist | disabled
      group_allow_from:
        - "group_openid_1"
      stt:
        provider: "zai"          # zai (GLM-ASR), openai (Whisper), etc.
        baseUrl: "https://open.bigmodel.cn/api/coding/paas/v4"
        apiKey: "your-stt-key"
        model: "glm-asr"
```

## 语音消息（STT）

语音转录分两个阶段工作：

1. **QQ 内置 ASR**（免费，始终首先尝试）— QQ 在语音消息附件中提供 `asr_refer_text`，使用腾讯自己的语音识别
2. **配置的 STT 提供商**（备用）— 如果 QQ 的 ASR 不返回文本，适配器会调用兼容 OpenAI 的 STT API：

   - **智谱/GLM (zai)**：默认提供商，使用 `glm-asr` 模型
   - **OpenAI Whisper**：设置 `QQ_STT_BASE_URL` 和 `QQ_STT_MODEL`
   - 任何兼容 OpenAI 的 STT 端点

## 故障排除

### 机器人立即断开连接（快速断开）

这通常意味着：
- **无效的 App ID / Secret** — 请在 q.qq.com 上仔细检查您的凭据
- **缺少权限** — 确保机器人已启用所需的权限
- **仅沙盒机器人** — 如果机器人处于沙盒模式，它只能接收来自 QQ 沙盒测试频道的消息

### 语音消息未转录

1. 检查附件数据中是否存在 QQ 内置的 `asr_refer_text`
2. 如果使用自定义 STT 提供商，验证 `QQ_STT_API_KEY` 是否正确设置
3. 检查网关日志中的 STT 错误消息

### 消息未传递

- 验证机器人的 **权限** 是否已在 q.qq.com 上启用
- 如果 DM 访问受到限制，请检查 `QQ_ALLOWED_USERS`
- 对于群消息，确保机器人被 **@ 提及**（群聊策略可能需要允许列表）
- 检查 `QQ_HOME_CHANNEL` 以进行定时任务/通知传递

### 连接错误

- 确保安装了 `aiohttp` 和 `httpx`：`pip install aiohttp httpx`
- 检查与 `api.sgroup.qq.com` 和 WebSocket 网关的网络连接
- 查看网关日志以获取详细的错误消息和重连行为