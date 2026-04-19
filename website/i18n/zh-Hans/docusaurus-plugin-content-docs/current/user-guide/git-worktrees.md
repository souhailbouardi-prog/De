---
sidebar_position: 3
sidebar_label: "Git Worktrees"
title: "Git Worktrees"
description: "使用 git worktrees 和隔离的检出在同一仓库上安全运行多个 Hermes 智能体"
---

# Git Worktrees

Hermes Agent 通常用于大型、长期存在的仓库。当您想要：

- 在同一项目上**并行运行多个智能体**，或
- 将实验性重构与主分支隔离，

Git **worktrees** 是为每个智能体提供自己的检出而不复制整个仓库的最安全方法。

本页展示如何将 worktrees 与 Hermes 结合使用，以便每个会话都有一个干净、隔离的工作目录。

## 为什么在 Hermes 中使用 Worktrees？

Hermes 将**当前工作目录**视为项目根目录：

- CLI：运行 `hermes` 或 `hermes chat` 的目录
- 消息网关：由 `MESSAGING_CWD` 设置的目录

如果您在**同一检出**中运行多个智能体，它们的更改可能会相互干扰：

- 一个智能体可能会删除或重写另一个智能体正在使用的文件。
- 很难理解哪些更改属于哪个实验。

使用 worktrees，每个智能体获得：

- 它自己的**分支和工作目录**
- 它自己的检查点管理器历史记录，用于 `/rollback`

另请参阅：[检查点和 /rollback](./checkpoints-and-rollback.md)。

## 快速开始：创建 Worktree

从您的主仓库（包含 `.git/`），为功能分支创建新的 worktree：

```bash
# 从主仓库根目录
cd /path/to/your/repo

# 在 ../repo-feature 中创建新分支和 worktree
git worktree add ../repo-feature feature/hermes-experiment
```

这创建了：

- 一个新目录：`../repo-feature`
- 一个新分支：在该目录中检出的 `feature/hermes-experiment`

现在您可以 `cd` 到新的 worktree 并在那里运行 Hermes：

```bash
cd ../repo-feature

# 在 worktree 中启动 Hermes
hermes
```

Hermes 将：

- 将 `../repo-feature` 视为项目根目录。
- 使用该目录进行上下文文件、代码编辑和工具操作。
- 使用**单独的检查点历史记录**，用于 `/rollback`，范围限定于此 worktree。

## 并行运行多个智能体

您可以创建多个 worktree，每个都有自己的分支：

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

- 在自己的分支上工作（`feature/hermes-a` vs `feature/hermes-b`）。
- 在不同的影子仓库哈希下写入检查点（派生自 worktree 路径）。
- 可以独立使用 `/rollback` 而不影响另一个。

这在以下情况下特别有用：

- 运行批量重构。
- 尝试同一任务的不同方法。
- 将 CLI + 网关会话配对到同一上游仓库。

## 安全清理 Worktrees

当您完成实验时：

1. 决定是保留还是丢弃工作。
2. 如果您想保留它：
   - 像往常一样将分支合并到主分支。
3. 移除 worktree：

```bash
cd /path/to/your/repo

# 移除 worktree 目录及其引用
git worktree remove ../repo-feature
```

注意事项：

- `git worktree remove` 将拒绝移除具有未提交更改的 worktree，除非您强制它。
- 移除 worktree **不会**自动删除分支；您可以使用普通的 `git branch` 命令删除或保留分支。
- 当您移除 worktree 时，`~/.hermes/checkpoints/` 下的 Hermes 检查点数据不会自动修剪，但它通常非常小。

## 最佳实践

- **每个 Hermes 实验一个 worktree**
  - 为每个重大更改创建专用分支/worktree。
  - 这使差异集中，PR 小且可审查。
- **以实验命名分支**
  - 例如 `feature/hermes-checkpoints-docs`、`feature/hermes-refactor-tests`。
- **频繁提交**
  - 使用 git 提交进行高级别里程碑。
  - 使用 [检查点和 /rollback](./checkpoints-and-rollback.md) 作为工具驱动编辑的安全网。
- **使用 worktree 时避免从裸仓库根目录运行 Hermes**
  - 最好使用 worktree 目录，以便每个智能体都有明确的范围。

## 使用 `hermes -w`（自动 Worktree 模式）

Hermes 有一个内置的 `-w` 标志，可以**自动创建一个带有自己分支的一次性 git worktree**。您不需要手动设置 worktree — 只需 `cd` 到您的仓库并运行：

```bash
cd /path/to/your/repo
hermes -w
```

Hermes 将：

- 在您仓库内的 `.worktrees/` 下创建一个临时 worktree。
- 检出一个隔离的分支（例如 `hermes/hermes-<hash>`）。
- 在该 worktree 内运行完整的 CLI 会话。

这是获得 worktree 隔离的最简单方法。您还可以将其与单个查询结合使用：

```bash
hermes -w -q "修复问题 #123"
```

对于并行智能体，打开多个终端并在每个终端中运行 `hermes -w` — 每次调用都会自动获得自己的 worktree 和分支。

## 总结

- 使用 **git worktrees** 为每个 Hermes 会话提供自己的干净检出。
- 使用 **分支** 捕获实验的高级历史记录。
- 使用 **检查点 + `/rollback`** 从每个 worktree 内的错误中恢复。

这种组合为您提供了：

- 强有力的保证，确保不同的智能体和实验不会相互干扰。
- 快速的迭代周期，可以轻松从错误的编辑中恢复。
- 干净、可审查的拉取请求。