---
sidebar_position: 5
title: "内置技能目录"
description: "Hermes Agent 随附的内置技能目录"
---

# 内置技能目录

Hermes 在安装时会将大型内置技能库复制到 `~/.hermes/skills/` 中。本页面列出了存储库中 `skills/` 目录下的内置技能。

## apple

Apple/macOS 特定技能 — iMessage、提醒事项、备忘录、查找我的和 macOS 自动化。这些技能仅在 macOS 系统上加载。

| 技能 | 描述 | 路径 |
|------|------|------|
| `apple-notes` | 通过 macOS 上的 memo CLI 管理 Apple 备忘录（创建、查看、搜索、编辑）。 | `apple/apple-notes` |
| `apple-reminders` | 通过 remindctl CLI 管理 Apple 提醒事项（列出、添加、完成、删除）。 | `apple/apple-reminders` |
| `findmy` | 通过 macOS 上的 FindMy.app 使用 AppleScript 和屏幕捕获跟踪 Apple 设备和 AirTag。 | `apple/findmy` |
| `imessage` | 通过 macOS 上的 imsg CLI 发送和接收 iMessages/SMS。 | `apple/imessage` |

## autonomous-ai-agents

用于生成和编排自主 AI 编码代理和多代理工作流的技能 — 运行独立的代理进程、委派任务和协调并行工作流。

| 技能 | 描述 | 路径 |
|------|------|------|
| `claude-code` | 将编码任务委派给 Claude Code（Anthropic 的 CLI 代理）。用于构建功能、重构、PR 审查和迭代编码。需要安装 claude CLI。 | `autonomous-ai-agents/claude-code` |
| `codex` | 将编码任务委派给 OpenAI Codex CLI 代理。用于构建功能、重构、PR 审查和批量问题修复。需要 codex CLI 和 git 存储库。 | `autonomous-ai-agents/codex` |
| `hermes-agent-spawning` | 生成额外的 Hermes Agent 实例作为自主子进程，用于独立的长时间运行任务。支持非交互式一次性模式 (-q) 和交互式 PTY 模式，用于多轮协作。与 delegate_task 不同 — 这运行一个完整的独立 hermes 进程。 | `autonomous-ai-agents/hermes-agent` |
| `opencode` | 将编码任务委派给 OpenCode CLI 代理，用于功能实现、重构、PR 审查和长时间运行的自主会话。需要安装并认证 opencode CLI。 | `autonomous-ai-agents/opencode` |

## data-science

用于数据科学工作流的技能 — 交互式探索、Jupyter 笔记本、数据分析和可视化。

| 技能 | 描述 | 路径 |
|------|------|------|
| `jupyter-live-kernel` | 通过 hamelnb 使用实时 Jupyter 内核进行有状态、迭代的 Python 执行。当任务涉及探索、迭代或检查中间结果时，加载此技能。 | `data-science/jupyter-live-kernel` |

## creative

创意内容生成 — ASCII 艺术、手绘风格图表和视觉设计工具。

| 技能 | 描述 | 路径 |
|------|------|------|
| `ascii-art` | 使用 pyfiglet（571 种字体）、cowsay、boxes、toilet、image-to-ascii、远程 API（asciified、ascii.co.uk）和 LLM 回退生成 ASCII 艺术。不需要 API 密钥。 | `creative/ascii-art` |
| `ascii-video` | "ASCII 艺术视频的制作流程 — 任何格式。将视频/音频/图像/生成输入转换为彩色 ASCII 字符视频输出（MP4、GIF、图像序列）。包括：视频到 ASCII 转换、音频响应音乐可视化、生成 ASCII 艺术动画、混合… | `creative/ascii-video` |
| `excalidraw` | 使用 Excalidraw JSON 格式创建手绘风格图表。生成 .excalidraw 文件用于架构图、流程图、序列图、概念图等。文件可以在 excalidraw.com 打开或上传以获取可共享链接。 | `creative/excalidraw` |
| `p5js` | 使用 p5.js 进行交互式和生成式视觉艺术的制作流程。创建草图，通过无头浏览器将其渲染为图像/视频，并提供实时预览。支持画布动画、数据可视化和创意编码实验。 | `creative/p5js` |

## devops

DevOps 和基础设施自动化技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `webhook-subscriptions` | 创建和管理用于事件驱动代理激活的 webhook 订阅。外部服务（GitHub、Stripe、CI/CD、IoT）POST 事件以触发代理运行。需要启用 webhook 平台。 | `devops/webhook-subscriptions` |

## dogfood

| 技能 | 描述 | 路径 |
|------|------|------|
| `dogfood` | 对 web 应用程序进行系统探索性 QA 测试 — 发现错误、捕获证据并生成结构化报告。 | `dogfood/dogfood` |
| `hermes-agent-setup` | 帮助用户配置 Hermes Agent — CLI 使用、设置向导、模型/提供商选择、工具、技能、语音/STT/TTS、网关和故障排除。 | `dogfood/hermes-agent-setup` |

## email

用于从终端发送、接收、搜索和管理电子邮件的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `himalaya` | 通过 IMAP/SMTP 管理电子邮件的 CLI。使用 himalaya 从终端列出、读取、编写、回复、转发、搜索和组织电子邮件。支持多个账户和使用 MML（MIME 元语言）的消息撰写。 | `email/himalaya` |

## gaming

用于设置、配置和管理游戏服务器、模组包和游戏相关基础设施的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `minecraft-modpack-server` | 从 CurseForge/Modrinth 服务器包 zip 设置模组化 Minecraft 服务器。涵盖 NeoForge/Forge 安装、Java 版本、JVM 调优、防火墙、LAN 配置、备份和启动脚本。 | `gaming/minecraft-modpack-server` |
| `pokemon-player` | 通过无头模拟自主玩 Pokemon 游戏。启动游戏服务器，从 RAM 读取结构化游戏状态，做出战略决策，并从终端发送按钮输入 — 全部从终端完成。 | `gaming/pokemon-player` |

## github

GitHub 工作流技能，用于使用 gh CLI 和 git 通过终端管理存储库、拉取请求、代码审查、问题和 CI/CD 管道。

| 技能 | 描述 | 路径 |
|------|------|------|
| `codebase-inspection` | 使用 pygount 分析代码库，用于 LOC 计数、语言分解和代码与注释比率。当被要求检查代码行数、存储库大小、语言组成或代码库统计信息时使用。 | `github/codebase-inspection` |
| `github-auth` | 使用 git（普遍可用）或 gh CLI 为代理设置 GitHub 认证。涵盖 HTTPS 令牌、SSH 密钥、凭据帮助程序和 gh auth — 具有检测流程，可自动选择正确的方法。 | `github/github-auth` |
| `github-code-review` | 通过分析 git diff、在 PR 上留下内联评论以及执行彻底的预推送审查来审查代码更改。使用 gh CLI 或回退到 git + GitHub REST API via curl。 | `github/github-code-review` |
| `github-issues` | 创建、管理、分类和关闭 GitHub 问题。搜索现有问题、添加标签、分配人员并链接到 PR。使用 gh CLI 或回退到 git + GitHub REST API via curl。 | `github/github-issues` |
| `github-pr-workflow` | 完整的拉取请求生命周期 — 创建分支、提交更改、打开 PR、监控 CI 状态、自动修复失败和合并。使用 gh CLI 或回退到 git + GitHub REST API via curl。 | `github/github-pr-workflow` |
| `github-repo-management` | 克隆、创建、分叉、配置和管理 GitHub 存储库。管理远程、密钥、发布和工作流。使用 gh CLI 或回退到 git + GitHub REST API via curl。 | `github/github-repo-management` |

## inference-sh

通过 inference.sh 云平台执行 AI 应用程序的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `inference-sh-cli` | 通过 inference.sh CLI (infsh) 运行 150+ AI 应用程序 — 图像生成、视频创建、LLM、搜索、3D、社交自动化。 | `inference-sh/cli` |

## leisure

| 技能 | 描述 | 路径 |
|------|------|------|
| `find-nearby` | 使用 OpenStreetMap 查找附近的地方（餐厅、咖啡馆、酒吧、药店等）。适用于坐标、地址、城市、邮政编码或 Telegram 位置引脚。不需要 API 密钥。 | `leisure/find-nearby` |

## mcp

用于处理 MCP（模型上下文协议）服务器、工具和集成的技能。包括内置的原生 MCP 客户端（在 config.yaml 中配置服务器以进行自动工具发现）和用于临时服务器交互的 mcporter CLI 桥接器。

| 技能 | 描述 | 路径 |
|------|------|------|
| `mcporter` | 使用 mcporter CLI 直接列出、配置、认证和调用 MCP 服务器/工具（HTTP 或 stdio），包括临时服务器、配置编辑和 CLI/类型生成。 | `mcp/mcporter` |
| `native-mcp` | 内置 MCP（模型上下文协议）客户端，连接到外部 MCP 服务器，发现其工具，并将它们注册为原生 Hermes Agent 工具。支持 stdio 和 HTTP 传输，具有自动重连、安全过滤和零配置工具注入。 | `mcp/native-mcp` |

## media

用于处理媒体内容的技能 — YouTube 字幕、GIF 搜索、音乐生成和音频可视化。

| 技能 | 描述 | 路径 |
|------|------|------|
| `gif-search` | 使用 curl 从 Tenor 搜索和下载 GIF。除了 curl 和 jq 外没有依赖项。对于查找反应 GIF、创建视觉内容和在聊天中发送 GIF 很有用。 | `media/gif-search` |
| `heartmula` | 设置和运行 HeartMuLa，开源音乐生成模型系列（类似 Suno）。从歌词 + 标签生成完整歌曲，支持多语言。 | `media/heartmula` |
| `songsee` | 通过 CLI 从音频文件生成频谱图和音频特征可视化（梅尔、色度、MFCC、节拍图等）。对于音频分析、音乐制作调试和视觉文档很有用。 | `media/songsee` |
| `youtube-content` | 获取 YouTube 视频字幕并将其转换为结构化内容（章节、摘要、线程、博客文章）。 | `media/youtube-content` |

## mlops

通用 ML 操作工具 — 模型中心管理、数据集操作和工作流编排。

| 技能 | 描述 | 路径 |
|------|------|------|
| `huggingface-hub` | Hugging Face Hub CLI (hf) — 搜索、下载和上传模型和数据集，管理存储库，部署推理端点。 | `mlops/huggingface-hub` |

## mlops/cloud

用于 ML 工作负载的 GPU 云提供商和无服务器计算平台。

| 技能 | 描述 | 路径 |
|------|------|------|
| `lambda-labs-gpu-cloud` | 用于 ML 训练和推理的预留和按需 GPU 云实例。当您需要具有简单 SSH 访问、持久文件系统或用于大规模训练的高性能多节点集群的专用 GPU 实例时使用。 | `mlops/cloud/lambda-labs` |
| `modal-serverless-gpu` | 用于运行 ML 工作负载的无服务器 GPU 云平台。当您需要无需基础设施管理的按需 GPU 访问、将 ML 模型部署为 API 或运行具有自动扩展的批处理作业时使用。 | `mlops/cloud/modal` |

## mlops/evaluation

模型评估基准、实验跟踪、数据管理、分词器和可解释性工具。

| 技能 | 描述 | 路径 |
|------|------|------|
| `evaluating-llms-harness` | 在 60+ 学术基准（MMLU、HumanEval、GSM8K、TruthfulQA、HellaSwag）上评估 LLM。当基准模型质量、比较模型、报告学术结果或跟踪训练进度时使用。EleutherAI、HuggingFace 和主要实验室使用的行业标准。Sup… | `mlops/evaluation/lm-evaluation-harness` |
| `huggingface-tokenizers` | 为研究和生产优化的快速分词器。基于 Rust 的实现可在 &lt;20 秒内对 1GB 进行分词。支持 BPE、WordPiece 和 Unigram 算法。训练自定义词汇表，跟踪对齐，处理填充/截断。与 transformers 无缝集成。Use… | `mlops/evaluation/huggingface-tokenizers` |
| `nemo-curator` | 用于 LLM 训练的 GPU 加速数据管理。支持文本/图像/视频/音频。功能包括模糊去重（快 16 倍）、质量过滤（30+ 启发式）、语义去重、PII 编辑、NSFW 检测。使用 RAPIDS 在 GPU 上扩展。用于准备高质量 t… | `mlops/evaluation/nemo-curator` |
| `sparse-autoencoder-training` | 提供使用 SAELens 训练和分析稀疏自编码器 (SAE) 的指导，以将神经网络激活分解为可解释的特征。当发现可解释特征、分析叠加或研究语言 m… 中的单义表示时使用 | `mlops/evaluation/saelens` |
| `weights-and-biases` | 通过自动日志记录跟踪 ML 实验，实时可视化训练，通过扫描优化超参数，并使用 W&B（协作 MLOps 平台）管理模型注册表 | `mlops/evaluation/weights-and-biases` |

## mlops/inference

模型服务、量化（GGUF/GPTQ）、结构化输出、推理优化和模型手术工具，用于部署和运行 LLM。

| 技能 | 描述 | 路径 |
|------|------|------|
| `instructor` | 使用 Pydantic 验证从 LLM 响应中提取结构化数据，自动重试失败的提取，使用类型安全解析复杂 JSON，并使用 Instructor（经过实战测试的结构化输出库）流式传输部分结果 | `mlops/inference/instructor` |
| `llama-cpp` | 在 CPU、Apple Silicon、AMD/Intel GPU 或 NVIDIA 上使用 llama.cpp 运行 LLM 推理 — 以及 GGUF 模型转换和量化（2–8 位，带有 K-quants 和 imatrix）。涵盖 CLI、Python 绑定、OpenAI 兼容服务器以及 Ollama/LM Studio 集成。用于边缘部署、M1/M2/M3/M4 Mac、无 CUDA 环境或灵活的本地量化。 | `mlops/inference/llama-cpp` |
| `obliteratus` | 使用 OBLITERATUS 从开放权重 LLM 中移除拒绝行为 — 机械可解释性技术（均值差异、SVD、白化 SVD、LEACE、SAE 分解等）来切除护栏，同时保留推理。9 种 CLI 方法，28 个分析模块，116 个模型预设 ac… | `mlops/inference/obliteratus` |
| `outlines` | 在生成过程中保证有效的 JSON/XML/代码结构，使用 Pydantic 模型进行类型安全输出，支持本地模型（Transformers、vLLM），并使用 Outlines（dottxt.ai 的结构化生成库）最大化推理速度 | `mlops/inference/outlines` |
| `serving-llms-vllm` | 使用 vLLM 的 PagedAttention 和连续批处理以高吞吐量提供 LLM。当部署生产 LLM API、优化推理延迟/吞吐量或使用有限 GPU 内存提供模型时使用。支持 OpenAI 兼容端点、量化（GPTQ/AWQ/FP8），an… | `mlops/inference/vllm` |
| `tensorrt-llm` | 使用 NVIDIA TensorRT 优化 LLM 推理，以实现最大吞吐量和最低延迟。用于在 NVIDIA GPU（A100/H100）上进行生产部署，当您需要比 PyTorch 快 10-100 倍的推理，或用于提供带有量化（FP8/INT4）、飞行中批处理和 mult… 的模型 | `mlops/inference/tensorrt-llm` |

## mlops/models

特定的模型架构和工具 — 计算机视觉（CLIP、SAM、Stable Diffusion）、语音（Whisper）、音频生成（AudioCraft）和多模态模型（LLaVA）。

| 技能 | 描述 | 路径 |
|------|------|------|
| `audiocraft-audio-generation` | 用于音频生成的 PyTorch 库，包括文本到音乐（MusicGen）和文本到声音（AudioGen）。当您需要从文本描述生成音乐、创建音效或执行旋律条件音乐生成时使用。 | `mlops/models/audiocraft` |
| `clip` | OpenAI 的连接视觉和语言的模型。启用零样本图像分类、图像-文本匹配和跨模态检索。在 4 亿图像-文本对上训练。用于图像搜索、内容审核或无需微调的视觉-语言任务。最适合 general-purpo… | `mlops/models/clip` |
| `llava` | 大型语言和视觉助手。启用视觉指令调整和基于图像的对话。结合 CLIP 视觉编码器和 Vicuna/LLaMA 语言模型。支持多轮图像聊天、视觉问答和指令跟随。用于视觉-语言 cha… | `mlops/models/llava` |
| `segment-anything-model` | 用于图像分割的基础模型，具有零样本迁移。当您需要使用点、框或掩码作为提示分割图像中的任何对象，或自动生成图像中的所有对象掩码时使用。 | `mlops/models/segment-anything` |
| `stable-diffusion-image-generation` | 通过 HuggingFace Diffusers 使用 Stable Diffusion 模型进行最先进的文本到图像生成。当从文本提示生成图像、执行图像到图像转换、修复或构建自定义扩散管道时使用。 | `mlops/models/stable-diffusion` |
| `whisper` | OpenAI 的通用语音识别模型。支持 99 种语言、转录、翻译成英语和语言识别。六种模型大小，从小型（39M 参数）到大型（1550M 参数）。用于语音到文本、播客转录或多语言音频 proc… | `mlops/models/whisper` |

## mlops/research

用于通过声明式编程构建和优化 AI 系统的 ML 研究框架。

| 技能 | 描述 | 路径 |
|------|------|------|
| `dspy` | 使用声明式编程构建复杂的 AI 系统，自动优化提示，使用 DSPy（斯坦福 NLP 的系统 LM 编程框架）创建模块化 RAG 系统和代理 | `mlops/research/dspy` |

## mlops/training

微调、RLHF/DPO/GRPO 训练、分布式训练框架和优化工具，用于训练 LLM 和其他模型。

| 技能 | 描述 | 路径 |
|------|------|------|
| `axolotl` | 使用 Axolotl 微调 LLM 的专家指导 — YAML 配置、100+ 模型、LoRA/QLoRA、DPO/KTO/ORPO/GRPO、多模态支持 | `mlops/training/axolotl` |
| `distributed-llm-pretraining-torchtitan` | 使用 torchtitan 提供 PyTorch 原生分布式 LLM 预训练，具有 4D 并行性（FSDP2、TP、PP、CP）。当从 8 到 512+ GPU 大规模预训练 Llama 3.1、DeepSeek V3 或自定义模型时使用，具有 Float8、torch.compile 和分布式检查点。 | `mlops/training/torchtitan` |
| `fine-tuning-with-trl` | 使用 TRL 通过强化学习微调 LLM — SFT 用于指令调整，DPO 用于偏好对齐，PPO/GRPO 用于奖励优化，以及奖励模型训练。当需要 RLHF、使模型与偏好对齐或从人类反馈中训练时使用。适用于 HuggingFace Tr… | `mlops/training/trl-fine-tuning` |
| `hermes-atropos-environments` | 构建、测试和调试用于 Atropos 训练的 Hermes Agent RL 环境。涵盖 HermesAgentBaseEnv 接口、奖励函数、代理循环集成、使用工具的评估、wandb 日志记录以及三种 CLI 模式（serve/process/evaluate）。当创建、审查或 f… | `mlops/training/hermes-atropos-environments` |
| `huggingface-accelerate` | 最简单的分布式训练 API。4 行代码即可为任何 PyTorch 脚本添加分布式支持。DeepSpeed/FSDP/Megatron/DDP 的统一 API。自动设备放置、混合精度（FP16/BF16/FP8）。交互式配置，单一启动命令。HuggingFace 生态系统标准。 | `mlops/training/accelerate` |
| `optimizing-attention-flash` | 使用 Flash Attention 优化 transformer 注意力，实现 2-4 倍速度提升和 10-20 倍内存减少。当训练/运行具有长序列（&gt;512 个 token）的 transformer、遇到注意力的 GPU 内存问题或需要更快的推理时使用。支持 PyTorch 原生 SDPA,… | `mlops/training/flash-attention` |
| `peft-fine-tuning` | 使用 LoRA、QLoRA 和 25+ 方法对 LLM 进行参数高效微调。当使用有限的 GPU 内存微调大型模型（7B-70B）、需要训练 &lt;1% 的参数且精度损失最小，或用于多适配器服务时使用。HuggingFace 的官方库 i… | `mlops/training/peft` |
| `pytorch-fsdp` | 使用 PyTorch FSDP 进行完全分片数据并行训练的专家指导 — 参数分片、混合精度、CPU 卸载、FSDP2 | `mlops/training/pytorch-fsdp` |
| `pytorch-lightning` | 高级 PyTorch 框架，具有 Trainer 类、自动分布式训练（DDP/FSDP/DeepSpeed）、回调系统和最小样板代码。使用相同的代码从小型笔记本电脑扩展到超级计算机。当您想要使用内置最佳实践的干净训练循环时使用。 | `mlops/training/pytorch-lightning` |
| `simpo-training` | 用于 LLM 对齐的简单偏好优化。DPO 的无参考替代方案，具有更好的性能（AlpacaEval 2.0 上 +6.4 点）。不需要参考模型，比 DPO 更高效。当需要比 DPO/PPO 更简单、更快的训练进行偏好对齐时使用。 | `mlops/training/simpo` |
| `slime-rl-training` | 使用 slime（Megatron+SGLang 框架）为 LLM 后训练提供 RL 指导。当训练 GLM 模型、实现自定义数据生成工作流或需要 Megatron-LM 与 RL 扩展的紧密集成时使用。 | `mlops/training/slime` |
| `unsloth` | 使用 Unsloth 进行快速微调的专家指导 — 2-5 倍更快的训练，50-80% 更少的内存，LoRA/QLoRA 优化 | `mlops/training/unsloth` |

## mlops/vector-databases

用于 RAG、语义搜索和 AI 应用程序后端的向量相似性搜索和嵌入数据库。

| 技能 | 描述 | 路径 |
|------|------|------|
| `chroma` | 用于 AI 应用程序的开源嵌入数据库。存储嵌入和元数据，执行向量和全文搜索，按元数据过滤。简单的 4 函数 API。从小型笔记本扩展到生产集群。用于语义搜索、RAG 应用程序或文档检索。Best… | `mlops/vector-databases/chroma` |
| `faiss` | Facebook 的库，用于密集向量的高效相似性搜索和聚类。支持数十亿向量、GPU 加速和各种索引类型（Flat、IVF、HNSW）。用于快速 k-NN 搜索、大规模向量检索，或当您需要纯相似性搜索而没有… | `mlops/vector-databases/faiss` |
| `pinecone` | 用于生产 AI 应用程序的托管向量数据库。完全托管，自动扩展，具有混合搜索（密集 + 稀疏）、元数据过滤和命名空间。低延迟（&lt;100ms p95）。用于生产 RAG、推荐系统或大规模语义搜索。最适合 server… | `mlops/vector-databases/pinecone` |
| `qdrant-vector-search` | 用于 RAG 和语义搜索的高性能向量相似性搜索引擎。当构建需要快速最近邻搜索、带过滤的混合搜索或具有 Rust 驱动性能的可扩展向量存储的生产 RAG 系统时使用。 | `mlops/vector-databases/qdrant` |

## note-taking

笔记技能，用于保存信息、协助研究以及协作进行多会话规划和信息共享。

| 技能 | 描述 | 路径 |
|------|------|------|
| `obsidian` | 在 Obsidian 保险库中读取、搜索和创建笔记。 | `note-taking/obsidian` |

## productivity

用于文档创建、演示、电子表格和其他生产力工作流的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `google-workspace` | 通过 Python 集成 Gmail、日历、云端硬盘、联系人、表格和文档。使用 OAuth2 自动令牌刷新。不需要外部二进制文件 — 完全在 Hermes venv 中使用 Google 的 Python 客户端库运行。 | `productivity/google-workspace` |
| `linear` | 通过 GraphQL API 管理 Linear 问题、项目和团队。创建、更新、搜索和组织问题。 | `productivity/linear` |
| `nano-pdf` | 使用 nano-pdf CLI 通过自然语言指令编辑 PDF。修改文本、修复拼写错误、更新标题，并对特定页面进行内容更改，无需手动编辑。 | `productivity/nano-pdf` |
| `notion` | Notion API，用于通过 curl 创建和管理页面、数据库和块。直接从终端搜索、创建、更新和查询 Notion 工作区。 | `productivity/notion` |
| `ocr-and-documents` | 从 PDF 和扫描文档中提取文本。对远程 URL 使用 web_extract，对本地基于文本的 PDF 使用 pymupdf，对 OCR/扫描文档使用 marker-pdf。对于 DOCX 使用 python-docx，对于 PPTX 请参阅 powerpoint 技能。 | `productivity/ocr-and-documents` |
| `powerpoint` | "任何时候涉及 .pptx 文件时使用此技能 — 作为输入、输出或两者。这包括：创建幻灯片、演示文稿或演示；读取、解析或从任何 .pptx 文件中提取文本（即使提取的内容将用于其他地方，例如在 a… | `productivity/powerpoint` |

## research

用于学术研究、论文发现、文献综述、领域侦察、市场数据、内容监控和科学知识检索的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `arxiv` | 使用 arXiv 的免费 REST API 搜索和检索学术论文。不需要 API 密钥。按关键字、作者、类别或 ID 搜索。与 web_extract 或 ocr-and-documents 技能结合使用，以阅读完整的论文内容。 | `research/arxiv` |
| `blogwatcher` | 使用 blogwatcher CLI 监控博客和 RSS/Atom 提要的更新。添加博客，扫描新文章，并跟踪您已阅读的内容。 | `research/blogwatcher` |
| `llm-wiki` | Karpathy 的 LLM Wiki — 构建和维护持久的、相互链接的 markdown 知识库。摄取源，查询编译的知识，并检查一致性。与 RAG 不同，wiki 一次编译知识并保持其更新。作为 Obsidian 保险库工作。Wiki 路径由 `WIKI_PATH` 环境变量控制（默认为 `~/wiki`）。 | `research/llm-wiki` |
| `domain-intel` | 使用 Python 标准库进行被动域侦察。子域发现、SSL 证书检查、WHOIS 查找、DNS 记录、域可用性检查和批量多域分析。不需要 API 密钥。 | `research/domain-intel` |
| `duckduckgo-search` | 通过 DuckDuckGo 进行免费网络搜索 — 文本、新闻、图像、视频。不需要 API 密钥。当安装时优先使用 `ddgs` CLI；仅在验证 `ddgs` 在当前运行时可用后才使用 Python DDGS 库。 | `research/duckduckgo-search` |
| `ml-paper-writing` | 为 NeurIPS、ICML、ICLR、ACL、AAAI、COLM 撰写出版级 ML/AI 论文。当从研究存储库起草论文、构建论点、验证引用或准备最终提交时使用。包括 LaTeX 模板、审稿人指南和引用验证… | `research/ml-paper-writing` |
| `polymarket` | 查询 Polymarket 预测市场数据 — 搜索市场，获取价格、订单簿和价格历史。通过公共 REST API 只读，不需要 API 密钥。 | `research/polymarket` |

## red-teaming

用于 LLM 红队、越狱和安全过滤器绕过研究的技能。

| 技能 | 描述 | 路径 |
|------|------|------|
| `godmode` | 使用 G0DM0D3 技术越狱 API 服务的 LLM — Parseltongue 输入混淆（33 种技术）、GODMODE CLASSIC 系统提示模板、ULTRAPLINIAN 多模型竞赛、编码升级和 Hermes 原生预填充/系统提示集成。适用于通过 API 访问的任何模型，包括闭源模型。 | `red-teaming/godmode` |

## smart-home

用于控制智能家居设备的技能 — 灯光、开关、传感器和家庭自动化系统。

| 技能 | 描述 | 路径 |
|------|------|------|
| `openhue` | 通过 OpenHue CLI 控制飞利浦 Hue 灯光、房间和场景。打开/关闭灯光，调整亮度、颜色、色温，并激活场景。 | `smart-home/openhue` |

## social-media

用于与社交平台交互的技能 — 发布、阅读、监控和账户操作。

| 技能 | 描述 | 路径 |
|------|------|------|
| `xitter` | 通过 x-cli 终端客户端使用官方 X API 凭据与 X/Twitter 交互。 | `social-media/xitter` |

## software-development

| 技能 | 描述 | 路径 |
|------|------|------|
| `code-review` | 执行以安全和质量为重点的彻底代码审查的指南 | `software-development/code-review` |
| `plan` | Hermes 的计划模式 — 检查上下文，将 markdown 计划写入活动工作区/后端工作目录中的 `.hermes/plans/`，并且不执行工作。 | `software-development/plan` |
| `requesting-code-review` | 完成任务、实现主要功能或合并之前使用。通过系统审查过程验证工作是否满足要求。 | `software-development/requesting-code-review` |
| `subagent-driven-development` | 执行具有独立任务的实施计划时使用。为每个任务分配新的 delegate_task，具有两阶段审查（规范合规性然后代码质量）。 | `software-development/subagent-driven-development` |
| `systematic-debugging` | 遇到任何错误、测试失败或意外行为时使用。4 阶段根本原因调查 — 在理解问题之前不进行修复。 | `software-development/systematic-debugging` |
| `test-driven-development` | 实现任何功能或错误修复时使用，在编写实现代码之前。通过测试优先方法强制执行 RED-GREEN-REFACTOR 循环。 | `software-development/test-driven-development` |
| `writing-plans` | 当您有多步骤任务的规范或要求时使用。创建全面的实施计划，包含小规模任务、确切的文件路径和完整的代码示例。 | `software-development/writing-plans` |

---

# 可选技能

可选技能随存储库一起提供，位于 `optional-skills/` 下，但**默认不激活**。它们涵盖更重或更小众的用例。使用以下命令安装它们：

```bash
hermes skills install official/<category>/<skill>
```

## autonomous-ai-agents

| 技能 | 描述 | 路径 |
|------|------|------|
| `blackbox` | 将编码任务委派给 Blackbox AI CLI 代理。多模型代理，内置法官，通过多个 LLM 运行任务并选择最佳结果。需要 blackbox CLI 和 Blackbox AI API 密钥。 | `autonomous-ai-agents/blackbox` |

## blockchain

| 技能 | 描述 | 路径 |
|------|------|------|
| `base` | 使用 USD 定价查询 Base（以太坊 L2）区块链数据 — 钱包余额、代币信息、交易详情、gas 分析、合约检查、鲸鱼检测和实时网络统计。使用 Base RPC + CoinGecko。不需要 API 密钥。 | `blockchain/base` |
| `solana` | 使用 USD 定价查询 Solana 区块链数据 — 钱包余额、带有价值的代币投资组合、交易详情、NFT、鲸鱼检测和实时网络统计。使用 Solana RPC + CoinGecko。不需要 API 密钥。 | `blockchain/solana` |

## creative

| 技能 | 描述 | 路径 |
|------|------|------|
| `blender-mcp` | 通过与 blender-mcp 插件的套接字连接直接从 Hermes 控制 Blender。创建 3D 对象、材质、动画，并运行任意 Blender Python (bpy) 代码。 | `creative/blender-mcp` |
| `meme-generation` | 通过选择模板并使用 Pillow 叠加文本生成真实的模因图像。生成实际的 .png 模因文件。 | `creative/meme-generation` |

## devops

| 技能 | 描述 | 路径 |
|------|------|------|
| `docker-management` | 管理 Docker 容器、镜像、卷、网络和 Compose 堆栈 — 生命周期操作、调试、清理和 Dockerfile 优化。 | `devops/docker-management` |

## email

| 技能 | 描述 | 路径 |
|------|------|------|
| `agentmail` | 通过 AgentMail 为代理提供自己的专用电子邮件收件箱。使用代理拥有的电子邮件地址（例如 hermes-agent@agentmail.to）自主发送、接收和管理电子邮件。 | `email/agentmail` |

## health

| 技能 | 描述 | 路径 |
|------|------|------|
| `neuroskill-bci` | 连接到运行中的 NeuroSkill 实例，并将用户的实时认知和情绪状态（专注、放松、情绪、认知负荷、睡意、心率、HRV、睡眠分期和 40+ 派生 EXG 分数）纳入响应。需要 BCI 可穿戴设备（Muse 2/S 或 OpenBCI）和 NeuroSkill 桌面应用程序。 | `health/neuroskill-bci` |

## mcp

| 技能 | 描述 | 路径 |
|------|------|------|
| `fastmcp` | 使用 FastMCP 在 Python 中构建、测试、检查、安装和部署 MCP 服务器。当创建新的 MCP 服务器、将 API 或数据库包装为 MCP 工具、公开资源或提示，或准备 FastMCP 服务器进行 HTTP 部署时使用。 | `mcp/fastmcp` |

## migration

| 技能 | 描述 | 路径 |
|------|------|------|
| `openclaw-migration` | 将用户的 OpenClaw 自定义足迹迁移到 Hermes Agent。从 ~/.openclaw 导入与 Hermes 兼容的记忆、SOUL.md、命令允许列表、用户技能和选定的工作区资产，然后报告无法迁移的内容及其原因。 | `migration/openclaw-migration` |

## productivity

| 技能 | 描述 | 路径 |
|------|------|------|
| `telephony` | 为 Hermes 提供电话功能 — 配置并持久化 Twilio 号码，发送和接收 SMS/MMS，直接拨打电话，通过 Bland.ai 或 Vapi 拨出 AI 驱动的外呼电话。 | `productivity/telephony` |

## research

| 技能 | 描述 | 路径 |
|------|------|------|
| `bioinformatics` | 来自 bioSkills 和 ClawBio 的 400+ 生物信息学技能的门户。涵盖基因组学、转录组学、单细胞、变异 calling、药物基因组学、宏基因组学、结构生物学等。 | `research/bioinformatics` |
| `qmd` | 使用 qmd（具有 BM25、向量搜索和 LLM 重排序的混合检索引擎）在本地搜索个人知识库、笔记、文档和会议记录。支持 CLI 和 MCP 集成。 | `research/qmd` |

## security

| 技能 | 描述 | 路径 |
|------|------|------|
| `1password` | 设置和使用 1Password CLI (op)。当安装 CLI、启用桌面应用程序集成、登录以及读取/注入命令密钥时使用。 | `security/1password` |
| `oss-forensics` | GitHub 存储库的供应链调查、证据恢复和取证分析。涵盖删除的提交恢复、强制推送检测、IOC 提取、多源证据收集和结构化取证报告。 | `security/oss-forensics` |
| `sherlock` | 跨 400+ 社交网络的 OSINT 用户名搜索。通过用户名搜索社交媒体账户。 | `security/sherlock` |