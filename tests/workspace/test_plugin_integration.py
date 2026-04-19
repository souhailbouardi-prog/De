"""End-to-end integration tests for workspace plugin architecture."""

from workspace import get_indexer
from workspace.base import BaseIndexer
from workspace.config import WorkspaceConfig
from workspace.default import DefaultIndexer


def test_get_indexer_returns_default_when_not_configured(make_workspace_config):
    cfg = make_workspace_config()
    indexer = get_indexer(cfg)
    assert isinstance(indexer, DefaultIndexer)
    assert isinstance(indexer, BaseIndexer)


def test_get_indexer_falls_back_on_unknown_plugin(make_workspace_config):
    cfg = make_workspace_config()
    cfg = WorkspaceConfig(
        workspace_root=cfg.workspace_root,
        indexer="nonexistent_xyz",
    )
    indexer = get_indexer(cfg)
    assert isinstance(indexer, DefaultIndexer)


def test_full_round_trip_through_factory(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(
        cfg.workspace_root / "docs" / "test.md", "# Test\n\nSearchable content here.\n"
    )

    indexer = get_indexer(cfg)
    summary = indexer.index()
    assert summary.files_indexed == 1

    results = indexer.search("searchable")
    assert len(results) > 0
    assert results[0].path.endswith("test.md")


def test_status_works_through_factory(make_workspace_config, write_file):
    cfg = make_workspace_config()
    write_file(cfg.workspace_root / "docs" / "a.md", "# A\n\nContent.\n")

    indexer = get_indexer(cfg)
    indexer.index()

    status = indexer.status()
    assert status["file_count"] >= 1
    assert status["chunk_count"] >= 1
