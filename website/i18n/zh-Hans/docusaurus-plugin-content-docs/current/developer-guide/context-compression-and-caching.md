# 上下文压缩与缓存

Hermes Agent 使用双重压缩系统和 Anthropic 提示缓存来
在长对话中高效管理上下文窗口使用。

源文件：`agent/context_engine.py` (ABC), `agent/context_compressor.py` (默认引擎),
`agent/prompt_caching.py`, `gateway/run.py` (会话卫生), `run_agent.py` (搜索 `_compress_context`)


## 可插拔上下文引擎

上下文管理基于 `ContextEngine` ABC (`agent/context_engine.py`) 构建。内置的 `ContextCompressor` 是默认实现，但插件可以替换为替代引擎（例如，无损上下文管理）。

```yaml
context:
  engine: "compressor"    # 默认 — 内置有损摘要
  engine: "lcm"           # 示例 — 提供无损上下文的插件
```

引擎负责：
- 决定何时触发压缩 (`should_compress()`)
- 执行压缩 (`compress()`)
- 可选地暴露智能体可以调用的工具（例如，`lcm_grep`）
- 跟踪 API 响应的令牌使用情况

选择通过 `config.yaml` 中的 `context.engine` 进行配置驱动。解析顺序：
1. 检查 `plugins/context_engine/<name>/` 目录
2. 检查通用插件系统 (`register_context_engine()`)
3. 回退到内置的 `ContextCompressor`

插件引擎**从不自动激活** — 用户必须显式将 `context.engine` 设置为插件的名称。默认的 `"compressor"` 始终使用内置引擎。

通过 `hermes plugins` → Provider Plugins → Context Engine 配置，或直接编辑 `config.yaml`。

要构建上下文引擎插件，请参阅 [上下文引擎插件](/docs/developer-guide/context-engine-plugin)。

## 双重压缩系统

Hermes 有两个独立的压缩层，它们独立运行：

```
                     ┌──────────────────────────┐
  传入消息           │   网关会话卫生            │ 在上下文 85% 时触发
  ─────────────────► │   (代理前，粗略估计)      │ 大型会话的安全网
                     └─────────────┬────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │   智能体 ContextCompressor │ 在上下文 50% 时触发（默认）
                     │   (循环内，真实令牌)       │ 正常上下文管理
                     └──────────────────────────┘
```

### 1. Gateway Session Hygiene (85% threshold)

Located in `gateway/run.py` (search for `Session hygiene: auto-compress`). This is a **safety net** that
runs before the agent processes a message. It prevents API failures when sessions
grow too large between turns (e.g., overnight accumulation in Telegram/Discord).

- **Threshold**: Fixed at 85% of model context length
- **Token source**: Prefers actual API-reported tokens from last turn; falls back
  to rough character-based estimate (`estimate_messages_tokens_rough`)
- **Fires**: Only when `len(history) >= 4` and compression is enabled
- **Purpose**: Catch sessions that escaped the agent's own compressor

The gateway hygiene threshold is intentionally higher than the agent's compressor.
Setting it at 50% (same as the agent) caused premature compression on every turn
in long gateway sessions.

### 2. Agent ContextCompressor (50% threshold, configurable)

Located in `agent/context_compressor.py`. This is the **primary compression
system** that runs inside the agent's tool loop with access to accurate,
API-reported token counts.


## Configuration

All compression settings are read from `config.yaml` under the `compression` key:

```yaml
compression:
  enabled: true              # Enable/disable compression (default: true)
  threshold: 0.50            # Fraction of context window (default: 0.50 = 50%)
  target_ratio: 0.20         # How much of threshold to keep as tail (default: 0.20)
  protect_last_n: 20         # Minimum protected tail messages (default: 20)

# Summarization model/provider configured under auxiliary:
auxiliary:
  compression:
    model: null              # Override model for summaries (default: auto-detect)
    provider: auto           # Provider: "auto", "openrouter", "nous", "main", etc.
    base_url: null           # Custom OpenAI-compatible endpoint
```

### Parameter Details

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `threshold` | `0.50` | 0.0-1.0 | Compression triggers when prompt tokens ≥ `threshold × context_length` |
| `target_ratio` | `0.20` | 0.10-0.80 | Controls tail protection token budget: `threshold_tokens × target_ratio` |
| `protect_last_n` | `20` | ≥1 | Minimum number of recent messages always preserved |
| `protect_first_n` | `3` | (hardcoded) | System prompt + first exchange always preserved |

### Computed Values (for a 200K context model at defaults)

```
context_length       = 200,000
threshold_tokens     = 200,000 × 0.50 = 100,000
tail_token_budget    = 100,000 × 0.20 = 20,000
max_summary_tokens   = min(200,000 × 0.05, 12,000) = 10,000
```


## Compression Algorithm

The `ContextCompressor.compress()` method follows a 4-phase algorithm:

### Phase 1: Prune Old Tool Results (cheap, no LLM call)

Old tool results (>200 chars) outside the protected tail are replaced with:
```
[Old tool output cleared to save context space]
```

This is a cheap pre-pass that saves significant tokens from verbose tool
outputs (file contents, terminal output, search results).

### Phase 2: Determine Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│  Message list                                               │
│                                                             │
│  [0..2]  ← protect_first_n (system + first exchange)        │
│  [3..N]  ← middle turns → SUMMARIZED                        │
│  [N..end] ← tail (by token budget OR protect_last_n)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Tail protection is **token-budget based**: walks backward from the end,
accumulating tokens until the budget is exhausted. Falls back to the fixed
`protect_last_n` count if the budget would protect fewer messages.

Boundaries are aligned to avoid splitting tool_call/tool_result groups.
The `_align_boundary_backward()` method walks past consecutive tool results
to find the parent assistant message, keeping groups intact.

### Phase 3: Generate Structured Summary

:::warning Summary model context length
The summary model must have a context window **at least as large** as the main agent model's. The entire middle section is sent to the summary model in a single `call_llm(task="compression")` call. If the summary model's context is smaller, the API returns a context-length error — `_generate_summary()` catches it, logs a warning, and returns `None`. The compressor then drops the middle turns **without a summary**, silently losing conversation context. This is the most common cause of degraded compaction quality.
:::

The middle turns are summarized using the auxiliary LLM with a structured
template:

```
## Goal
[What the user is trying to accomplish]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions]

## Progress
### Done
[Completed work — specific file paths, commands run, results]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues encountered]

## Key Decisions
[Important technical decisions and why]

## Relevant Files
[Files read, modified, or created — with brief note on each]

## Next Steps
[What needs to happen next]

## Critical Context
[Specific values, error messages, configuration details]
```

Summary budget scales with the amount of content being compressed:
- Formula: `content_tokens × 0.20` (the `_SUMMARY_RATIO` constant)
- Minimum: 2,000 tokens
- Maximum: `min(context_length × 0.05, 12,000)` tokens

### Phase 4: Assemble Compressed Messages

The compressed message list is:
1. Head messages (with a note appended to system prompt on first compression)
2. Summary message (role chosen to avoid consecutive same-role violations)
3. Tail messages (unmodified)

Orphaned tool_call/tool_result pairs are cleaned up by `_sanitize_tool_pairs()`:
- Tool results referencing removed calls → removed
- Tool calls whose results were removed → stub result injected

### Iterative Re-compression

On subsequent compressions, the previous summary is passed to the LLM with
instructions to **update** it rather than summarize from scratch. This preserves
information across multiple compactions — items move from "In Progress" to "Done",
new progress is added, and obsolete information is removed.

The `_previous_summary` field on the compressor instance stores the last summary
text for this purpose.


## Before/After Example

### Before Compression (45 messages, ~95K tokens)

```
[0] system:    "You are a helpful assistant..." (system prompt)
[1] user:      "Help me set up a FastAPI project"
[2] assistant: <tool_call> terminal: mkdir project </tool_call>
[3] tool:      "directory created"
[4] assistant: <tool_call> write_file: main.py </tool_call>
[5] tool:      "file written (2.3KB)"
    ... 30 more turns of file editing, testing, debugging ...
[38] assistant: <tool_call> terminal: pytest </tool_call>
[39] tool:      "8 passed, 2 failed\n..."  (5KB output)
[40] user:      "Fix the failing tests"
[41] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[42] tool:      "import pytest\n..."  (3KB)
[43] assistant: "I see the issue with the test fixtures..."
[44] user:      "Great, also add error handling"
```

### After Compression (25 messages, ~45K tokens)

```
[0] system:    "You are a helpful assistant...
               [Note: Some earlier conversation turns have been compacted...]"
[1] user:      "Help me set up a FastAPI project"
[2] assistant: "[CONTEXT COMPACTION] Earlier turns were compacted...

               ## Goal
               Set up a FastAPI project with tests and error handling

               ## Progress
               ### Done
               - Created project structure: main.py, tests/, requirements.txt
               - Implemented 5 API endpoints in main.py
               - Wrote 10 test cases in tests/test_api.py
               - 8/10 tests passing

               ### In Progress
               - Fixing 2 failing tests (test_create_user, test_delete_user)

               ## Relevant Files
               - main.py — FastAPI app with 5 endpoints
               - tests/test_api.py — 10 test cases
               - requirements.txt — fastapi, pytest, httpx

               ## Next Steps
               - Fix failing test fixtures
               - Add error handling"
[3] user:      "Fix the failing tests"
[4] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[5] tool:      "import pytest\n..."
[6] assistant: "I see the issue with the test fixtures..."
[7] user:      "Great, also add error handling"
```


## Prompt Caching (Anthropic)

Source: `agent/prompt_caching.py`

Reduces input token costs by ~75% on multi-turn conversations by caching the
conversation prefix. Uses Anthropic's `cache_control` breakpoints.

### Strategy: system_and_3

Anthropic allows a maximum of 4 `cache_control` breakpoints per request. Hermes
uses the "system_and_3" strategy:

```
Breakpoint 1: System prompt           (stable across all turns)
Breakpoint 2: 3rd-to-last non-system message  ─┐
Breakpoint 3: 2nd-to-last non-system message   ├─ Rolling window
Breakpoint 4: Last non-system message          ─┘
```

### How It Works

`apply_anthropic_cache_control()` deep-copies the messages and injects
`cache_control` markers:

```python
# Cache marker format
marker = {"type": "ephemeral"}
# Or for 1-hour TTL:
marker = {"type": "ephemeral", "ttl": "1h"}
```

The marker is applied differently based on content type:

| Content Type | Where Marker Goes |
|-------------|-------------------|
| String content | Converted to `[{"type": "text", "text": ..., "cache_control": ...}]` |
| List content | Added to the last element's dict |
| None/empty | Added as `msg["cache_control"]` |
| Tool messages | Added as `msg["cache_control"]` (native Anthropic only) |

### Cache-Aware Design Patterns

1. **Stable system prompt**: The system prompt is breakpoint 1 and cached across
   all turns. Avoid mutating it mid-conversation (compression appends a note
   only on the first compaction).

2. **Message ordering matters**: Cache hits require prefix matching. Adding or
   removing messages in the middle invalidates the cache for everything after.

3. **Compression cache interaction**: After compression, the cache is invalidated
   for the compressed region but the system prompt cache survives. The rolling
   3-message window re-establishes caching within 1-2 turns.

4. **TTL selection**: Default is `5m` (5 minutes). Use `1h` for long-running
   sessions where the user takes breaks between turns.

### Enabling Prompt Caching

Prompt caching is automatically enabled when:
- The model is an Anthropic Claude model (detected by model name)
- The provider supports `cache_control` (native Anthropic API or OpenRouter)

```yaml
# config.yaml — TTL is configurable
model:
  cache_ttl: "5m"   # "5m" or "1h"
```

The CLI shows caching status at startup:
```
💾 Prompt caching: ENABLED (Claude via OpenRouter, 5m TTL)
```


## Context Pressure Warnings

The agent emits context pressure warnings at 85% of the compression threshold
(not 85% of context — 85% of the threshold which is itself 50% of context):

```
⚠️  Context is 85% to compaction threshold (42,500/50,000 tokens)
```

After compression, if usage drops below 85% of threshold, the warning state
is cleared. If compression fails to reduce below the warning level (the
conversation is too dense), the warning persists but compression won't
re-trigger until the threshold is exceeded again.