---
sidebar_position: 9
---

# 添加平台适配器

本指南涵盖如何向 Hermes 网关添加新的消息传递平台。平台适配器将 Hermes 连接到外部消息服务（Telegram、Discord、企业微信等），以便用户可以通过该服务与代理交互。

:::tip
添加平台适配器涉及代码、配置和文档中的 20+ 文件。将本指南用作清单 — 适配器文件本身通常只占工作量的 40%。
:::

## 架构概述

```
用户 ↔ 消息平台 ↔ 平台适配器 ↔ 网关运行器 ↔ AIAgent
```

每个适配器都扩展自 `gateway/platforms/base.py` 中的 `BasePlatformAdapter` 并实现：

- **`connect()`** — 建立连接（WebSocket、长轮询、HTTP 服务器等）
- **`disconnect()`** — 清理关闭
- **`send()`** — 向聊天发送文本消息
- **`send_typing()`** — 显示输入指示器（可选）
- **`get_chat_info()`** — 返回聊天元数据

入站消息由适配器接收并通过 `self.handle_message(event)` 转发，基类将其路由到网关运行器。

## 分步清单

### 1. 平台枚举

将您的平台添加到 `gateway/config.py` 中的 `Platform` 枚举：

```python
class Platform(str, Enum):
    # ... 现有平台 ...
    NEWPLAT = "newplat"
```

### 2. 适配器文件

创建 `gateway/platforms/newplat.py`：

```python
from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter, MessageEvent, MessageType, SendResult,
)

def check_newplat_requirements() -> bool:
    """Return True if dependencies are available."""
    return SOME_SDK_AVAILABLE

class NewPlatAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.NEWPLAT)
        # 从 config.extra dict 读取配置
        extra = config.extra or {}
        self._api_key = extra.get("api_key") or os.getenv("NEWPLAT_API_KEY", "")

    async def connect(self) -> bool:
        # 设置连接，开始轮询/webhook
        self._mark_connected()
        return True

    async def disconnect(self) -> None:
        self._running = False
        self._mark_disconnected()

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        # 通过平台 API 发送消息
        return SendResult(success=True, message_id="...")

    async def get_chat_info(self, chat_id):
        return {"name": chat_id, "type": "dm"}
```

对于入站消息，构建 `MessageEvent` 并调用 `self.handle_message(event)`：

```python
source = self.build_source(
    chat_id=chat_id,
    chat_name=name,
    chat_type="dm",  # 或 "group"
    user_id=user_id,
    user_name=user_name,
)
event = MessageEvent(
    text=content,
    message_type=MessageType.TEXT,
    source=source,
    message_id=msg_id,
)
await self.handle_message(event)
```

### 3. 网关配置 (`gateway/config.py`)

三个接触点：

1. **`get_connected_platforms()`** — 添加对平台所需凭证的检查
2. **`load_gateway_config()`** — 添加令牌环境映射条目：`Platform.NEWPLAT: "NEWPLAT_TOKEN"`
3. **`_apply_env_overrides()`** — 将所有 `NEWPLAT_*` 环境变量映射到配置

### 4. 网关运行器 (`gateway/run.py`)

五个接触点：

1. **`_create_adapter()`** — 添加 `elif platform == Platform.NEWPLAT:` 分支
2. **`_is_user_authorized()` allowed_users 映射** — `Platform.NEWPLAT: "NEWPLAT_ALLOWED_USERS"`
3. **`_is_user_authorized()` allow_all 映射** — `Platform.NEWPLAT: "NEWPLAT_ALLOW_ALL_USERS"`
4. 早期环境检查 `_any_allowlist` 元组 — 添加 `"NEWPLAT_ALLOWED_USERS"`
5. 早期环境检查 `_allow_all` 元组 — 添加 `"NEWPLAT_ALLOW_ALL_USERS"`
6. **`_UPDATE_ALLOWED_PLATFORMS` 冻结集** — 添加 `Platform.NEWPLAT`

### 5. 跨平台交付

1. **`gateway/platforms/webhook.py`** — 将 `"newplat"` 添加到交付类型元组
2. **`cron/scheduler.py`** — 添加到 `_KNOWN_DELIVERY_PLATFORMS` 冻结集和 `_deliver_result()` 平台映射

### 6. CLI 集成

1. **`hermes_cli/config.py`** — 将所有 `NEWPLAT_*` 变量添加到 `_EXTRA_ENV_KEYS`
2. **`hermes_cli/gateway.py`** — 向 `_PLATFORMS` 列表添加条目，包含 key、label、emoji、token_var、setup_instructions 和 vars
3. **`hermes_cli/platforms.py`** — 添加 `PlatformInfo` 条目，包含 label 和 default_toolset（由 `skills_config` 和 `tools_config` TUI 使用）
4. **`hermes_cli/setup.py`** — 添加 `_setup_newplat()` 函数（可以委托给 `gateway.py`）并向消息平台列表添加元组
5. **`hermes_cli/status.py`** — 添加平台检测条目：`"NewPlat": ("NEWPLAT_TOKEN", "NEWPLAT_HOME_CHANNEL")`
6. **`hermes_cli/dump.py`** — 向平台检测字典添加 `"newplat": "NEWPLAT_TOKEN"`

### 7. 工具

1. **`tools/send_message_tool.py`** — 向平台映射添加 `"newplat": Platform.NEWPLAT`
2. **`tools/cronjob_tools.py`** — 将 `newplat` 添加到交付目标描述字符串

### 8. 工具集

1. **`toolsets.py`** — 添加带有 `_HERMES_CORE_TOOLS` 的 `"hermes-newplat"` 工具集定义
2. **`toolsets.py`** — 将 `"hermes-newplat"` 添加到 `"hermes-gateway"` 包含列表

### 9. 可选：平台提示

**`agent/prompt_builder.py`** — 如果您的平台有特定的渲染限制（无 markdown、消息长度限制等），向 `_PLATFORM_HINTS` 字典添加条目。这会向系统提示注入平台特定的指导：

```python
_PLATFORM_HINTS = {
    # ...
    "newplat": (
        "You are chatting via NewPlat. It supports markdown formatting "
        "but has a 4000-character message limit."
    ),
}
```

并非所有平台都需要提示 — 只有当代理的行为应该不同时才添加。

### 10. 测试

创建 `tests/gateway/test_newplat.py`，涵盖：

- 从配置构建适配器
- 消息事件构建
- 发送方法（模拟外部 API）
- 平台特定功能（加密、路由等）

### 11. 文档

| 文件 | 要添加的内容 |
|------|-------------|
| `website/docs/user-guide/messaging/newplat.md` | 完整的平台设置页面 |
| `website/docs/user-guide/messaging/index.md` | 平台比较表、架构图、工具集表、安全部分、后续步骤链接 |
| `website/docs/reference/environment-variables.md` | 所有 NEWPLAT_* 环境变量 |
| `website/docs/reference/toolsets-reference.md` | hermes-newplat 工具集 |
| `website/docs/integrations/index.md` | 平台链接 |
| `website/sidebars.ts` | 文档页面的侧边栏条目 |
| `website/docs/developer-guide/architecture.md` | 适配器计数 + 列表 |
| `website/docs/developer-guide/gateway-internals.md` | 适配器文件列表 |

## 一致性审计

在将新平台 PR 标记为完成之前，针对已建立的平台运行一致性审计：

```bash
# 查找提及参考平台的每个 .py 文件
search_files "bluebubbles" output_mode="files_only" file_glob="*.py"

# 查找提及新平台的每个 .py 文件
search_files "newplat" output_mode="files_only" file_glob="*.py"

# 第一个集合中但第二个集合中没有的任何文件都是潜在的差距
```

对 `.md` 和 `.ts` 文件重复此操作。调查每个差距 — 是平台枚举（需要更新）还是平台特定引用（跳过）？

## 常见模式

### 长轮询适配器

如果您的适配器使用长轮询（如 Telegram 或微信），使用轮询循环任务：

```python
async def connect(self):
    self._poll_task = asyncio.create_task(self._poll_loop())
    self._mark_connected()

async def _poll_loop(self):
    while self._running:
        messages = await self._fetch_updates()
        for msg in messages:
            await self.handle_message(self._build_event(msg))
```

### 回调/Webhook 适配器

如果平台将消息推送到您的端点（如企业微信回调），运行 HTTP 服务器：

```python
async def connect(self):
    self._app = web.Application()
    self._app.router.add_post("/callback", self._handle_callback)
    # ... 启动 aiohttp 服务器
    self._mark_connected()

async def _handle_callback(self, request):
    event = self._build_event(await request.text())
    await self._message_queue.put(event)
    return web.Response(text="success")  # 立即确认
```

对于具有严格响应截止时间的平台（例如，企业微信的 5 秒限制），始终立即确认并稍后通过 API 主动传递代理的回复。代理会话运行 3–30 分钟 — 在回调响应窗口内进行内联回复是不可行的。

### 令牌锁

如果适配器持有带有唯一凭证的持久连接，添加作用域锁以防止两个配置文件使用相同的凭证：

```python
from gateway.status import acquire_scoped_lock, release_scoped_lock

async def connect(self):
    if not acquire_scoped_lock("newplat", self._token):
        logger.error("Token already in use by another profile")
        return False
    # ... 连接

async def disconnect(self):
    release_scoped_lock("newplat", self._token)
```

## 参考实现

| 适配器 | 模式 | 复杂度 | 适合参考 |
|---------|---------|------------|-------------------|
| `bluebubbles.py` | REST + webhook | 中等 | 简单 REST API 集成 |
| `weixin.py` | 长轮询 + CDN | 高 | 媒体处理、加密 |
| `wecom_callback.py` | 回调/webhook | 中等 | HTTP 服务器、AES 加密、多应用 |
| `telegram.py` | 长轮询 + Bot API | 高 | 具有群组、线程的全功能适配器 |
