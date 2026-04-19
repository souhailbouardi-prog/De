---
sidebar_position: 15
---

# 企业微信回调（自建应用）

使用回调/webhook模式将Hermes连接到企业微信作为自建企业应用。

:::info 企业微信机器人 vs 企业微信回调
Hermes支持两种企业微信集成模式：
- **[企业微信机器人](wecom.md)** — 机器人风格，通过WebSocket连接。设置更简单，可在群聊中使用。
- **企业微信回调**（本页面）— 自建应用，接收加密XML回调。在用户的企业微信侧边栏中显示为一级应用。支持多企业路由。
:::

## 工作原理

1. 您在企业微信管理控制台中注册自建应用
2. 企业微信将加密的XML推送到您的HTTP回调端点
3. Hermes解密消息，将其排队给代理
4. 立即确认（静默 — 不会向用户显示任何内容）
5. 代理处理请求（通常需要3–30分钟）
6. 回复通过企业微信 `message/send` API 主动传递

## 前提条件

- 具有管理员访问权限的企业微信企业账户
- `aiohttp` 和 `httpx` Python包（默认安装中包含）
- 用于回调URL的可公开访问的服务器（或像ngrok这样的隧道）

## 设置

### 1. 在企业微信中创建自建应用

1. 前往 [企业微信管理控制台](https://work.weixin.qq.com/) → **应用** → **创建应用**
2. 记录您的 **企业ID**（显示在管理控制台顶部）
3. 在应用设置中，创建 **应用密钥**
4. 从应用概览页面记录 **Agent ID**
5. 在 **接收消息** 下，配置回调URL：
   - URL: `http://YOUR_PUBLIC_IP:8645/wecom/callback`
   - Token: 生成随机令牌（企业微信会提供一个）
   - EncodingAESKey: 生成密钥（企业微信会提供一个）

### 2. 配置环境变量

添加到您的 `.env` 文件：

```bash
WECOM_CALLBACK_CORP_ID=your-corp-id
WECOM_CALLBACK_CORP_SECRET=your-corp-secret
WECOM_CALLBACK_AGENT_ID=1000002
WECOM_CALLBACK_TOKEN=your-callback-token
WECOM_CALLBACK_ENCODING_AES_KEY=your-43-char-aes-key

# 可选
WECOM_CALLBACK_HOST=0.0.0.0
WECOM_CALLBACK_PORT=8645
WECOM_CALLBACK_ALLOWED_USERS=user1,user2
```

### 3. 启动网关

```bash
hermes gateway start
```

回调适配器在配置的端口上启动HTTP服务器。企业微信将通过GET请求验证回调URL，然后开始通过POST发送消息。

## 配置参考

在 `config.yaml` 中的 `platforms.wecom_callback.extra` 下设置这些，或使用环境变量：

| 设置 | 默认值 | 描述 |
|---------|---------|-------------|
| `corp_id` | — | 企业微信企业ID（必需） |
| `corp_secret` | — | 自建应用的应用密钥（必需） |
| `agent_id` | — | 自建应用的Agent ID（必需） |
| `token` | — | 回调验证令牌（必需） |
| `encoding_aes_key` | — | 43字符的AES密钥，用于回调加密（必需） |
| `host` | `0.0.0.0` | HTTP回调服务器的绑定地址 |
| `port` | `8645` | HTTP回调服务器的端口 |
| `path` | `/wecom/callback` | 回调端点的URL路径 |

## 多应用路由

对于运行多个自建应用的企业（例如，跨不同部门或子公司），在 `config.yaml` 中配置 `apps` 列表：

```yaml
platforms:
  wecom_callback:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8645
      apps:
        - name: "dept-a"
          corp_id: "ww_corp_a"
          corp_secret: "secret-a"
          agent_id: "1000002"
          token: "token-a"
          encoding_aes_key: "key-a-43-chars..."
        - name: "dept-b"
          corp_id: "ww_corp_b"
          corp_secret: "secret-b"
          agent_id: "1000003"
          token: "token-b"
          encoding_aes_key: "key-b-43-chars..."
```

用户通过 `corp_id:user_id` 进行范围限定，以防止跨企业冲突。当用户发送消息时，适配器记录他们所属的应用（企业），并通过正确应用的访问令牌路由回复。

## 访问控制

限制哪些用户可以与应用交互：

```bash
# 允许特定用户
WECOM_CALLBACK_ALLOWED_USERS=zhangsan,lisi,wangwu

# 或允许所有用户
WECOM_CALLBACK_ALLOW_ALL_USERS=true
```

## 端点

适配器公开：

| 方法 | 路径 | 用途 |
|--------|------|---------|
| GET | `/wecom/callback` | URL验证握手（企业微信在设置期间发送） |
| POST | `/wecom/callback` | 加密消息回调（企业微信在此发送用户消息） |
| GET | `/health` | 健康检查 — 返回 `{"status": "ok"}` |

## 加密

所有回调有效负载都使用EncodingAESKey通过AES-CBC加密。适配器处理：

- **入站**：解密XML有效负载，验证SHA1签名
- **出站**：通过主动API发送回复（非加密回调响应）

加密实现与腾讯官方的WXBizMsgCrypt SDK兼容。

## 限制

- **无流式传输** — 回复在代理完成后以完整消息形式到达
- **无输入指示器** — 回调模型不支持输入状态
- **仅文本** — 目前支持文本消息输入；图像/文件/语音输入尚未实现。代理通过企业微信平台提示了解出站媒体功能（图像、文档、视频、语音）。
- **响应延迟** — 代理会话需要3–30分钟；用户在处理完成时看到回复