---
sidebar_position: 8
sidebar_label: "SMS (Twilio)"
title: "SMS (Twilio)"
description: "通过Twilio设置Hermes Agent作为SMS聊天机器人"
---

# SMS设置 (Twilio)

Hermes通过[Twilio](https://www.twilio.com/) API连接到SMS。人们向您的Twilio电话号码发送文本消息，然后收到AI回复 — 与Telegram或Discord相同的对话体验，但通过标准文本消息。

:::info 共享凭据
SMS网关与可选的[电话技能](/docs/reference/skills-catalog)共享凭据。如果您已经为语音通话或一次性SMS设置了Twilio，网关将使用相同的`TWILIO_ACCOUNT_SID`、`TWILIO_AUTH_TOKEN`和`TWILIO_PHONE_NUMBER`。
:::

---

## 先决条件

- **Twilio账户** — [在twilio.com注册](https://www.twilio.com/try-twilio)（提供免费试用）
- **具有SMS功能的Twilio电话号码**
- **可公开访问的服务器** — 当SMS到达时，Twilio会向您的服务器发送webhook
- **aiohttp** — `pip install 'hermes-agent[sms]'`

---

## 步骤1：获取您的Twilio凭据

1. 前往[Twilio控制台](https://console.twilio.com/)
2. 从仪表板复制您的**Account SID**和**Auth Token**
3. 前往**Phone Numbers → Manage → Active Numbers** — 以E.164格式记下您的电话号码（例如，`+15551234567`）

---

## 步骤2：配置Hermes

### 交互式设置（推荐）

```bash
hermes gateway setup
```

从平台列表中选择**SMS (Twilio)**。向导会提示您输入凭据。

### 手动设置

添加到 `~/.hermes/.env`：

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567

# 安全：限制特定电话号码（推荐）
SMS_ALLOWED_USERS=+15559876543,+15551112222

# 可选：设置定时任务传递的主频道
SMS_HOME_CHANNEL=+15559876543
```

---

## 步骤3：配置Twilio Webhook

Twilio需要知道在哪里发送传入的消息。在[Twilio控制台](https://console.twilio.com/)中：

1. 前往**Phone Numbers → Manage → Active Numbers**
2. 点击您的电话号码
3. 在**Messaging → A MESSAGE COMES IN**下，设置：
   - **Webhook**：`https://your-server:8080/webhooks/twilio`
   - **HTTP Method**：`POST`

:::tip 暴露您的Webhook
如果您在本地运行Hermes，请使用隧道来暴露webhook：

```bash
# 使用cloudflared
cloudflared tunnel --url http://localhost:8080

# 使用ngrok
ngrok http 8080
```

将生成的公共URL设置为您的Twilio webhook。
:::

**将`SMS_WEBHOOK_URL`设置为您在Twilio中配置的相同URL。** 这对于Twilio签名验证是必需的 — 适配器会拒绝在没有它的情况下启动：

```bash
# 必须与Twilio控制台中的webhook URL匹配
SMS_WEBHOOK_URL=https://your-server:8080/webhooks/twilio
```

Webhook端口默认为`8080`。可以通过以下方式覆盖：

```bash
SMS_WEBHOOK_PORT=3000
```

---

## 步骤4：启动网关

```bash
hermes gateway
```

您应该看到：

```
[sms] Twilio webhook server listening on 0.0.0.0:8080, from: +1555***4567
```

如果您看到`Refusing to start: SMS_WEBHOOK_URL is required`，请将`SMS_WEBHOOK_URL`设置为您在Twilio控制台中配置的公共URL（见步骤3）。

向您的Twilio号码发送文本 — Hermes将通过SMS响应。

---

## 环境变量

| 变量 | 必需 | 描述 |
|----------|----------|-------------|
| `TWILIO_ACCOUNT_SID` | 是 | Twilio Account SID（以`AC`开头） |
| `TWILIO_AUTH_TOKEN` | 是 | Twilio Auth Token（也用于webhook签名验证） |
| `TWILIO_PHONE_NUMBER` | 是 | 您的Twilio电话号码（E.164格式） |
| `SMS_WEBHOOK_URL` | 是 | 用于Twilio签名验证的公共URL — 必须与Twilio控制台中的webhook URL匹配 |
| `SMS_WEBHOOK_PORT` | 否 | Webhook监听器端口（默认：`8080`） |
| `SMS_WEBHOOK_HOST` | 否 | Webhook绑定地址（默认：`0.0.0.0`） |
| `SMS_INSECURE_NO_SIGNATURE` | 否 | 设置为`true`以禁用签名验证（仅本地开发 — **不用于生产**） |
| `SMS_ALLOWED_USERS` | 否 | 允许聊天的逗号分隔E.164电话号码 |
| `SMS_ALLOW_ALL_USERS` | 否 | 设置为`true`以允许任何人（不推荐） |
| `SMS_HOME_CHANNEL` | 否 | 用于定时任务/通知传递的电话号码 |
| `SMS_HOME_CHANNEL_NAME` | 否 | 主频道的显示名称（默认：`Home`） |

---

## SMS特定行为

- **仅纯文本** — Markdown会自动剥离，因为SMS将其呈现为文字字符
- **1600字符限制** — 更长的响应会在自然边界（换行符，然后是空格）处分割成多条消息
- **回显预防** — 来自您自己的Twilio号码的消息被忽略，以防止循环
- **电话号码编辑** — 电话号码在日志中被编辑以保护隐私

---

## 安全

### Webhook签名验证

Hermes通过验证`X-Twilio-Signature`头（HMAC-SHA1）来验证入站webhook确实来自Twilio。这可以防止攻击者注入伪造消息。

**`SMS_WEBHOOK_URL`是必需的。** 将其设置为您在Twilio控制台中配置的公共URL。适配器会拒绝在没有它的情况下启动。

对于没有公共URL的本地开发，您可以禁用验证：

```bash
# 仅本地开发 — 不用于生产
SMS_INSECURE_NO_SIGNATURE=true
```

### 用户允许列表

**网关默认拒绝所有用户。** 配置允许列表：

```bash
# 推荐：限制特定电话号码
SMS_ALLOWED_USERS=+15559876543,+15551112222

# 或允许所有人（不推荐用于具有终端访问权限的机器人）
SMS_ALLOW_ALL_USERS=true
```

:::warning
SMS没有内置加密。除非您了解安全影响，否则不要将SMS用于敏感操作。对于敏感用例，首选Signal或Telegram。
:::

---

## 故障排除

### 消息未到达

1. 检查您的Twilio webhook URL是否正确且可公开访问
2. 验证`TWILIO_ACCOUNT_SID`和`TWILIO_AUTH_TOKEN`是否正确
3. 检查Twilio控制台 → **Monitor → Logs → Messaging** 中的传递错误
4. 确保您的电话号码在`SMS_ALLOWED_USERS`中（或`SMS_ALLOW_ALL_USERS=true`）

### 回复未发送

1. 检查`TWILIO_PHONE_NUMBER`是否正确设置（带有`+`的E.164格式）
2. 验证您的Twilio账户是否有支持SMS的号码
3. 检查Hermes网关日志中的Twilio API错误

### Webhook端口冲突

如果端口8080已被使用，请更改它：

```bash
SMS_WEBHOOK_PORT=3001
```

更新Twilio控制台中的webhook URL以匹配。