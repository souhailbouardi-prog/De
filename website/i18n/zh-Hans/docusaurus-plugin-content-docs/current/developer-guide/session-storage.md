# 会话存储

Hermes Agent 使用 SQLite 数据库 (`~/.hermes/state.db`) 来持久化会话
元数据、完整消息历史记录和模型配置，跨越 CLI 和网关
会话。这取代了早期的每个会话 JSONL 文件方法。

源文件：`hermes_state.py`


## 架构概述

```
~/.hermes/state.db (SQLite, WAL 模式)
├── sessions          — 会话元数据、令牌计数、计费
├── messages          — 每个会话的完整消息历史记录
├── messages_fts      — 用于全文搜索的 FTS5 虚拟表
└── schema_version    — 跟踪迁移状态的单行表
```

关键设计决策：
- **WAL 模式** 用于并发读取器 + 一个写入器（网关多平台）
- **FTS5 虚拟表** 用于跨所有会话消息的快速文本搜索
- **会话谱系** 通过 `parent_session_id` 链（压缩触发的拆分）
- **源标记** (`cli`, `telegram`, `discord`, 等) 用于平台过滤
- 批处理运行器和 RL 轨迹不存储在此处（单独的系统）


## SQLite 模式

### Sessions 表

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_title_unique
    ON sessions(title) WHERE title IS NOT NULL;
```

### Messages Table

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_details TEXT,
    codex_reasoning_items TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
```

Notes:
- `tool_calls` is stored as a JSON string (serialized list of tool call objects)
- `reasoning_details` and `codex_reasoning_items` are stored as JSON strings
- `reasoning` stores the raw reasoning text for providers that expose it
- Timestamps are Unix epoch floats (`time.time()`)

### FTS5 Full-Text Search

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

The FTS5 table is kept in sync via three triggers that fire on INSERT, UPDATE,
and DELETE of the `messages` table:

```sql
CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```


## Schema Version and Migrations

当前 schema 版本：**6**

`schema_version` 表存储一个整数。初始化时，`_init_schema()` 检查当前版本并按顺序应用迁移：

| 版本 | 变更 |
|---------|--------|
| 1 | 初始 schema（sessions、messages、FTS5） |
| 2 | 向 messages 添加 `finish_reason` 列 |
| 3 | 向 sessions 添加 `title` 列 |
| 4 | 在 `title` 上添加唯一索引（允许 NULL，非 NULL 必须唯一） |
| 5 | 添加计费列：`cache_read_tokens`、`cache_write_tokens`、`reasoning_tokens`、`billing_provider`、`billing_base_url`、`billing_mode`、`estimated_cost_usd`、`actual_cost_usd`、`cost_status`、`cost_source`、`pricing_version` |
| 6 | 向 messages 添加推理列：`reasoning`、`reasoning_details`、`codex_reasoning_items` |

每次迁移使用 `ALTER TABLE ADD COLUMN` 包装在 try/except 中以处理列已存在的情况（幂等）。版本号在每次成功的迁移块之后递增。

## Write Contention Handling

多个 hermes 进程（gateway + CLI 会话 + worktree 智能体）共享一个 `state.db`。`SessionDB` 类通过以下方式处理写竞争：

- **短 SQLite 超时**（1 秒）而不是默认的 30 秒
- **应用级重试**带有随机抖动（20-150ms，最多 15 次重试）
- **BEGIN IMMEDIATE** 事务在事务开始时暴露锁竞争
- **定期 WAL 检查点**每 50 次成功写入（PASSIVE 模式）

这避免了" convoy 效应"，即 SQLite 的确定性内部退避导致所有竞争写入者在相同间隔重试。

```
_WRITE_MAX_RETRIES = 15
_WRITE_RETRY_MIN_S = 0.020   # 20ms
_WRITE_RETRY_MAX_S = 0.150   # 150ms
_CHECKPOINT_EVERY_N_WRITES = 50
```


## Schema Version and Migrations

当前 schema 版本：**6**

`schema_version` 表存储一个整数。初始化时，`_init_schema()` 检查当前版本并按顺序应用迁移：

| 版本 | 变更 |
|---------|--------|
| 1 | 初始 schema（sessions、messages、FTS5） |
| 2 | 向 messages 添加 `finish_reason` 列 |
| 3 | 向 sessions 添加 `title` 列 |
| 4 | 在 `title` 上添加唯一索引（允许 NULL，非 NULL 必须唯一） |
| 5 | 添加计费列：`cache_read_tokens`、`cache_write_tokens`、`reasoning_tokens`、`billing_provider`、`billing_base_url`、`billing_mode`、`estimated_cost_usd`、`actual_cost_usd`、`cost_status`、`cost_source`、`pricing_version` |
| 6 | 向 messages 添加推理列：`reasoning`、`reasoning_details`、`codex_reasoning_items` |

每次迁移使用 `ALTER TABLE ADD COLUMN` 包装在 try/except 中以处理列已存在的情况（幂等）。版本号在每次成功的迁移块之后递增。

## Write Contention Handling

多个 hermes 进程（gateway + CLI 会话 + worktree 智能体）共享一个 `state.db`。`SessionDB` 类通过以下方式处理写竞争：

- **短 SQLite 超时**（1 秒）而不是默认的 30 秒
- **应用级重试**带有随机抖动（20-150ms，最多 15 次重试）
- **BEGIN IMMEDIATE** 事务在事务开始时暴露锁竞争
- **定期 WAL 检查点**每 50 次成功写入（PASSIVE 模式）

这避免了" convoy 效应"，即 SQLite 的确定性内部退避导致所有竞争写入者在相同间隔重试。

## Common Operations

### Initialize

```python
from hermes_state import SessionDB

db = SessionDB()                           # 默认: ~/.hermes/state.db
db = SessionDB(db_path=Path("/tmp/test.db"))  # 自定义路径
```

### 创建和管理会话

```python
# 创建新会话
db.create_session(
    session_id="sess_abc123",
    source="cli",
    model="anthropic/claude-sonnet-4.6",
    user_id="user_1",
    parent_session_id=None,  # 或用于谱系的先前会话 ID
)

# 结束会话
db.end_session("sess_abc123", end_reason="user_exit")

# 重新打开会话（清除 ended_at/end_reason）
db.reopen_session("sess_abc123")
```

### 存储消息

```python
msg_id = db.append_message(
    session_id="sess_abc123",
    role="assistant",
    content="Here's the answer...",
    tool_calls=[{"id": "call_1", "function": {"name": "terminal", "arguments": "{}"}}],
    token_count=150,
    finish_reason="stop",
    reasoning="Let me think about this...",
)
```

### 检索消息

```python
# 带有所有元数据的原始消息
messages = db.get_messages("sess_abc123")

# OpenAI 对话格式（用于 API 重放）
conversation = db.get_messages_as_conversation("sess_abc123")
# 返回: [{"role": "user", "content": "..."}, {"role": "assistant", ...}]
```

### Session Titles

```python
# Set a title (must be unique among non-NULL titles)
db.set_session_title("sess_abc123", "Fix Docker Build")

# Resolve by title (returns most recent in lineage)
session_id = db.resolve_session_by_title("Fix Docker Build")

# Auto-generate next title in lineage
next_title = db.get_next_title_in_lineage("Fix Docker Build")
# Returns: "Fix Docker Build #2"
```


## Full-Text Search

`search_messages()` 方法支持 FTS5 查询语法，并自动清理用户输入。

### 基本搜索

```python
results = db.search_messages("docker deployment")
```

### FTS5 查询语法

| 语法 | 示例 | 含义 |
|--------|---------|---------|
| 关键词 | `docker deployment` | 两个术语（隐含 AND） |
| 引号短语 | `"exact phrase"` | 精确短语匹配 |
| 布尔 OR | `docker OR kubernetes` | 任一术语 |
| 布尔 NOT | `python NOT java` | 排除术语 |
| 前缀 | `deploy*` | 前缀匹配 |

### 过滤搜索

```python
# 仅搜索 CLI 会话
results = db.search_messages("error", source_filter=["cli"])

# 排除 gateway 会话
results = db.search_messages("bug", exclude_sources=["telegram", "discord"])

# 仅搜索用户消息
results = db.search_messages("help", role_filter=["user"])
```

### 搜索结果格式

每个结果包括：
- `id`、`session_id`、`role`、`timestamp`
- `snippet` — FTS5 生成的片段，带有 `>>>match<<<` 标记
- `context` — 匹配前后的 1 条消息（内容截断为 200 字符）
- `source`、`model`、`session_started` — 来自父会话

`_sanitize_fts5_query()` 方法处理边缘情况：
- 剥离不匹配的引号和特殊字符
- 将带连字符的术语用引号包装（`chat-send` → `"chat-send"`）
- 移除悬空的布尔运算符（`hello AND` → `hello`）


## Session Lineage

会话可以通过 `parent_session_id` 形成链。这在网关中触发会话分割时发生。

### 查询：查找会话谱系

```sql
-- 查找会话的所有祖先
WITH RECURSIVE lineage AS (
    SELECT * FROM sessions WHERE id = ?
    UNION ALL
    SELECT s.* FROM sessions s
    JOIN lineage l ON s.id = l.parent_session_id
)
SELECT id, title, started_at, parent_session_id FROM lineage;

-- 查找会话的所有后代
WITH RECURSIVE descendants AS (
    SELECT * FROM sessions WHERE id = ?
    UNION ALL
    SELECT s.* FROM sessions s
    JOIN descendants d ON s.parent_session_id = d.id
)
SELECT id, title, started_at FROM descendants;
```

### 查询：带有预览的最近会话

```sql
SELECT s.*,
    COALESCE(
        (SELECT SUBSTR(m.content, 1, 63)
         FROM messages m
         WHERE m.session_id = s.id AND m.role = 'user' AND m.content IS NOT NULL
         ORDER BY m.timestamp, m.id LIMIT 1),
        ''
    ) AS preview,
    COALESCE(
        (SELECT MAX(m2.timestamp) FROM messages m2 WHERE m2.session_id = s.id),
        s.started_at
    ) AS last_active
FROM sessions s
ORDER BY s.started_at DESC
LIMIT 20;
```

### 查询：Token 使用统计

```sql
-- 按模型分类的总 token
SELECT model,
       COUNT(*) as session_count,
       SUM(input_tokens) as total_input,
       SUM(output_tokens) as total_output,
       SUM(estimated_cost_usd) as total_cost
FROM sessions
WHERE model IS NOT NULL
GROUP BY model
ORDER BY total_cost DESC;

-- Sessions with highest token usage
SELECT id, title, model, input_tokens + output_tokens AS total_tokens,
       estimated_cost_usd
FROM sessions
ORDER BY total_tokens DESC
LIMIT 10;
```


## Export and Cleanup

```python
# 导出单个会话及其消息
data = db.export_session("sess_abc123")

# 导出所有会话（带消息）为字典列表
all_data = db.export_all(source="cli")

# 删除旧会话（仅限已结束的会话）
deleted_count = db.prune_sessions(older_than_days=90)
deleted_count = db.prune_sessions(older_than_days=30, source="telegram")

# 清除消息但保留会话记录
db.clear_messages("sess_abc123")

# 删除会话及其所有消息
db.delete_session("sess_abc123")
```


## 数据库位置

默认路径：`~/.hermes/state.db`

这由 `hermes_constants.get_hermes_home()` 解析而来，默认值为 `~/.hermes/`，或 `HERMES_HOME` 环境变量的值。

数据库文件、WAL 文件（`state.db-wal`）和共享内存文件（`state.db-shm`）都在同一目录中创建。