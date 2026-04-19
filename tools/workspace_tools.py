"""Workspace tools — search, index, and manage the workspace knowledgebase.

Each workspace operation is a separate tool with a focused schema.
All tools register under toolset="workspace" and are gated on
workspace.enabled in the hermes config.
"""

from pathlib import Path

from tools.registry import registry, tool_error, tool_result


def _check_workspace_enabled() -> bool:
    try:
        from workspace.config import load_workspace_config

        return load_workspace_config().enabled
    except Exception:
        return False


def _get_indexer():
    from workspace import get_indexer
    from workspace.config import load_workspace_config

    return get_indexer(load_workspace_config())


# ---------------------------------------------------------------------------
# workspace_search
# ---------------------------------------------------------------------------

SEARCH_SCHEMA = {
    "name": "workspace_search",
    "description": (
        "BM25 full-text search across files indexed in the workspace "
        "knowledgebase. Returns ranked chunks with path, line range, "
        "score, and content snippet. "
        "PREFER THIS over terminal grep/find/cat when the user asks "
        "about indexed code or documentation — it is faster, returns "
        "ranked results, and avoids scanning the filesystem. Fall back "
        "to reading files directly only if the search output is "
        "insufficient for answering."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "path_prefix": {
                "type": "string",
                "description": "Filter results to files under this absolute path prefix.",
            },
            "file_glob": {
                "type": "string",
                "description": "Filename glob filter, e.g. '*.md', '*.py'.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results (default 20).",
                "default": 20,
            },
        },
        "required": ["query"],
    },
}


def _handle_search(args: dict, **kwargs) -> str:
    try:
        from workspace.constants import resolve_path_prefix

        query = args.get("query", "").strip()
        if not query:
            return tool_error("query is required")
        indexer = _get_indexer()
        results = indexer.search(
            query,
            limit=args.get("limit", 20),
            path_prefix=resolve_path_prefix(args.get("path_prefix")),
            file_glob=args.get("file_glob"),
        )
        return tool_result([r.to_dict() for r in results])
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# workspace_index
# ---------------------------------------------------------------------------

INDEX_SCHEMA = {
    "name": "workspace_index",
    "description": (
        "Rebuild the workspace index. Scans all configured roots, "
        "chunks files, and updates the FTS5 search index. "
        "This is expensive — only call when files have changed."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


def _handle_index(args: dict, **kwargs) -> str:
    try:
        indexer = _get_indexer()
        summary = indexer.index()
        return tool_result(summary.to_dict())
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# workspace_status
# ---------------------------------------------------------------------------

STATUS_SCHEMA = {
    "name": "workspace_status",
    "description": (
        "Show workspace index statistics: file count, chunk count, "
        "database size, and database path."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


def _handle_status(args: dict, **kwargs) -> str:
    try:
        indexer = _get_indexer()
        return tool_result(indexer.status())
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# workspace_list
# ---------------------------------------------------------------------------

LIST_SCHEMA = {
    "name": "workspace_list",
    "description": "List all files currently in the workspace index with size and chunk count.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of files to return (default 50).",
                "default": 50,
            },
        },
    },
}


def _handle_list(args: dict, **kwargs) -> str:
    try:
        indexer = _get_indexer()
        files = indexer.list_files()
        limit = args.get("limit", 50)
        return tool_result(files[:limit])
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# workspace_retrieve
# ---------------------------------------------------------------------------

RETRIEVE_SCHEMA = {
    "name": "workspace_retrieve",
    "description": (
        "Get all indexed chunks for a specific file by its absolute path. "
        "Unlike search, this returns every chunk — useful when you know "
        "which file you want but need its full indexed content."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file.",
            },
        },
        "required": ["path"],
    },
}


def _handle_retrieve(args: dict, **kwargs) -> str:
    try:
        raw_path = args.get("path", "")
        if not raw_path:
            return tool_error("path is required")
        resolved = str(Path(raw_path).expanduser().resolve())
        indexer = _get_indexer()
        results = indexer.retrieve(resolved)
        return tool_result({"path": resolved, "chunks": [r.to_dict() for r in results]})
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# workspace_delete
# ---------------------------------------------------------------------------

DELETE_SCHEMA = {
    "name": "workspace_delete",
    "description": "Remove a file and its chunks from the workspace index.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to remove from the index.",
            },
        },
        "required": ["path"],
    },
}


def _handle_delete(args: dict, **kwargs) -> str:
    try:
        raw_path = args.get("path", "")
        if not raw_path:
            return tool_error("path is required")
        resolved = str(Path(raw_path).expanduser().resolve())
        indexer = _get_indexer()
        deleted = indexer.delete(resolved)
        return tool_result({"path": resolved, "deleted": deleted})
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="workspace_search",
    toolset="workspace",
    schema=SEARCH_SCHEMA,
    handler=_handle_search,
    check_fn=_check_workspace_enabled,
)

registry.register(
    name="workspace_index",
    toolset="workspace",
    schema=INDEX_SCHEMA,
    handler=_handle_index,
    check_fn=_check_workspace_enabled,
)

registry.register(
    name="workspace_status",
    toolset="workspace",
    schema=STATUS_SCHEMA,
    handler=_handle_status,
    check_fn=_check_workspace_enabled,
)

registry.register(
    name="workspace_list",
    toolset="workspace",
    schema=LIST_SCHEMA,
    handler=_handle_list,
    check_fn=_check_workspace_enabled,
)

registry.register(
    name="workspace_retrieve",
    toolset="workspace",
    schema=RETRIEVE_SCHEMA,
    handler=_handle_retrieve,
    check_fn=_check_workspace_enabled,
)

registry.register(
    name="workspace_delete",
    toolset="workspace",
    schema=DELETE_SCHEMA,
    handler=_handle_delete,
    check_fn=_check_workspace_enabled,
)
