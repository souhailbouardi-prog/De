---
sidebar_position: 8
title: "在 Hermes 中使用语音模式"
description: "在 CLI、Telegram、Discord 和 Discord 语音频道中设置和使用 Hermes 语音模式的实用指南"
---

# 在 Hermes 中使用语音模式

本指南是 [语音模式功能参考](/docs/user-guide/features/voice-mode) 的实用配套指南。

如果功能页面解释了语音模式可以做什么，本指南将展示如何实际使用它。

## 语音模式的适用场景

语音模式在以下情况下特别有用：
- 您想要免提 CLI 工作流
- 您想要在 Telegram 或 Discord 中获得语音回复
- 您想要 Hermes 坐在 Discord 语音频道中进行实时对话
- 您想要在四处走动而不是打字时快速捕获想法、调试或来回交流

## 选择您的语音模式设置

Hermes 中实际上有三种不同的语音体验。

| 模式 | 最适合 | 平台 |
|---|---|---|
| 交互式麦克风循环 | 编码或研究时的个人免提使用 | CLI |
| 聊天中的语音回复 | 与正常消息一起的语音响应 | Telegram、Discord |
| 实时语音频道机器人 | VC 中的群组或个人实时对话 | Discord 语音频道 |

一个好的路径是：
1. 首先让文本工作
2. 其次启用语音回复
3. 如果您想要完整体验，最后移至 Discord 语音频道

## 步骤 1：确保正常的 Hermes 首先工作

在接触语音模式之前，验证：
- Hermes 启动
- 您的提供商已配置
- 代理可以正常回答文本提示

```bash
hermes
```

问一些简单的问题：

```text
你有哪些工具可用？
```

如果这还不稳定，先修复文本模式。

## 步骤 2：安装正确的附加组件

### CLI 麦克风 + 播放

```bash
pip install "hermes-agent[voice]"
```

### 消息平台

```bash
pip install "hermes-agent[messaging]"
```

### 高级 ElevenLabs TTS

```bash
pip install "hermes-agent[tts-premium]"
```

### 本地 NeuTTS（可选）

```bash
python -m pip install -U neutts[all]
```

### 所有组件

```bash
pip install "hermes-agent[all]"
```

## 步骤 3：安装系统依赖

### macOS

```bash
brew install portaudio ffmpeg opus
brew install espeak-ng
```

### Ubuntu / Debian

```bash
sudo apt install portaudio19-dev ffmpeg libopus0
sudo apt install espeak-ng
```

这些的重要性：
- `portaudio` → CLI 语音模式的麦克风输入/播放
- `ffmpeg` → TTS 和消息传递的音频转换
- `opus` → Discord 语音编解码器支持
- `espeak-ng` → NeuTTS 的音素化后端

## 步骤 4：选择 STT 和 TTS 提供商

Hermes 支持本地和云语音堆栈。

### 最简单/最便宜的设置

使用本地 STT 和免费的 Edge TTS：
- STT 提供商：`local`
- TTS 提供商：`edge`

这通常是最好的起点。

### 环境文件示例

添加到 `~/.hermes/.env`：

```bash
# 云 STT 选项（本地不需要密钥）
GROQ_API_KEY=***
VOICE_TOOLS_OPENAI_KEY=***

# 高级 TTS（可选）
ELEVENLABS_API_KEY=***
```

### 提供商推荐

#### 语音转文本

- `local` → 隐私和零成本使用的最佳默认选择
- `groq` → 非常快的云转录
- `openai` → 良好的付费备选

#### 文本转语音

- `edge` → 免费且对大多数用户来说足够好
- `neutts` → 免费本地/设备上 TTS
- `elevenlabs` → 最佳质量
- `openai` → 良好的中间选择
- `mistral` → 多语言，原生 Opus

### 如果您使用 `hermes setup`

如果您在设置向导中选择 NeuTTS，Hermes 会检查 `neutts` 是否已安装。如果缺少，向导会告诉您 NeuTTS 需要 Python 包 `neutts` 和系统包 `espeak-ng`，提供为您安装它们，使用平台包管理器安装 `espeak-ng`，然后运行：

```bash
python -m pip install -U neutts[all]
```

如果您跳过该安装或安装失败，向导会回退到 Edge TTS。

## 步骤 5：推荐配置

```yaml
voice:
  record_key: "ctrl+b"
  max_recording_seconds: 120
  auto_tts: false
  silence_threshold: 200
  silence_duration: 3.0

stt:
  provider: "local"
  local:
    model: "base"

tts:
  provider: "edge"
  edge:
    voice: "en-US-AriaNeural"
```

这对大多数人来说是一个很好的保守默认值。

如果您想使用本地 TTS，请将 `tts` 块切换为：

```yaml
tts:
  provider: "neutts"
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

## 使用场景 1：CLI 语音模式

## 开启它

启动 Hermes：

```bash
hermes
```

在 CLI 内部：

```text
/voice on
```

### 录制流程

默认键：
- `Ctrl+B`

工作流：
1. 按 `Ctrl+B`
2. 说话
3. 等待静音检测自动停止录制
4. Hermes 转录并响应
5. 如果 TTS 开启，它会说出答案
6. 循环可以自动重启以连续使用

### 有用的命令

```text
/voice
/voice on
/voice off
/voice tts
/voice status
```

### 良好的 CLI 工作流

#### 快速调试

说：

```text
I keep getting a docker permission error. Help me debug it.
```

然后免提继续：
- "Read the last error again"
- "Explain the root cause in simpler terms"
- "Now give me the exact fix"

#### 研究 / 头脑风暴

非常适合：
- 边思考边四处走动
- 口述半成型的想法
- 要求 Hermes 实时组织您的想法

#### 无障碍 / 低打字会话

如果打字不方便，语音模式是保持完整 Hermes 循环的最快方式之一。

## 调整 CLI 行为

### 静音阈值

如果 Hermes 开始/停止过于激进，请调整：

```yaml
voice:
  silence_threshold: 250
```

更高的阈值 = 更不敏感。

### 静音持续时间

如果您在句子之间暂停很多，请增加：

```yaml
voice:
  silence_duration: 4.0
```

### 录制键

如果 `Ctrl+B` 与您的终端或 tmux 习惯冲突：

```yaml
voice:
  record_key: "ctrl+space"
```

## 使用场景 2：Telegram 或 Discord 中的语音回复

此模式比完整的语音频道更简单。

Hermes 保持正常的聊天机器人状态，但可以说出回复。

### 启动网关

```bash
hermes gateway
```

### 开启语音回复

在 Telegram 或 Discord 中：

```text
/voice on
```

或

```text
/voice tts
```

### 模式

| 模式 | 含义 |
|---|---|
| `off` | 仅文本 |
| `voice_only` | 仅当用户发送语音时才说话 |
| `all` | 说出每个回复 |

### 何时使用哪种模式

- 如果您只希望对语音消息的回复使用语音，请使用 `/voice on`
- 如果您想要一个全天候的语音助手，请使用 `/voice tts`

### 良好的消息传递工作流

#### 手机上的 Telegram 助手

在以下情况使用：
- 您远离机器
- 您想要发送语音笔记并获得快速语音回复
- 您希望 Hermes 像便携式研究或运维助手一样工作

#### 带有语音输出的 Discord DMs

当您想要私人互动而不需要服务器频道提及行为时很有用。

## 使用场景 3：Discord 语音频道

这是最先进的模式。

Hermes 加入 Discord VC，监听用户语音，转录，运行正常的代理管道，并在频道中说出回复。

## 所需的 Discord 权限

除了正常的文本机器人设置外，确保机器人具有：
- Connect
- Speak
- 最好是 Use Voice Activity

还需要在开发者门户中启用特权意图：
- Presence Intent
- Server Members Intent
- Message Content Intent

## 加入和离开

在机器人所在的 Discord 文本频道中：

```text
/voice join
/voice leave
/voice status
```

### 加入后会发生什么

- 用户在 VC 中说话
- Hermes 检测语音边界
- 转录会发布在相关的文本频道中
- Hermes 以文本和音频响应
- 文本频道是发出 `/voice join` 的频道

### Discord VC 使用的最佳实践

- 保持 `DISCORD_ALLOWED_USERS` 严格
- 首先使用专用的机器人/测试频道
- 在尝试 VC 模式之前，验证 STT 和 TTS 在普通文本聊天语音模式下工作

## 语音质量建议

### 最佳质量设置

- STT：本地 `large-v3` 或 Groq `whisper-large-v3`
- TTS：ElevenLabs

### 最佳速度/便利性设置

- STT：本地 `base` 或 Groq
- TTS：Edge

### 最佳零成本设置

- STT：本地
- TTS：Edge

## 常见失败模式

### "未找到音频设备"

安装 `portaudio`。

### "机器人加入但听不到任何声音"

检查：
- 您的 Discord 用户 ID 在 `DISCORD_ALLOWED_USERS` 中
- 您没有静音
- 特权意图已启用
- 机器人具有 Connect/Speak 权限

### "它转录但不说话"

检查：
- TTS 提供商配置
- ElevenLabs 或 OpenAI 的 API 密钥/配额
- Edge 转换路径的 `ffmpeg` 安装

### "Whisper 输出垃圾"

尝试：
- 更安静的环境
- 更高的 `silence_threshold`
- 不同的 STT 提供商/模型
- 更短、更清晰的话语

### "它在 DMs 中工作但在服务器频道中不工作"

这通常是提及政策。

默认情况下，机器人在 Discord 服务器文本频道中需要 `@mention`，除非另有配置。

## 建议的第一周设置

如果您想要最短的成功路径：

1. 让文本 Hermes 工作
2. 安装 `hermes-agent[voice]`
3. 使用带有本地 STT + Edge TTS 的 CLI 语音模式
4. 然后在 Telegram 或 Discord 中启用 `/voice on`
5. 只有在那之后，尝试 Discord VC 模式

这种进展保持了较小的调试面。

## 接下来阅读哪里

- [语音模式功能参考](/docs/user-guide/features/voice-mode)
- [消息网关](/docs/user-guide/messaging)
- [Discord 设置](/docs/user-guide/messaging/discord)
- [Telegram 设置](/docs/user-guide/messaging/telegram)
- [配置](/docs/user-guide/configuration)