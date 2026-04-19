"""Slash command handler for /workspace in the interactive CLI.

Parses /workspace [subcommand] [args] and formats output with Rich.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console


def handle_workspace_slash(cmd: str, console: Optional[Console] = None) -> None:
    console = console or Console()
    parts = cmd.strip().split()
    if parts and parts[0].lower() in ("/workspace", "workspace"):
        parts = parts[1:]

    if not parts:
        _print_status(console)
        return

    action = parts[0].lower()

    if action == "status":
        _print_status(console)
    elif action == "index":
        _print_index(console)
    elif action == "list":
        _print_list(console)
    elif action == "search":
        query = " ".join(parts[1:]).strip()
        if not query:
            console.print("Usage: /workspace search <query>")
            return
        _print_search(console, query)
    elif action == "retrieve":
        path = parts[1] if len(parts) > 1 else ""
        if not path:
            console.print("Usage: /workspace retrieve <path>")
            return
        _print_retrieve(console, path)
    elif action == "delete":
        path = parts[1] if len(parts) > 1 else ""
        if not path:
            console.print("Usage: /workspace delete <path>")
            return
        _print_delete(console, path)
    elif action == "roots":
        _print_roots(console, parts[1:])
    else:
        console.print(
            "Usage: /workspace [status|index|list|search <query>"
            "|retrieve <path>|delete <path>|roots ...]"
        )


def _get_indexer_and_config():
    from workspace import get_indexer
    from workspace.config import load_workspace_config

    config = load_workspace_config()
    if not config.enabled:
        return None, config
    return get_indexer(config), config


def _print_status(console: Console) -> None:
    indexer, config = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return
    info = indexer.status()
    if not info:
        console.print("No status available.")
        return
    for k, v in info.items():
        if k == "db_size_bytes":
            console.print(f"  {k}: {v / (1024 * 1024):.1f} MB")
        else:
            console.print(f"  {k}: {v}")


def _print_search(console: Console, query: str) -> None:
    indexer, _ = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return
    results = indexer.search(query, limit=20)
    if not results:
        console.print("No results found.")
        return
    for r in results:
        section = f"  {r.section}" if r.section else ""
        console.print(
            f"\n{r.path}:{r.line_start}-{r.line_end} "
            f"(score: {r.score:.1f}){section}"
        )
        snippet = r.content[:200].replace("\n", " ")
        if len(r.content) > 200:
            snippet += "..."
        console.print(f"  {snippet}")


def _print_list(console: Console) -> None:
    indexer, _ = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return
    files = indexer.list_files()
    if not files:
        console.print("No files indexed.")
        return
    console.print(f"{len(files)} indexed files:\n")
    for f in files:
        size_kb = f.get("size_bytes", 0) / 1024
        chunks = f.get("chunks", 0)
        console.print(f"  {f['path']}  ({size_kb:.0f} KB, {chunks} chunks)")


def _print_retrieve(console: Console, raw_path: str) -> None:
    indexer, _ = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return
    path = str(Path(raw_path).expanduser().resolve())
    results = indexer.retrieve(path)
    if not results:
        console.print(f"No indexed chunks for: {path}")
        return
    console.print(f"{len(results)} chunks for {path}:\n")
    for r in results:
        section = f"  [{r.section}]" if r.section else ""
        console.print(f"  chunk {r.chunk_index}: lines {r.line_start}-{r.line_end}{section}")
        snippet = r.content[:200].replace("\n", " ")
        if len(r.content) > 200:
            snippet += "..."
        console.print(f"    {snippet}\n")


def _print_delete(console: Console, raw_path: str) -> None:
    indexer, _ = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return
    path = str(Path(raw_path).expanduser().resolve())
    deleted = indexer.delete(path)
    if deleted:
        console.print(f"Deleted from index: {path}")
    else:
        console.print(f"Not found in index: {path}")


def _print_index(console: Console) -> None:
    indexer, _ = _get_indexer_and_config()
    if indexer is None:
        console.print("[bold red]Workspace is disabled[/]")
        return

    def _progress(current: int, total: int, path: str) -> None:
        name = Path(path).name
        console.print(f"  [{current}/{total}] {name}", highlight=False)

    summary = indexer.index(progress=_progress)
    console.print(
        f"\nIndexed {summary.files_indexed} files "
        f"({summary.chunks_created} chunks), "
        f"skipped {summary.files_skipped}, "
        f"errored {summary.files_errored}, "
        f"pruned {summary.files_pruned} stale. "
        f"Took {summary.duration_seconds:.1f}s."
    )
    if summary.errors:
        console.print("\n[bold red]Errors:[/]")
        for err in summary.errors:
            console.print(f"  [{err.stage}] {err.path}: {err.message}")


def _print_roots(console: Console, parts: list[str]) -> None:
    from workspace.config import load_workspace_config

    if not parts or parts[0].lower() == "list":
        config = load_workspace_config()
        roots = config.knowledgebase.roots
        if not roots:
            console.print("No workspace roots configured.")
            return
        for r in roots:
            flag = " (recursive)" if r.recursive else ""
            console.print(f"  {r.path}{flag}")
        return

    action = parts[0].lower()
    if action == "add":
        if len(parts) < 2:
            console.print("Usage: /workspace roots add <path> [--recursive]")
            return
        path = str(Path(parts[1]).expanduser().resolve())
        recursive = "--recursive" in parts[2:]
        from workspace.commands import _add_root

        _add_root(path, recursive)
        console.print(f"Added workspace root: {path} (recursive={recursive})")
    elif action == "remove":
        if len(parts) < 2:
            console.print("Usage: /workspace roots remove <path>")
            return
        path = str(Path(parts[1]).expanduser().resolve())
        from workspace.commands import _remove_root

        _remove_root(path)
        console.print(f"Removed workspace root: {path}")
    else:
        console.print("Usage: /workspace roots [list|add|remove]")
