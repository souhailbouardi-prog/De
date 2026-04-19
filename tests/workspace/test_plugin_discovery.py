"""Tests for workspace plugin discovery."""

import textwrap


def test_load_workspace_indexer_returns_none_for_unknown():
    from plugins.workspace import load_workspace_indexer

    result = load_workspace_indexer("nonexistent_plugin_xyz")
    assert result is None


def test_load_workspace_indexer_finds_register_pattern(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "fake_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        textwrap.dedent("""\
        from workspace.base import BaseIndexer
        from workspace.types import IndexSummary

        class FakeIndexer(BaseIndexer):
            def __init__(self, config):
                self._config = config
            def index(self, *, progress=None):
                return IndexSummary(
                    files_indexed=0, files_skipped=0, files_pruned=0,
                    files_errored=0, chunks_created=0, duration_seconds=0.0,
                    errors=[], errors_truncated=False,
                )
            def search(self, query, *, limit=20, path_prefix=None, file_glob=None):
                return []

        def register(ctx):
            ctx.register_workspace_indexer(FakeIndexer)
        """),
        encoding="utf-8",
    )

    from plugins.workspace import _load_indexer_from_dir

    cls = _load_indexer_from_dir(plugin_dir)
    assert cls is not None
    assert cls.__name__ == "FakeIndexer"


def test_load_workspace_indexer_finds_bare_subclass(tmp_path):
    plugin_dir = tmp_path / "bare_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        textwrap.dedent("""\
        from workspace.base import BaseIndexer
        from workspace.types import IndexSummary

        class BareIndexer(BaseIndexer):
            def __init__(self, config):
                self._config = config
            def index(self, *, progress=None):
                return IndexSummary(
                    files_indexed=0, files_skipped=0, files_pruned=0,
                    files_errored=0, chunks_created=0, duration_seconds=0.0,
                    errors=[], errors_truncated=False,
                )
            def search(self, query, *, limit=20, path_prefix=None, file_glob=None):
                return []
        """),
        encoding="utf-8",
    )

    from plugins.workspace import _load_indexer_from_dir

    cls = _load_indexer_from_dir(plugin_dir)
    assert cls is not None
    assert cls.__name__ == "BareIndexer"


def test_discover_workspace_indexers_returns_list():
    from plugins.workspace import discover_workspace_indexers

    result = discover_workspace_indexers()
    assert isinstance(result, list)
