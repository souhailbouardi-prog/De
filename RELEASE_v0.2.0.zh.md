# Hermes Agent v0.2.0 (v2026.3.12)

**发布日期：** 2026年3月12日

> 自 v0.1.0（初始预公开基础版本）以来的第一个标记发布。在短短两周多的时间里，Hermes Agent 从一个小型内部项目发展成为一个功能齐全的 AI 代理平台 — 这要归功于社区贡献的爆发式增长。此版本涵盖了来自 **63 位贡献者**的 **216 个合并拉取请求**，解决了 **119 个问题**。

---

## ✨ 亮点

- **多平台消息传递网关** — Telegram、Discord、Slack、WhatsApp、Signal、电子邮件（IMAP/SMTP）和 Home Assistant 平台，具有统一的会话管理、媒体附件和每个平台的工具配置。

- **MCP（模型上下文协议）客户端** — 原生 MCP 支持，具有 stdio 和 HTTP 传输、重连、资源/提示发现和采样（服务器发起的 LLM 请求）。([#291](https://github.com/NousResearch/hermes-agent/pull/291) — @0xbyt4, [#301](https://github.com/NousResearch/hermes-agent/pull/301), [#753](https://github.com/NousResearch/hermes-agent/pull/753))

- **技能生态系统** — 15+ 类别中的 70+ 捆绑和可选技能，带有技能中心用于社区发现、每个平台的启用/禁用、基于工具可用性的条件激活以及先决条件验证。([#743](https://github.com/NousResearch/hermes-agent/pull/743) — @teyrebaz33, [#785](https://github.com/NousResearch/hermes-agent/pull/785) — @teyrebaz33)

- **集中式提供商路由器** — 统一的 `call_llm()`/`async_call_llm()` API 取代了分散在视觉、摘要、压缩和轨迹保存中的提供商逻辑。所有辅助消费者通过单一代码路径路由，具有自动凭据解析。([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))

- **ACP 服务器** — 通过代理通信协议标准集成 VS Code、Zed 和 JetBrains 编辑器。([#949](https://github.com/NousResearch/hermes-agent/pull/949))

- **CLI 皮肤/主题引擎** — 数据驱动的视觉定制：横幅、微调器、颜色、品牌。7 个内置皮肤 + 自定义 YAML 皮肤。

- **Git 工作树隔离** — `hermes -w` 在 git 工作树中启动隔离的代理会话，以便在同一 repo 上安全并行工作。([#654](https://github.com/NousResearch/hermes-agent/pull/654))

- **文件系统检查点和回滚** — 破坏性操作前的自动快照，使用 `/rollback` 恢复。([#824](https://github.com/NousResearch/hermes-agent/pull/824))

- **3,289 个测试** — 从几乎零测试覆盖率到涵盖代理、网关、工具、cron 和 CLI 的全面测试套件。

---

## 🏗️ 核心代理与架构

### 提供商和模型支持
- 具有 `resolve_provider_client()` + `call_llm()` API 的集中式提供商路由器 ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))
- Nous Portal 作为设置中的一等提供商 ([#644](https://github.com/NousResearch/hermes-agent/issues/644))
- OpenAI Codex（Responses API），支持 ChatGPT 订阅 ([#43](https://github.com/NousResearch/hermes-agent/pull/43)) — @grp06
- Codex OAuth 视觉支持 + 多模态内容适配器
- 针对实时 API 验证 `/model`，而不是硬编码列表
- 自托管 Firecrawl 支持 ([#460](https://github.com/NousResearch/hermes-agent/pull/460)) — @caentzminger
- Kimi Code API 支持 ([#635](https://github.com/NousResearch/hermes-agent/pull/635)) — @christomitov
- MiniMax 模型 ID 更新 ([#473](https://github.com/NousResearch/hermes-agent/pull/473)) — @tars90percent
- OpenRouter 提供商路由配置（provider_preferences）
- 401 错误时的 Nous 凭据刷新 ([#571](https://github.com/NousResearch/hermes-agent/pull/571), [#269](https://github.com/NousResearch/hermes-agent/pull/269)) — @rewbs
- z.ai/GLM、Kimi/Moonshot、MiniMax、Azure OpenAI 作为一等提供商
- 将 `/model` 和 `/provider` 统一为单一视图

### 代理循环与对话
- 用于提供商弹性的简单回退模型 ([#740](https://github.com/NousResearch/hermes-agent/pull/740))
- 跨父级 + 子代理委托的共享迭代预算
- 通过工具结果注入的迭代预算压力
- 可配置的子代理提供商/模型，具有完整的凭据解析
- 通过压缩处理 413 payload-too-large，而不是中止 ([#153](https://github.com/NousResearch/hermes-agent/pull/153)) — @tekelala
- 压缩后重试重建的负载 ([#616](https://github.com/NousResearch/hermes-agent/pull/616)) — @tripledoublev
- 自动压缩病理上大型网关会话 ([#628](https://github.com/NousResearch/hermes-agent/issues/628))
- 工具调用修复中间件 — 自动小写和无效工具处理程序
- 推理努力配置和 `/reasoning` 命令 ([#921](https://github.com/NousResearch/hermes-agent/pull/921))
- 检测并阻止上下文压缩后的文件重读/搜索循环 ([#705](https://github.com/NousResearch/hermes-agent/pull/705)) — @0xbyt4

### 会话与内存
- 具有唯一标题、自动谱系、丰富列表和按名称恢复的会话命名 ([#720](https://github.com/NousResearch/hermes-agent/pull/720))
- 具有搜索过滤的交互式会话浏览器 ([#733](https://github.com/NousResearch/hermes-agent/pull/733))
- 恢复会话时显示以前的消息 ([#734](https://github.com/NousResearch/hermes-agent/pull/734))
- Honcho AI 原生跨会话用户建模 ([#38](https://github.com/NousResearch/hermes-agent/pull/38)) — @erosika
- 会话到期时的主动异步内存刷新
- 智能上下文长度探测，具有持久缓存 + 横幅显示
- 网关中用于切换到命名会话的 `/resume` 命令
- 消息平台的会话重置策略

---

## 📱 消息平台（网关）

### Telegram
- 原生文件附件：send_document + send_video
- PDF、文本和 Office 文件的文档文件处理 — @tekelala
- 论坛主题会话隔离 ([#766](https://github.com/NousResearch/hermes-agent/pull/766)) — @spanishflu-est1918
- 通过 MEDIA: 协议的浏览器截图共享 ([#657](https://github.com/NousResearch/hermes-agent/pull/657))
- 附近查找技能的位置支持
- TTS 语音消息累积修复 ([#176](https://github.com/NousResearch/hermes-agent/pull/176)) — @Bartok9
- 改进的错误处理和日志记录 ([#763](https://github.com/NousResearch/hermes-agent/pull/763)) — @aydnOktay
- 斜体正则表达式换行修复 + 43 个格式测试 ([#204](https://github.com/NousResearch/hermes-agent/pull/204)) — @0xbyt4

### Discord
- 会话上下文中包含的频道主题 ([#248](https://github.com/NousResearch/hermes-agent/pull/248)) — @Bartok9
- 用于机器人消息过滤的 DISCORD_ALLOW_BOTS 配置 ([#758](https://github.com/NousResearch/hermes-agent/pull/758))
- 文档和视频支持 ([#784](https://github.com/NousResearch/hermes-agent/pull/784))
- 改进的错误处理和日志记录 ([#761](https://github.com/NousResearch/hermes-agent/pull/761)) — @aydnOktay

### Slack
- App_mention 404 修复 + 文档/视频支持 ([#784](https://github.com/NousResearch/hermes-agent/pull/784))
- 结构化日志记录替换打印语句 — @aydnOktay

### WhatsApp
- 原生媒体发送 — 图像、视频、文档 ([#292](https://github.com/NousResearch/hermes-agent/pull/292)) — @satelerd
- 多用户会话隔离 ([#75](https://github.com/NousResearch/hermes-agent/pull/75)) — @satelerd
- 跨平台端口清理，替换仅限 Linux 的 fuser ([#433](https://github.com/NousResearch/hermes-agent/pull/433)) — @Farukest
- DM 中断键不匹配修复 ([#350](https://github.com/NousResearch/hermes-agent/pull/350)) — @Farukest

### Signal
- 通过 signal-cli-rest-api 的完整 Signal 信使网关 ([#405](https://github.com/NousResearch/hermes-agent/issues/405))
- 消息事件中的媒体 URL 支持 ([#871](https://github.com/NousResearch/hermes-agent/pull/871))

### 电子邮件（IMAP/SMTP）
- 新的电子邮件网关平台 — @0xbyt4

### Home Assistant
- REST 工具 + WebSocket 网关集成 ([#184](https://github.com/NousResearch/hermes-agent/pull/184)) — @0xbyt4
- 服务发现和增强设置
- 工具集映射修复 ([#538](https://github.com/NousResearch/hermes-agent/pull/538)) — @Himess

### 网关核心
- 向用户公开子代理工具调用和思考 ([#186](https://github.com/NousResearch/hermes-agent/pull/186)) — @cutepawss
- 可配置的后台进程监视器通知 ([#840](https://github.com/NousResearch/hermes-agent/pull/840))
- Telegram/Discord/Slack 的 `edit_message()` 带有回退
- `/compress`、`/usage`、`/update` 斜杠命令
- 消除网关会话中的 3x SQLite 消息重复 ([#873](https://github.com/NousResearch/hermes-agent/pull/873))
- 稳定网关轮次的系统提示以获得缓存命中 ([#754](https://github.com/NousResearch/hermes-agent/pull/754))
- 网关退出时的 MCP 服务器关闭 ([#796](https://github.com/NousResearch/hermes-agent/pull/796)) — @0xbyt4
- 将 session_db 传递给 AIAgent，修复 session_search 错误 ([#108](https://github.com/NousResearch/hermes-agent/pull/108)) — @Bartok9
- 在 /retry、/undo 中持久化转录更改；修复 /reset 属性 ([#217](https://github.com/NousResearch/hermes-agent/pull/217)) — @Farukest
- 防止 Windows 崩溃的 UTF-8 编码修复 ([#369](https://github.com/NousResearch/hermes-agent/pull/369)) — @ch3ronsa

---

## 🖥️ CLI 与用户体验

### 交互式 CLI
- 数据驱动的皮肤/主题引擎 — 7 个内置皮肤（default、ares、mono、slate、poseidon、sisyphus、charizard）+ 自定义 YAML 皮肤
- `/personality` 命令，支持自定义个性 + 禁用 ([#773](https://github.com/NousResearch/hermes-agent/pull/773)) — @teyrebaz33
- 绕过代理循环的用户定义快速命令 ([#746](https://github.com/NousResearch/hermes-agent/pull/746)) — @teyrebaz33
- `/reasoning` 命令，用于努力级别和显示切换 ([#921](https://github.com/NousResearch/hermes-agent/pull/921))
- `/verbose` 斜杠命令，用于在运行时切换调试 ([#94](https://github.com/NousResearch/hermes-agent/pull/94)) — @cesareth
- `/insights` 命令 — 使用分析、成本估算和活动模式 ([#552](https://github.com/NousResearch/hermes-agent/pull/552))
- `/background` 命令，用于管理后台进程
- 带有命令类别的 `/help` 格式化
- Bell-on-complete — 代理完成时的终端铃声 ([#738](https://github.com/NousResearch/hermes-agent/pull/738))
- 上下箭头历史导航
- 剪贴板图像粘贴（Alt+V / Ctrl+V）
- 缓慢斜杠命令的加载指示器 ([#882](https://github.com/NousResearch/hermes-agent/pull/882))
- patch_stdout 下的微调器闪烁修复 ([#91](https://github.com/NousResearch/hermes-agent/pull/91)) — @0xbyt4
- 用于编程单一查询模式的 `--quiet/-Q` 标志
- 绕过所有批准提示的 `--fuck-it-ship-it` 标志 ([#724](https://github.com/NousResearch/hermes-agent/pull/724)) — @dmahan93
- 工具摘要标志 ([#767](https://github.com/NousResearch/hermes-agent/pull/767)) — @luisv-1
- SSH 上的终端闪烁修复 ([#284](https://github.com/NousResearch/hermes-agent/pull/284)) — @ygd58
- 多行粘贴检测修复 ([#84](https://github.com/NousResearch/hermes-agent/pull/84)) — @0xbyt4

### 设置与配置
- 模块化设置向导，具有部分子命令和工具优先 UX
- 容器资源配置提示
- 所需二进制文件的后端验证
- 配置迁移系统（当前 v7）
- API 密钥正确路由到 .env 而不是 config.yaml ([#469](https://github.com/NousResearch/hermes-agent/pull/469)) — @ygd58
- .env 的原子写入，防止崩溃时 API 密钥丢失 ([#954](https://github.com/NousResearch/hermes-agent/pull/954))
- `hermes tools` — 带有 curses UI 的每个平台工具启用/禁用
- `hermes doctor` 用于所有配置提供商的健康检查
- `hermes update` 带有网关服务的自动重启
- CLI 横幅中显示更新可用通知
- 多个命名的自定义提供商
- PATH 设置的 shell 配置检测改进 ([#317](https://github.com/NousResearch/hermes-agent/pull/317)) — @mehmetkr-31
- 一致的 HERMES_HOME 和 .env 路径解析 ([#51](https://github.com/NousResearch/hermes-agent/pull/51), [#48](https://github.com/NousResearch/hermes-agent/pull/48)) — @deankerr
- macOS 上的 Docker 后端修复 + Nous Portal 的子代理身份验证 ([#46](https://github.com/NousResearch/hermes-agent/pull/46)) — @rsavitt

---

## 🔧 工具系统

### MCP（模型上下文协议）
- 具有 stdio + HTTP 传输的原生 MCP 客户端 ([#291](https://github.com/NousResearch/hermes-agent/pull/291) — @0xbyt4, [#301](https://github.com/NousResearch/hermes-agent/pull/301))
- 采样支持 — 服务器发起的 LLM 请求 ([#753](https://github.com/NousResearch/hermes-agent/pull/753))
- 资源和提示发现
- 自动重连和安全加固
- 横幅集成，`/reload-mcp` 命令
- `hermes tools` UI 集成

### 浏览器
- 本地浏览器后端 — 零成本无头 Chromium（不需要 Browserbase）
- 控制台/错误工具、带注释的截图、自动录制、dogfood QA 技能 ([#745](https://github.com/NousResearch/hermes-agent/pull/745))
- 通过 MEDIA: 在所有消息平台上共享截图 ([#657](https://github.com/NousResearch/hermes-agent/pull/657))

### 终端与执行
- 带有 json_parse、shell_quote、重试助手的 `execute_code` 沙箱
- Docker：自定义卷挂载 ([#158](https://github.com/NousResearch/hermes-agent/pull/158)) — @Indelwin
- Daytona 云沙箱后端 ([#451](https://github.com/NousResearch/hermes-agent/pull/451)) — @rovle
- SSH 后端修复 ([#59](https://github.com/NousResearch/hermes-agent/pull/59)) — @deankerr
- Shell 噪声过滤和登录 shell 执行以确保环境一致性
- execute_code stdout 溢出的头部+尾部截断
- 可配置的后台进程通知模式

### 文件操作
- 文件系统检查点和 `/rollback` 命令 ([#824](https://github.com/NousResearch/hermes-agent/pull/824))
- 用于 patch 和 search_files 的结构化工具结果提示（下一步操作指导）([#722](https://github.com/NousResearch/hermes-agent/issues/722))
- 传递到沙箱容器配置的 Docker 卷 ([#687](https://github.com/NousResearch/hermes-agent/pull/687)) — @manuelschipper

---

## 🧩 技能生态系统

### 技能系统
- 每个平台的技能启用/禁用 ([#743](https://github.com/NousResearch/hermes-agent/pull/743)) — @teyrebaz33
- 基于工具可用性的条件技能激活 ([#785](https://github.com/NousResearch/hermes-agent/pull/785)) — @teyrebaz33
- 技能先决条件 — 隐藏具有未满足依赖项的技能 ([#659](https://github.com/NousResearch/hermes-agent/pull/659)) — @kshitijk4poor
- 可选技能 — 随附但默认不激活
- `hermes skills browse` — 分页中心浏览
- 技能子类别组织
- 平台条件技能加载
- 原子技能文件写入 ([#551](https://github.com/NousResearch/hermes-agent/pull/551)) — @aydnOktay
- 技能同步数据丢失预防 ([#563](https://github.com/NousResearch/hermes-agent/pull/563)) — @0xbyt4
- CLI 和网关的动态技能斜杠命令

### 新技能（精选）
- **ASCII Art** — pyfiglet（571 种字体）、cowsay、image-to-ascii ([#209](https://github.com/NousResearch/hermes-agent/pull/209)) — @0xbyt4
- **ASCII Video** — 完整生产管道 ([#854](https://github.com/NousResearch/hermes-agent/pull/854)) — @SHL0MS
- **DuckDuckGo Search** — Firecrawl 回退 ([#267](https://github.com/NousResearch/hermes-agent/pull/267)) — @gamedevCloudy；DDGS API 扩展 ([#598](https://github.com/NousResearch/hermes-agent/pull/598)) — @areu01or00
- **Solana Blockchain** — 钱包余额、USD 定价、代币名称 ([#212](https://github.com/NousResearch/hermes-agent/pull/212)) — @gizdusum
- **AgentMail** — 代理拥有的电子邮件收件箱 ([#330](https://github.com/NousResearch/hermes-agent/pull/330)) — @teyrebaz33
- **Polymarket** — 预测市场数据（只读）([#629](https://github.com/NousResearch/hermes-agent/pull/629))
- **OpenClaw Migration** — 官方迁移工具 ([#570](https://github.com/NousResearch/hermes-agent/pull/570)) — @unmodeled-tyler
- **Domain Intelligence** — 被动侦察：子域名、SSL、WHOIS、DNS ([#136](https://github.com/NousResearch/hermes-agent/pull/136)) — @FurkanL0
- **Superpowers** — 软件开发技能 ([#137](https://github.com/NousResearch/hermes-agent/pull/137)) — @kaos35
- **Hermes-Atropos** — RL 环境开发技能 ([#815](https://github.com/NousResearch/hermes-agent/pull/815))
- 此外：arXiv 搜索、OCR/文档、Excalidraw 图表、YouTube 转录、GIF 搜索、Pokémon 播放器、Minecraft 模组包服务器、OpenHue（Philips Hue）、Google Workspace、Notion、PowerPoint、Obsidian、find-nearby 和 40+ MLOps 技能

---

## 🔒 安全性与可靠性

### 安全加固
- skill_view 中的路径遍历修复 — 防止读取任意文件 ([#220](https://github.com/NousResearch/hermes-agent/issues/220)) — @Farukest
- sudo 密码管道中的 shell 注入预防 ([#65](https://github.com/NousResearch/hermes-agent/pull/65)) — @leonsgithub
- 危险命令检测：多行绕过修复 ([#233](https://github.com/NousResearch/hermes-agent/pull/233)) — @Farukest；tee/进程替换模式 ([#280](https://github.com/NousResearch/hermes-agent/pull/280)) — @dogiladeveloper
- skills_guard 中的符号链接边界检查修复 ([#386](https://github.com/NousResearch/hermes-agent/pull/386)) — @Farukest
- macOS 上写入拒绝列表中的符号链接绕过修复 ([#61](https://github.com/NousResearch/hermes-agent/pull/61)) — @0xbyt4
- 多词提示注入绕过预防 ([#192](https://github.com/NousResearch/hermes-agent/pull/192)) — @0xbyt4
- Cron 提示注入扫描器绕过修复 ([#63](https://github.com/NousResearch/hermes-agent/pull/63)) — @0xbyt4
- 对敏感文件强制执行 0600/0700 文件权限 ([#757](https://github.com/NousResearch/hermes-agent/pull/757))
- .env 文件权限限制为仅所有者 ([#529](https://github.com/NousResearch/hermes-agent/pull/529)) — @Himess
- `--force` 标志正确阻止覆盖危险裁决 ([#388](https://github.com/NousResearch/hermes-agent/pull/388)) — @Farukest
- FTS5 查询清理 + DB 连接泄漏修复 ([#565](https://github.com/NousResearch/hermes-agent/pull/565)) — @0xbyt4
- 扩展秘密编辑模式 + 配置切换以禁用
- 内存中的永久允许列表，防止数据泄漏 ([#600](https://github.com/NousResearch/hermes-agent/pull/600)) — @alireza78a

### 原子写入（数据丢失预防）
- sessions.json ([#611](https://github.com/NousResearch/hermes-agent/pull/611)) — @alireza78a
- Cron 作业 ([#146](https://github.com/NousResearch/hermes-agent/pull/146)) — @alireza78a
- .env 配置 ([#954](https://github.com/NousResearch/hermes-agent/pull/954))
- 进程检查点 ([#298](https://github.com/NousResearch/hermes-agent/pull/298)) — @aydnOktay
- 批处理运行器 ([#297](https://github.com/NousResearch/hermes-agent/pull/297)) — @aydnOktay
- 技能文件 ([#551](https://github.com/NousResearch/hermes-agent/pull/551)) — @aydnOktay

### 可靠性
- 保护所有 print() 免受 systemd/无头环境的 OSError ([#963](https://github.com/NousResearch/hermes-agent/pull/963))
- 在 run_conversation 开始时重置所有重试计数器 ([#607](https://github.com/NousResearch/hermes-agent/pull/607)) — @0xbyt4
- 批准回调超时时返回拒绝而不是 None ([#603](https://github.com/NousResearch/hermes-agent/pull/603)) — @0xbyt4
- 修复整个代码库中的 None 消息内容崩溃 ([#277](https://github.com/NousResearch/hermes-agent/pull/277))
- 修复本地 LLM 后端的上下文超限崩溃 ([#403](https://github.com/NousResearch/hermes-agent/pull/403)) — @ch3ronsa
- 防止 `_flush_sentinel` 泄漏到外部 API ([#227](https://github.com/NousResearch/hermes-agent/pull/227)) — @Farukest
- 防止调用者中的 conversation_history 突变 ([#229](https://github.com/NousResearch/hermes-agent/pull/229)) — @Farukest
- 修复 systemd 重启循环 ([#614](https://github.com/NousResearch/hermes-agent/pull/614)) — @voidborne-d
- 关闭文件句柄和套接字以防止 fd 泄漏 ([#568](https://github.com/NousResearch/hermes-agent/pull/568) — @alireza78a, [#296](https://github.com/NousResearch/hermes-agent/pull/296) — @alireza78a, [#709](https://github.com/NousResearch/hermes-agent/pull/709) — @memosr)
- 防止剪贴板 PNG 转换中的数据丢失 ([#602](https://github.com/NousResearch/hermes-agent/pull/602)) — @0xbyt4
- 消除终端输出中的 shell 噪声 ([#293](https://github.com/NousResearch/hermes-agent/pull/293)) — @0xbyt4
- 提示、cron 和 execute_code 的时区感知 now() ([#309](https://github.com/NousResearch/hermes-agent/pull/309)) — @areu01or00

### Windows 兼容性
- 保护 POSIX 专用进程函数 ([#219](https://github.com/NousResearch/hermes-agent/pull/219)) — @Farukest
- 通过 Git Bash + 基于 ZIP 的更新回退的 Windows 原生支持
- 用于 PTY 支持的 pywinpty ([#457](https://github.com/NousResearch/hermes-agent/pull/457)) — @shitcoinsherpa
- 所有配置/数据文件 I/O 上的显式 UTF-8 编码 ([#458](https://github.com/NousResearch/hermes-agent/pull/458)) — @shitcoinsherpa
- 兼容 Windows 的路径处理 ([#354](https://github.com/NousResearch/hermes-agent/pull/354), [#390](https://github.com/NousResearch/hermes-agent/pull/390)) — @Farukest
- 用于驱动器号路径的基于正则表达式的搜索输出解析 ([#533](https://github.com/NousResearch/hermes-agent/pull/533)) — @Himess
- Windows 的身份验证存储文件锁 ([#455](https://github.com/NousResearch/hermes-agent/pull/455)) — @shitcoinsherpa

---

## 🐛 值得注意的错误修复

- 修复 DeepSeek V3 工具调用解析器静默丢弃多行 JSON 参数 ([#444](https://github.com/NousResearch/hermes-agent/pull/444)) — @PercyDikec
- 修复网关转录因偏移不匹配每回合丢失 1 条消息 ([#395](https://github.com/NousResearch/hermes-agent/pull/395)) — @PercyDikec
- 修复 /retry 命令静默丢弃代理的最终响应 ([#441](https://github.com/NousResearch/hermes-agent/pull/441)) — @PercyDikec
- 修复 think-block 剥离后 max-iterations 重试返回空字符串 ([#438](https://github.com/NousResearch/hermes-agent/pull/438)) — @PercyDikec
- 修复 max-iterations 重试使用硬编码的 max_tokens ([#436](https://github.com/NousResearch/hermes-agent/pull/436)) — @Farukest
- 修复 Codex 状态字典键不匹配 ([#448](https://github.com/NousResearch/hermes-agent/pull/448)) 和可见性过滤器 ([#446](https://github.com/NousResearch/hermes-agent/pull/446)) — @PercyDikec
- 从最终面向用户的响应中剥离 \<think\> 块 ([#174](https://github.com/NousResearch/hermes-agent/pull/174)) — @Bartok9
- 修复 \<think\> 块正则表达式在模型字面上讨论标签时剥离可见内容 ([#786](https://github.com/NousResearch/hermes-agent/issues/786))
- 修复 Mistral 422 错误，来自助手消息中剩余的 finish_reason ([#253](https://github.com/NousResearch/hermes-agent/pull/253)) — @Sertug17
- 修复 OPENROUTER_API_KEY 在所有代码路径上的解析顺序 ([#295](https://github.com/NousResearch/hermes-agent/pull/295)) — @0xbyt4
- 修复 OPENAI_BASE_URL API 密钥优先级 ([#420](https://github.com/NousResearch/hermes-agent/pull/420)) — @manuelschipper
- 修复 Anthropic "prompt is too long" 400 错误未被检测为上下文长度错误 ([#813](https://github.com/NousResearch/hermes-agent/issues/813))
- 修复 SQLite 会话转录累积重复消息 — 3-4x 令牌膨胀 ([#860](https://github.com/NousResearch/hermes-agent/issues/860))
- 修复设置向导在首次安装时跳过 API 密钥提示 ([#748](https://github.com/NousResearch/hermes-agent/pull/748))
- 修复设置向导为 Nous Portal 显示 OpenRouter 模型列表 ([#575](https://github.com/NousResearch/hermes-agent/pull/575)) — @PercyDikec
- 修复通过 hermes model 切换时提供商选择不持久 ([#881](https://github.com/NousResearch/hermes-agent/pull/881))
- 修复 Docker 后端在 macOS 上 docker 不在 PATH 中时失败 ([#889](https://github.com/NousResearch/hermes-agent/pull/889))
- 修复 ClawHub Skills Hub 适配器的 API 端点更改 ([#286](https://github.com/NousResearch/hermes-agent/pull/286)) — @BP602
- 修复 API 密钥存在时 Honcho 自动启用 ([#243](https://github.com/NousResearch/hermes-agent/pull/243)) — @Bartok9
- 修复 Python 3.11+ 上的重复 'skills' 子解析器崩溃 ([#898](https://github.com/NousResearch/hermes-agent/issues/898))
- 修复内容包含章节符号时的内存工具条目解析 ([#162](https://github.com/NousResearch/hermes-agent/pull/162)) — @aydnOktay
- 修复交互式提示失败时管道安装静默中止 ([#72](https://github.com/NousResearch/hermes-agent/pull/72)) — @cutepawss
- 修复递归删除检测中的误报 ([#68](https://github.com/NousResearch/hermes-agent/pull/68)) — @cutepawss
- 修复代码库中的 Ruff  lint 警告 ([#608](https://github.com/NousResearch/hermes-agent/pull/608)) — @JackTheGit
- 修复 Anthropic 原生 base URL 快速失败 ([#173](https://github.com/NousResearch/hermes-agent/pull/173)) — @adavyas
- 修复 install.sh 在移动 Node.js 目录之前创建 ~/.hermes ([#53](https://github.com/NousResearch/hermes-agent/pull/53)) — @JoshuaMart
- 修复 Ctrl+C 时 atexit 清理期间的 SystemExit 回溯 ([#55](https://github.com/NousResearch/hermes-agent/pull/55)) — @bierlingm
- 恢复缺失的 MIT 许可证文件 ([#620](https://github.com/NousResearch/hermes-agent/pull/620)) — @stablegenius49

---

## 🧪 测试

- **3,289 个测试** 涵盖代理、网关、工具、cron 和 CLI
- 带有 pytest-xdist 的并行测试套件 ([#802](https://github.com/NousResearch/hermes-agent/pull/802)) — @OutThisLife
- 单元测试批次 1：8 个核心模块 ([#60](https://github.com/NousResearch/hermes-agent/pull/60)) — @0xbyt4
- 单元测试批次 2：8 个更多模块 ([#62](https://github.com/NousResearch/hermes-agent/pull/62)) — @0xbyt4
- 单元测试批次 3：8 个未测试模块 ([#191](https://github.com/NousResearch/hermes-agent/pull/191)) — @0xbyt4
- 单元测试批次 4：5 个安全/逻辑关键模块 ([#193](https://github.com/NousResearch/hermes-agent/pull/193)) — @0xbyt4
- AIAgent (run_agent.py) 单元测试 ([#67](https://github.com/NousResearch/hermes-agent/pull/67)) — @0xbyt4
- 轨迹压缩器测试 ([#203](https://github.com/NousResearch/hermes-agent/pull/203)) — @0xbyt4
- 澄清工具测试 ([#121](https://github.com/NousResearch/hermes-agent/pull/121)) — @Bartok9
- Telegram 格式测试 — 43 个斜体/粗体/代码渲染测试 ([#204](https://github.com/NousResearch/hermes-agent/pull/204)) — @0xbyt4
- 视觉工具类型提示 + 42 个测试 ([#792](https://github.com/NousResearch/hermes-agent/pull/792))
- 压缩器工具调用边界回归测试 ([#648](https://github.com/NousResearch/hermes-agent/pull/648)) — @intertwine
- 测试结构重组 ([#34](https://github.com/NousResearch/hermes-agent/pull/34)) — @0xbyt4
- Shell 噪声消除 + 修复 36 个测试失败 ([#293](https://github.com/NousResearch/hermes-agent/pull/293)) — @0xbyt4

---

## 🔬 RL 与评估环境

- WebResearchEnv — 多步骤网络研究 RL 环境 ([#434](https://github.com/NousResearch/hermes-agent/pull/434)) — @jackx707
- Modal 沙箱并发限制，避免死锁 ([#621](https://github.com/NousResearch/hermes-agent/pull/621)) — @voteblake
- Hermes-atropos-environments 捆绑技能 ([#815](https://github.com/NousResearch/hermes-agent/pull/815))
- 用于评估的本地 vLLM 实例支持 — @dmahan93
- YC-Bench 长期代理基准环境
- OpenThoughts-TBLite 评估环境和脚本

---

## 📚 文档

- 完整的文档网站（Docusaurus），包含 37+ 页面
- 针对 Telegram、Discord、Slack、WhatsApp、Signal、电子邮件的综合平台设置指南
- AGENTS.md — AI 编码助手的开发指南
- CONTRIBUTING.md ([#117](https://github.com/NousResearch/hermes-agent/pull/117)) — @Bartok9
- 斜杠命令参考 ([#142](https://github.com/NousResearch/hermes-agent/pull/142)) — @Bartok9
- 全面的 AGENTS.md 准确性审计 ([#732](https://github.com/NousResearch/hermes-agent/pull/732))
- 皮肤/主题系统文档
- MCP 文档和示例
- 文档准确性审计 — 35+ 更正
- 文档拼写错误修复 ([#825](https://github.com/NousResearch/hermes-agent/pull/825), [#439](https://github.com/NousResearch/hermes-agent/pull/439)) — @JackTheGit
- CLI 配置优先级和术语标准化 ([#166](https://github.com/NousResearch/hermes-agent/pull/166), [#167](https://github.com/NousResearch/hermes-agent/pull/167), [#168](https://github.com/NousResearch/hermes-agent/pull/168)) — @Jr-kenny
- Telegram 令牌正则表达式文档 ([#713](https://github.com/NousResearch/hermes-agent/pull/713)) — @VolodymyrBg

---

## 👥 贡献者

感谢 63 位贡献者使此发布成为可能！在短短两周多的时间里，Hermes Agent 社区齐心协力交付了大量工作。

### 核心
- **@teknium1** — 43 个 PR：项目负责人，核心架构，提供商路由器，会话，技能，CLI，文档

### 顶级社区贡献者
- **@0xbyt4** — 40 个 PR：MCP 客户端，Home Assistant，安全修复（符号链接，提示注入，cron），广泛的测试覆盖（6 批），ascii-art 技能，shell 噪声消除，技能同步，Telegram 格式化等数十个
- **@Farukest** — 16 个 PR：安全加固（路径遍历，危险命令检测，符号链接边界），Windows 兼容性（POSIX 防护，路径处理），WhatsApp 修复，max-iterations 重试，网关修复
- **@aydnOktay** — 11 个 PR：原子写入（进程检查点，批处理运行器，技能文件），Telegram、Discord、代码执行、转录、TTS 和技能的错误处理改进
- **@Bartok9** — 9 个 PR：CONTRIBUTING.md，斜杠命令参考，Discord 频道主题，think-block 剥离，TTS 修复，Honcho 修复，会话计数修复，澄清测试
- **@PercyDikec** — 7 个 PR：DeepSeek V3 解析器修复，/retry 响应丢弃，网关转录偏移，Codex 状态/可见性，max-iterations 重试，设置向导修复
- **@teyrebaz33** — 5 个 PR：技能启用/禁用系统，快速命令，个性定制，条件技能激活
- **@alireza78a** — 5 个 PR：原子写入（cron，会话），fd 泄漏预防，安全允许列表，代码执行套接字清理
- **@shitcoinsherpa** — 3 个 PR：Windows 支持（pywinpty，UTF-8 编码，身份验证存储锁）
- **@Himess** — 3 个 PR：Cron/HomeAssistant/Daytona 修复，Windows 驱动器号解析，.env 权限
- **@satelerd** — 2 个 PR：WhatsApp 原生媒体，多用户会话隔离
- **@rovle** — 1 个 PR：Daytona 云沙箱后端（4 个提交）
- **@erosika** — 1 个 PR：Honcho AI 原生内存集成
- **@dmahan93** — 1 个 PR：--fuck-it-ship-it 标志 + RL 环境工作
- **@SHL0MS** — 1 个 PR：ASCII 视频技能

### 所有贡献者
@0xbyt4, @BP602, @Bartok9, @Farukest, @FurkanL0, @Himess, @Indelwin, @JackTheGit, @JoshuaMart, @Jr-kenny, @OutThisLife, @PercyDikec, @SHL0MS, @Sertug17, @VencentSoliman, @VolodymyrBg, @adavyas, @alireza78a, @areu01or00, @aydnOktay, @batuhankocyigit, @bierlingm, @caentzminger, @cesareth, @ch3ronsa, @christomitov, @cutepawss, @deankerr, @dmahan93, @dogiladeveloper, @dragonkhoi, @erosika, @gamedevCloudy, @gizdusum, @grp06, @intertwine, @jackx707, @jdblackstar, @johnh4098, @kaos35, @kshitijk4poor, @leonsgithub, @luisv-1, @manuelschipper, @mehmetkr-31, @memosr, @PeterFile, @rewbs, @rovle, @rsavitt, @satelerd, @spanishflu-est1918, @stablegenius49, @tars90percent, @tekelala, @teknium1, @teyrebaz33, @tripledoublev, @unmodeled-tyler, @voidborne-d, @voteblake, @ygd58

---

**完整变更日志**：[v0.1.0...v2026.3.12](https://github.com/NousResearch/hermes-agent/compare/v0.1.0...v2026.3.12)