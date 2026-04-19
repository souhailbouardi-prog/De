# tests/workspace/test_base_indexer.py
"""Tests for BaseIndexer ABC contract."""

import pytest

from workspace.base import BaseIndexer


def test_base_indexer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError, match="abstract"):
        BaseIndexer(None)


def test_concrete_subclass_must_implement_index_and_search():
    class Incomplete(BaseIndexer):
        def __init__(self, config):
            pass

    with pytest.raises(TypeError, match="abstract"):
        Incomplete(None)


def test_concrete_subclass_with_both_methods_instantiates():
    class Complete(BaseIndexer):
        def __init__(self, config):
            self._config = config

        def index(self, *, progress=None):
            from workspace.types import IndexSummary

            return IndexSummary(
                files_indexed=0,
                files_skipped=0,
                files_pruned=0,
                files_errored=0,
                chunks_created=0,
                duration_seconds=0.0,
                errors=[],
                errors_truncated=False,
            )

        def search(self, query, *, limit=20, path_prefix=None, file_glob=None):
            return []

    indexer = Complete(None)
    assert indexer.status() == {}
