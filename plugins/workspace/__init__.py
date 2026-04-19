"""Workspace indexer plugin discovery.

Scans ``plugins/workspace/<name>/`` directories for indexer plugins.
Each subdirectory must contain ``__init__.py`` with a class implementing
the BaseIndexer ABC.

Usage:
    from plugins.workspace import discover_workspace_indexers, load_workspace_indexer

    available = discover_workspace_indexers()
    indexer_cls = load_workspace_indexer("witchcraft")
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_WORKSPACE_PLUGINS_DIR = Path(__file__).parent


def discover_workspace_indexers() -> list[tuple[str, str, bool]]:
    """Scan plugins/workspace/ for available indexer plugins.

    Returns list of (name, description, is_available) tuples.
    Does NOT import the indexers — just reads plugin.yaml for metadata
    and does a lightweight availability check.
    """
    results: list[tuple[str, str, bool]] = []
    if not _WORKSPACE_PLUGINS_DIR.is_dir():
        return results

    for child in sorted(_WORKSPACE_PLUGINS_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        init_file = child / "__init__.py"
        if not init_file.exists():
            continue

        # Read description from plugin.yaml if available
        desc = ""
        yaml_file = child / "plugin.yaml"
        if yaml_file.exists():
            try:
                import yaml

                with open(yaml_file) as f:
                    meta = yaml.safe_load(f) or {}
                desc = meta.get("description", "")
            except Exception:
                pass

        # Quick availability check — try loading
        available = True
        try:
            cls = _load_indexer_from_dir(child)
            available = cls is not None
        except Exception:
            available = False

        results.append((child.name, desc, available))

    return results


def load_workspace_indexer(name: str) -> Optional[type]:
    """Load and return a workspace indexer class by name.

    Returns the class (not an instance) so the caller can instantiate
    with ``cls(config)``.  Returns None if not found or on failure.
    """
    engine_dir = _WORKSPACE_PLUGINS_DIR / name
    if not engine_dir.is_dir():
        logger.debug(
            "Workspace indexer '%s' not found in %s", name, _WORKSPACE_PLUGINS_DIR
        )
        return None

    try:
        cls = _load_indexer_from_dir(engine_dir)
        if cls:
            return cls
        logger.warning("Workspace indexer '%s' loaded but no indexer class found", name)
        return None
    except Exception as e:
        logger.warning("Failed to load workspace indexer '%s': %s", name, e)
        return None


def _load_indexer_from_dir(indexer_dir: Path) -> Optional[type]:
    """Import an indexer module and extract the BaseIndexer subclass.

    The module must have either:
    - A register(ctx) function (plugin-style) — we simulate a ctx
    - A top-level class that extends BaseIndexer — we return the class
    """
    name = indexer_dir.name
    module_name = f"plugins.workspace.{name}"
    init_file = indexer_dir / "__init__.py"

    if not init_file.exists():
        return None

    # Check if already loaded
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        # Handle relative imports within the plugin
        # First ensure the parent packages are registered
        for parent in ("plugins", "plugins.workspace"):
            if parent not in sys.modules:
                parent_path = Path(__file__).parent
                if parent == "plugins":
                    parent_path = parent_path.parent
                parent_init = parent_path / "__init__.py"
                if parent_init.exists():
                    spec = importlib.util.spec_from_file_location(
                        parent,
                        str(parent_init),
                        submodule_search_locations=[str(parent_path)],
                    )
                    if spec and spec.loader:
                        parent_mod = importlib.util.module_from_spec(spec)
                        sys.modules[parent] = parent_mod
                        try:
                            spec.loader.exec_module(parent_mod)
                        except Exception:
                            pass

        # Now load the indexer module
        spec = importlib.util.spec_from_file_location(
            module_name,
            str(init_file),
            submodule_search_locations=[str(indexer_dir)],
        )
        if not spec or not spec.loader:
            return None

        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod

        # Register submodules so relative imports work
        for sub_file in indexer_dir.glob("*.py"):
            if sub_file.name == "__init__.py":
                continue
            sub_name = sub_file.stem
            full_sub_name = f"{module_name}.{sub_name}"
            if full_sub_name not in sys.modules:
                sub_spec = importlib.util.spec_from_file_location(
                    full_sub_name, str(sub_file)
                )
                if sub_spec and sub_spec.loader:
                    sub_mod = importlib.util.module_from_spec(sub_spec)
                    sys.modules[full_sub_name] = sub_mod
                    try:
                        sub_spec.loader.exec_module(sub_mod)
                    except Exception as e:
                        logger.debug(
                            "Failed to load submodule %s: %s", full_sub_name, e
                        )

        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            logger.debug("Failed to exec_module %s: %s", module_name, e)
            sys.modules.pop(module_name, None)
            return None

    # Try register(ctx) pattern first (how plugins are written)
    if hasattr(mod, "register"):
        collector = _IndexerCollector()
        try:
            mod.register(collector)
            if collector.indexer_cls:
                return collector.indexer_cls
        except Exception as e:
            logger.debug("register() failed for %s: %s", name, e)

    # Fallback: find a BaseIndexer subclass
    from workspace.base import BaseIndexer

    for attr_name in dir(mod):
        attr = getattr(mod, attr_name, None)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseIndexer)
            and attr is not BaseIndexer
        ):
            return attr

    return None


class _IndexerCollector:
    """Fake plugin context that captures register_workspace_indexer calls."""

    def __init__(self):
        self.indexer_cls = None

    def register_workspace_indexer(self, cls):
        self.indexer_cls = cls

    # No-op for other registration methods
    def register_tool(self, *args, **kwargs):
        pass

    def register_hook(self, *args, **kwargs):
        pass

    def register_cli_command(self, *args, **kwargs):
        pass

    def register_memory_provider(self, *args, **kwargs):
        pass

    def register_context_engine(self, *args, **kwargs):
        pass
