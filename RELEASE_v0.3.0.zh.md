# Hermes Agent v0.3.0 (v2026.3.17)

**发布日期:** 2026年3月17日

> 流媒体、插件和提供商发布 — 统一的实时令牌交付、一流的插件架构、使用Vercel AI Gateway重建的提供商系统、原生Anthropic提供商、智能审批、实时Chrome CDP浏览器连接、ACP IDE集成、Honcho内存、语音模式、持久化shell以及跨所有平台的50+错误修复。

---

## ✨ 亮点

- **统一的流媒体基础设施** — 在CLI和所有网关平台中实现实时逐令牌交付。响应在生成时流式传输，而不是作为一个块到达。([#1538](https://github.com/NousResearch/hermes-agent/pull/1538))

- **一流的插件架构** — 将Python文件放入`~/.hermes/plugins/`即可扩展Hermes，添加自定义工具、命令和钩子。无需分叉。([#1544](https://github.com/NousResearch/hermes-agent/pull/1544), [#1555](https://github.com/NousResearch/hermes-agent/pull/1555))

- **原生Anthropic提供商** — 直接Anthropic API调用，支持Claude Code凭证自动发现、OAuth PKCE流程和原生提示缓存。无需OpenRouter中间人。([#1097](https://github.com/NousResearch/hermes-agent/pull/1097))

- **智能审批 + /stop 命令** — 受Codex启发的审批系统，学习哪些命令是安全的并记住您的偏好。`/stop`立即终止当前代理运行。([#1543](https://github.com/NousResearch/hermes-agent/pull/1543))

- **Honcho内存集成** — 异步内存写入、可配置的召回模式、会话标题集成以及网关模式下的多用户隔离。由@erosika提供。([#736](https://github.com/NousResearch/hermes-agent/pull/736))

- **语音模式** — CLI中的一键通话、Telegram/Discord中的语音笔记、Discord语音频道支持以及通过faster-whisper进行本地Whisper转录。([#1299](https://github.com/NousResearch/hermes-agent/pull/1299), [#1185](https://github.com/NousResearch/hermes-agent/pull/1185), [#1429](https://github.com/NousResearch/hermes-agent/pull/1429))

- **并发工具执行** — 多个独立工具调用现在通过ThreadPoolExecutor并行运行，显著减少多工具回合的延迟。([#1152](https://github.com/NousResearch/hermes-agent/pull/1152))

- **PII 编辑** — 当启用`privacy.redact_pii`时，个人身份信息会在将上下文发送到LLM提供商之前自动 scrub。([#1542](https://github.com/NousResearch/hermes-agent/pull/1542))

- **`/browser connect` 通过CDP** — 通过Chrome DevTools Protocol将浏览器工具附加到实时Chrome实例。调试、检查和与您已经打开的页面交互。([#1549](https://github.com/NousResearch/hermes-agent/pull/1549))

- **Vercel AI Gateway提供商** — 通过Vercel的AI Gateway路由Hermes，以访问其模型目录和基础设施。([#1628](https://github.com/NousResearch/hermes-agent/pull/1628))

- **集中式提供商路由器** — 重建的提供商系统，具有`call_llm` API、统一的`/model`命令、模型切换时的自动检测提供商以及辅助/委托客户端的直接端点覆盖。([#1003](https://github.com/NousResearch/hermes-agent/pull/1003), [#1506](https://github.com/NousResearch/hermes-agent/pull/1506), [#1375](https://github.com/NousResearch/hermes-agent/pull/1375))

- **ACP服务器（IDE集成）** — VS Code、Zed和JetBrains现在可以作为代理后端连接到Hermes，支持完整的斜杠命令。([#1254](https://github.com/NousResearch/hermes-agent/pull/1254), [#1532](https://github.com/NousResearch/hermes-agent/pull/1532))

- **持久化Shell模式** — 本地和SSH终端后端可以在工具调用之间保持shell状态 — cd、环境变量和别名保持不变。由@alt-glitch提供。([#1067](https://github.com/NousResearch/hermes-agent/pull/1067), [#1483](https://github.com/NousResearch/hermes-agent/pull/1483))

- **智能体在线蒸馏（OPD）** — 用于蒸馏智能体策略的新RL训练环境，扩展了Atropos训练生态系统。([#1149](https://github.com/NousResearch/hermes-agent/pull/1149))

---

## 🏗️ 核心智能体与架构

### 提供商与模型支持
- **集中式提供商路由器**，具有`call_llm` API和统一的`/model`命令 — 无缝切换模型和提供商 ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))
- **Vercel AI Gateway** 提供商支持 ([#1628](https://github.com/NousResearch/hermes-agent/pull/1628))
- **自动检测提供商** 当通过`/model`切换模型时 ([#1506](https://github.com/NousResearch/hermes-agent/pull/1506))
- **直接端点覆盖** 用于辅助和委托客户端 — 将视觉/子代理调用指向特定端点 ([#1375](https://github.com/NousResearch/hermes-agent/pull/1375))
- **原生Anthropic辅助视觉** — 使用Claude的原生视觉API，而不是通过OpenAI兼容端点路由 ([#1377](https://github.com/NousResearch/hermes-agent/pull/1377))
- Anthropic OAuth流程改进 — 自动运行`claude setup-token`、重新认证、PKCE状态持久化、身份指纹识别 ([#1132](https://github.com/NousResearch/hermes-agent/pull/1132), [#1360](https://github.com/NousResearch/hermes-agent/pull/1360), [#1396](https://github.com/NousResearch/hermes-agent/pull/1396), [#1597](https://github.com/NousResearch/hermes-agent/pull/1597))
- 修复Claude 4.6模型没有`budget_tokens`的自适应思考 — 由@ASRagab提供 ([#1128](https://github.com/NousResearch/hermes-agent/pull/1128))
- 通过适配器修复Anthropic缓存标记 — 由@brandtcormorant提供 ([#1216](https://github.com/NousResearch/hermes-agent/pull/1216))
- 重试Anthropic 429/529错误并向用户显示详细信息 — 由@0xbyt4提供 ([#1585](https://github.com/NousResearch/hermes-agent/pull/1585))
- 修复Anthropic适配器max_tokens、回退崩溃、代理base_url — 由@0xbyt4提供 ([#1121](https://github.com/NousResearch/hermes-agent/pull/1121))
- 修复DeepSeek V3解析器丢弃多个并行工具调用 — 由@mr-emmett-one提供 ([#1365](https://github.com/NousResearch/hermes-agent/pull/1365), [#1300](https://github.com/NousResearch/hermes-agent/pull/1300))
- 接受未列出的模型并发出警告，而不是拒绝 ([#1047](https://github.com/NousResearch/hermes-agent/pull/1047), [#1102](https://github.com/NousResearch/hermes-agent/pull/1102))
- 为不支持的OpenRouter模型跳过推理参数 ([#1485](https://github.com/NousResearch/hermes-agent/pull/1485))
- MiniMax Anthropic API兼容性修复 ([#1623](https://github.com/NousResearch/hermes-agent/pull/1623))
- 自定义端点`/models`验证和`/v1`基础URL建议 ([#1480](https://github.com/NousResearch/hermes-agent/pull/1480))
- 从`custom_providers`配置解析委托提供商 ([#1328](https://github.com/NousResearch/hermes-agent/pull/1328))
- Kimi模型添加和User-Agent修复 ([#1039](https://github.com/NousResearch/hermes-agent/pull/1039))
- 为Mistral兼容性去除`call_id`/`response_item_id` ([#1058](https://github.com/NousResearch/hermes-agent/pull/1058))

### 智能体循环与对话
- **Anthropic上下文编辑API** 支持 ([#1147](https://github.com/NousResearch/hermes-agent/pull/1147))
- 改进的上下文压缩传递摘要 — 压缩器现在保留更多可操作状态 ([#1273](https://github.com/NousResearch/hermes-agent/pull/1273))
- 运行中上下文压缩后同步session_id ([#1160](https://github.com/NousResearch/hermes-agent/pull/1160))
- 会话卫生阈值调整为50%，以实现更主动的压缩 ([#1096](https://github.com/NousResearch/hermes-agent/pull/1096), [#1161](https://github.com/NousResearch/hermes-agent/pull/1161))
- 通过`--pass-session-id`标志在系统提示中包含会话ID ([#1040](https://github.com/NousResearch/hermes-agent/pull/1040))
- 防止在重试期间重用已关闭的OpenAI客户端 ([#1391](https://github.com/NousResearch/hermes-agent/pull/1391))
- 清理聊天负载和提供商优先级 ([#1253](https://github.com/NousResearch/hermes-agent/pull/1253))
- 处理来自Codex和本地后端的字典工具调用参数 ([#1393](https://github.com/NousResearch/hermes-agent/pull/1393), [#1440](https://github.com/NousResearch/hermes-agent/pull/1440))

### 内存与会话
- **改进内存优先级** — 用户偏好和更正权重高于程序知识 ([#1548](https://github.com/NousResearch/hermes-agent/pull/1548))
- 系统提示中更严格的内存和会话召回指导 ([#1329](https://github.com/NousResearch/hermes-agent/pull/1329))
- 将CLI令牌计数持久化到会话DB以用于`/insights` ([#1498](https://github.com/NousResearch/hermes-agent/pull/1498))
- 保持Honcho召回不在缓存的系统前缀中 ([#1201](https://github.com/NousResearch/hermes-agent/pull/1201))
- 更正`seed_ai_identity`以使用`session.add_messages()` ([#1475](https://github.com/NousResearch/hermes-agent/pull/1475))
- 为多用户网关隔离Honcho会话路由 ([#1500](https://github.com/NousResearch/hermes-agent/pull/1500))

---

## 📱 消息平台（网关）

### 网关核心
- **系统网关服务模式** — 作为系统级systemd服务运行，而不仅仅是用户级 ([#1371](https://github.com/NousResearch/hermes-agent/pull/1371))
- **网关安装范围提示** — 在设置过程中选择用户vs系统范围 ([#1374](https://github.com/NousResearch/hermes-agent/pull/1374))
- **推理热重载** — 无需重启网关即可更改推理设置 ([#1275](https://github.com/NousResearch/hermes-agent/pull/1275))
- 默认群组会话为每用户隔离 — 群组聊天中不再有用户之间的共享状态 ([#1495](https://github.com/NousResearch/hermes-agent/pull/1495), [#1417](https://github.com/NousResearch/hermes-agent/pull/1417))
- 加强网关重启恢复 ([#1310](https://github.com/NousResearch/hermes-agent/pull/1310))
- 在关闭期间取消活动运行 ([#1427](https://github.com/NousResearch/hermes-agent/pull/1427))
- NixOS和非标准系统的SSL证书自动检测 ([#1494](https://github.com/NousResearch/hermes-agent/pull/1494))
- 为无头服务器上的`systemctl --user`自动检测D-Bus会话总线 ([#1601](https://github.com/NousResearch/hermes-agent/pull/1601))
- 在无头服务器上的网关安装期间自动启用systemd linger ([#1334](https://github.com/NousResearch/hermes-agent/pull/1334))
- 当`hermes`不在PATH上时回退到模块入口点 ([#1355](https://github.com/NousResearch/hermes-agent/pull/1355))
- 修复macOS launchd上`hermes update`后出现双网关的问题 ([#1567](https://github.com/NousResearch/hermes-agent/pull/1567))
- 从systemd单元中移除递归ExecStop ([#1530](https://github.com/NousResearch/hermes-agent/pull/1530))
- 防止网关模式下的日志处理程序累积 ([#1251](https://github.com/NousResearch/hermes-agent/pull/1251))
- 在可重试的启动失败时重启 — 由@jplew提供 ([#1517](https://github.com/NousResearch/hermes-agent/pull/1517))
- 智能体运行后回填网关会话的模型 ([#1306](https://github.com/NousResearch/hermes-agent/pull/1306))
- 基于PID的网关终止和延迟配置写入 ([#1499](https://github.com/NousResearch/hermes-agent/pull/1499))

### Telegram
- 缓冲媒体组以防止照片突发导致的自中断 ([#1341](https://github.com/NousResearch/hermes-agent/pull/1341), [#1422](https://github.com/NousResearch/hermes-agent/pull/1422))
- 在连接和发送期间对瞬态TLS故障进行重试 ([#1535](https://github.com/NousResearch/hermes-agent/pull/1535))
- 加强轮询冲突处理 ([#1339](https://github.com/NousResearch/hermes-agent/pull/1339))
- 在MarkdownV2中转义块指示器和内联代码 ([#1478](https://github.com/NousResearch/hermes-agent/pull/1478), [#1626](https://github.com/NousResearch/hermes-agent/pull/1626))
- 断开连接前检查更新器/应用状态 ([#1389](https://github.com/NousResearch/hermes-agent/pull/1389))

### Discord
- `/thread`命令，具有`auto_thread`配置和媒体元数据修复 ([#1178](https://github.com/NousResearch/hermes-agent/pull/1178))
- 在@提及上自动创建线程，在机器人线程中跳过提及文本 ([#1438](https://github.com/NousResearch/hermes-agent/pull/1438))
- 对系统消息重试时不使用回复引用 ([#1385](https://github.com/NousResearch/hermes-agent/pull/1385))
- 保留原生文档和视频附件支持 ([#1392](https://github.com/NousResearch/hermes-agent/pull/1392))
- 延迟discord适配器注释以避免可选导入崩溃 ([#1314](https://github.com/NousResearch/hermes-agent/pull/1314))

### Slack
- 线程处理全面改革 — 进度消息、响应和会话隔离都尊重线程 ([#1103](https://github.com/NousResearch/hermes-agent/pull/1103))
- 格式设置、反应、用户解析和命令改进 ([#1106](https://github.com/NousResearch/hermes-agent/pull/1106))
- 修复MAX_MESSAGE_LENGTH 3900 → 39000 ([#1117](https://github.com/NousResearch/hermes-agent/pull/1117))
- 文件上传回退保留线程上下文 — 由@0xbyt4提供 ([#1122](https://github.com/NousResearch/hermes-agent/pull/1122))
- 改进设置指南 ([#1387](https://github.com/NousResearch/hermes-agent/pull/1387))

### 电子邮件
- 修复IMAP UID跟踪和SMTP TLS验证 ([#1305](https://github.com/NousResearch/hermes-agent/pull/1305))
- 通过config.yaml添加`skip_attachments`选项 ([#1536](https://github.com/NousResearch/hermes-agent/pull/1536))

### Home Assistant
- 默认关闭事件过滤 ([#1169](https://github.com/NousResearch/hermes-agent/pull/1169))

---

## 🖥️ CLI与用户体验

### 交互式CLI
- **持久化CLI状态栏** — 始终可见的模型、提供商和令牌计数 ([#1522](https://github.com/NousResearch/hermes-agent/pull/1522))
- **输入提示中的文件路径自动完成** ([#1545](https://github.com/NousResearch/hermes-agent/pull/1545))
- **`/plan`命令** — 从规范生成实施计划 ([#1372](https://github.com/NousResearch/hermes-agent/pull/1372), [#1381](https://github.com/NousResearch/hermes-agent/pull/1381))
- **主要`/rollback`改进** — 更丰富的检查点历史，更清晰的用户体验 ([#1505](https://github.com/NousResearch/hermes-agent/pull/1505))
- **启动时预加载CLI技能** — 技能在第一个提示之前就已准备就绪 ([#1359](https://github.com/NousResearch/hermes-agent/pull/1359))
- **集中式斜杠命令注册表** — 所有命令只定义一次，在各处使用 ([#1603](https://github.com/NousResearch/hermes-agent/pull/1603))
- `/bg`作为`/background`的别名 ([#1590](https://github.com/NousResearch/hermes-agent/pull/1590))
- 斜杠命令的前缀匹配 — `/mod`解析为`/model` ([#1320](https://github.com/NousResearch/hermes-agent/pull/1320))
- `/new`、`/reset`、`/clear`现在启动真正的新会话 ([#1237](https://github.com/NousResearch/hermes-agent/pull/1237))
- 接受会话ID前缀用于会话操作 ([#1425](https://github.com/NousResearch/hermes-agent/pull/1425))
- TUI提示和强调输出现在尊重活动皮肤 ([#1282](https://github.com/NousResearch/hermes-agent/pull/1282))
- 在注册表中集中工具表情符号元数据 + 皮肤集成 ([#1484](https://github.com/NousResearch/hermes-agent/pull/1484))
- 危险命令审批中添加了"查看完整命令"选项 — 由@teknium1基于社区设计 ([#887](https://github.com/NousResearch/hermes-agent/pull/887))
- 非阻塞启动更新检查和横幅去重 ([#1386](https://github.com/NousResearch/hermes-agent/pull/1386))
- `/reasoning`命令输出排序和内联思考提取修复 ([#1031](https://github.com/NousResearch/hermes-agent/pull/1031))
- 详细模式显示完整的未截断输出 ([#1472](https://github.com/NousResearch/hermes-agent/pull/1472))
- 修复`/status`以报告实时状态和令牌 ([#1476](https://github.com/NousResearch/hermes-agent/pull/1476))
- 种子默认全局SOUL.md ([#1311](https://github.com/NousResearch/hermes-agent/pull/1311))

### 设置与配置
- **OpenClaw迁移** 在首次设置期间 — 由@kshitijk4poor提供 ([#981](https://github.com/NousResearch/hermes-agent/pull/981))
- `hermes claw migrate`命令 + 迁移文档 ([#1059](https://github.com/NousResearch/hermes-agent/pull/1059))
- 智能视觉设置，尊重用户选择的提供商 ([#1323](https://github.com/NousResearch/hermes-agent/pull/1323))
- 端到端处理无头设置流程 ([#1274](https://github.com/NousResearch/hermes-agent/pull/1274))
- 在setup.py中优先使用curses而不是`simple_term_menu` ([#1487](https://github.com/NousResearch/hermes-agent/pull/1487))
- 在`/status`中显示有效模型和提供商 ([#1284](https://github.com/NousResearch/hermes-agent/pull/1284))
- 配置设置示例使用占位符语法 ([#1322](https://github.com/NousResearch/hermes-agent/pull/1322))
- 重新加载.env而不是过时的shell覆盖 ([#1434](https://github.com/NousResearch/hermes-agent/pull/1434))
- 修复is_coding_plan NameError崩溃 — 由@0xbyt4提供 ([#1123](https://github.com/NousResearch/hermes-agent/pull/1123))
- 将缺失的包添加到setuptools配置 — 由@alt-glitch提供 ([#912](https://github.com/NousResearch/hermes-agent/pull/912))
- 安装程序：在每个提示中澄清为什么需要sudo ([#1602](https://github.com/NousResearch/hermes-agent/pull/1602))

---

## 🔧 工具系统

### 终端与执行
- **持久化shell模式** 用于本地和SSH后端 — 在工具调用之间保持shell状态 — 由@alt-glitch提供 ([#1067](https://github.com/NousResearch/hermes-agent/pull/1067), [#1483](https://github.com/NousResearch/hermes-agent/pull/1483))
- **Tirith执行前命令扫描** — 在执行前分析命令的安全层 ([#1256](https://github.com/NousResearch/hermes-agent/pull/1256))
- 从所有子进程环境中剥离Hermes提供商环境变量 ([#1157](https://github.com/NousResearch/hermes-agent/pull/1157), [#1172](https://github.com/NousResearch/hermes-agent/pull/1172), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399), [#1419](https://github.com/NousResearch/hermes-agent/pull/1419)) — 初始修复由@eren-karakus0提供
- SSH预检检查 ([#1486](https://github.com/NousResearch/hermes-agent/pull/1486))
- Docker后端：使cwd工作区挂载明确选择加入 ([#1534](https://github.com/NousResearch/hermes-agent/pull/1534))
- 在execute_code沙箱中添加项目根目录到PYTHONPATH ([#1383](https://github.com/NousResearch/hermes-agent/pull/1383))
- 消除网关平台上的execute_code进度垃圾信息 ([#1098](https://github.com/NousResearch/hermes-agent/pull/1098))
- 更清晰的docker后端预检错误 ([#1276](https://github.com/NousResearch/hermes-agent/pull/1276))

### 浏览器
- **`/browser connect`** — 通过CDP将浏览器工具附加到实时Chrome实例 ([#1549](https://github.com/NousResearch/hermes-agent/pull/1549))
- 改进浏览器清理、本地浏览器PATH设置和屏幕截图恢复 ([#1333](https://github.com/NousResearch/hermes-agent/pull/1333))

### MCP
- **选择性工具加载** 与实用程序策略 — 过滤哪些MCP工具可用 ([#1302](https://github.com/NousResearch/hermes-agent/pull/1302))
- 当`mcp_servers`配置更改时自动重新加载MCP工具，无需重启 ([#1474](https://github.com/NousResearch/hermes-agent/pull/1474))
- 解决npx标准输入输出连接失败问题 ([#1291](https://github.com/NousResearch/hermes-agent/pull/1291))
- 保存平台工具配置时保留MCP工具集 ([#1421](https://github.com/NousResearch/hermes-agent/pull/1421))

### 视觉
- 统一视觉后端门控 ([#1367](https://github.com/NousResearch/hermes-agent/pull/1367))
- 显示实际错误原因而不是通用消息 ([#1338](https://github.com/NousResearch/hermes-agent/pull/1338))
- 使Claude图像处理端到端工作 ([#1408](https://github.com/NousResearch/hermes-agent/pull/1408))

### Cron
- **将cron管理压缩到一个工具中** — 单个`cronjob`工具替换多个命令 ([#1343](https://github.com/NousResearch/hermes-agent/pull/1343))
- 抑制向自动交付目标的重复cron发送 ([#1357](https://github.com/NousResearch/hermes-agent/pull/1357))
- 将cron会话持久化到SQLite ([#1255](https://github.com/NousResearch/hermes-agent/pull/1255))
- 每个作业的运行时覆盖（提供商、模型、base_url） ([#1398](https://github.com/NousResearch/hermes-agent/pull/1398))
- `save_job_output`中的原子写入，防止崩溃时数据丢失 ([#1173](https://github.com/NousResearch/hermes-agent/pull/1173))
- 为`deliver=origin`保留线程上下文 ([#1437](https://github.com/NousResearch/hermes-agent/pull/1437))

### 补丁工具
- 避免在V4A补丁应用中损坏管道字符 ([#1286](https://github.com/NousResearch/hermes-agent/pull/1286))
- 宽松的`block_anchor`阈值和unicode标准化 ([#1539](https://github.com/NousResearch/hermes-agent/pull/1539))

### 委托
- 向子代理结果添加可观察性元数据（模型、令牌、持续时间、工具跟踪） ([#1175](https://github.com/NousResearch/hermes-agent/pull/1175))

---

## 🧩 技能生态系统

### 技能系统
- **集成skills.sh** 作为ClawHub旁边的 hub 源 ([#1303](https://github.com/NousResearch/hermes-agent/pull/1303))
- 加载时的安全技能环境设置 ([#1153](https://github.com/NousResearch/hermes-agent/pull/1153))
- 尊重危险判决的政策表 ([#1330](https://github.com/NousResearch/hermes-agent/pull/1330))
- 加强ClawHub技能搜索精确匹配 ([#1400](https://github.com/NousResearch/hermes-agent/pull/1400))
- 修复ClawHub技能安装 — 使用`/download` ZIP端点 ([#1060](https://github.com/NousResearch/hermes-agent/pull/1060))
- 避免将本地技能错误标记为内置 — 由@arceus77-7提供 ([#862](https://github.com/NousResearch/hermes-agent/pull/862))

### 新技能
- **Linear** 项目管理 ([#1230](https://github.com/NousResearch/hermes-agent/pull/1230))
- **X/Twitter** 通过x-cli ([#1285](https://github.com/NousResearch/hermes-agent/pull/1285))
- **电话** — Twilio、SMS和AI通话 ([#1289](https://github.com/NousResearch/hermes-agent/pull/1289))
- **1Password** — 由@arceus77-7提供 ([#883](https://github.com/NousResearch/hermes-agent/pull/883), [#1179](https://github.com/NousResearch/hermes-agent/pull/1179))
- **NeuroSkill BCI** 集成 ([#1135](https://github.com/NousResearch/hermes-agent/pull/1135))
- **Blender MCP** 用于3D建模 ([#1531](https://github.com/NousResearch/hermes-agent/pull/1531))
- **OSS安全取证** ([#1482](https://github.com/NousResearch/hermes-agent/pull/1482))
- **并行CLI** 研究技能 ([#1301](https://github.com/NousResearch/hermes-agent/pull/1301))
- **OpenCode** CLI技能 ([#1174](https://github.com/NousResearch/hermes-agent/pull/1174))
- **ASCII视频** 技能重构 — 由@SHL0MS提供 ([#1213](https://github.com/NousResearch/hermes-agent/pull/1213), [#1598](https://github.com/NousResearch/hermes-agent/pull/1598))

---

## 🎙️ 语音模式

- 语音模式基础 — CLI中的一键通话、Telegram/Discord中的语音笔记 ([#1299](https://github.com/NousResearch/hermes-agent/pull/1299))
- 通过faster-whisper进行免费本地Whisper转录 ([#1185](https://github.com/NousResearch/hermes-agent/pull/1185))
- Discord语音频道可靠性修复 ([#1429](https://github.com/NousResearch/hermes-agent/pull/1429))
- 恢复网关语音笔记的本地STT回退 ([#1490](https://github.com/NousResearch/hermes-agent/pull/1490))
- 在网关转录中尊重`stt.enabled: false` ([#1394](https://github.com/NousResearch/hermes-agent/pull/1394))
- 修复Telegram语音笔记上的虚假无能消息（Issue [#1033](https://github.com/NousResearch/hermes-agent/issues/1033))

---

## 🔌 ACP（IDE集成）

- 恢复ACP服务器实现 ([#1254](https://github.com/NousResearch/hermes-agent/pull/1254))
- 支持ACP适配器中的斜杠命令 ([#1532](https://github.com/NousResearch/hermes-agent/pull/1532))

---

## 🧪 RL训练

- **智能体在线蒸馏（OPD）** 环境 — 用于智能体策略蒸馏的新RL训练环境 ([#1149](https://github.com/NousResearch/hermes-agent/pull/1149))
- 使tinker-atropos RL训练完全可选 ([#1062](https://github.com/NousResearch/hermes-agent/pull/1062))

---

## 🔒 安全与可靠性

### 安全强化
- **Tirith执行前命令扫描** — 执行前对终端命令进行静态分析 ([#1256](https://github.com/NousResearch/hermes-agent/pull/1256))
- **PII编辑** 当启用`privacy.redact_pii`时 ([#1542](https://github.com/NousResearch/hermes-agent/pull/1542))
- 从所有子进程环境中剥离Hermes提供商/网关/工具环境变量 ([#1157](https://github.com/NousResearch/hermes-agent/pull/1157), [#1172](https://github.com/NousResearch/hermes-agent/pull/1172), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399), [#1419](https://github.com/NousResearch/hermes-agent/pull/1419))
- Docker cwd工作区挂载现在明确选择加入 — 从不自动挂载主机目录 ([#1534](https://github.com/NousResearch/hermes-agent/pull/1534))
- 转义fork bomb正则表达式模式中的括号和大括号 ([#1397](https://github.com/NousResearch/hermes-agent/pull/1397))
- 加强`.worktreeinclude`路径包含 ([#1388](https://github.com/NousResearch/hermes-agent/pull/1388))
- 使用描述作为`pattern_key`以防止审批冲突 ([#1395](https://github.com/NousResearch/hermes-agent/pull/1395))

### 可靠性
- 保护初始化时的标准输入输出写入 ([#1271](https://github.com/NousResearch/hermes-agent/pull/1271))
- 会话日志写入重用共享原子JSON助手 ([#1280](https://github.com/NousResearch/hermes-agent/pull/1280))
- 中断时受保护的原子临时清理 ([#1401](https://github.com/NousResearch/hermes-agent/pull/1401))

---

## 🐛 显著错误修复

- **`/status`始终显示0个令牌** — 现在报告实时状态（Issue [#1465](https://github.com/NousResearch/hermes-agent/issues/1465), [#1476](https://github.com/NousResearch/hermes-agent/pull/1476))
- **自定义模型端点不工作** — 恢复配置保存的端点解析（Issue [#1460](https://github.com/NousResearch/hermes-agent/issues/1460), [#1373](https://github.com/NousResearch/hermes-agent/pull/1373))
- **MCP工具在重启前不可见** — 配置更改时自动重新加载（Issue [#1036](https://github.com/NousResearch/hermes-agent/issues/1036), [#1474](https://github.com/NousResearch/hermes-agent/pull/1474))
- **`hermes tools`移除MCP工具** — 保存时保留MCP工具集（Issue [#1247](https://github.com/NousResearch/hermes-agent/issues/1247), [#1421](https://github.com/NousResearch/hermes-agent/pull/1421))
- **终端子进程继承`OPENAI_BASE_URL`** 破坏外部工具（Issue [#1002](https://github.com/NousResearch/hermes-agent/issues/1002), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399))
- **网关重启时后台进程丢失** — 改进的恢复（Issue [#1144](https://github.com/NousResearch/hermes-agent/issues/1144))
- **Cron作业不持久化状态** — 现在存储在SQLite中（Issue [#1416](https://github.com/NousResearch/hermes-agent/issues/1416), [#1255](https://github.com/NousResearch/hermes-agent/pull/1255))
- **Cronjob `deliver: origin`不保留线程上下文**（Issue [#1219](https://github.com/NousResearch/hermes-agent/issues/1219), [#1437](https://github.com/NousResearch/hermes-agent/pull/1437))
- **网关systemd服务在浏览器进程孤立时无法自动重启**（Issue [#1617](https://github.com/NousResearch/hermes-agent/issues/1617))
- **`/background`完成报告在Telegram中被截断**（Issue [#1443](https://github.com/NousResearch/hermes-agent/issues/1443))
- **模型切换不生效**（Issue [#1244](https://github.com/NousResearch/hermes-agent/issues/1244), [#1183](https://github.com/NousResearch/hermes-agent/pull/1183))
- **`hermes doctor`报告cronjob不可用**（Issue [#878](https://github.com/NousResearch/hermes-agent/issues/878), [#1180](https://github.com/NousResearch/hermes-agent/pull/1180))
- **WhatsApp桥接消息未从移动设备接收**（Issue [#1142](https://github.com/NousResearch/hermes-agent/issues/1142))
- **设置向导在无头SSH上挂起**（Issue [#905](https://github.com/NousResearch/hermes-agent/issues/905), [#1274](https://github.com/NousResearch/hermes-agent/pull/1274))
- **日志处理程序累积** 降低网关性能（Issue [#990](https://github.com/NousResearch/hermes-agent/issues/990), [#1251](https://github.com/NousResearch/hermes-agent/pull/1251))
- **网关NULL模型在DB中**（Issue [#987](https://github.com/NousResearch/hermes-agent/issues/987), [#1306](https://github.com/NousResearch/hermes-agent/pull/1306))
- **严格端点拒绝重放的tool_calls**（Issue [#893](https://github.com/NousResearch/hermes-agent/issues/893))
- **剩余硬编码的`~/.hermes`路径** — 现在都尊重`HERMES_HOME`（Issue [#892](https://github.com/NousResearch/hermes-agent/issues/892), [#1233](https://github.com/NousResearch/hermes-agent/pull/1233))
- **委托工具不适用于自定义推理提供商**（Issue [#1011](https://github.com/NousResearch/hermes-agent/issues/1011), [#1328](https://github.com/NousResearch/hermes-agent/pull/1328))
- **Skills Guard阻止官方技能**（Issue [#1006](https://github.com/NousResearch/hermes-agent/issues/1006), [#1330](https://github.com/NousResearch/hermes-agent/pull/1330))
- **设置在模型选择之前写入提供商**（Issue [#1182](https://github.com/NousResearch/hermes-agent/issues/1182))
- **`GatewayConfig.get()` AttributeError** 崩溃所有消息处理（Issue [#1158](https://github.com/NousResearch/hermes-agent/issues/1158), [#1287](https://github.com/NousResearch/hermes-agent/pull/1287))
- **`/update`因"command not found"而硬失败**（Issue [#1049](https://github.com/NousResearch/hermes-agent/issues/1049))
- **图像分析静默失败**（Issue [#1034](https://github.com/NousResearch/hermes-agent/issues/1034), [#1338](https://github.com/NousResearch/hermes-agent/pull/1338))
- **API `BadRequestError` from `'dict'` object has no attribute `'strip'`**（Issue [#1071](https://github.com/NousResearch/hermes-agent/issues/1071))
- **斜杠命令需要确切的全名** — 现在使用前缀匹配（Issue [#928](https://github.com/NousResearch/hermes-agent/issues/928), [#1320](https://github.com/NousResearch/hermes-agent/pull/1320))
- **当无头终端关闭时网关停止响应**（Issue [#1005](https://github.com/NousResearch/hermes-agent/issues/1005))

---

## 🧪 测试

- 覆盖空缓存的Anthropic工具调用回合 ([#1222](https://github.com/NousResearch/hermes-agent/pull/1222))
- 修复解析器和快速命令覆盖中的过时CI假设 ([#1236](https://github.com/NousResearch/hermes-agent/pull/1236))
- 修复没有隐式事件循环的网关异步测试 ([#1278](https://github.com/NousResearch/hermes-agent/pull/1278))
- 使网关异步测试xdist安全 ([#1281](https://github.com/NousResearch/hermes-agent/pull/1281))
- cron的跨时区天真时间戳回归 ([#1319](https://github.com/NousResearch/hermes-agent/pull/1319))
- 隔离codex提供商测试与本地环境 ([#1335](https://github.com/NousResearch/hermes-agent/pull/1335))
- 锁定重试替换语义 ([#1379](https://github.com/NousResearch/hermes-agent/pull/1379))
- 改进会话搜索工具中的错误日志记录 — 由@aydnOktay提供 ([#1533](https://github.com/NousResearch/hermes-agent/pull/1533))

---

## 📚 文档

- 全面的SOUL.md指南 ([#1315](https://github.com/NousResearch/hermes-agent/pull/1315))
- 语音模式文档 ([#1316](https://github.com/NousResearch/hermes-agent/pull/1316), [#1362](https://github.com/NousResearch/hermes-agent/pull/1362))
- 提供商贡献指南 ([#1361](https://github.com/NousResearch/hermes-agent/pull/1361))
- ACP和内部系统实现指南 ([#1259](https://github.com/NousResearch/hermes-agent/pull/1259))
- 扩展Docusaurus覆盖CLI、工具、技能和皮肤 ([#1232](https://github.com/NousResearch/hermes-agent/pull/1232))
- 终端后端和Windows故障排除 ([#1297](https://github.com/NousResearch/hermes-agent/pull/1297))
- 技能中心参考部分 ([#1317](https://github.com/NousResearch/hermes-agent/pull/1317))
- 检查点、/rollback和git工作树指南 ([#1493](https://github.com/NousResearch/hermes-agent/pull/1493), [#1524](https://github.com/NousResearch/hermes-agent/pull/1524))
- CLI状态栏和/usage参考 ([#1523](https://github.com/NousResearch/hermes-agent/pull/1523))
- 回退提供商 + /background命令文档 ([#1430](https://github.com/NousResearch/hermes-agent/pull/1430))
- 网关服务范围文档 ([#1378](https://github.com/NousResearch/hermes-agent/pull/1378))
- Slack线程回复行为文档 ([#1407](https://github.com/NousResearch/hermes-agent/pull/1407))
- 使用Nous蓝色调色板重新设计的登陆页面 — 由@austinpickett提供 ([#974](https://github.com/NousResearch/hermes-agent/pull/974))
- 修复多个文档拼写错误 — 由@JackTheGit提供 ([#953](https://github.com/NousResearch/hermes-agent/pull/953))
- 稳定网站图表 ([#1405](https://github.com/NousResearch/hermes-agent/pull/1405))
- README中的CLI与消息传递快速参考 ([#1491](https://github.com/NousResearch/hermes-agent/pull/1491))
- 为Docusaurus添加搜索 ([#1053](https://github.com/NousResearch/hermes-agent/pull/1053))
- Home Assistant集成文档 ([#1170](https://github.com/NousResearch/hermes-agent/pull/1170))

---

## 👥 贡献者

### 核心
- **@teknium1** — 220+ PR，涵盖代码库的每个领域

### 顶级社区贡献者

- **@0xbyt4** (4 PR) — Anthropic适配器修复（max_tokens、回退崩溃、429/529重试）、Slack文件上传线程上下文、设置NameError修复
- **@erosika** (1 PR) — Honcho内存集成：异步写入、内存模式、会话标题集成
- **@SHL0MS** (2 PR) — ASCII视频技能设计模式和重构
- **@alt-glitch** (2 PR) — 本地/SSH后端的持久化shell模式、setuptools打包修复
- **@arceus77-7** (2 PR) — 1Password技能、修复技能列表错误标记
- **@kshitijk4poor** (1 PR) — 设置向导期间的OpenClaw迁移
- **@ASRagab** (1 PR) — 修复Claude 4.6模型的自适应思考
- **@eren-karakus0** (1 PR) — 从子进程环境中剥离Hermes提供商环境变量
- **@mr-emmett-one** (1 PR) — 修复DeepSeek V3解析器多工具调用支持
- **@jplew** (1 PR) — 可重试启动失败时的网关重启
- **@brandtcormorant** (1 PR) — 修复空文本块的Anthropic缓存控制
- **@aydnOktay** (1 PR) — 改进会话搜索工具中的错误日志记录
- **@austinpickett** (1 PR) — 使用Nous蓝色调色板重新设计登陆页面
- **@JackTheGit** (1 PR) — 文档拼写错误修复

### 所有贡献者

@0xbyt4, @alt-glitch, @arceus77-7, @ASRagab, @austinpickett, @aydnOktay, @brandtcormorant, @eren-karakus0, @erosika, @JackTheGit, @jplew, @kshitijk4poor, @mr-emmett-one, @SHL0MS, @teknium1

---

**完整变更日志**: [v2026.3.12...v2026.3.17](https://github.com/NousResearch/hermes-agent/compare/v2026.3.12...v2026.3.17)