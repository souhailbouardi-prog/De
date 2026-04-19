---
sidebar_position: 16
title: "仪表板插件"
description: "为 Hermes 网页仪表板构建自定义标签页和扩展"
---

# 仪表板插件

仪表板插件允许您向网页仪表板添加自定义标签页。插件可以显示自己的 UI、调用 Hermes API，以及可选地注册后端端点 — 所有这些都不需要修改仪表板源代码。

## 快速开始

创建一个带有清单和 JS 文件的插件目录：

```bash
mkdir -p ~/.hermes/plugins/my-plugin/dashboard/dist
```

**manifest.json：**

```json
{
  "name": "my-plugin",
  "label": "我的插件",
  "icon": "Sparkles",
  "version": "1.0.0",
  "tab": {
    "path": "/my-plugin",
    "position": "after:skills"
  },
  "entry": "dist/index.js"
}
```

**dist/index.js：**

```javascript
(function () {
  var SDK = window.__HERMES_PLUGIN_SDK__;
  var React = SDK.React;
  var Card = SDK.components.Card;
  var CardHeader = SDK.components.CardHeader;
  var CardTitle = SDK.components.CardTitle;
  var CardContent = SDK.components.CardContent;

  function MyPage() {
    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement(CardTitle, null, "我的插件")
      ),
      React.createElement(CardContent, null,
        React.createElement("p", { className: "text-sm text-muted-foreground" },
          "来自我的自定义仪表板标签页！"
        )
      )
    );
  }

  window.__HERMES_PLUGINS__.register("my-plugin", MyPage);
})();
```

刷新仪表板 — 您的标签页会出现在导航栏中。

## 插件结构

插件位于标准的 `~/.hermes/plugins/` 目录中。仪表板扩展是一个 `dashboard/` 子文件夹：

```
~/.hermes/plugins/my-plugin/
  plugin.yaml              # 可选 — 现有的 CLI/网关插件清单
  __init__.py              # 可选 — 现有的 CLI/网关钩子
  dashboard/               # 仪表板扩展
    manifest.json          # 必需 — 标签页配置、图标、入口点
    dist/
      index.js             # 必需 — 预构建的 JS 捆绑包
      style.css            # 可选 — 自定义 CSS
    plugin_api.py          # 可选 — 后端 API 路由
```

单个插件可以从一个目录扩展 CLI/网关（通过 `plugin.yaml` + `__init__.py`）和仪表板（通过 `dashboard/`）。

## 清单参考

`manifest.json` 文件向仪表板描述您的插件：

```json
{
  "name": "my-plugin",
  "label": "我的插件",
  "description": "此插件的功能",
  "icon": "Sparkles",
  "version": "1.0.0",
  "tab": {
    "path": "/my-plugin",
    "position": "after:skills"
  },
  "entry": "dist/index.js",
  "css": "dist/style.css",
  "api": "plugin_api.py"
}
```

| 字段 | 必需 | 描述 |
|------|------|------|
| `name` | 是 | 唯一的插件标识符（小写，允许连字符） |
| `label` | 是 | 显示在导航标签页中的名称 |
| `description` | 否 | 简短描述 |
| `icon` | 否 | Lucide 图标名称（默认：`Puzzle`） |
| `version` | 否 | 语义化版本字符串 |
| `tab.path` | 是 | 标签页的 URL 路径（例如 `/my-plugin`） |
| `tab.position` | 否 | 标签页的插入位置：`end`（默认）、`after:<tab>`、`before:<tab>` |
| `entry` | 是 | 相对于 `dashboard/` 的 JS 捆绑包路径 |
| `css` | 否 | 要注入的 CSS 文件路径 |
| `api` | 否 | 带有 FastAPI 路由的 Python 文件路径 |

### 标签页位置

`position` 字段控制标签页在导航中的显示位置：

- `"end"` — 在所有内置标签页之后（默认）
- `"after:skills"` — 在技能标签页之后
- `"before:config"` — 在配置标签页之前
- `"after:cron"` — 在 Cron 标签页之后

冒号后的是目标标签页的路径段（不带前导斜杠）。

### 可用图标

插件可以使用以下任何 Lucide 图标名称：

`Activity`, `BarChart3`, `Clock`, `Code`, `Database`, `Eye`, `FileText`, `Globe`, `Heart`, `KeyRound`, `MessageSquare`, `Package`, `Puzzle`, `Settings`, `Shield`, `Sparkles`, `Star`, `Terminal`, `Wrench`, `Zap`

未识别的图标名称会回退到 `Puzzle`。

## 插件 SDK

插件不捆绑 React 或 UI 组件 — 它们使用 `window.__HERMES_PLUGIN_SDK__` 上暴露的 SDK。这避免了版本冲突并保持插件捆绑包很小。

### SDK 内容

```javascript
var SDK = window.__HERMES_PLUGIN_SDK__;

// React
SDK.React              // React 实例
SDK.hooks.useState     // React 钩子
SDK.hooks.useEffect
SDK.hooks.useCallback
SDK.hooks.useMemo
SDK.hooks.useRef
SDK.hooks.useContext
SDK.hooks.createContext

// API
SDK.api                // Hermes API 客户端（getStatus、getSessions 等）
SDK.fetchJSON          // 用于自定义端点的原始 fetch — 自动处理认证

// UI 组件（shadcn/ui 风格）
SDK.components.Card
SDK.components.CardHeader
SDK.components.CardTitle
SDK.components.CardContent
SDK.components.Badge
SDK.components.Button
SDK.components.Input
SDK.components.Label
SDK.components.Select
SDK.components.SelectOption
SDK.components.Separator
SDK.components.Tabs
SDK.components.TabsList
SDK.components.TabsTrigger

// 工具
SDK.utils.cn           // Tailwind 类合并器（clsx + twMerge）
SDK.utils.timeAgo      // 从 Unix 时间戳生成 "5m ago"
SDK.utils.isoTimeAgo   // 从 ISO 字符串生成 "5m ago"

// 钩子
SDK.useI18n            // i18n 翻译
SDK.useTheme           // 当前主题信息
```

### 使用 SDK.fetchJSON

用于调用插件的后端 API 端点：

```javascript
SDK.fetchJSON("/api/plugins/my-plugin/data")
  .then(function (result) {
    console.log(result);
  })
  .catch(function (err) {
    console.error("API 调用失败:", err);
  });
```

`fetchJSON` 会自动注入会话认证令牌、处理错误并解析 JSON。

### 使用现有 API 方法

`SDK.api` 对象包含所有内置 Hermes 端点的方法：

```javascript
// 获取代理状态
SDK.api.getStatus().then(function (status) {
  console.log("版本:", status.version);
});

// 列出会话
SDK.api.getSessions(10).then(function (resp) {
  console.log("会话数量:", resp.sessions.length);
});
```

## 后端 API 路由

插件可以通过在清单中设置 `api` 字段来注册 FastAPI 路由。创建一个导出 `router` 的 Python 文件：

```python
# plugin_api.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"items": ["one", "two", "three"]}

@router.post("/action")
async def do_action(body: dict):
    return {"ok": True, "received": body}
```

路由被挂载在 `/api/plugins/<name>/`，因此上面的路由变为：
- `GET /api/plugins/my-plugin/data`
- `POST /api/plugins/my-plugin/action`

插件 API 路由绕过会话令牌认证，因为仪表板服务器只绑定到 localhost。

### 访问 Hermes 内部

后端路由可以从 hermes-agent 代码库导入：

```python
from fastapi import APIRouter
from hermes_state import SessionDB
from hermes_cli.config import load_config

router = APIRouter()

@router.get("/session-count")
async def session_count():
    db = SessionDB()
    try:
        count = len(db.list_sessions(limit=9999))
        return {"count": count}
    finally:
        db.close()
```

## 自定义 CSS

如果您的插件需要自定义样式，添加一个 CSS 文件并在清单中引用它：

```json
{
  "css": "dist/style.css"
}
```

CSS 文件在插件加载时作为 `<link>` 标签注入。使用特定的类名以避免与仪表板现有样式冲突。

```css
/* dist/style.css */
.my-plugin-chart {
  border: 1px solid var(--color-border);
  background: var(--color-card);
  padding: 1rem;
}
```

您可以使用仪表板的 CSS 自定义属性（例如 `--color-border`、`--color-foreground`）来匹配活动主题。

## 插件加载流程

1. 仪表板加载 — `main.tsx` 在 `window.__HERMES_PLUGIN_SDK__` 上暴露 SDK
2. `App.tsx` 调用 `usePlugins()`，获取 `GET /api/dashboard/plugins`
3. 对于每个插件：注入 CSS `<link>`（如果声明），加载 JS `<script>`
4. 插件 JS 调用 `window.__HERMES_PLUGINS__.register(name, Component)`
5. 仪表板将标签页添加到导航并将组件挂载为路由

插件在脚本加载后最多有 2 秒的时间注册。如果插件加载失败，仪表板会继续运行而不包含它。

## 插件发现

仪表板扫描这些目录以查找 `dashboard/manifest.json`：

1. **用户插件：** `~/.hermes/plugins/<name>/dashboard/manifest.json`
2. **捆绑插件：** `<repo>/plugins/<name>/dashboard/manifest.json`
3. **项目插件：** `./.hermes/plugins/<name>/dashboard/manifest.json`（仅当设置了 `HERMES_ENABLE_PROJECT_PLUGINS` 时）

用户插件优先 — 如果同一插件名称存在于多个源中，用户版本获胜。

要在添加新插件后强制重新扫描而不重启服务器：

```bash
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

## 插件 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/dashboard/plugins` | GET | 列出发现的插件 |
| `/api/dashboard/plugins/rescan` | GET | 强制重新扫描新插件 |
| `/dashboard-plugins/<name>/<path>` | GET | 提供插件静态资产 |
| `/api/plugins/<name>/*` | * | 插件注册的 API 路由 |

## 示例插件

存储库在 `plugins/example-dashboard/` 中包含一个示例插件，演示：

- 使用 SDK 组件（Card、Badge、Button）
- 调用后端 API 路由
- 通过 `window.__HERMES_PLUGINS__.register()` 注册

要尝试它，运行 `hermes dashboard` — "示例" 标签页会出现在技能标签页之后。

## 提示

- **无需构建步骤** — 编写纯 JavaScript IIFE。如果您喜欢 JSX，可以使用任何捆绑器（esbuild、Vite、webpack），将 React 作为外部依赖，目标输出为 IIFE。
- **保持捆绑包小** — React 和所有 UI 组件由 SDK 提供。您的捆绑包应该只包含插件逻辑。
- **使用主题变量** — 在 CSS 中引用 `var(--color-*)` 以自动匹配用户选择的任何主题。
- **本地测试** — 运行 `hermes dashboard --no-open` 并使用浏览器开发工具验证您的插件是否正确加载和注册。