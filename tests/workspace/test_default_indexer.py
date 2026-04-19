"""Tests for DefaultIndexer — verifies it satisfies BaseIndexer contract."""

from workspace.base import BaseIndexer
from workspace.default import DefaultIndexer
from workspace.types import IndexSummary, SearchResult


def test_default_indexer_is_base_indexer_subclass():
    assert issubclass(DefaultIndexer, BaseIndexer)


def test_default_indexer_indexes_and_searches(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(
        cfg.workspace_root / "docs" / "hello.md", "# Hello\n\nWorld of workspace.\n"
    )

    indexer = DefaultIndexer(cfg)
    summary = indexer.index()

    assert isinstance(summary, IndexSummary)
    assert summary.files_indexed == 1
    assert summary.files_errored == 0

    results = indexer.search("workspace")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


def test_default_indexer_search_respects_limit(make_workspace_config, write_file):
    cfg = make_workspace_config()
    for i in range(5):
        write_file(
            cfg.workspace_root / "docs" / f"doc{i}.md",
            f"# Doc {i}\n\nThis document talks about testing limit param.\n",
        )

    indexer = DefaultIndexer(cfg)
    indexer.index()

    results = indexer.search("document", limit=2)
    assert len(results) <= 2


def test_default_indexer_status_returns_dict(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(cfg.workspace_root / "docs" / "a.md", "# A\n\nContent.\n")

    indexer = DefaultIndexer(cfg)
    indexer.index()

    status = indexer.status()
    assert isinstance(status, dict)
    assert "file_count" in status
    assert "chunk_count" in status
    assert "db_path" in status


def test_default_indexer_index_is_idempotent(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(cfg.workspace_root / "docs" / "a.md", "# A\n\nContent A.\n")

    indexer = DefaultIndexer(cfg)
    first = indexer.index()
    assert first.files_indexed == 1

    second = indexer.index()
    assert second.files_indexed == 0
    assert second.files_skipped >= 1


def test_default_indexer_progress_callback(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(cfg.workspace_root / "docs" / "a.md", "# A\n\nContent.\n")

    calls = []
    indexer = DefaultIndexer(cfg)
    indexer.index(progress=lambda cur, total, path: calls.append((cur, total, path)))

    assert len(calls) > 0
    assert calls[0][0] == 1
    assert calls[0][1] >= 1
