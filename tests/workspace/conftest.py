from pathlib import Path

import pytest

from workspace.config import KnowledgebaseConfig, WorkspaceConfig
from workspace.constants import DEFAULT_IGNORE_PATTERNS


@pytest.fixture
def make_workspace_config(tmp_path: Path):
    def _make(raw: dict | None = None) -> WorkspaceConfig:
        raw = raw or {}
        hermes_home = tmp_path / "cfg_home"
        hermes_home.mkdir(exist_ok=True)
        ws_root = hermes_home / "workspace"
        ws_raw = raw.get("workspace", {})
        kb_raw = raw.get("knowledgebase", {})
        cfg = WorkspaceConfig(
            enabled=ws_raw.get("enabled", True),
            workspace_root=ws_root,
            knowledgebase=KnowledgebaseConfig.model_validate(kb_raw),
        )
        cfg.workspace_root.mkdir(parents=True, exist_ok=True)
        (cfg.workspace_root / ".hermesignore").write_text(
            DEFAULT_IGNORE_PATTERNS + "\n.hermesignore\n",
            encoding="utf-8",
        )
        return cfg

    return _make


@pytest.fixture
def write_file():
    def _write(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return _write
