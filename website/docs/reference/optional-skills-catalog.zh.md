---
sidebar_position: 9
title: "可选技能目录"
description: "随 hermes-agent 一起提供的官方可选技能 — 通过 hermes skills install official/<category>/<skill> 安装"
---

# 可选技能目录

官方可选技能随 hermes-agent 仓库一起提供在 `optional-skills/` 下，但**默认不活跃**。请显式安装它们：

```bash
hermes skills install official/<category>/<skill>
```

例如：

```bash
hermes skills install official/blockchain/solana
hermes skills install official/mlops/flash-attention
```

安装后，技能会出现在代理的技能列表中，并且可以在检测到相关任务时自动加载。

要卸载：

```bash
hermes skills uninstall <skill-name>
```

---

## 自主 AI 代理

| 技能 | 描述 |
|-------|-------------|
| **blackbox** | 将编码任务委托给 Blackbox AI CLI 代理。多模型代理，内置评判器，通过多个 LLM 运行任务并选择最佳结果。 |
| **honcho** | 配置并在 Hermes 中使用 Honcho 内存 — 跨会话用户建模、多配置文件对等隔离、观察配置和辩证推理。 |

## 区块链

| 技能 | 描述 |
|-------|-------------|
| **base** | 使用 USD 定价查询 Base (Ethereum L2) 区块链数据 — 钱包余额、代币信息、交易详情、 gas 分析、合约检查、鲸鱼检测和实时网络统计。无需 API 密钥。 |
| **solana** | 使用 USD 定价查询 Solana 区块链数据 — 钱包余额、代币投资组合、交易详情、NFT、鲸鱼检测和实时网络统计。无需 API 密钥。 |

## 通信

| 技能 | 描述 |
|-------|-------------|
| **one-three-one-rule** | 用于提案和决策的结构化沟通框架。 |

## 创意

| 技能 | 描述 |
|-------|-------------|
| **blender-mcp** | 通过与 blender-mcp 插件的套接字连接直接从 Hermes 控制 Blender。创建 3D 对象、材质、动画，并运行任意 Blender Python (bpy) 代码。 |
| **concept-diagrams** | 生成扁平、最小化的明暗感知 SVG 图表作为独立 HTML 文件，使用统一的教育视觉语言（9 种语义色彩渐变，自动暗色模式）。最适合物理设置、化学机制、数学曲线、物理对象（飞机、涡轮机、智能手机）、平面图、横截面、生命周期/过程叙述和中心辐射系统图。附带 15 个示例图表。 |
| **meme-generation** | 通过选择模板并使用 Pillow 覆盖文本生成真实的模因图像。生成实际的 `.png` 模因文件。 |

## DevOps

| 技能 | 描述 |
|-------|-------------|
| **cli** | 通过 inference.sh CLI (infsh) 运行 150+ AI 应用 — 图像生成、视频创建、LLM、搜索、3D 和社交自动化。 |
| **docker-management** | 管理 Docker 容器、镜像、卷、网络和 Compose 堆栈 — 生命周期操作、调试、清理和 Dockerfile 优化。 |

## 电子邮件

| 技能 | 描述 |
|-------|-------------|
| **agentmail** | 通过 AgentMail 为代理提供自己的专用电子邮件收件箱。使用代理拥有的电子邮件地址自主发送、接收和管理电子邮件。 |

## 健康

| 技能 | 描述 |
|-------|-------------|
| **neuroskill-bci** | 用于神经科学研究工作流的脑机接口 (BCI) 集成。 |

## MCP

| 技能 | 描述 |
|-------|-------------|
| **fastmcp** | 使用 Python 中的 FastMCP 构建、测试、检查、安装和部署 MCP 服务器。涵盖将 API 或数据库包装为 MCP 工具、公开资源或提示，以及部署。 |

## 迁移

| 技能 | 描述 |
|-------|-------------|
| **openclaw-migration** | 将用户的 OpenClaw 自定义内容迁移到 Hermes Agent。导入记忆、SOUL.md、命令允许列表、用户技能和选定的工作区资产。 |

## MLOps

最大的可选类别 — 涵盖从数据策划到生产推理的完整 ML 管道。

| 技能 | 描述 |
|-------|-------------|
| **accelerate** | 最简单的分布式训练 API。4 行代码为任何 PyTorch 脚本添加分布式支持。DeepSpeed/FSDP/Megatron/DDP 的统一 API。 |
| **chroma** | 开源嵌入数据库。存储嵌入和元数据，执行向量和全文搜索。用于 RAG 和语义搜索的简单 4 函数 API。 |
| **faiss** | Facebook 的高效相似性搜索和密集向量聚类库。支持数十亿个向量、GPU 加速和各种索引类型（Flat、IVF、HNSW）。 |
| **flash-attention** | 使用 Flash Attention 优化 transformer 注意力，速度提高 2-4 倍，内存减少 10-20 倍。支持 PyTorch SDPA、flash-attn 库、H100 FP8 和滑动窗口。 |
| **guidance** | 使用正则表达式和语法控制 LLM 输出，保证有效的 JSON/XML/代码生成，强制结构化格式，并使用 Guidance（Microsoft Research 的约束生成框架）构建多步骤工作流。 |
| **hermes-atropos-environments** | 为 Atropos 训练构建、测试和调试 Hermes Agent RL 环境。涵盖 HermesAgentBaseEnv 接口、奖励函数、代理循环集成和评估。 |
| **huggingface-tokenizers** | 用于研究和生产的快速基于 Rust 的分词器。在不到 20 秒内分词 1GB。支持 BPE、WordPiece 和 Unigram 算法。 |
| **instructor** | 使用 Pydantic 验证从 LLM 响应中提取结构化数据，自动重试失败的提取，并流式传输部分结果。 |
| **lambda-labs** | 用于 ML 训练和推理的预留和按需 GPU 云实例。SSH 访问、持久文件系统和多节点集群。 |
| **llava** | 大型语言和视觉助手 — 结合 CLIP 视觉和 LLaMA 语言模型的视觉指令调优和基于图像的对话。 |
| **nemo-curator** | 用于 LLM 训练的 GPU 加速数据策划。模糊去重（快 16 倍）、质量过滤（30+ 启发式）、语义去重、PII 脱敏。随 RAPIDS 扩展。 |
| **pinecone** | 用于生产 AI 的托管向量数据库。自动扩展、混合搜索（密集 + 稀疏）、元数据过滤和低延迟（p95 低于 100ms）。 |
| **pytorch-lightning** | 高级 PyTorch 框架，带有 Trainer 类、自动分布式训练（DDP/FSDP/DeepSpeed）、回调和最小样板代码。 |
| **qdrant** | 高性能向量相似性搜索引擎。由 Rust 驱动，具有快速最近邻搜索、带过滤的混合搜索和可扩展向量存储。 |
| **saelens** | 使用 SAELens 训练和分析稀疏自动编码器 (SAE)，将神经网络激活分解为可解释的特征。 |
| **simpo** | 简单偏好优化 — 比 DPO 性能更好的无参考替代方案（在 AlpacaEval 2.0 上 +6.4 分）。不需要参考模型。 |
| **slime** | 使用 Megatron+SGLang 框架通过 RL 进行 LLM 后训练。自定义数据生成工作流和与 Megatron-LM 的紧密集成以实现 RL 扩展。 |
| **tensorrt-llm** | 使用 NVIDIA TensorRT 优化 LLM 推理以获得最大吞吐量。在 A100/H100 上通过量化（FP8/INT4）和飞行中批处理比 PyTorch 快 10-100 倍。 |
| **torchtitan** | 具有 4D 并行性（FSDP2、TP、PP、CP）的 PyTorch 原生分布式 LLM 预训练。通过 Float8 和 torch.compile 从 8 扩展到 512+ GPU。 |

## 生产力

| 技能 | 描述 |
|-------|-------------|
| **canvas** | Canvas LMS 集成 — 使用 API 令牌认证获取已注册的课程和作业。 |
| **memento-flashcards** | 用于学习和知识保留的间隔重复抽认卡系统。 |
| **siyuan** | SiYuan 笔记 API，用于在自托管知识库中搜索、阅读、创建和管理块和文档。 |
| **telephony** | 为 Hermes 提供电话功能 — 配置 Twilio 号码、发送/接收 SMS/MMS、拨打电话，并通过 Bland.ai 或 Vapi 进行 AI 驱动的外呼。 |

## 研究

| 技能 | 描述 |
|-------|-------------|
| **bioinformatics** | 来自 bioSkills 和 ClawBio 的 400+ 生物信息学技能的网关。涵盖基因组学、转录组学、单细胞、变异 calling、药物基因组学、宏基因组学和结构生物学。 |
| **domain-intel** | 使用 Python 标准库进行被动域名侦察。子域名发现、SSL 证书检查、WHOIS 查找、DNS 记录和批量多域名分析。无需 API 密钥。 |
| **duckduckgo-search** | 通过 DuckDuckGo 进行免费网络搜索 — 文本、新闻、图像、视频。无需 API 密钥。 |
| **gitnexus-explorer** | 使用 GitNexus 索引代码库并通过 Web UI 和 Cloudflare 隧道提供交互式知识图谱。 |
| **parallel-cli** | Parallel CLI 的供应商技能 — 代理原生网络搜索、提取、深度研究、丰富和监控。 |
| **qmd** | 使用 qmd（具有 BM25、向量搜索和 LLM 重排序的混合检索引擎）本地搜索个人知识库、笔记、文档和会议记录。 |
| **scrapling** | 使用 Scrapling 进行网络抓取 — HTTP 获取、隐身浏览器自动化、Cloudflare 绕过和通过 CLI 和 Python 进行蜘蛛爬取。 |

## 安全

| 技能 | 描述 |
|-------|-------------|
| **1password** | 设置和使用 1Password CLI (op)。安装 CLI，启用桌面应用集成，登录，并为命令读取/注入密钥。 |
| **oss-forensics** | 开源软件取证 — 分析包、依赖项和供应链风险。 |
| **sherlock** | 跨 400+ 社交网络的 OSINT 用户名搜索。通过用户名追踪社交媒体账户。 |

---

## 贡献可选技能

要向存储库添加新的可选技能：

1. 在 `optional-skills/<category>/<skill-name>/` 下创建目录
2. 添加带有标准前置内容（名称、描述、版本、作者）的 `SKILL.md`
3. 在 `references/`、`templates/` 或 `scripts/` 子目录中包含任何支持文件
4. 提交拉取请求 — 技能合并后将出现在此目录中