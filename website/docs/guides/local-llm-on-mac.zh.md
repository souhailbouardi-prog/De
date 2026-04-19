---
sidebar_position: 2
title: "在 Mac 上运行本地 LLM"
description: "在 macOS 上使用 llama.cpp 或 MLX 设置本地 OpenAI 兼容的 LLM 服务器，包括模型选择、内存优化和 Apple Silicon 上的真实基准测试"
---

# 在 Mac 上运行本地 LLM

本指南将引导您在 macOS 上运行带有 OpenAI 兼容 API 的本地 LLM 服务器。您将获得完全的隐私、零 API 成本，以及在 Apple Silicon 上令人惊讶的良好性能。

我们涵盖两个后端：

| 后端 | 安装 | 擅长 | 格式 |
|---------|---------|---------|--------|
| **llama.cpp** | `brew install llama.cpp` | 最快的首令牌时间，用于低内存的量化 KV 缓存 | GGUF |
| **omlx** | [omlx.ai](https://omlx.ai) | 最快的令牌生成，原生 Metal 优化 | MLX (safetensors) |

两者都公开 OpenAI 兼容的 `/v1/chat/completions` 端点。Hermes 可以与任何一个一起工作 — 只需将其指向 `http://localhost:8080` 或 `http://localhost:8000`。

:::info 仅限 Apple Silicon
本指南针对配备 Apple Silicon（M1 及更新版本）的 Mac。Intel Mac 可以使用 llama.cpp，但没有 GPU 加速 — 预计性能会显著降低。
:::

---

## 选择模型

对于入门，我们推荐 **Qwen3.5-9B** — 这是一个强大的推理模型，通过量化可以舒适地容纳在 8GB+ 的统一内存中。

| 变体 | 磁盘大小 | 所需 RAM（128K 上下文） | 后端 |
|---------|-------------|---------------------------|---------|
| Qwen3.5-9B-Q4_K_M (GGUF) | 5.3 GB | ~10 GB（带量化 KV 缓存） | llama.cpp |
| Qwen3.5-9B-mlx-lm-mxfp4 (MLX) | ~5 GB | ~12 GB | omlx |

**内存经验法则：** 模型大小 + KV 缓存。9B Q4 模型约为 5 GB。128K 上下文下的 KV 缓存（Q4 量化）增加约 4-5 GB。使用默认（f16）KV 缓存时，这会膨胀到约 16 GB。llama.cpp 中的量化 KV 缓存标志是内存受限系统的关键技巧。

对于更大的模型（27B、35B），您需要 32 GB+ 的统一内存。9B 是 8-16 GB 机器的最佳选择。

---

## 选项 A：llama.cpp

llama.cpp 是最便携的本地 LLM 运行时。在 macOS 上，它开箱即用地使用 Metal 进行 GPU 加速。

### 安装

```bash
brew install llama.cpp
```

这会为您提供全局的 `llama-server` 命令。

### 下载模型

您需要一个 GGUF 格式的模型。最简单的来源是通过 `huggingface-cli` 从 Hugging Face 下载：

```bash
brew install huggingface-cli
```

然后下载：

```bash
huggingface-cli download unsloth/Qwen3.5-9B-GGUF Qwen3.5-9B-Q4_K_M.gguf --local-dir ~/models
```

:::tip  gated 模型
Hugging Face 上的一些模型需要身份验证。如果您收到 401 或 404 错误，请先运行 `huggingface-cli login`。
:::

### 启动服务器

```bash
llama-server -m ~/models/Qwen3.5-9B-Q4_K_M.gguf \
  -ngl 99 \
  -c 131072 \
  -np 1 \
  -fa on \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  --host 0.0.0.0
```

以下是每个标志的作用：

| 标志 | 目的 |
|------|---------|
| `-ngl 99` | 将所有层卸载到 GPU（Metal）。使用较高的数字以确保没有任何内容留在 CPU 上。 |
| `-c 131072` | 上下文窗口大小（128K 令牌）。如果内存不足，请减少此值。 |
| `-np 1` | 并行槽位数。单用户使用时保持为 1 — 更多槽位会分割您的内存预算。 |
| `-fa on` | 闪存注意力。减少内存使用并加速长上下文推理。 |
| `--cache-type-k q4_0` | 将键缓存量化为 4 位。**这是最大的内存节省器。** |
| `--cache-type-v q4_0` | 将值缓存量化为 4 位。与上述一起使用，这会将 KV 缓存内存减少约 75%（与 f16 相比）。 |
| `--host 0.0.0.0` | 监听所有接口。如果不需要网络访问，请使用 `127.0.0.1`。 |

当您看到以下内容时，服务器已准备就绪：

```
main: server is listening on http://0.0.0.0:8080
srv  update_slots: all slots are idle
```

### 内存受限系统的优化

`--cache-type-k q4_0 --cache-type-v q4_0` 标志是内存有限系统最重要的优化。以下是 128K 上下文下的影响：

| KV 缓存类型 | KV 缓存内存（128K 上下文，9B 模型） |
|---------------|--------------------------------------|
| f16（默认） | ~16 GB |
| q8_0 | ~8 GB |
| **q4_0** | **~4 GB** |

在 8 GB Mac 上，使用 `q4_0` KV 缓存并将上下文减少到 `-c 32768`（32K）。在 16 GB 上，您可以舒适地使用 128K 上下文。在 32 GB+ 上，您可以运行更大的模型或多个并行槽位。

如果仍然内存不足，请首先减少上下文大小（`-c`），然后尝试更小的量化（Q3_K_M 而不是 Q4_K_M）。

### 测试

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.5-9B-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }' | jq .choices[0].message.content
```

### 获取模型名称

如果您忘记了模型名称，请查询模型端点：

```bash
curl -s http://localhost:8080/v1/models | jq '.data[].id'
```

---

## 选项 B：通过 omlx 使用 MLX

[omlx](https://omlx.ai) 是一个 macOS 原生应用程序，用于管理和提供 MLX 模型。MLX 是 Apple 自己的机器学习框架，专门针对 Apple Silicon 的统一内存架构进行了优化。

### 安装

从 [omlx.ai](https://omlx.ai) 下载并安装。它提供了模型管理的 GUI 和内置服务器。

### 下载模型

使用 omlx 应用程序浏览和下载模型。搜索 `Qwen3.5-9B-mlx-lm-mxfp4` 并下载它。模型存储在本地（通常在 `~/.omlx/models/` 中）。

### 启动服务器

omlx 默认在 `http://127.0.0.1:8000` 上提供模型。从应用 UI 开始提供服务，或使用可用的 CLI。

### 测试

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.5-9B-mlx-lm-mxfp4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }' | jq .choices[0].message.content
```

### 列出可用模型

omlx 可以同时提供多个模型：

```bash
curl -s http://127.0.0.1:8000/v1/models | jq '.data[].id'
```

---

## 基准测试：llama.cpp vs MLX

两个后端在同一台机器（Apple M5 Max，128 GB 统一内存）上测试，运行相同的模型（Qwen3.5-9B），量化水平相当（GGUF 的 Q4_K_M，MLX 的 mxfp4）。五个不同的提示，每个运行三次，后端顺序测试以避免资源竞争。

### 结果

| 指标 | llama.cpp (Q4_K_M) | MLX (mxfp4) | 获胜者 |
|--------|-------------------|-------------|--------|
| **TTFT（平均）** | **67 ms** | 289 ms | llama.cpp（快 4.3 倍） |
| **TTFT（p50）** | **66 ms** | 286 ms | llama.cpp（快 4.3 倍） |
| **生成（平均）** | 70 令牌/秒 | **96 令牌/秒** | MLX（快 37%） |
| **生成（p50）** | 70 令牌/秒 | **96 令牌/秒** | MLX（快 37%） |
| **总时间（512 令牌）** | 7.3s | **5.5s** | MLX（快 25%） |

### 这意味着什么

- **llama.cpp** 在提示处理方面表现出色 — 其闪存注意力 + 量化 KV 缓存管道在 ~66ms 内为您提供第一个令牌。如果您正在构建感知响应性很重要的交互式应用程序（聊天机器人、自动完成），这是一个有意义的优势。

- **MLX** 一旦启动，令牌生成速度快约 37%。对于批处理工作负载、长格式生成或任何总完成时间比初始延迟更重要的任务，MLX 完成得更快。

- 两个后端都**非常一致** — 运行之间的差异可以忽略不计。您可以依赖这些数字。

### 您应该选择哪一个？

| 使用场景 | 推荐 |
|----------|---------------|
| 交互式聊天，低延迟工具 | llama.cpp |
| 长格式生成，批量处理 | MLX (omlx) |
| 内存受限（8-16 GB） | llama.cpp（量化 KV 缓存无与伦比） |
| 同时提供多个模型 | omlx（内置多模型支持） |
| 最大兼容性（也适用于 Linux） | llama.cpp |

---

## 连接到 Hermes

一旦您的本地服务器运行：

```bash
hermes model
```

选择 **Custom endpoint** 并按照提示操作。它会询问基本 URL 和模型名称 — 使用您上面设置的任何后端的值。

---

## 超时

Hermes 会自动检测本地端点（localhost、LAN IP）并放宽其流式传输超时。大多数设置不需要配置。

如果您仍然遇到超时错误（例如，在慢速硬件上使用非常大的上下文），您可以覆盖流式读取超时：

```bash
# 在您的 .env 中 — 从 120s 默认值提高到 30 分钟
HERMES_STREAM_READ_TIMEOUT=1800
```

| 超时 | 默认值 | 本地自动调整 | 环境变量覆盖 |
|---------|---------|----------------------|------------------|
| 流式读取（套接字级别） | 120s | 提高到 1800s | `HERMES_STREAM_READ_TIMEOUT` |
|  stale 流检测 | 180s | 完全禁用 | `HERMES_STREAM_STALE_TIMEOUT` |
| API 调用（非流式） | 1800s | 无需更改 | `HERMES_API_TIMEOUT` |

流式读取超时是最可能导致问题的 — 它是接收下一个数据块的套接字级别截止时间。在大型上下文的预填充期间，本地模型在处理提示时可能会数分钟没有输出。自动检测会透明地处理这一点。