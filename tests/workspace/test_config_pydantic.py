"""Tests for Pydantic config models."""

import pytest
from pydantic import ValidationError

from workspace.config import (
    ChunkingConfig,
    IndexingConfig,
    KnowledgebaseConfig,
    SearchConfig,
    WorkspaceConfig,
    load_workspace_config,
)


def test_chunking_config_defaults():
    c = ChunkingConfig()
    assert c.chunk_size == 512
    assert c.overlap == 32


def test_chunking_config_clamps_overlap_when_none():
    c = ChunkingConfig(chunk_size=20)
    assert c.overlap == 19


def test_chunking_config_explicit_overlap():
    c = ChunkingConfig(chunk_size=512, overlap=64)
    assert c.overlap == 64


def test_chunking_config_rejects_zero_chunk_size():
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=0)


def test_chunking_config_rejects_negative_chunk_size():
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=-1)


def test_chunking_config_rejects_overlap_gte_chunk_size():
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=100, overlap=100)


def test_chunking_config_rejects_negative_overlap():
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=100, overlap=-1)


def test_indexing_config_rejects_zero():
    with pytest.raises(ValidationError):
        IndexingConfig(max_file_mb=0)


def test_search_config_rejects_zero():
    with pytest.raises(ValidationError):
        SearchConfig(default_limit=0)


def test_workspace_config_defaults():
    c = WorkspaceConfig()
    assert c.enabled is True
    assert c.indexer == "default"
    assert c.plugin_config == {}


def test_workspace_config_is_frozen():
    c = WorkspaceConfig()
    with pytest.raises(ValidationError):
        c.enabled = False


def test_knowledgebase_config_from_dict():
    kb = KnowledgebaseConfig.model_validate(
        {
            "roots": [{"path": "/tmp/test", "recursive": True}],
            "chunking": {"chunk_size": 256},
        }
    )
    assert len(kb.roots) == 1
    assert kb.roots[0].path == "/tmp/test"
    assert kb.roots[0].recursive is True
    assert kb.chunking.chunk_size == 256


def test_deprecated_keys_are_silently_ignored():
    kb = KnowledgebaseConfig.model_validate(
        {
            "chunking": {
                "strategy": "semantic",
                "threshold": 0,
                "chunk_size": 128,
            }
        }
    )
    assert kb.chunking.chunk_size == 128
    assert not hasattr(kb.chunking, "strategy")


def test_load_workspace_config_from_raw_dict(tmp_path):
    raw = {
        "workspace": {
            "enabled": True,
            "path": str(tmp_path / "ws"),
            "indexer": "witchcraft",
            "plugin_config": {"db_path": "/tmp/wc"},
        },
        "knowledgebase": {
            "chunking": {"chunk_size": 1024},
        },
    }
    cfg = load_workspace_config(raw)
    assert cfg.indexer == "witchcraft"
    assert cfg.plugin_config == {"db_path": "/tmp/wc"}
    assert cfg.knowledgebase.chunking.chunk_size == 1024
    assert cfg.workspace_root == (tmp_path / "ws").resolve()


def test_load_workspace_config_default_when_empty():
    raw = {}
    cfg = load_workspace_config(raw)
    assert cfg.enabled is True
    assert cfg.indexer == "default"
