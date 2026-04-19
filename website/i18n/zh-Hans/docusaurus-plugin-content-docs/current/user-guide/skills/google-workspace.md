---
sidebar_position: 2
sidebar_label: "Google Workspace"
title: "Google Workspace — Gmail、日历、云端硬盘、表格和文档"
description: "发送电子邮件、管理日历事件、搜索云端硬盘、读/写表格和访问文档 — 全部通过 OAuth2 认证的 Google API"
---

# Google Workspace 技能

Hermes 的 Gmail、日历、云端硬盘、联系人和表格与文档集成。使用 OAuth2 并自动刷新令牌。优先使用 [Google Workspace CLI (`gws`)](https://github.com/nicholasgasior/gws) 以获得更广泛的覆盖，否则回退到 Google 的 Python 客户端库。

**技能路径：** `skills/productivity/google-workspace/`

## 设置

设置完全由智能体驱动 — 要求 Hermes 设置 Google Workspace，它会引导您完成每个步骤。流程：

1. **创建 Google Cloud 项目** 并启用所需的 API（Gmail、日历、云端硬盘、表格、文档、人员）
2. **创建 OAuth 2.0 凭据**（桌面应用类型）并下载客户端密钥 JSON
3. **授权** — Hermes 生成授权 URL，您在浏览器中批准，粘贴回重定向 URL
4. **完成** — 从该点开始令牌自动刷新

:::tip 仅电子邮件用户
如果您只需要电子邮件（不需要日历/云端硬盘/表格），请改用 **himalaya** 技能 — 它使用 Gmail 应用密码，需要 2 分钟。无需 Google Cloud 项目。
:::

## Gmail

### 搜索

```bash
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"
```

返回 JSON，包含每条消息的 `id`、`from`、`subject`、`date`、`snippet` 和 `labels`。

### 阅读

```bash
$GAPI gmail get MESSAGE_ID
```

返回完整消息正文作为文本（首选纯文本，回退到 HTML）。

### 发送

```bash
# 基本发送
$GAPI gmail send "Hello world" --to recipient@example.com

# 带附件发送
$GAPI gmail send "Report attached" --to boss@company.com --attach report.pdf

# HTML 邮件
$GAPI gmail send "<h1>Title</h1><p>Content</p>" --to recipient@example.com --html
```

### 标签管理

```bash
# 列出所有标签
$GAPI gmail labels

# 添加标签到消息
$GAPI gmail label MESSAGE_ID --add "IMPORTANT"

# 从消息移除标签
$GAPI gmail label MESSAGE_ID --remove "INBOX"
```

## 日历

### 创建事件

```bash
# 基本事件
$GAPI calendar create "Team meeting" --start "2025-04-20 14:00" --duration 60

# 完整事件
$GAPI calendar create "Project review" \
  --start "2025-04-20 14:00" \
  --end "2025-04-20 16:00" \
  --location "Conference Room A" \
  --description "Review Q1 progress" \
  --attendees alice@example.com,bob@example.com
```

### 搜索事件

```bash
# 即将到来的事件
$GAPI calendar list --days 7

# 特定日期范围
$GAPI calendar list --start "2025-04-20" --end "2025-04-27"

# 搜索关键词
$GAPI calendar search "meeting"
```

### 更新/删除事件

```bash
# 更新事件
$GAPI calendar update EVENT_ID --start "2025-04-20 15:00"

# 删除事件
$GAPI calendar delete EVENT_ID
```

## 云端硬盘

### 搜索文件

```bash
# 基本搜索
$GAPI drive search "report"

# 按类型搜索
$GAPI drive search "report" --type spreadsheet

# 按日期搜索
$GAPI drive search "report" --newer-than "30d"
```

### 下载文件

```bash
# 下载到当前目录
$GAPI drive download FILE_ID

# 下载到特定路径
$GAPI drive download FILE_ID --output /path/to/save
```

### 上传文件

```bash
# 上传文件
$GAPI drive upload report.pdf --name "Q1 Report"

# 上传到特定文件夹
$GAPI drive upload report.pdf --folder FOLDER_ID
```

## 表格

### 读取数据

```bash
# 读取整个表格
$GAPI sheets read SPREADSHEET_ID

# 读取特定范围
$GAPI sheets read SPREADSHEET_ID --range "Sheet1!A1:C10"
```

### 写入数据

```bash
# 更新单个单元格
$GAPI sheets write SPREADSHEET_ID --range "Sheet1!A1" --value "Hello"

# 批量更新
$GAPI sheets write SPREADSHEET_ID --range "Sheet1!A1:C3" --values "data.csv"

# 追加行
$GAPI sheets append SPREADSHEET_ID --range "Sheet1!A1" --values "new_data.csv"
```

### 创建表格

```bash
# 创建新表格
$GAPI sheets create "Project Tracker" --rows 100 --cols 10
```

## 文档

### 读取文档

```bash
# 读取文档内容
$GAPI docs read DOCUMENT_ID
```

### 创建文档

```bash
# 创建新文档
$GAPI docs create "Meeting Notes" --content "Discussion points..."
```

## 联系人

### 搜索联系

```bash
# 搜索联系人
$GAPI people search "John Doe"

# 列出所有联系
$GAPI people list
```

## 故障排除

### 令牌刷新失败

如果令牌刷新失败：

1. 删除 `~/.hermes/skills/productivity/google-workspace/token.json`
2. 重新运行设置：要求 Hermes "重新设置 Google Workspace"

### 权限错误

如果遇到权限错误：

1. 检查 Google Cloud 控制台中的 API 是否已启用
2. 验证 OAuth 同意屏幕是否包含所有必需的作用域
3. 重新授权：删除令牌文件并重新运行设置

### 配额限制

Google API 有配额限制。如果遇到限制：

- 使用 Google Workspace CLI (`gws`) 以获得更高的配额
- 实施请求速率限制
- 考虑升级到付费 Google Workspace 计划