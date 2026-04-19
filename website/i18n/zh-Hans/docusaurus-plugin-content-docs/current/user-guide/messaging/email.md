---
sidebar_position: 7
title: "Email"
description: "通过IMAP/SMTP设置Hermes Agent作为电子邮件助手"
---

# 电子邮件设置

Hermes可以使用标准的IMAP和SMTP协议接收和回复电子邮件。向代理的地址发送电子邮件，它会在同一线程中回复——不需要特殊客户端或机器人API。适用于Gmail、Outlook、Yahoo、Fastmail或任何支持IMAP/SMTP的提供商。

:::info 无外部依赖
电子邮件适配器使用Python内置的`imaplib`、`smtplib`和`email`模块。不需要额外的包或外部服务。
:::

---

## 先决条件

- **专用电子邮件账户** 用于您的Hermes代理（不要使用个人电子邮件）
- **在电子邮件账户上启用IMAP**
- **应用密码** 如果使用Gmail或其他启用2FA的提供商

### Gmail设置

1. 在您的Google账户上启用双因素认证
2. 前往 [应用密码](https://myaccount.google.com/apppasswords)
3. 创建新的应用密码（选择"邮件"或"其他"）
4. 复制16字符的密码——您将使用此密码代替常规密码

### Outlook / Microsoft 365

1. 前往 [安全设置](https://account.microsoft.com/security)
2. 如果尚未激活，启用2FA
3. 在"其他安全选项"下创建应用密码
4. IMAP主机：`outlook.office365.com`，SMTP主机：`smtp.office365.com`

### 其他提供商

大多数电子邮件提供商支持IMAP/SMTP。查看您的提供商文档获取：
- IMAP主机和端口（通常是带有SSL的993端口）
- SMTP主机和端口（通常是带有STARTTLS的587端口）
- 是否需要应用密码

---

## 步骤1：配置Hermes

最简单的方法：

```bash
hermes gateway setup
```

从平台菜单中选择 **Email**。向导会提示您输入电子邮件地址、密码、IMAP/SMTP主机和允许的发件人。

### 手动配置

添加到 `~/.hermes/.env`：

```bash
# 必需
EMAIL_ADDRESS=hermes@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop    # 应用密码（不是常规密码）
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_SMTP_HOST=smtp.gmail.com

# 安全（推荐）
EMAIL_ALLOWED_USERS=your@email.com,colleague@work.com

# 可选
EMAIL_IMAP_PORT=993                    # 默认：993（IMAP SSL）
EMAIL_SMTP_PORT=587                    # 默认：587（SMTP STARTTLS）
EMAIL_POLL_INTERVAL=15                 # 收件箱检查间隔（默认：15秒）
EMAIL_HOME_ADDRESS=your@email.com      # 定时任务的默认传递目标
```

---

## 步骤2：启动网关

```bash
hermes gateway              # 在前台运行
hermes gateway install      # 安装为用户服务
sudo hermes gateway install --system   # 仅Linux：启动时系统服务
```

启动时，适配器：
1. 测试IMAP和SMTP连接
2. 将所有现有收件箱邮件标记为"已读"（仅处理新邮件）
3. 开始轮询新消息

---

## 工作原理

### 接收消息

适配器以可配置的间隔（默认：15秒）轮询IMAP收件箱中的未读消息。对于每封新邮件：

- **主题行** 作为上下文包含（例如，`[Subject: Deploy to production]`）
- **回复邮件**（主题以`Re:`开头）跳过主题前缀——线程上下文已经建立
- **附件** 本地缓存：
  - 图像（JPEG、PNG、GIF、WebP）→ 可用于视觉工具
  - 文档（PDF、ZIP等）→ 可用于文件访问
- **仅HTML邮件** 剥离标签以提取纯文本
- **自消息** 被过滤掉以防止回复循环
- **自动/无回复发件人** 被静默忽略——`noreply@`、`mailer-daemon@`、`bounce@`、`no-reply@`以及带有`Auto-Submitted`、`Precedence: bulk`或`List-Unsubscribe`头的邮件

### 发送回复

回复通过SMTP发送，具有正确的电子邮件线程：

- **In-Reply-To** 和 **References** 头维护线程
- **主题行** 保留`Re:`前缀（无双重`Re: Re:`）
- **Message-ID** 用代理的域生成
- 响应以纯文本形式发送（UTF-8）

### 文件附件

代理可以在回复中发送文件附件。在响应中包含`MEDIA:/path/to/file`，文件将被附加到 outgoing email。

### 跳过附件

要忽略所有传入附件（用于恶意软件保护或带宽节省），请添加到您的`config.yaml`：

```yaml
platforms:
  email:
    skip_attachments: true
```

启用后，附件和内联部分在有效负载解码前被跳过。邮件正文文本仍正常处理。

---

## 访问控制

电子邮件访问遵循与所有其他Hermes平台相同的模式：

1. **设置`EMAIL_ALLOWED_USERS`** → 仅处理来自这些地址的电子邮件
2. **未设置允许列表** → 未知发件人获得配对代码
3. **`EMAIL_ALLOW_ALL_USERS=true`** → 接受任何发件人（谨慎使用）

:::warning
**始终配置`EMAIL_ALLOWED_USERS`。** 没有它，任何知道代理电子邮件地址的人都可以发送命令。代理默认具有终端访问权限。
:::

---

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| **启动时"IMAP连接失败"** | 验证`EMAIL_IMAP_HOST`和`EMAIL_IMAP_PORT`。确保在账户上启用了IMAP。对于Gmail，在设置→转发和POP/IMAP中启用它。 |
| **启动时"SMTP连接失败"** | 验证`EMAIL_SMTP_HOST`和`EMAIL_SMTP_PORT`。检查您的密码是否正确（对Gmail使用应用密码）。 |
| **未收到消息** | 检查`EMAIL_ALLOWED_USERS`是否包含发件人的电子邮件。检查垃圾邮件文件夹——某些提供商会标记自动回复。 |
| **"认证失败"** | 对于Gmail，您必须使用应用密码，而不是常规密码。确保首先启用2FA。 |
| **重复回复** | 确保只运行一个网关实例。检查`hermes gateway status`。 |
| **响应缓慢** | 默认轮询间隔为15秒。使用`EMAIL_POLL_INTERVAL=5`减少以获得更快的响应（但更多IMAP连接）。 |
| **回复未线程化** | 适配器使用In-Reply-To头。一些电子邮件客户端（尤其是基于Web的）可能无法正确线程化自动消息。 |

---

## 安全

:::warning
**使用专用电子邮件账户。** 不要使用个人电子邮件——代理在`.env`中存储密码，并通过IMAP拥有完整的收件箱访问权限。
:::

- 使用**应用密码**代替主密码（对启用2FA的Gmail是必需的）
- 设置`EMAIL_ALLOWED_USERS`以限制谁可以与代理交互
- 密码存储在`~/.hermes/.env`中——保护此文件（`chmod 600`）
- IMAP默认使用SSL（端口993），SMTP默认使用STARTTLS（端口587）——连接已加密

---

## 环境变量参考

| 变量 | 必需 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `EMAIL_ADDRESS` | 是 | — | 代理的电子邮件地址 |
| `EMAIL_PASSWORD` | 是 | — | 电子邮件密码或应用密码 |
| `EMAIL_IMAP_HOST` | 是 | — | IMAP服务器主机（例如，`imap.gmail.com`） |
| `EMAIL_SMTP_HOST` | 是 | — | SMTP服务器主机（例如，`smtp.gmail.com`） |
| `EMAIL_IMAP_PORT` | 否 | `993` | IMAP服务器端口 |
| `EMAIL_SMTP_PORT` | 否 | `587` | SMTP服务器端口 |
| `EMAIL_POLL_INTERVAL` | 否 | `15` | 收件箱检查间隔（秒） |
| `EMAIL_ALLOWED_USERS` | 否 | — | 逗号分隔的允许发件人地址 |
| `EMAIL_HOME_ADDRESS` | 否 | — | 定时任务的默认传递目标 |
| `EMAIL_ALLOW_ALL_USERS` | 否 | `false` | 允许所有发件人（不推荐） |