"""Utilities for session-scoped repository/workspace pinning."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class RepoContextError(ValueError):
    """Raised when a repo/workspace pin cannot be resolved."""


def resolve_repo_target(raw_path: str, base_dir: str | None = None) -> tuple[str, str, bool]:
    """Resolve *raw_path* into a canonical repo/workspace root.

    Returns ``(root_path, name, is_git_repo)``.

    - Relative paths resolve against ``base_dir`` when provided, otherwise the
      current working directory.
    - File paths are converted to their parent directory.
    - If the path is inside a Git repo, the repo toplevel is returned.
    - Non-Git directories are still allowed and treated as workspace roots.
    """
    raw = str(raw_path or "").strip()
    if not raw:
        raise RepoContextError("Usage: /repo <path> (or /repo clear)")

    base = Path(base_dir or os.getcwd()).expanduser()
    target = Path(raw).expanduser()
    if not target.is_absolute():
        target = base / target

    try:
        target = target.resolve(strict=False)
    except OSError as exc:
        raise RepoContextError(f"Could not resolve path '{raw}': {exc}") from exc

    if target.exists() and target.is_file():
        target = target.parent

    if not target.exists():
        raise RepoContextError(f"Path does not exist: {target}")
    if not target.is_dir():
        raise RepoContextError(f"Path is not a directory: {target}")

    git_root = _git_toplevel(target)
    root = Path(git_root) if git_root else target
    root = root.resolve()
    return str(root), root.name or str(root), bool(git_root)


def build_repo_pin_prompt(repo_root: str | None, repo_name: str | None = None) -> str:
    """Return an ephemeral prompt block describing the pinned repo/workspace."""
    root = str(repo_root or "").strip()
    if not root:
        return ""
    name = str(repo_name or Path(root).name or root).strip()
    return (
        "[SESSION REPOSITORY PIN]\n"
        f"This session is pinned to the repository/workspace `{name}` at `{root}`.\n"
        "Treat this location as the default scope for coding, file edits, searches, "
        "and terminal work. Do not drift to another repository unless the user "
        "explicitly changes the repo pin or clearly asks to work elsewhere."
    )


def _git_toplevel(path: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    top = (proc.stdout or "").strip()
    return top or None
