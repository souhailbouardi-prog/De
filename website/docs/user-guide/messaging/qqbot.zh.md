# QQ机器人

通过**官方QQ机器人API (v2)** 将Hermes连接到QQ — 支持私聊（C2C）、群聊@提及、频道和带有语音转写的直接消息。

## 概述

QQ机器人适配器使用[官方QQ机器人API](https://bot.q.qq.com/wiki/develop/api-v2/)来：

- 通过与QQ网关的持久**WebSocket**连接接收消息
- 通过**REST API**发送文本和markdown回复
- 下载和处理图像、语音消息和文件附件
- 使用腾讯内置的ASR或可配置的STT服务提供商转录语音消息

## 前提条件

1. **QQ机器人应用** — 在[q.qq.com](https://q.qq.com)注册：
   - 创建新应用并记录您的**App ID**和**App Secret**
   - 启用所需的意图：C2C消息、群聊@消息、频道消息
   - 配置机器人为沙盒模式进行测试，或发布为生产环境

2. **依赖项** — 适配器需要 `aiohttp` 和 `httpx`：
   ```bash
   pip install aiohttp httpx
   ```

## 配置

### 交互式设置

```bash
hermes setup gateway
```

从平台列表中选择 **QQ Bot** 并按照提示操作。

### 手动配置

在 `~/.hermes/.env` 中设置所需的环境变量：

```bash
QQ_APP_ID=your-app-id
QQ_CLIENT_SECRET=your-app-secret
```

## 环境变量

| 变量 | 描述 | 默认值 |
|---|---|---|
| `QQ_APP_ID` | QQ机器人App ID（必需） | — |
| `QQ_CLIENT_SECRET` | QQ机器人App Secret（必需） | — |
| `QQBOT_HOME_CHANNEL` | 用于定时任务/通知传递的OpenID | — |
| `QQBOT_HOME_CHANNEL_NAME` | 主频道的显示名称 | `Home` |
| `QQ_ALLOWED_USERS` | 用于私聊访问的逗号分隔用户OpenID | 开放（所有用户） |
| `QQ_ALLOW_ALL_USERS` | 设置为 `true` 以允许所有私聊 | `false` |
| `QQ_MARKDOWN_SUPPORT` | 启用QQ markdown（msg_type 2） | `true` |
| `QQ_STT_API_KEY` | 语音转文本服务的API密钥 | — |
| `QQ_STT_BASE_URL` | STT服务的基础URL | `https://open.bigmodel.cn/api/coding/paas/v4` |
| `QQ_STT_MODEL` | STT模型名称 | `glm-asr` |

## 高级配置

对于精细控制，在 `~/.hermes/config.yaml` 中添加平台设置：

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

语音转录分为两个阶段：

1. **QQ内置ASR**（免费，始终首先尝试）— QQ在语音消息附件中提供 `asr_refer_text`，使用腾讯自己的语音识别
2. **配置的STT服务**（回退）— 如果QQ的ASR没有返回文本，适配器会调用OpenAI兼容的STT API：

   - **智谱/GLM (zai)**：默认服务，使用 `glm-asr` 模型
   - **OpenAI Whisper**：设置 `QQ_STT_BASE_URL` 和 `QQ_STT_MODEL`
   - 任何OpenAI兼容的STT端点

## 故障排除

### 机器人立即断开连接（快速断开）

这通常意味着：
- **无效的App ID / Secret** — 仔细检查您在q.qq.com上的凭证
- **缺少权限** — 确保机器人已启用所需的意图
- **仅限沙盒的机器人** — 如果机器人处于沙盒模式，它只能从QQ的沙盒测试频道接收消息

### 语音消息未被转录

1. 检查QQ内置的 `asr_refer_text` 是否存在于附件数据中
2. 如果使用自定义STT服务，验证 `QQ_STT_API_KEY` 是否已正确设置
3. 检查网关日志中的STT错误消息

### 消息未送达

- 验证机器人的**意图**在q.qq.com上已启用
- 如果私聊访问受限，检查 `QQ_ALLOWED_USERS`
- 对于群聊消息，确保机器人被**@提及**（群聊策略可能需要允许列表）
- 检查 `QQBOT_HOME_CHANNEL` 用于定时任务/通知传递

### 连接错误

- 确保已安装 `aiohttp` 和 `httpx`：`pip install aiohttp httpx`
- 检查与 `api.sgroup.qq.com` 和WebSocket网关的网络连接
- 查看网关日志以获取详细的错误消息和重连行为