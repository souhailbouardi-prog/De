---
sidebar_position: 3
sidebar_label: "Git 工作树"
title: "Git 工作树"
description: "使用 git 工作树和隔离检出，在同一个仓库上安全运行多个 Hermes 代理"
---

# Git 工作树

Hermes Agent 通常用于大型、长期存在的仓库。当您想要：

- 在同一个项目上并行运行 **多个代理**，或者
- 将实验性重构与主分支隔离开来时，

Git **工作树** 是为每个代理提供自己的检出而不复制整个仓库的最安全方式。

本页面展示了如何将工作树与 Hermes 结合使用，以便每个会话都有一个干净、隔离的工作目录。

## 为什么在 Hermes 中使用工作树？

Hermes 将 **当前工作目录** 视为项目根目录：

- CLI：您运行 `hermes` 或 `hermes chat` 的目录
- 消息网关：由 `MESSAGING_CWD` 设置的目录

如果在 **同一个检出** 中运行多个代理，它们的更改可能会相互干扰：

- 一个代理可能会删除或重写另一个代理正在使用的文件。
- 更难理解哪些更改属于哪个实验。

使用工作树，每个代理获得：

- 它自己的 **分支和工作目录**
- 它自己的 **检查点管理器历史记录**，用于 `/rollback`

另请参阅：[检查点和 /rollback](./checkpoints-and-rollback.zh.md)。

## 快速入门：创建工作树

从您的主仓库（包含 `.git/`），为功能分支创建一个新的工作树：

```bash
# 从主仓库根目录
cd /path/to/your/repo

# 在 ../repo-feature 中创建新分支和工作树
git worktree add ../repo-feature feature/hermes-experiment
```

这会创建：

- 一个新目录：`../repo-feature`
- 一个新分支：在该目录中检出的 `feature/hermes-experiment`

现在您可以 `cd` 到新的工作树并在那里运行 Hermes：

```bash
cd ../repo-feature

# 在工作树中启动 Hermes
hermes
```

Hermes 将：

- 将 `../repo-feature` 视为项目根目录。
- 使用该目录处理上下文文件、代码编辑和工具。
- 为作用于此工作树的 `/rollback` 使用 **单独的检查点历史记录**。

## 并行运行多个代理

您可以创建多个工作树，每个都有自己的分支：

```bash
cd /path/to/your/repo

git worktree add ../repo-experiment-a feature/hermes-a
git worktree add ../repo-experiment-b feature/hermes-b
```

在单独的终端中：

```bash
# 终端 1
cd ../repo-experiment-a
hermes

# 终端 2
cd ../repo-experiment-b
hermes
```

每个 Hermes 进程：

- 在自己的分支上工作（`feature/hermes-a` 与 `feature/hermes-b`）。
- 在不同的影子仓库哈希下写入检查点（从工作树路径派生）。
- 可以独立使用 `/rollback` 而不影响另一个。

这在以下情况下特别有用：

- 运行批量重构。
- 尝试不同方法完成同一任务。
- 将 CLI + 网关会话配对到同一个上游仓库。

## 安全清理工作树

当您完成实验后：

1. 决定是保留还是丢弃工作。
2. 如果想要保留：
   - 像往常一样将分支合并到主分支。
3. 删除工作树：

```bash
cd /path/to/your/repo

# 删除工作树目录及其引用
git worktree remove ../repo-feature
```

注意事项：

- `git worktree remove` 将拒绝删除具有未提交更改的工作树，除非您强制删除。
- 删除工作树不会 **自动** 删除分支；您可以使用普通的 `git branch` 命令删除或保留分支。
- 删除工作树时，`~/.hermes/checkpoints/` 下的 Hermes 检查点数据不会自动清理，但它通常非常小。

## 最佳实践

- **每个 Hermes 实验一个工作树**
  - 为每个实质性更改创建专用的分支/工作树。
  - 这使差异保持集中，PR 小且可审查。
- **按实验命名分支**
  - 例如 `feature/hermes-checkpoints-docs`、`feature/hermes-refactor-tests`。
- **频繁提交**
  - 使用 git 提交记录高级里程碑。
  - 使用 [检查点和 /rollback](./checkpoints-and-rollback.zh.md) 作为工具驱动编辑之间的安全网。
- **使用工作树时避免从裸仓库根目录运行 Hermes**
  - 改用工作树目录，这样每个代理都有明确的范围。

## 使用 `hermes -w`（自动工作树模式）

Hermes 有一个内置的 `-w` 标志，可以 **自动创建一个可丢弃的 git 工作树** 及其自己的分支。您不需要手动设置工作树 — 只需 `cd` 到您的仓库并运行：

```bash
cd /path/to/your/repo
hermes -w
```

Hermes 将：

- 在您的仓库内的 `.worktrees/` 下创建一个临时工作树。
- 检出一个隔离分支（例如 `hermes/hermes-<hash>`）。
- 在该工作树内运行完整的 CLI 会话。

这是获得工作树隔离的最简单方法。您也可以将它与单个查询结合使用：

```bash
hermes -w -q "Fix issue #123"
```

对于并行代理，打开多个终端并在每个终端中运行 `hermes -w` — 每次调用都会自动获得自己的工作树和分支。

## 总结

- 使用 **git 工作树** 为每个 Hermes 会话提供自己的干净检出。
- 使用 **分支** 记录您实验的高级历史记录。
- 使用 **检查点 + `/rollback`** 在每个工作树内从错误中恢复。

这种组合为您提供：

- 强有力的保证，确保不同代理和实验不会相互干扰。
- 快速的迭代周期，易于从错误的编辑中恢复。
- 干净、可审查的拉取请求。
