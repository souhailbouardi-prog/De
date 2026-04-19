---
sidebar_position: 4
title: "贡献指南"
description: "如何为 Hermes Agent 做贡献 — 开发设置、代码风格、PR 流程"
---

# 贡献指南

感谢您为 Hermes Agent 做贡献！本指南涵盖设置开发环境、理解代码库以及让您的 PR 合并。

## 贡献优先级

我们按以下顺序重视贡献：

1. **错误修复** — 崩溃、不正确行为、数据丢失
2. **跨平台兼容性** — macOS、不同 Linux 发行版、WSL2
3. **安全加固** — shell 注入、提示注入、路径遍历
4. **性能和健壮性** — 重试逻辑、错误处理、优雅降级
5. **新技能** — 广泛有用的技能（参见[创建技能](creating-skills.md)）
6. **新工具** — 很少需要；大多数功能应该是技能
7. **文档** — 修复、澄清、新示例

## 常见贡献路径

- 构建新工具？从[添加工具](./adding-tools.md)开始
- 构建新技能？从[创建技能](./creating-skills.md)开始
- 构建新推理提供商？从[添加提供商](./adding-providers.md)开始

## 开发设置

### 先决条件

| 要求 | 说明 |
|-------------|-------|
| **Git** | 支持 `--recurse-submodules` |
| **Python 3.11+** | 如果缺少，uv 会安装它 |
| **uv** | 快速 Python 包管理器（[安装](https://docs.astral.sh/uv/)） |
| **Node.js 18+** | 可选 — 浏览器工具和 WhatsApp 桥接需要 |

### 克隆和安装

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 使用 Python 3.11 创建 venv
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# 安装所有额外功能（消息传递、cron、CLI 菜单、开发工具）
uv pip install -e ".[all,dev]"
uv pip install -e "./tinker-atropos"

# Optional: browser tools
npm install
```

### Configure for Development

```bash
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env

# Add at minimum an LLM provider key:
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env
```

### Run

```bash
# Symlink for global access
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# Verify
hermes doctor
hermes chat -q "Hello"
```

### Run Tests

```bash
pytest tests/ -v
```

## Code Style

- **PEP 8** with practical exceptions (no strict line length enforcement)
- **Comments**: Only when explaining non-obvious intent, trade-offs, or API quirks
- **Error handling**: Catch specific exceptions. Use `logger.warning()`/`logger.error()` with `exc_info=True` for unexpected errors
- **Cross-platform**: Never assume Unix (see below)
- **Profile-safe paths**: Never hardcode `~/.hermes` — use `get_hermes_home()` from `hermes_constants` for code paths and `display_hermes_home()` for user-facing messages. See [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md#profiles-multi-instance-support) for full rules.

## Cross-Platform Compatibility

Hermes officially supports Linux, macOS, and WSL2. Native Windows is **not supported**, but the codebase includes some defensive coding patterns to avoid hard crashes in edge cases. Key rules:

### 1. `termios` and `fcntl` are Unix-only

Always catch both `ImportError` and `NotImplementedError`:

```python
try:
    from simple_term_menu import TerminalMenu
    menu = TerminalMenu(options)
    idx = menu.show()
except (ImportError, NotImplementedError):
    # Fallback: numbered menu
    for i, opt in enumerate(options):
        print(f"  {i+1}. {opt}")
    idx = int(input("Choice: ")) - 1
```

### 2. File encoding

Some environments may save `.env` files in non-UTF-8 encodings:

```python
try:
    load_dotenv(env_path)
except UnicodeDecodeError:
    load_dotenv(env_path, encoding="latin-1")
```

### 3. Process management

`os.setsid()`, `os.killpg()`, and signal handling differ across platforms:

```python
import platform
if platform.system() != "Windows":
    kwargs["preexec_fn"] = os.setsid
```

### 4. Path separators

Use `pathlib.Path` instead of string concatenation with `/`.

## Security Considerations

Hermes has terminal access. Security matters.

### Existing Protections

| Layer | Implementation |
|-------|---------------|
| **Sudo password piping** | Uses `shlex.quote()` to prevent shell injection |
| **Dangerous command detection** | Regex patterns in `tools/approval.py` with user approval flow |
| **Cron prompt injection** | Scanner blocks instruction-override patterns |
| **Write deny list** | Protected paths resolved via `os.path.realpath()` to prevent symlink bypass |
| **Skills guard** | Security scanner for hub-installed skills |
| **Code execution sandbox** | Child process runs with API keys stripped |
| **Container hardening** | Docker: all capabilities dropped, no privilege escalation, PID limits |

### Contributing Security-Sensitive Code

- Always use `shlex.quote()` when interpolating user input into shell commands
- Resolve symlinks with `os.path.realpath()` before access control checks
- Don't log secrets
- Catch broad exceptions around tool execution
- Test on all platforms if your change touches file paths or processes

## Pull Request Process

### Branch Naming

```
fix/description        # Bug fixes
feat/description       # New features
docs/description       # Documentation
test/description       # Tests
refactor/description   # Code restructuring
```

### Before Submitting

1. **Run tests**: `pytest tests/ -v`
2. **Test manually**: Run `hermes` and exercise the code path you changed
3. **Check cross-platform impact**: Consider macOS and different Linux distros
4. **Keep PRs focused**: One logical change per PR

### PR Description

Include:
- **What** changed and **why**
- **How to test** it
- **What platforms** you tested on
- Reference any related issues

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Type | Use for |
|------|---------|
| `fix` | Bug fixes |
| `feat` | New features |
| `docs` | Documentation |
| `test` | Tests |
| `refactor` | Code restructuring |
| `chore` | Build, CI, dependency updates |

Scopes: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `whatsapp`, `security`

Examples:
```
fix(cli): prevent crash in save_config_value when model is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
```

## Reporting Issues

- Use [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)
- Include: OS, Python version, Hermes version (`hermes version`), full error traceback
- Include steps to reproduce
- Check existing issues before creating duplicates
- For security vulnerabilities, please report privately

## Community

- **Discord**: [discord.gg/NousResearch](https://discord.gg/NousResearch)
- **GitHub Discussions**: For design proposals and architecture discussions
- **Skills Hub**: Upload specialized skills and share with the community

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE).