"""
Hermes migration export command.

Creates a migration bundle from current Hermes installation.
"""

import json
import os
import tarfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from hermes_cli.colors import Colors, color
from hermes_cli.migrate_core import (
    get_hermes_home,
    _collect_migration_items,
    _should_skip_dir,
    _should_skip_file,
    _is_text_file,
    _remap_content,
    _SECRET_FILES,
    create_manifest,
    detect_platform,
    _log_warning,
)

# Placeholder written into bundle text files; replaced with real target home at import time.
_TARGET_HOME_PLACEHOLDER = "{{HERMES_HOME}}"


def _add_file_to_tarball(tf, full_path: Path, arcname: str, source_home: Path) -> None:
    """Add a file to tarball, remapping source_home paths in text files.

    Text files (.yaml, .json, .md, .sh, etc.) have their home-directory paths
    rewritten to _TARGET_HOME_PLACEHOLDER so they can be restored on a different
    machine. Binary files are added verbatim.
    """
    if _is_text_file(Path(arcname).name):
        content = full_path.read_text(encoding="utf-8", errors="replace")
        remapped = _remap_content(content, source_home, Path(_TARGET_HOME_PLACEHOLDER))
        data = remapped.encode("utf-8")
        info = tarfile.TarInfo(name=arcname)
        info.size = len(data)
        tf.addfile(info, BytesIO(data))
    else:
        tf.add(str(full_path), arcname=arcname)


def export_bundle(output_path: Optional[str], preset: str = "safe") -> Path:
    """Create a migration bundle from current Hermes installation."""
    hermes_home = get_hermes_home()
    if not hermes_home.exists():
        raise FileNotFoundError(f"Hermes home not found: {hermes_home}")

    if output_path:
        output = Path(output_path)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = Path(f"hermes-migration-{ts}.tar.gz")

    source_platform = detect_platform()
    manifest = create_manifest(preset, source_platform)

    items = _collect_migration_items(preset)
    migrated_count = 0

    with tarfile.open(output, "w:gz") as tf:
        # Add manifest
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest_bytes)
        tf.addfile(manifest_info, BytesIO(manifest_bytes))

        for rel_path, item_info in items.items():
            src = hermes_home / rel_path
            if not src.exists():
                continue

            # Respect _collect_migration_items skip decisions (preset-based secrets)
            if item_info.get("status") == "skipped":
                continue

            try:
                if src.is_dir():
                    for parent, dirs, files in os.walk(src):
                        dirs[:] = [d for d in dirs if not _should_skip_dir(d, source_platform["os"])]
                        for fname in files:
                            # Secret files (nested at any depth) are excluded by safe preset
                            if preset != "full" and fname in _SECRET_FILES:
                                continue
                            if _should_skip_file(fname, source_platform["os"]):
                                continue
                            full_path = Path(parent) / fname
                            arcname = full_path.relative_to(hermes_home).as_posix()
                            _add_file_to_tarball(tf, full_path, arcname, source_platform["home"])
                            migrated_count += 1
                else:
                    if _should_skip_file(rel_path, source_platform["os"]):
                        continue
                    _add_file_to_tarball(tf, src, rel_path, source_platform["home"])
                    migrated_count += 1
            except (OSError, IOError) as e:
                _log_warning(f"Could not add {rel_path}: {e}")

    size_kb = output.stat().st_size // 1024

    print(color("\n✓ Bundle created", Colors.GREEN))
    print(f"  Path:    {output}")
    print(f"  Size:    {size_kb} KB")
    print(f"  Preset:  {preset}")
    print(f"  Source:  {source_platform['os']} ({source_platform['home']})")
    print(f"  Items:   {migrated_count} files/directories")
    print()
    print("Transfer this file to your new machine, then run:")
    print(color(f"  hermes migrate import -i {output.name}", Colors.CYAN))
    print()

    return output
