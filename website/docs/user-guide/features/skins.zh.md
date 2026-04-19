---
sidebar_position: 10
title: "皮肤与主题"
description: "使用内置和用户定义的皮肤自定义 Hermes CLI"
---

# 皮肤与主题

皮肤控制 Hermes CLI 的**视觉呈现**：横幅颜色、 spinner 表情和动词、响应框标签、品牌文本和工具活动前缀。

对话风格和视觉风格是分开的概念：

- **个性** 改变智能体的语气和措辞。
- **皮肤** 改变 CLI 的外观。

## 更改皮肤

```bash
/skin                # 显示当前皮肤并列出可用皮肤
/skin ares           # 切换到内置皮肤
/skin mytheme        # 切换到 ~/.hermes/skins/mytheme.yaml 中的自定义皮肤
```

或在 `~/.hermes/config.yaml` 中设置默认皮肤：

```yaml
display:
  skin: default
```

## 内置皮肤

| 皮肤 | 描述 | 智能体品牌 | 视觉特征 |
|------|------|------------|----------|
| `default` | 经典 Hermes — 金色和可爱 | `Hermes Agent` | 温暖的金色边框，玉米丝色文本，spinner 中的可爱表情。熟悉的双蛇杖横幅。干净且诱人。 |
| `ares` | 战神主题 — 深红色和青铜色 | `Ares Agent` | 深红色边框带有青铜色装饰。激进的 spinner 动词（"锻造"、"行进"、"锤炼钢铁"）。自定义剑盾 ASCII 艺术横幅。 |
| `mono` | 单色 — 干净的灰度 | `Hermes Agent` | 全灰色 — 无颜色。边框为 `#555555`，文本为 `#c9d1d9`。理想用于最小终端设置或屏幕录制。 |
| `slate` | 清凉蓝色 — 面向开发者 | `Hermes Agent` | 皇家蓝边框（`#4169e1`），柔和的蓝色文本。冷静且专业。无自定义 spinner — 使用默认表情。 |
| `daylight` | 浅色主题，适用于带有深色文本和清凉蓝色装饰的明亮终端 | `Hermes Agent` | 为白色或明亮终端设计。深色板岩文本带有蓝色边框，浅色状态表面，以及在浅色终端配置文件中保持可读的浅色完成菜单。 |
| `warm-lightmode` | 温暖的棕色/金色文本，适用于浅色终端背景 | `Hermes Agent` | 为浅色终端准备的温暖羊皮纸色调。深棕色文本带有马鞍棕色装饰，奶油色状态表面。比凉爽的 daylight 主题更朴实的替代方案。 |
| `poseidon` | 海神主题 — 深蓝色和海泡沫色 | `Poseidon Agent` | 深蓝到海泡沫色渐变。海洋主题 spinner（"绘制洋流"、"探测深度"）。三叉戟 ASCII 艺术横幅。 |
| `sisyphus` | 西西弗斯主题 — 朴素的灰度，带有持久性 | `Sisyphus Agent` | 浅灰色带有鲜明对比。巨石主题 spinner（"推上坡"、"重置巨石"、"忍受循环"）。巨石和山丘 ASCII 艺术横幅。 |
| `charizard` | 火山主题 — 焦橙色和余烬色 | `Charizard Agent` | 温暖的焦橙色到余烬色渐变。火焰主题 spinner（"飞入气流"、"测量燃烧"）。龙剪影 ASCII 艺术横幅。 |

## 可配置键的完整列表

### 颜色 (`colors:`)

控制整个 CLI 中的所有颜色值。值为十六进制颜色字符串。

| 键 | 描述 | 默认值（`default` 皮肤） |
|-----|------|--------------------------|
| `banner_border` | 启动横幅周围的面板边框 | `#CD7F32`（青铜色） |
| `banner_title` | 横幅中的标题文本颜色 | `#FFD700`（金色） |
| `banner_accent` | 横幅中的节标题（可用工具等） | `#FFBF00`（琥珀色） |
| `banner_dim` | 横幅中的静音文本（分隔符、次要标签） | `#B8860B`（深金色） |
| `banner_text` | 横幅中的正文文本（工具名称、技能名称） | `#FFF8DC`（玉米丝色） |
| `ui_accent` | 通用 UI 强调色（高亮、活动元素） | `#FFBF00` |
| `ui_label` | UI 标签和标签 | `#4dd0e1`（青色） |
| `ui_ok` | 成功指示器（检查标记、完成） | `#4caf50`（绿色） |
| `ui_error` | 错误指示器（失败、阻塞） | `#ef5350`（红色） |
| `ui_warn` | 警告指示器（警告、批准提示） | `#ffa726`（橙色） |
| `prompt` | 交互式提示文本颜色 | `#FFF8DC` |
| `input_rule` | 输入区域上方的水平规则 | `#CD7F32` |
| `response_border` | 智能体响应框周围的边框（ANSI 转义） | `#FFD700` |
| `session_label` | 会话标签颜色 | `#DAA520` |
| `session_border` | 会话 ID 暗边框颜色 | `#8B8682` |
| `status_bar_bg` | TUI 状态/使用栏的背景颜色 | `#1a1a2e` |
| `voice_status_bg` | 语音模式状态徽章的背景颜色 | `#1a1a2e` |
| `completion_menu_bg` | 完成菜单列表的背景颜色 | `#1a1a2e` |
| `completion_menu_current_bg` | 活动完成行的背景颜色 | `#333355` |
| `completion_menu_meta_bg` | 完成元列的背景颜色 | `#1a1a2e` |
| `completion_menu_meta_current_bg` | 活动完成元列的背景颜色 | `#333355` |

### Spinner (`spinner:`)

控制在等待 API 响应时显示的动画 spinner。

| 键 | 类型 | 描述 | 示例 |
|-----|------|------|-------|
| `waiting_faces` | 字符串列表 | 等待 API 响应时循环的表情 | `["(⚔)", "(⛨)", "(▲)"]` |
| `thinking_faces` | 字符串列表 | 模型推理期间循环的表情 | `["(⚔)", "(⌁)", "(<>)"]` |
| `thinking_verbs` | 字符串列表 | 在 spinner 消息中显示的动词 | `["forging", "plotting", "hammering plans"]` |
| `wings` | [左, 右] 对列表 | spinner 周围的装饰性括号 | `[["⟪⚔", "⚔⟫"], ["⟪▲", "▲⟫"]]` |

当 spinner 值为空时（如 `default` 和 `mono` 中），使用 `display.py` 中的硬编码默认值。

### 品牌 (`branding:`)

在整个 CLI 界面中使用的文本字符串。

| 键 | 描述 | 默认值 |
|-----|------|--------|
| `agent_name` | 在横幅标题和状态显示中显示的名称 | `Hermes Agent` |
| `welcome` | CLI 启动时显示的欢迎消息 | `Welcome to Hermes Agent! Type your message or /help for commands.` |
| `goodbye` | 退出时显示的消息 | `Goodbye! ⚕` |
| `response_label` | 响应框标题上的标签 | ` ⚕ Hermes ` |
| `prompt_symbol` | 用户输入提示前的符号 | `❯ ` |
| `help_header` | `/help` 命令输出的标题文本 | `(^_^)? Available Commands` |

### 其他顶级键

| 键 | 类型 | 描述 | 默认值 |
|-----|------|------|--------|
| `tool_prefix` | 字符串 | 在 CLI 中工具输出行前加上的字符 | `┊` |
| `tool_emojis` | 字典 | 用于 spinner 和进度的每个工具的 emoji 覆盖（`{tool_name: emoji}`） | `{}` |
| `banner_logo` | 字符串 | 富标记 ASCII 艺术徽标（替换默认的 HERMES_AGENT 横幅） | `""` |
| `banner_hero` | 字符串 | 富标记英雄艺术（替换默认的双蛇杖艺术） | `""` |

## 自定义皮肤

在 `~/.hermes/skins/` 下创建 YAML 文件。用户皮肤从内置的 `default` 皮肤继承缺失的值，因此您只需要指定要更改的键。

### 完整的自定义皮肤 YAML 模板

```yaml
# ~/.hermes/skins/mytheme.yaml
# 完整的皮肤模板 — 显示所有键。删除任何不需要的键；
# 缺失的值会自动从 'default' 皮肤继承。

name: mytheme
description: My custom theme

colors:
  banner_border: "#CD7F32"
  banner_title: "#FFD700"
  banner_accent: "#FFBF00"
  banner_dim: "#B8860B"
  banner_text: "#FFF8DC"
  ui_accent: "#FFBF00"
  ui_label: "#4dd0e1"
  ui_ok: "#4caf50"
  ui_error: "#ef5350"
  ui_warn: "#ffa726"
  prompt: "#FFF8DC"
  input_rule: "#CD7F32"
  response_border: "#FFD700"
  session_label: "#DAA520"
  session_border: "#8B8682"
  status_bar_bg: "#1a1a2e"
  voice_status_bg: "#1a1a2e"
  completion_menu_bg: "#1a1a2e"
  completion_menu_current_bg: "#333355"
  completion_menu_meta_bg: "#1a1a2e"
  completion_menu_meta_current_bg: "#333355"

spinner:
  waiting_faces:
    - "(⚔)"
    - "(⛨)"
    - "(▲)"
  thinking_faces:
    - "(⚔)"
    - "(⌁)"
    - "(<>)"
  thinking_verbs:
    - "processing"
    - "analyzing"
    - "computing"
    - "evaluating"
  wings:
    - ["⟪⚡", "⚡⟫"]
    - ["⟪●", "●⟫"]

branding:
  agent_name: "My Agent"
  welcome: "Welcome to My Agent! Type your message or /help for commands."
  goodbye: "See you later! ⚡"
  response_label: " ⚡ My Agent "
  prompt_symbol: "⚡ ❯ "
  help_header: "(⚡) Available Commands"

tool_prefix: "┊"

# 每个工具的 emoji 覆盖（可选）
tool_emojis:
  terminal: "⚔"
  web_search: "🔮"
  read_file: "📄"

# 自定义 ASCII 艺术横幅（可选，支持 Rich 标记）
# banner_logo: |
#   [bold #FFD700] MY AGENT [/]
# banner_hero: |
#   [#FFD700]  Custom art here  [/]
```

### 最小自定义皮肤示例

由于所有内容都从 `default` 继承，最小皮肤只需要更改不同的部分：

```yaml
name: cyberpunk
description: Neon terminal theme

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"

spinner:
  thinking_verbs: ["jacking in", "decrypting", "uploading"]
  wings:
    - ["⟨⚡", "⚡⟩"]

branding:
  agent_name: "Cyber Agent"
  response_label: " ⚡ Cyber "

tool_prefix: "▏"
```

## Hermes Mod — 视觉皮肤编辑器

[Hermes Mod](https://github.com/cocktailpeanut/hermes-mod) 是一个社区构建的 Web UI，用于可视化创建和管理皮肤。无需手动编写 YAML，您可以获得带有实时预览的点击式编辑器。

![Hermes Mod 皮肤编辑器](https://raw.githubusercontent.com/cocktailpeanut/hermes-mod/master/nous.png)

**它的功能：**

- 列出所有内置和自定义皮肤
- 将任何皮肤打开到视觉编辑器中，包含所有 Hermes 皮肤字段（颜色、spinner、品牌、工具前缀、工具 emoji）
- 从文本提示生成 `banner_logo` 文本艺术
- 将上传的图像（PNG、JPG、GIF、WEBP）转换为 `banner_hero` ASCII 艺术，具有多种渲染样式（盲文、ASCII 坡道、块、点）
- 直接保存到 `~/.hermes/skins/`
- 通过更新 `~/.hermes/config.yaml` 激活皮肤
- 显示生成的 YAML 和实时预览

### 安装

**选项 1 — Pinokio（一键）：**

在 [pinokio.computer](https://pinokio.computer) 上找到它并一键安装。

**选项 2 — npx（从终端最快）：**

```bash
npx -y hermes-mod
```

**选项 3 — 手动：**

```bash
git clone https://github.com/cocktailpeanut/hermes-mod.git
cd hermes-mod/app
npm install
npm start
```

### 使用

1. 启动应用程序（通过 Pinokio 或终端）。
2. 打开 **Skin Studio**。
3. 选择要编辑的内置或自定义皮肤。
4. 从文本生成徽标和/或上传图像作为英雄艺术。选择渲染样式和宽度。
5. 编辑颜色、spinner、品牌和其他字段。
6. 点击 **Save** 将皮肤 YAML 写入 `~/.hermes/skins/`。
7. 点击 **Activate** 将其设置为当前皮肤（更新 `config.yaml` 中的 `display.skin`）。

Hermes Mod 尊重 `HERMES_HOME` 环境变量，因此它也适用于 [配置文件](/docs/user-guide/profiles)。

## 操作说明

- 内置皮肤从 `hermes_cli/skin_engine.py` 加载。
- 未知皮肤自动回退到 `default`。
- `/skin` 立即更新当前会话的活动 CLI 主题。
- `~/.hermes/skins/` 中的用户皮肤优先于同名的内置皮肤。
- 通过 `/skin` 进行的皮肤更改仅在会话期间有效。要将皮肤设置为永久默认值，请在 `config.yaml` 中设置。
- `banner_logo` 和 `banner_hero` 字段支持 Rich 控制台标记（例如，`[bold #FF0000]text[/]`）用于彩色 ASCII 艺术。