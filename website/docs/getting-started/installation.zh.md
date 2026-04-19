---
sidebar_position: 2
title: "安装"
description: "在Linux、macOS、WSL2或通过Termux在Android上安装Hermes Agent"
---

# 安装

使用单行安装程序在两分钟内启动并运行Hermes Agent，或按照手动步骤获得完全控制。

## 快速安装

### Linux / macOS / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Android / Termux

Hermes现在也提供了Termux感知的安装路径：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

安装程序会自动检测Termux并切换到经过测试的Android流程：
- 使用Termux `pkg`安装系统依赖（`git`、`python`、`nodejs`、`ripgrep`、`ffmpeg`、构建工具）
- 使用`python -m venv`创建虚拟环境
- 自动导出`ANDROID_API_LEVEL`用于Android wheel构建
- 使用`pip`安装精选的`.[termux]`额外包
- 默认跳过未经测试的浏览器/WhatsApp引导

如果您想要完全明确的路径，请按照专门的[Termux指南](./termux.zh.md)操作。

:::warning Windows
**不支持**原生Windows。请安装[WSL2](https://learn.microsoft.com/zh-cn/windows/wsl/install)并从那里运行Hermes Agent。上述安装命令在WSL2内有效。
:::

### 安装程序的功能

安装程序会自动处理所有内容 — 所有依赖项（Python、Node.js、ripgrep、ffmpeg）、仓库克隆、虚拟环境、全局`hermes`命令设置以及LLM提供商配置。完成后，您就可以开始聊天了。

### 安装后

重新加载您的shell并开始聊天：

```bash
source ~/.bashrc   # 或: source ~/.zshrc
hermes             # 开始聊天！
```

稍后要重新配置个别设置，请使用专用命令：

```bash
hermes model          # 选择您的LLM提供商和模型
hermes tools          # 配置启用哪些工具
hermes gateway setup  # 设置消息平台
hermes config set     # 设置个别配置值
hermes setup          # 或运行完整设置向导一次性配置所有内容
```

---

## 先决条件

唯一的先决条件是**Git**。安装程序会自动处理其他所有内容：

- **uv**（快速Python包管理器）
- **Python 3.11**（通过uv，无需sudo）
- **Node.js v22**（用于浏览器自动化和WhatsApp桥接）
- **ripgrep**（快速文件搜索）
- **ffmpeg**（用于TTS的音频格式转换）

:::info
您**不需要**手动安装Python、Node.js、ripgrep或ffmpeg。安装程序会检测缺失的内容并为您安装。只需确保`git`可用（`git --version`）。
:::

:::tip Nix用户
如果您使用Nix（在NixOS、macOS或Linux上），有一个专用的设置路径，包括Nix flake、声明式NixOS模块和可选的容器模式。请参阅**[Nix & NixOS设置](./nix-setup.zh.md)**指南。
:::

---

## 手动安装

如果您更喜欢完全控制安装过程，请按照以下步骤操作。

### 步骤1：克隆仓库

使用`--recurse-submodules`克隆以拉取所需的子模块：

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

如果您已经克隆但没有使用`--recurse-submodules`：
```bash
git submodule update --init --recursive
```

### 步骤2：安装uv并创建虚拟环境

```bash
# 安装uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建使用Python 3.11的venv（uv会在不存在时下载它 — 无需sudo）
uv venv venv --python 3.11
```

:::tip
使用`hermes`**不需要**激活venv。入口点有一个硬编码的shebang指向venv Python，因此一旦创建符号链接，它就可以全局工作。
:::

### 步骤3：安装Python依赖项

```bash
# 告诉uv要安装到哪个venv
export VIRTUAL_ENV="$(pwd)/venv"

# 安装所有额外包
uv pip install -e ".[all]"
```

如果您只想要核心代理（无Telegram/Discord/cron支持）：
```bash
uv pip install -e "."
```

<details>
<summary><strong>可选额外包 breakdown</strong></summary>

| 额外包 | 增加内容 | 安装命令 |
|-------|-------------|-----------------|
| `all` | 以下所有内容 | `uv pip install -e ".[all]"` |
| `messaging` | Telegram、Discord和Slack网关 | `uv pip install -e ".[messaging]"` |
| `cron` | 用于计划任务的Cron表达式解析 | `uv pip install -e ".[cron]"` |
| `cli` | 设置向导的终端菜单UI | `uv pip install -e ".[cli]"` |
| `modal` | Modal云执行后端 | `uv pip install -e ".[modal]"` |
| `tts-premium` | ElevenLabs premium voices | `uv pip install -e ".[tts-premium]"` |
| `voice` | CLI麦克风输入 + 音频播放 | `uv pip install -e ".[voice]"` |
| `pty` | PTY终端支持 | `uv pip install -e ".[pty]"` |
| `termux` | 经过测试的Android / Termux捆绑包（`cron`、`cli`、`pty`、`mcp`、`honcho`、`acp`） | `python -m pip install -e ".[termux]" -c constraints-termux.txt` |
| `honcho` | AI原生内存（Honcho集成） | `uv pip install -e ".[honcho]"` |
| `mcp` | 模型上下文协议支持 | `uv pip install -e ".[mcp]"` |
| `homeassistant` | Home Assistant集成 | `uv pip install -e ".[homeassistant]"` |
| `acp` | ACP编辑器集成支持 | `uv pip install -e ".[acp]"` |
| `slack` | Slack消息传递 | `uv pip install -e ".[slack]"` |
| `dev` | pytest和测试工具 | `uv pip install -e ".[dev]"` |

您可以组合额外包：`uv pip install -e ".[messaging,cron]"`

:::tip Termux用户
`.[all]`目前在Android上不可用，因为`voice`额外包会拉取`faster-whisper`，后者依赖于未为Android发布的`ctranslate2` wheels。使用`.[termux]`作为经过测试的移动安装路径，然后仅在需要时添加个别额外包。
:::

</details>

### 步骤4：安装可选子模块（如果需要）

```bash
# RL训练后端（可选）
uv pip install -e "./tinker-atropos"
```

两者都是可选的 — 如果您跳过它们，相应的工具集将不可用。

### 步骤5：安装Node.js依赖项（可选）

仅在需要**浏览器自动化**（Browserbase驱动）和**WhatsApp桥接**时需要：

```bash
npm install
```

### 步骤6：创建配置目录

```bash
# 创建目录结构
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache,whatsapp/session}

# 复制示例配置文件
cp cli-config.yaml.example ~/.hermes/config.yaml

# 创建一个空的.env文件用于API密钥
touch ~/.hermes/.env
```

### 步骤7：添加您的API密钥

打开`~/.hermes/.env`并至少添加一个LLM提供商密钥：

```bash
# 必需 — 至少一个LLM提供商：
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 可选 — 启用其他工具：
FIRECRAWL_API_KEY=fc-your-key          # 网络搜索和抓取（或自托管，见文档）
FAL_KEY=your-fal-key                   # 图像生成（FLUX）
```

或通过CLI设置：
```bash
hermes config set OPENROUTER_API_KEY sk-or-v1-your-key-here
```

### 步骤8：将`hermes`添加到您的PATH

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes
```

如果`~/.local/bin`不在您的PATH中，请将其添加到您的shell配置：

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# Fish
fish_add_path $HOME/.local/bin
```

### 步骤9：配置您的提供商

```bash
hermes model       # 选择您的LLM提供商和模型
```

### 步骤10：验证安装

```bash
hermes version    # 检查命令是否可用
hermes doctor     # 运行诊断以验证一切正常工作
hermes status     # 检查您的配置
hermes chat -q "Hello! What tools do you have available?"
```

---

## 快速参考：手动安装（浓缩版）

对于只想要命令的人：

```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆并进入
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 创建使用Python 3.11的venv
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# 安装所有内容
uv pip install -e ".[all]"
uv pip install -e "./tinker-atropos"
npm install  # 可选，用于浏览器工具和WhatsApp

# 配置
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache,whatsapp/session}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env

# 使hermes全局可用
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# 验证
hermes doctor
hermes
```

---

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| `hermes: command not found` | 重新加载您的shell（`source ~/.bashrc`）或检查PATH |
| `API key not set` | 运行`hermes model`配置您的提供商，或`hermes config set OPENROUTER_API_KEY your_key` |
| 更新后缺少配置 | 运行`hermes config check`然后`hermes config migrate` |

要获取更多诊断信息，请运行`hermes doctor` — 它会告诉您确切缺少什么以及如何修复它。