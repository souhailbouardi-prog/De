"""Workspace configuration — Pydantic models.

Builds WorkspaceConfig from the main hermes config.yaml dict.
Defaults come from the model field definitions.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from workspace.constants import get_workspace_root
from workspace.types import WorkspaceRoot


class ChunkingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    chunk_size: int = 512
    overlap: int | None = None

    @field_validator("chunk_size")
    @classmethod
    def _chunk_size_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"chunk_size must be > 0, got {v}")
        return v

    @model_validator(mode="after")
    def _clamp_overlap(self) -> "ChunkingConfig":
        if self.overlap is None:
            object.__setattr__(self, "overlap", min(32, max(0, self.chunk_size - 1)))
        elif self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError(
                f"overlap must be >= 0 and < chunk_size ({self.chunk_size}), got {self.overlap}"
            )
        return self


class IndexingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_file_mb: int = 10

    @field_validator("max_file_mb")
    @classmethod
    def _positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"max_file_mb must be > 0, got {v}")
        return v


class SearchConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    default_limit: int = 20

    @field_validator("default_limit")
    @classmethod
    def _at_least_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"default_limit must be >= 1, got {v}")
        return v


class ParsingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    default: str = "markitdown"
    overrides: dict[str, str] = {}


class KnowledgebaseConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    roots: list[WorkspaceRoot] = []
    chunking: ChunkingConfig = ChunkingConfig()
    indexing: IndexingConfig = IndexingConfig()
    search: SearchConfig = SearchConfig()
    parsing: ParsingConfig = ParsingConfig()


class WorkspaceConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    enabled: bool = True
    workspace_root: Path = Path.home() / ".hermes" / "workspace"
    indexer: str = "default"
    plugin_config: dict = {}
    knowledgebase: KnowledgebaseConfig = KnowledgebaseConfig()


def load_workspace_config(raw: dict | None = None) -> WorkspaceConfig:
    if raw is None:
        from hermes_cli.config import load_config

        raw = load_config()
    ws = raw.get("workspace", {})
    kb = raw.get("knowledgebase", {})
    from hermes_constants import get_hermes_home

    hermes_home = get_hermes_home()
    return WorkspaceConfig(
        enabled=ws.get("enabled", True),
        workspace_root=get_workspace_root(hermes_home, ws.get("path", "")),
        indexer=ws.get("indexer", "default"),
        plugin_config=ws.get("plugin_config", {}),
        knowledgebase=KnowledgebaseConfig.model_validate(kb),
    )
