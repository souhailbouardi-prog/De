---
sidebar_position: 3
title: "更新与卸载"
description: "如何将 Hermes Agent 更新到最新版本或卸载它"
---

# 更新与卸载

## 更新

使用单个命令更新到最新版本：

```bash
hermes update
```

这会拉取最新代码，更新依赖项，并提示您配置自上次更新以来添加的任何新选项。

:::tip
`hermes update` 会自动检测新的配置选项并提示您添加它们。如果您跳过了该提示，可以手动运行 `hermes config check` 查看缺失的选项，然后运行 `hermes config migrate` 以交互方式添加它们。
:::

### 更新期间会发生什么

当您运行 `hermes update` 时，会发生以下步骤：

1. **Git pull** — 从 `main` 分支拉取最新代码并更新子模块
2. **依赖项安装** — 运行 `uv pip install -e ".[all]"` 以获取新的或更改的依赖项
3. **配置迁移** — 检测自您版本以来添加的新配置选项并提示您设置它们
4. **网关自动重启** — 如果网关服务正在运行（Linux 上的 systemd，macOS 上的 launchd），它会在更新完成后**自动重启**，以便新代码立即生效

预期输出如下：

```
$ hermes update
更新 Hermes Agent...
📥 拉取最新代码...
已经是最新的。  (或：更新 abc1234..def5678)
📦 更新依赖项...
✅ 依赖项已更新
🔍 检查新的配置选项...
✅ 配置是最新的  (或：找到 2 个新选项 — 运行迁移...)
🔄 重启网关服务...
✅ 网关已重启
✅ Hermes Agent 更新成功！
```

### 推荐的更新后验证

`hermes update` 处理主要的更新路径，但快速验证可以确认所有内容都已干净地落地：

1. `git status --short` — if the tree is unexpectedly dirty, inspect before continuing
2. `hermes doctor` — checks config, dependencies, and service health
3. `hermes --version` — confirm the version bumped as expected
4. If you use the gateway: `hermes gateway status`
5. If `doctor` reports npm audit issues: run `npm audit fix` in the flagged directory

:::warning Dirty working tree after update
If `git status --short` shows unexpected changes after `hermes update`, stop and inspect them before continuing. This usually means local modifications were reapplied on top of the updated code, or a dependency step refreshed lockfiles.
:::

### Checking your current version

```bash
hermes version
```

Compare against the latest release at the [GitHub releases page](https://github.com/NousResearch/hermes-agent/releases) or check for available updates:

```bash
hermes update --check
```

### Updating from Messaging Platforms

You can also update directly from Telegram, Discord, Slack, or WhatsApp by sending:

```
/update
```

This pulls the latest code, updates dependencies, and restarts the gateway. The bot will briefly go offline during the restart (typically 5–15 seconds) and then resume.

### Manual Update

If you installed manually (not via the quick installer):

```bash
cd /path/to/hermes-agent
export VIRTUAL_ENV="$(pwd)/venv"

# Pull latest code and submodules
git pull origin main
git submodule update --init --recursive

# Reinstall (picks up new dependencies)
uv pip install -e ".[all]"
uv pip install -e "./tinker-atropos"

# Check for new config options
hermes config check
hermes config migrate   # Interactively add any missing options
```

### Rollback instructions

If an update introduces a problem, you can roll back to a previous version:

```bash
cd /path/to/hermes-agent

# List recent versions
git log --oneline -10

# Roll back to a specific commit
git checkout <commit-hash>
git submodule update --init --recursive
uv pip install -e ".[all]"

# Restart the gateway if running
hermes gateway restart
```

To roll back to a specific release tag:

```bash
git checkout v0.6.0
git submodule update --init --recursive
uv pip install -e ".[all]"
```

:::warning
Rolling back may cause config incompatibilities if new options were added. Run `hermes config check` after rolling back and remove any unrecognized options from `config.yaml` if you encounter errors.
:::

### Note for Nix users

If you installed via Nix flake, updates are managed through the Nix package manager:

```bash
# Update the flake input
nix flake update hermes-agent

# Or rebuild with the latest
nix profile upgrade hermes-agent
```

Nix installations are immutable — rollback is handled by Nix's generation system:

```bash
nix profile rollback
```

See [Nix Setup](./nix-setup.md) for more details.

---

## Uninstalling

```bash
hermes uninstall
```

The uninstaller gives you the option to keep your configuration files (`~/.hermes/`) for a future reinstall.

### Manual Uninstall

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

:::info
If you installed the gateway as a system service, stop and disable it first:
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::