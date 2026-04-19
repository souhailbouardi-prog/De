# workspace/base.py
"""BaseIndexer ABC — the plugin contract for workspace backends.

Implementations must define __init__(config), index(), and search().
status() is optional (default returns empty dict).
"""

from abc import ABC, abstractmethod
from typing import Callable

from workspace.config import WorkspaceConfig
from workspace.types import IndexSummary, SearchResult

ProgressCallback = Callable[[int, int, str], None]


class BaseIndexer(ABC):
    @abstractmethod
    def __init__(self, config: WorkspaceConfig) -> None: ...

    @abstractmethod
    def index(self, *, progress: ProgressCallback | None = None) -> IndexSummary: ...

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        path_prefix: str | None = None,
        file_glob: str | None = None,
    ) -> list[SearchResult]: ...

    def status(self) -> dict:
        return {}

    def list_files(self) -> list[dict]:
        return []

    def retrieve(self, path: str) -> list[SearchResult]:
        return []

    def delete(self, path: str) -> bool:
        return False
