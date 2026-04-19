---
sidebar_position: 9
title: "可选技能目录"
description: "随 hermes-agent 提供的官方可选技能 — 通过 hermes skills install official/<category>/<skill> 安装"
---

# 可选技能目录

官方可选技能随 hermes-agent 仓库提供，位于 `optional-skills/` 下，但**默认不激活**。请显式安装它们：

```bash
hermes skills install official/<category>/<skill>
```

例如：

```bash
hermes skills install official/blockchain/solana
hermes skills install official/mlops/flash-attention
```

安装后，技能会出现在智能体的技能列表中，并可以在检测到相关任务时自动加载。

要卸载：

```bash
hermes skills uninstall <skill-name>
```

---

## 自主 AI 智能体

| 技能 | 描述 |
|-------|-------------|
| **blackbox** | 将编码任务委托给 Blackbox AI CLI 智能体。具有内置评判器的多模型智能体，通过多个 LLM 运行任务并选择最佳结果。 |
| **honcho** | 配置和使用 Honcho 内存与 Hermes — 跨会话用户建模、多配置文件对等隔离、观察配置和辩证推理。 |

## 区块链

| 技能 | 描述 |
|-------|-------------|
| **base** | 查询 Base（以太坊 L2）区块链数据，带美元定价 — 钱包余额、代币信息、交易详情、燃气分析、合约检查、鲸鱼检测和实时网络统计。无需 API 密钥。 |
| **solana** | 查询 Solana 区块链数据，带美元定价 — 钱包余额、代币组合、交易详情、NFT、鲸鱼检测和实时网络统计。无需 API 密钥。 |

## 通信

| 技能 | 描述 |
|-------|-------------|
| **one-three-one-rule** | 用于提案和决策的结构化通信框架。 |

## 创意

| 技能 | 描述 |
|-------|-------------|
| **blender-mcp** | 通过与 blender-mcp 插件的套接字连接直接从 Hermes 控制 Blender。创建 3D 对象、材质、动画，并运行任意 Blender Python (bpy) 代码。 |
| **meme-generation** | 通过选择模板并使用 Pillow 覆盖文本生成真实的 meme 图像。生成实际的 `.png` meme 文件。 |

## DevOps

| 技能 | 描述 |
|-------|-------------|
| **cli** | 通过 inference.sh CLI (infsh) 运行 150+ AI 应用 — 图像生成、视频创建、LLM、搜索、3D 和社交自动化。 |
| **docker-management** | 管理 Docker 容器、镜像、卷、网络和 Compose 堆栈 — 生命周期操作、调试、清理和 Dockerfile 优化。 |

## 电子邮件

| 技能 | 描述 |
|-------|-------------|
| **agentmail** | 通过 AgentMail 给智能体提供自己的专用电子邮件收件箱。使用智能体拥有的电子邮件地址自主发送、接收和管理电子邮件。 |

## 健康

| 技能 | 描述 |
|-------|-------------|
| **neuroskill-bci** | 用于神经科学研究工作流程的脑机接口 (BCI) 集成。 |

## MCP

| 技能 | 描述 |
|-------|-------------|
| **fastmcp** | 使用 FastMCP 在 Python 中构建、测试、检查、安装和部署 MCP 服务器。涵盖将 API 或数据库包装为 MCP 工具、公开资源或提示，以及部署。 |

## 迁移

| 技能 | 描述 |
|-------|-------------|
| **openclaw-migration** | 将用户的 OpenClaw 自定义足迹迁移到 Hermes Agent。导入记忆、SOUL.md、命令允许列表、用户技能和选定的工作区资产。 |

## MLOps

最大的可选类别 — 涵盖从数据整理到生产推理的完整 ML 管道。

| 技能 | 描述 |
|-------|-------------|
| **accelerate** | 最简单的分布式训练 API。4 行代码即可为任何 PyTorch 脚本添加分布式支持。DeepSpeed/FSDP/Megatron/DDP 的统一 API。 |
| **chroma** | 开源嵌入数据库。存储嵌入和元数据，执行向量和全文搜索。用于 RAG 和语义搜索的简单 4 函数 API。 |
| **faiss** | Facebook 的高效相似性搜索和密集向量聚类库。支持数十亿向量、GPU 加速和各种索引类型（Flat、IVF、HNSW）。 |
| **flash-attention** | 使用 Flash Attention 优化 Transformer 注意力，实现 2-4 倍速度提升和 10-20 倍内存减少。支持 PyTorch SDPA、flash-attn 库、H100 FP8 和滑动窗口。 |
| **hermes-atropos-environments** | 为 Atropos 训练构建、测试和调试 Hermes Agent RL 环境。涵盖 HermesAgentBaseEnv 接口、奖励函数、智能体循环集成和评估。 |
| **huggingface-tokenizers** | 用于研究和生产的快速 Rust 基础分词器。在 20 秒内分词 1GB。支持 BPE、WordPiece 和 Unigram 算法。 |
| **instructor** | 使用 Pydantic 验证从 LLM 响应中提取结构化数据，自动重试失败的提取，并流式传输部分结果。 |
| **lambda-labs** | 用于 ML 训练和推理的预留和按需 GPU 云实例。SSH 访问、持久文件系统和多节点集群。 |
| **llava** | 大型语言和视觉助手 — 视觉指令调整和基于图像的对话，结合 CLIP 视觉和 LLaMA 语言模型。 |
| **nemo-curator** | 用于 LLM 训练的 GPU 加速数据整理。模糊去重（快 16 倍）、质量过滤（30+ 启发式）、语义去重、PII 编辑。通过 RAPIDS 扩展。 |
| **pinecone** | 用于生产 AI 的托管向量数据库。自动扩展、混合搜索（密集 + 稀疏）、元数据过滤和低延迟（p95 低于 100ms）。 |
| **pytorch-lightning** | 高级 PyTorch 框架，具有 Trainer 类、自动分布式训练（DDP/FSDP/DeepSpeed）、回调和最小样板代码。 |
| **qdrant** | 高性能向量相似性搜索引擎。由 Rust 驱动，具有快速最近邻搜索、带过滤的混合搜索和可扩展向量存储。 |
| **saelens** | 使用 SAELens 训练和分析稀疏自编码器 (SAE)，将神经网络激活分解为可解释特征。 |
| **simpo** | 简单偏好优化 — DPO 的无参考替代方案，性能更好（AlpacaEval 2.0 上 +6.4 分）。无需参考模型。 |
| **slime** | 使用 Megatron+SGLang 框架通过 RL 进行 LLM 后训练。自定义数据生成工作流程和与 Megatron-LM 的紧密集成用于 RL 扩展。 |
| **tensorrt-llm** | 使用 NVIDIA TensorRT 优化 LLM 推理以获得最大吞吐量。在 A100/H100 上通过量化（FP8/INT4）和飞行中批处理比 PyTorch 快 10-100 倍。 |
| **torchtitan** | PyTorch 原生分布式 LLM 预训练，具有 4D 并行性（FSDP2、TP、PP、CP）。使用 Float8 和 torch.compile 从 8 扩展到 512+ GPU。 |

## 生产力

| 技能 | 描述 |
|-------|-------------|
| **canvas** | Canvas LMS 集成 — 使用 API 令牌认证获取已注册课程和作业。 |
| **memento-flashcards** | 用于学习和知识保留的间隔重复闪卡系统。 |
| **siyuan** | SiYuan 笔记 API，用于在自托管知识库中搜索、阅读、创建和管理块和文档。 |
| **telephony** | 为 Hermes 提供电话功能 — 配置 Twilio 号码、发送/接收 SMS/MMS、拨打电话，以及通过 Bland.ai 或 Vapi 进行 AI 驱动的外呼。 |

## 研究

| 技能 | 描述 |
|-------|-------------|
| **bioinformatics** | 来自 bioSkills 和 ClawBio 的 400+ 生物信息学技能的网关。涵盖基因组学、转录组学、单细胞、变异 calling、药物基因组学、宏基因组学和结构生物学。 |
| **domain-intel** | 使用 Python 标准库进行被动域名侦察。子域名发现、SSL 证书检查、WHOIS 查找、DNS 记录和批量多域名分析。无需 API 密钥。 |
| **duckduckgo-search** | 通过 DuckDuckGo 进行免费网络搜索 — 文本、新闻、图像、视频。无需 API 密钥。 |
| **gitnexus-explorer** | 使用 GitNexus 索引代码库并通过 Web UI 和 Cloudflare 隧道提供交互式知识图谱。 |
| **parallel-cli** | Parallel CLI 的供应商技能 — 智能体原生网络搜索、提取、深度研究、丰富和监控。 |
| **qmd** | 使用 qmd 在本地搜索个人知识库、笔记、文档和会议记录 — 具有 BM25、向量搜索和 LLM 重排序的混合检索引擎。 |
| **scrapling** | 使用 Scrapling 进行网络抓取 — HTTP 获取、隐身浏览器自动化、Cloudflare 绕过和通过 CLI 和 Python 进行蜘蛛爬行。 |

## 安全

| 技能 | 描述 |
|-------|-------------|
| **1password** | 设置和使用 1Password CLI (op)。安装 CLI，启用桌面应用集成，登录，并为命令读取/注入密钥。 |
| **oss-forensics** | 开源软件取证 — 分析包、依赖项和供应链风险。 |
| **sherlock** | 跨 400+ 社交网络的 OSINT 用户名搜索。通过用户名查找社交媒体账户。 |

---

## 贡献可选技能

要向仓库添加新的可选技能：

1. 在 `optional-skills/<category>/<skill-name>/` 下创建目录
2. 添加带有标准前置内容（名称、描述、版本、作者）的 `SKILL.md`
3. 在 `references/`、`templates/` 或 `scripts/` 子目录中包含任何支持文件
4. 提交拉取请求 — 技能在合并后会出现在此目录中