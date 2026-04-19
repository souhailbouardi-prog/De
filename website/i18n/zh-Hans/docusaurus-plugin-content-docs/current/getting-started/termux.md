---
sidebar_position: 3
title: "Android / Termux"
description: "使用 Termux 直接在 Android 手机上运行 Hermes Agent"
---

# 在 Android 上使用 Termux 运行 Hermes

这是通过 [Termux](https://termux.dev/) 直接在 Android 手机上运行 Hermes Agent 的经过测试的路径。

它为您提供手机上可用的本地 CLI，以及目前已知可以在 Android 上干净安装的核心额外功能。

## 测试路径支持哪些功能？

经过测试的 Termux 捆绑包安装：
- Hermes CLI
- cron 支持
- PTY/后台终端支持
- MCP 支持
- Honcho 记忆支持
- ACP 支持

具体来说，它映射到：

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

## 目前测试路径还不包括哪些功能？

一些功能仍然需要桌面/服务器风格的依赖项，这些依赖项尚未为 Android 发布，或者尚未在手机上验证：

- `.[all]` 目前在 Android 上不受支持
- `voice` 额外功能被 `faster-whisper -> ctranslate2` 阻止，而 `ctranslate2` 不发布 Android 轮子
- Termux 安装程序中跳过了自动浏览器 / Playwright 引导
- Termux 内部不支持基于 Docker 的终端隔离

这并不妨碍 Hermes 作为手机原生 CLI 智能体良好工作 — 只是意味着推荐的移动安装有意比桌面/服务器安装更窄。

---

## 选项 1：一行安装程序

Hermes 现在提供了一个支持 Termux 的安装程序路径：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

在 Termux 上，安装程序自动：
- uses `pkg` for system packages
- creates the venv with `python -m venv`
- installs `.[termux]` with `pip`
- links `hermes` into `$PREFIX/bin` so it stays on your Termux PATH
- skips the untested browser / WhatsApp bootstrap

If you want the explicit commands or need to debug a failed install, use the manual path below.

---

## Option 2: Manual install (fully explicit)

### 1. Update Termux and install system packages

```bash
pkg update
pkg install -y git python clang rust make pkg-config libffi openssl nodejs ripgrep ffmpeg
```

Why these packages?
- `python` — runtime + venv support
- `git` — clone/update the repo
- `clang`, `rust`, `make`, `pkg-config`, `libffi`, `openssl` — needed to build a few Python dependencies on Android
- `nodejs` — optional Node runtime for experiments beyond the tested core path
- `ripgrep` — fast file search
- `ffmpeg` — media / TTS conversions

### 2. Clone Hermes

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

### 3. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
```

`ANDROID_API_LEVEL` is important for Rust / maturin-based packages such as `jiter`.

### 4. Install the tested Termux bundle

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

If you only want the minimal core agent, this also works:

```bash
python -m pip install -e '.' -c constraints-termux.txt
```

### 5. Put `hermes` on your Termux PATH

```bash
ln -sf "$PWD/venv/bin/hermes" "$PREFIX/bin/hermes"
```

`$PREFIX/bin` is already on PATH in Termux, so this makes the `hermes` command persist across new shells without re-activating the venv every time.

### 6. Verify the install

```bash
hermes version
hermes doctor
```

### 7. Start Hermes

```bash
hermes
```

---

## Recommended follow-up setup

### Configure a model

```bash
hermes model
```

Or set keys directly in `~/.hermes/.env`.

### Re-run the full interactive setup wizard later

```bash
hermes setup
```

### Install optional Node dependencies manually

The tested Termux path skips Node/browser bootstrap on purpose. If you want to experiment with browser tooling later:

```bash
pkg install nodejs-lts
npm install
```

The browser tool automatically includes Termux directories (`/data/data/com.termux/files/usr/bin`) in its PATH search, so `agent-browser` and `npx` are discovered without any extra PATH configuration.

Treat browser / WhatsApp tooling on Android as experimental until documented otherwise.

---

## Troubleshooting

### `No solution found` when installing `.[all]`

Use the tested Termux bundle instead:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

The blocker is currently the `voice` extra:
- `voice` pulls `faster-whisper`
- `faster-whisper` depends on `ctranslate2`
- `ctranslate2` does not publish Android wheels

### `uv pip install` fails on Android

Use the Termux path with the stdlib venv + `pip` instead:

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `jiter` / `maturin` complains about `ANDROID_API_LEVEL`

Set the API level explicitly before installing:

```bash
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `hermes doctor` says ripgrep or Node is missing

Install them with Termux packages:

```bash
pkg install ripgrep nodejs
```

### Build failures while installing Python packages

Make sure the build toolchain is installed:

```bash
pkg install clang rust make pkg-config libffi openssl
```

Then retry:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

---

## Known limitations on phones

- Docker backend is unavailable
- local voice transcription via `faster-whisper` is unavailable in the tested path
- browser automation setup is intentionally skipped by the installer
- some optional extras may work, but only `.[termux]` is currently documented as the tested Android bundle

If you hit a new Android-specific issue, please open a GitHub issue with:
- your Android version
- `termux-info`
- `python --version`
- `hermes doctor`
- the exact install command and full error output