---
sidebar_position: 9
title: "语音与 TTS"
description: "跨所有平台的文本到语音和语音消息转录"
---

# 语音与 TTS

Hermes Agent 支持跨所有消息平台的文本到语音输出和语音消息转录。

:::tip Nous 订阅者
如果您有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，可以通过**[工具网关](tool-gateway.md)**使用 OpenAI TTS，无需单独的 OpenAI API 密钥。运行 `hermes model` 或 `hermes tools` 启用它。
:::

## 文本到语音

使用七个提供程序将文本转换为语音：

| 提供程序 | 质量 | 成本 | API 密钥 |
|----------|---------|------|---------|
| **Edge TTS** (默认) | 良好 | 免费 | 无需 |
| **ElevenLabs** | 优秀 | 付费 | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | 良好 | 付费 | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax TTS** | 优秀 | 付费 | `MINIMAX_API_KEY` |
| **Mistral (Voxtral TTS)** | 优秀 | 付费 | `MISTRAL_API_KEY` |
| **Google Gemini TTS** | 优秀 | 免费层级 | `GEMINI_API_KEY` |
| **xAI TTS** | 优秀 | 付费 | `XAI_API_KEY` |
| **NeuTTS** | 良好 | 免费 | 无需 |

### 平台交付

| 平台 | 交付 | 格式 |
|----------|----------|--------|
| Telegram | 语音气泡（内联播放） | Opus `.ogg` |
| Discord | 语音气泡（Opus/OGG），回退到文件附件 | Opus/MP3 |
| WhatsApp | 音频文件附件 | MP3 |
| CLI | 保存到 `~/.hermes/audio_cache/` | MP3 |

### 配置

```yaml
# 在 ~/.hermes/config.yaml 中
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "gemini" | "xai" | "neutts"
  speed: 1.0                    # 全局速度乘数（提供程序特定设置会覆盖此）
  edge:
    voice: "en-US-AriaNeural"   # 322 个语音，74 种语言
    speed: 1.0                  # 转换为速率百分比（+/-%）
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    base_url: "https://api.openai.com/v1"  # 覆盖 OpenAI 兼容的 TTS 端点
    speed: 1.0                  # 0.25 - 4.0
  minimax:
    model: "speech-2.8-hd"     # speech-2.8-hd（默认）, speech-2.8-turbo
    voice_id: "English_Graceful_Lady"  # 请参阅 https://platform.minimax.io/faq/system-voice-id
    speed: 1                    # 0.5 - 2.0
    vol: 1                      # 0 - 10
    pitch: 0                    # -12 - 12
  mistral:
    model: "voxtral-mini-tts-2603"
    voice_id: "c69964a6-ab8b-4f8a-9465-ec0925096ec8"  # Paul - Neutral（默认）
  gemini:
    model: "gemini-2.5-flash-preview-tts"  # 或 gemini-2.5-pro-preview-tts
    voice: "Kore"               # 30 个预构建语音：Zephyr、Puck、Kore、Enceladus、Gacrux 等。
  xai:
    voice_id: "eve"             # xAI TTS 语音（请参阅 https://docs.x.ai/docs/api-reference#tts）
    language: "en"              # ISO 639-1 代码
    sample_rate: 24000          # 22050 / 24000（默认） / 44100 / 48000
    bit_rate: 128000            # MP3 比特率；仅在 codec=mp3 时适用
    # base_url: "https://api.x.ai/v1"   # 通过 XAI_BASE_URL 环境变量覆盖
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

**速度控制**：全局 `tts.speed` 值默认适用于所有提供程序。每个提供程序可以用自己的 `speed` 设置覆盖它（例如，`tts.openai.speed: 1.5`）。提供程序特定的速度优先于全局值。默认值为 `1.0`（正常速度）。

### Telegram 语音气泡和 ffmpeg

Telegram 语音气泡需要 Opus/OGG 音频格式：

- **OpenAI、ElevenLabs 和 Mistral** 原生生成 Opus — 无需额外设置
- **Edge TTS**（默认）输出 MP3，需要 **ffmpeg** 来转换：
- **MiniMax TTS** 输出 MP3，需要 **ffmpeg** 来为 Telegram 语音气泡转换
- **Google Gemini TTS** 输出原始 PCM，使用 **ffmpeg** 直接为 Telegram 语音气泡编码 Opus
- **xAI TTS** 输出 MP3，需要 **ffmpeg** 来为 Telegram 语音气泡转换
- **NeuTTS** 输出 WAV，也需要 **ffmpeg** 来为 Telegram 语音气泡转换

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

没有 ffmpeg 时，Edge TTS、MiniMax TTS 和 NeuTTS 音频会作为常规音频文件发送（可播放，但显示为矩形播放器而不是语音气泡）。

:::tip
如果您想要语音气泡而不安装 ffmpeg，请切换到 OpenAI、ElevenLabs 或 Mistral 提供程序。
:::

## 语音消息转录（STT）

在 Telegram、Discord、WhatsApp、Slack 或 Signal 上发送的语音消息会自动转录并作为文本注入到对话中。代理将转录视为正常文本。

| 提供程序 | 质量 | 成本 | API 密钥 |
|----------|---------|------|---------| 
| **Local Whisper** (默认) | 良好 | 免费 | 无需 |
| **Groq Whisper API** | 良好–最佳 | 免费层级 | `GROQ_API_KEY` |
| **OpenAI Whisper API** | 良好–最佳 | 付费 | `VOICE_TOOLS_OPENAI_KEY` 或 `OPENAI_API_KEY` |

:::info 零配置
当 `faster-whisper` 安装时，本地转录开箱即用。如果不可用，Hermes 还可以从常见安装位置（如 `/opt/homebrew/bin`）使用本地 `whisper` CLI，或通过 `HERMES_LOCAL_STT_COMMAND` 使用自定义命令。
:::

### 配置

```yaml
# 在 ~/.hermes/config.yaml 中
stt:
  provider: "local"           # "local" | "groq" | "openai" | "mistral"
  local:
    model: "base"             # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"        # whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe
  mistral:
    model: "voxtral-mini-latest"  # voxtral-mini-latest, voxtral-mini-2602
```

### 提供程序详细信息

**本地 (faster-whisper)** — 通过 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 本地运行 Whisper。默认使用 CPU，如果可用则使用 GPU。模型大小：

| 模型 | 大小 | 速度 | 质量 |
|-------|------|-------|---------|
| `tiny` | ~75 MB | 最快 | 基本 |
| `base` | ~150 MB | 快速 | 良好（默认） |
| `small` | ~500 MB | 中等 | 更好 |
| `medium` | ~1.5 GB | 更慢 | 很好 |
| `large-v3` | ~3 GB | 最慢 | 最佳 |

**Groq API** — 需要 `GROQ_API_KEY`。当您想要免费的托管 STT 选项时，良好的云回退。

**OpenAI API** — 首先接受 `VOICE_TOOLS_OPENAI_KEY`，然后回退到 `OPENAI_API_KEY`。支持 `whisper-1`、`gpt-4o-mini-transcribe` 和 `gpt-4o-transcribe`。

**Mistral API (Voxtral Transcribe)** — 需要 `MISTRAL_API_KEY`。使用 Mistral 的 [Voxtral Transcribe](https://docs.mistral.ai/capabilities/audio/speech_to_text/) 模型。支持 13 种语言、说话人 diarization 和单词级时间戳。使用 `pip install hermes-agent[mistral]` 安装。

**自定义本地 CLI 回退** — 如果您希望 Hermes 直接调用本地转录命令，请设置 `HERMES_LOCAL_STT_COMMAND`。命令模板支持 `{input_path}`、`{output_dir}`、`{language}` 和 `{model}` 占位符。

### 回退行为

如果您配置的提供程序不可用，Hermes 会自动回退：
- **本地 faster-whisper 不可用** → 在云提供程序之前尝试本地 `whisper` CLI 或 `HERMES_LOCAL_STT_COMMAND`
- **未设置 Groq 密钥** → 回退到本地转录，然后是 OpenAI
- **未设置 OpenAI 密钥** → 回退到本地转录，然后是 Groq
- **未设置 Mistral 密钥/SDK** → 在自动检测中跳过；回退到下一个可用提供程序
- **没有可用的** → 语音消息通过，并带有给用户的准确说明
