---
sidebar_position: 8
title: "代码执行"
description: "带有 RPC 工具访问的沙箱化 Python 执行 — 将多步骤工作流压缩到单个轮次"
---

# 代码执行（程序化工具调用）

`execute_code` 工具允许智能体编写 Python 脚本，以编程方式调用 Hermes 工具，从而将多步骤工作流压缩到单个 LLM 轮次中。脚本在智能体主机上的沙箱化子进程中运行，通过 Unix 域套接字 RPC 进行通信。

## 工作原理

1. 智能体使用 `from hermes_tools import ...` 编写 Python 脚本
2. Hermes 生成带有 RPC 函数的 `hermes_tools.py` 存根模块
3. Hermes 打开 Unix 域套接字并启动 RPC 监听器线程
4. 脚本在子进程中运行 — 工具调用通过套接字传回 Hermes
5. 只有脚本的 `print()` 输出返回给 LLM；中间工具结果永远不会进入上下文窗口

```python
# 智能体可以编写这样的脚本：
from hermes_tools import web_search, web_extract

results = web_search("Python 3.13 features", limit=5)
for r in results["data"]["web"]:
    content = web_extract([r["url"]])
    # ... 过滤和处理 ...
print(summary)
```

**沙箱中可用的工具：** `web_search`、`web_extract`、`read_file`、`write_file`、`search_files`、`patch`、`terminal`（仅前台）。

## 智能体何时使用此功能

智能体在以下情况使用 `execute_code`：

- **3+ 个工具调用**，且它们之间有处理逻辑
- 批量数据过滤或条件分支
- 对结果进行循环处理

关键优势：中间工具结果永远不会进入上下文窗口 — 只有最终的 `print()` 输出返回，显著减少令牌使用量。

## 实用示例

### 数据处理管道

```python
from hermes_tools import search_files, read_file
import json

# 查找所有配置文件并提取数据库设置
matches = search_files("database", path=".", file_glob="*.yaml", limit=20)
configs = []
for match in matches.get("matches", []):
    content = read_file(match["path"])
    configs.append({"file": match["path"], "preview": content["content"][:200]})

print(json.dumps(configs, indent=2))
```

### 多步骤网络研究

```python
from hermes_tools import web_search, web_extract
import json

# 一次搜索、提取和总结
results = web_search("Rust async runtime comparison 2025", limit=5)
summaries = []
for r in results["data"]["web"]:
    page = web_extract([r["url"]])
    for p in page.get("results", []):
        if p.get("content"):
            summaries.append({
                "title": r["title"],
                "url": r["url"],
                "excerpt": p["content"][:500]
            })

print(json.dumps(summaries, indent=2))
```

### 批量文件重构

```python
from hermes_tools import search_files, read_file, patch

# 查找所有使用已弃用 API 的 Python 文件并修复它们
matches = search_files("old_api_call", path="src/", file_glob="*.py")
fixed = 0
for match in matches.get("matches", []):
    result = patch(
        path=match["path"],
        old_string="old_api_call(",
        new_string="new_api_call(",
        replace_all=True
    )
    if "error" not in str(result):
        fixed += 1

print(f"Fixed {fixed} files out of {len(matches.get('matches', []))} matches")
```

### 构建和测试管道

```python
from hermes_tools import terminal, read_file
import json

# 运行测试、解析结果并报告
result = terminal("cd /project && python -m pytest --tb=short -q 2>&1", timeout=120)
output = result.get("output", "")

# 解析测试输出
passed = output.count(" passed")
failed = output.count(" failed")
errors = output.count(" error")

report = {
    "passed": passed,
    "failed": failed,
    "errors": errors,
    "exit_code": result.get("exit_code", -1),
    "summary": output[-500:] if len(output) > 500 else output
}

print(json.dumps(report, indent=2))
```

## 资源限制

| 资源 | 限制 | 说明 |
|----------|-------|-------|
| **超时** | 5 分钟（300秒） | 脚本会被 SIGTERM 终止，5秒后发送 SIGKILL |
| **标准输出** | 50 KB | 输出被截断并显示 `[output truncated at 50KB]` 通知 |
| **标准错误** | 10 KB | 非零退出时包含在输出中用于调试 |
| **工具调用** | 每次执行 50 次 | 达到限制时返回错误 |

所有限制可通过 `config.yaml` 配置：

```yaml
# 在 ~/.hermes/config.yaml 中
code_execution:
  timeout: 300       # 每个脚本的最大秒数（默认：300）
  max_tool_calls: 50 # 每次执行的最大工具调用次数（默认：50）
```

## 脚本内工具调用的工作原理

当您的脚本调用 `web_search("query")` 这样的函数时：

1. 调用被序列化为 JSON 并通过 Unix 域套接字发送到父进程
2. 父进程通过标准的 `handle_function_call` 处理程序进行调度
3. 结果通过套接字发送回来
4. 函数返回解析后的结果

这意味着脚本内的工具调用与普通工具调用行为完全相同 — 相同的速率限制、相同的错误处理、相同的功能。唯一的限制是 `terminal()` 只能在前台运行（没有 `background` 或 `pty` 参数）。

## 错误处理

当脚本失败时，智能体会收到结构化的错误信息：

- **非零退出码**：标准错误包含在输出中，以便智能体看到完整的回溯
- **超时**：脚本被终止，智能体看到 `"Script timed out after 300s and was killed."`
- **中断**：如果用户在执行过程中发送新消息，脚本会被终止，智能体看到 `[execution interrupted — user sent a new message]`
- **工具调用限制**：当达到 50 次调用限制时，后续工具调用会返回错误消息

响应始终包含 `status`（success/error/timeout/interrupted）、`output`、`tool_calls_made` 和 `duration_seconds`。

## 安全性

:::danger 安全模型
子进程在**最小环境**中运行。API 密钥、令牌和凭证默认被剥离。脚本通过 RPC 通道专门访问工具 — 除非明确允许，否则无法从环境变量读取密钥。
:::

包含 `KEY`、`TOKEN`、`SECRET`、`PASSWORD`、`CREDENTIAL`、`PASSWD` 或 `AUTH` 名称的环境变量被排除。只有安全的系统变量（`PATH`、`HOME`、`LANG`、`SHELL`、`PYTHONPATH`、`VIRTUAL_ENV` 等）会被传递。

### 技能环境变量传递

当技能在其前置物质中声明 `required_environment_variables` 时，这些变量会在技能加载后**自动传递**给 `execute_code` 和 `terminal` 沙箱。这允许技能使用其声明的 API 密钥，而不会削弱任意代码的安全状态。

对于非技能用例，您可以在 `config.yaml` 中显式允许列出变量：

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANOTHER_TOKEN
```

有关完整详情，请参阅 [安全指南](/docs/user-guide/security#environment-variable-passthrough)。

脚本在执行后会被清理的临时目录中运行。子进程在其自己的进程组中运行，以便在超时时或中断时可以被干净地终止。

## execute_code 与 terminal 的比较

| 使用场景 | execute_code | terminal |
|----------|-------------|----------|
| 步骤间有工具调用的多步骤工作流 | ✅ | ❌ |
| 简单的 shell 命令 | ❌ | ✅ |
| 过滤/处理大型工具输出 | ✅ | ❌ |
| 运行构建或测试套件 | ❌ | ✅ |
| 循环处理搜索结果 | ✅ | ❌ |
| 交互式/后台进程 | ❌ | ✅ |
| 环境中需要 API 密钥 | ⚠️ 仅通过 [传递](/docs/user-guide/security#environment-variable-passthrough) | ✅（大多数会传递） |

**经验法则：** 当您需要以编程方式调用 Hermes 工具并在调用之间添加逻辑时，使用 `execute_code`。使用 `terminal` 运行 shell 命令、构建和进程。

## 平台支持

代码执行需要 Unix 域套接字，仅在** Linux 和 macOS **上可用。它在 Windows 上自动禁用 — 智能体会回退到常规的顺序工具调用。
