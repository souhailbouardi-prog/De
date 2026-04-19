---
title: "图像生成"
description: "通过 FAL.ai 生成图像 — 8 个模型，包括 FLUX 2、GPT-Image、Nano Banana Pro、Ideogram、Recraft V4 Pro 等，可通过 `hermes tools` 选择。"
sidebar_label: "图像生成"
sidebar_position: 6
---

# 图像生成

Hermes Agent 通过 FAL.ai 从文本提示生成图像。开箱即用支持八种模型，每种都有不同的速度、质量和成本权衡。活动模型可通过 `hermes tools` 由用户配置，并持久保存在 `config.yaml` 中。

## 支持的模型

| 模型 | 速度 | 优势 | 价格 |
|---|---|---|---|
| `fal-ai/flux-2/klein/9b` *(默认)* | `<1s` | 快速、清晰的文本 | $0.006/MP |
| `fal-ai/flux-2-pro` | ~6s | 工作室级照片真实感 | $0.03/MP |
| `fal-ai/z-image/turbo` | ~2s | 双语 EN/CN、6B 参数 | $0.005/MP |
| `fal-ai/nano-banana-pro` | ~8s | Gemini 3 Pro、推理深度、文本渲染 | $0.15/图像（1K） |
| `fal-ai/gpt-image-1.5` | ~15s | 提示遵守度 | $0.034/图像 |
| `fal-ai/ideogram/v3` | ~5s | 最佳排版 | $0.03–0.09/图像 |
| `fal-ai/recraft/v4/pro/text-to-image` | ~8s | 设计、品牌系统、生产就绪 | $0.25/图像 |
| `fal-ai/qwen-image` | ~12s | 基于 LLM、复杂文本 | $0.02/MP |

价格是撰写本文时 FAL 的定价；请查看 [fal.ai](https://fal.ai/) 了解当前数字。

## 设置

:::tip Nous 订阅者
如果您有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，您可以通过**[工具网关](tool-gateway.md)**使用图像生成，而无需 FAL API 密钥。您的模型选择在两条路径上都持久存在。

如果托管网关为特定模型返回 `HTTP 4xx`，则该模型尚未在门户端代理 — 代理会告诉您这一点，并提供补救步骤（设置 `FAL_KEY` 以直接访问，或选择不同的模型）。
:::

### 获取 FAL API 密钥

1. 在 [fal.ai](https://fal.ai/) 注册
2. 从您的仪表板生成 API 密钥

### 配置和选择模型

运行工具命令：

```bash
hermes tools
```

导航到 **🎨 Image Generation**，选择您的后端（Nous Subscription 或 FAL.ai），然后选择器会在列对齐的表格中显示所有支持的模型 — 箭头键导航，Enter 选择：

```
  Model                          Speed    Strengths                    Price
  fal-ai/flux-2/klein/9b         <1s      Fast, crisp text             $0.006/MP   ← currently in use
  fal-ai/flux-2-pro              ~6s      Studio photorealism          $0.03/MP
  fal-ai/z-image/turbo           ~2s      Bilingual EN/CN, 6B          $0.005/MP
  ...
```

您的选择保存到 `config.yaml`：

```yaml
image_gen:
  model: fal-ai/flux-2/klein/9b
  use_gateway: false            # 如果使用 Nous Subscription 则为 true
```

### GPT-Image 质量

`fal-ai/gpt-image-1.5` 请求质量固定为 `medium`（1024×1024 时约 $0.034/图像）。我们不将 `low` / `high` 层级作为面向用户的选项公开，以便 Nous Portal 计费对所有用户保持可预测性 — 层级之间的成本差异约为 22 倍。如果您想要更便宜的 GPT-Image 选项，请选择不同的模型；如果您想要更高质量，请使用 Klein 9B 或 Imagen 级模型。

## 使用

面向代理的架构有意保持最小 — 模型会获取您配置的任何内容：

```
Generate an image of a serene mountain landscape with cherry blossoms
```

```
Create a square portrait of a wise old owl — use the typography model
```

```
Make me a futuristic cityscape, landscape orientation
```

## 宽高比

从代理的角度来看，每个模型都接受相同的三种宽高比。在内部，每个模型的原生大小规格会自动填充：

| 代理输入 | image_size（flux/z-image/qwen/recraft/ideogram） | aspect_ratio（nano-banana-pro） | image_size（gpt-image） |
|---|---|---|---|
| `landscape` | `landscape_16_9` | `16:9` | `1536x1024` |
| `square` | `square_hd` | `1:1` | `1024x1024` |
| `portrait` | `portrait_16_9` | `9:16` | `1024x1536` |

这种转换发生在 `_build_fal_payload()` 中 — 代理代码永远不需要知道每个模型的架构差异。

## 自动放大

通过 FAL 的 **Clarity Upscaler** 进行的放大是按模型门控的：

| 模型 | 放大？ | 原因 |
|---|---|---|
| `fal-ai/flux-2-pro` | ✓ | 向后兼容（是选择器之前的默认值） |
| 所有其他 | ✗ | 快速模型会失去它们的亚秒级价值主张；高分辨率模型不需要它 |

当放大运行时，它使用这些设置：

| 设置 | 值 |
|---|---|
| 放大因子 | 2× |
| 创意 | 0.35 |
| 相似度 | 0.6 |
| 引导比例 | 4 |
| 推理步骤 | 18 |

如果放大失败（网络问题、速率限制），原始图像会自动返回。

## 内部工作原理

1. **模型解析** — `_resolve_fal_model()` 从 `config.yaml` 读取 `image_gen.model`，回退到 `FAL_IMAGE_MODEL` 环境变量，然后回退到 `fal-ai/flux-2/klein/9b`。
2. **有效负载构建** — `_build_fal_payload()` 将您的 `aspect_ratio` 转换为模型的原生格式（预设枚举、宽高比枚举或 GPT 文字），合并模型的默认参数，应用任何调用者覆盖，然后过滤到模型的 `supports` 白名单，以便永远不会发送不受支持的键。
3. **提交** — `_submit_fal_request()` 通过直接 FAL 凭据或托管的 Nous 网关路由。
4. **放大** — 仅在模型的元数据有 `upscale: True` 时运行。
5. **交付** — 最终图像 URL 返回给代理，代理发出 `MEDIA:<url>` 标签，平台适配器将其转换为原生媒体。

## 调试

启用调试日志：

```bash
export IMAGE_TOOLS_DEBUG=true
```

调试日志转到 `./logs/image_tools_debug_<session_id>.json`，包含每个调用的详细信息（模型、参数、时间、错误）。

## 平台交付

| 平台 | 交付 |
|---|---|
| **CLI** | 图像 URL 打印为 markdown `![](url)` — 点击打开 |
| **Telegram** | 带有提示作为标题的照片消息 |
| **Discord** | 嵌入在消息中 |
| **Slack** | 由 Slack 展开的 URL |
| **WhatsApp** | 媒体消息 |
| **其他** | 纯文本中的 URL |

## 限制

- **需要 FAL 凭据**（直接 `FAL_KEY` 或 Nous Subscription）
- **仅限文本到图像** — 无图像修复、img2img 或通过此工具编辑
- **临时 URL** — FAL 返回的托管 URL 在数小时/数天后过期；如果需要请在本地保存
- **每个模型的约束** — 某些模型不支持 `seed`、`num_inference_steps` 等。`supports` 过滤器静默删除不受支持的参数；这是预期行为
