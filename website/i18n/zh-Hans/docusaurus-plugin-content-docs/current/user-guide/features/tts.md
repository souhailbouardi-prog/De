---
sidebar_position: 9
title: "语音与 TTS"
description: "跨所有平台的文本转语音和语音消息转录"
---

# 语音与 TTS

Hermes Agent 在所有消息平台上支持文本转语音输出和语音消息转录。

## 文本转语音

使用六个提供者将文本转换为语音：

| 提供者 | 质量 | 成本 | API 密钥 |
|----------|---------|------|---------|
| **Edge TTS**（默认） | 良好 | 免费 | 无需 |
| **ElevenLabs** | 优秀 | 付费 | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | 良好 | 付费 | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax TTS** | 优秀 | 付费 | `MINIMAX_API_KEY` |
| **Mistral (Voxtral TTS)** | 优秀 | 付费 | `MISTRAL_API_KEY` |
| **NeuTTS** | 良好 | 免费 | 无需 |

### 平台交付

| 平台 | 交付方式 | 格式 |
|----------|----------|--------|
| Telegram | 语音气泡（内联播放） | Opus `.ogg` |
| Discord | 语音气泡（Opus/OGG），回退到文件附件 | Opus/MP3 |
| WhatsApp | 音频文件附件 | MP3 |
| CLI | 保存到 `~/.hermes/audio_cache/` | MP3 |

### 配置

```yaml
# In ~/.hermes/config.yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "neutts"
  speed: 1.0                    # Global speed multiplier (provider-specific settings override this)
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
    speed: 1.0                  # Converted to rate percentage (+/-%)
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    base_url: "https://api.openai.com/v1"  # Override for OpenAI-compatible TTS endpoints
    speed: 1.0                  # 0.25 - 4.0
  minimax:
    model: "speech-2.8-hd"     # speech-2.8-hd (default), speech-2.8-turbo
    voice_id: "English_Graceful_Lady"  # See https://platform.minimax.io/faq/system-voice-id
    speed: 1                    # 0.5 - 2.0
    vol: 1                      # 0 - 10
    pitch: 0                    # -12 - 12
  mistral:
    model: "voxtral-mini-tts-2603"
    voice_id: "c69964a6-ab8b-4f8a-9465-ec0925096ec8"  # Paul - Neutral (default)
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

**速度控制**：全局 `tts.speed` 值默认适用于所有提供者。每个提供者可以用自己的 `speed` 设置覆盖它（例如，`tts.openai.speed: 1.5`）。提供者特定的速度优先于全局值。默认值为 `1.0`（正常速度）。

### Telegram 语音气泡与 ffmpeg

Telegram 语音气泡需要 Opus/OGG 音频格式：

- **OpenAI、ElevenLabs 和 Mistral** 原生生成 Opus — 无需额外设置
- **Edge TTS**（默认）输出 MP3，需要 **ffmpeg** 转换：
- **MiniMax TTS** 输出 MP3，需要 **ffmpeg** 转换为 Telegram 语音气泡
- **NeuTTS** 输出 WAV，也需要 **ffmpeg** 转换为 Telegram 语音气泡

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

没有 ffmpeg 时，Edge TTS、MiniMax TTS 和 NeuTTS 音频会作为常规音频文件发送（可播放，但显示为矩形播放器而非语音气泡）。

:::tip
如果您想要语音气泡而不安装 ffmpeg，请切换到 OpenAI、ElevenLabs 或 Mistral 提供者。
:::

## 语音消息转录（STT）

在 Telegram、Discord、WhatsApp、Slack 或 Signal 上发送的语音消息会被自动转录并作为文本注入到对话中。智能体将转录视为普通文本。

| 提供者 | 质量 | 成本 | API 密钥 |
|----------|---------|------|---------| 
| **Local Whisper** (default) | Good | Free | None needed |
| **Groq Whisper API** | Good–Best | Free tier | `GROQ_API_KEY` |
| **OpenAI Whisper API** | Good–Best | Paid | `VOICE_TOOLS_OPENAI_KEY` or `OPENAI_API_KEY` |

:::info Zero Config
Local transcription works out of the box when `faster-whisper` is installed. If that's unavailable, Hermes can also use a local `whisper` CLI from common install locations (like `/opt/homebrew/bin`) or a custom command via `HERMES_LOCAL_STT_COMMAND`.
:::

### Configuration

```yaml
# In ~/.hermes/config.yaml
stt:
  provider: "local"           # "local" | "groq" | "openai" | "mistral"
  local:
    model: "base"             # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"        # whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe
  mistral:
    model: "voxtral-mini-latest"  # voxtral-mini-latest, voxtral-mini-2602
```

### Provider Details

**Local (faster-whisper)** — Runs Whisper locally via [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Uses CPU by default, GPU if available. Model sizes:

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `tiny` | ~75 MB | Fastest | Basic |
| `base` | ~150 MB | Fast | Good (default) |
| `small` | ~500 MB | Medium | Better |
| `medium` | ~1.5 GB | Slower | Great |
| `large-v3` | ~3 GB | Slowest | Best |

**Groq API** — Requires `GROQ_API_KEY`. Good cloud fallback when you want a free hosted STT option.

**OpenAI API** — Accepts `VOICE_TOOLS_OPENAI_KEY` first and falls back to `OPENAI_API_KEY`. Supports `whisper-1`, `gpt-4o-mini-transcribe`, and `gpt-4o-transcribe`.

**Mistral API (Voxtral Transcribe)** — Requires `MISTRAL_API_KEY`. Uses Mistral's [Voxtral Transcribe](https://docs.mistral.ai/capabilities/audio/speech_to_text/) models. Supports 13 languages, speaker diarization, and word-level timestamps. Install with `pip install hermes-agent[mistral]`.

**Custom local CLI fallback** — Set `HERMES_LOCAL_STT_COMMAND` if you want Hermes to call a local transcription command directly. The command template supports `{input_path}`, `{output_dir}`, `{language}`, and `{model}` placeholders.

### Fallback Behavior

If your configured provider isn't available, Hermes automatically falls back:
- **Local faster-whisper unavailable** → Tries a local `whisper` CLI or `HERMES_LOCAL_STT_COMMAND` before cloud providers
- **Groq key not set** → Falls back to local transcription, then OpenAI
- **OpenAI key not set** → Falls back to local transcription, then Groq
- **Mistral key/SDK not set** → Skipped in auto-detect; falls through to next available provider
- **Nothing available** → Voice messages pass through with an accurate note to the user
