import json
import shutil
import sqlite3
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from workspace.commands import workspace_command
from workspace.default import DefaultIndexer
from workspace.store import SQLiteFTS5Store


def test_default_overlap_is_clamped_for_small_chunk_sizes(make_workspace_config):
    cfg = make_workspace_config(
        {"knowledgebase": {"chunking": {"chunk_size": 12}}},
    )
    # Default overlap is 32, clamped to chunk_size - 1 when chunk_size is smaller.
    assert cfg.knowledgebase.chunking.overlap == 11


def test_markdown_metadata_has_clean_shape(make_workspace_config, write_file):
    """Code rows carry only `language`; tables and images carry no metadata."""
    cfg = make_workspace_config(
        {"knowledgebase": {"chunking": {"chunk_size": 64}}},
    )

    md = write_file(
        cfg.workspace_root / "docs" / "mixed.md",
        """# Title

Some intro prose to ensure the markdown path is used.

```python
def first_block():
    return 1
```

| Name | Score |
| ---- | ----- |
| A    | 10    |
| B    | 20    |

![first image](img/one.png)

## Second

More prose in the second section.

```python
def second_block():
    return 2
```

| Lang | Lines |
| ---- | ----- |
| py   | 2     |

![second image](img/two.png)
""",
    )

    summary = DefaultIndexer(cfg).index()
    assert summary.files_indexed == 1
    assert summary.files_errored == 0

    with SQLiteFTS5Store(cfg.workspace_root) as store:
        rows = store.conn.execute(
            "SELECT kind, chunk_metadata, content FROM chunks WHERE abs_path = ? "
            "ORDER BY start_char",
            (str(md.resolve()),),
        ).fetchall()

    code_rows = [r for r in rows if r["kind"] == "markdown_code"]
    table_rows = [r for r in rows if r["kind"] == "markdown_table"]
    image_rows = [r for r in rows if r["kind"] == "markdown_image"]

    assert len(code_rows) == 2
    assert len(table_rows) == 2
    assert len(image_rows) == 2

    # Code: exactly {"language": "python"}, nothing else.
    for r in code_rows:
        meta = json.loads(r["chunk_metadata"])
        assert meta == {"language": "python"}

    # Tables and images have no chunk_metadata.
    for r in table_rows:
        assert r["chunk_metadata"] is None
    for r in image_rows:
        assert r["chunk_metadata"] is None

    # Image `content` is the alias (the searchable text).
    assert [r["content"] for r in image_rows] == ["first image", "second image"]


def test_failed_reindex_keeps_previous_committed_rows(
    make_workspace_config,
    write_file,
    monkeypatch: pytest.MonkeyPatch,
):
    cfg = make_workspace_config()

    file_a = write_file(cfg.workspace_root / "docs" / "a.txt", "stable old content\n")
    file_b = write_file(cfg.workspace_root / "docs" / "b.txt", "other old content\n")

    initial = DefaultIndexer(cfg).index()
    assert initial.files_indexed == 2

    with SQLiteFTS5Store(cfg.workspace_root) as store:
        original_record = store.get_file_record(str(file_a.resolve()))
        assert original_record is not None

    original_insert = SQLiteFTS5Store.insert_chunks
    target_path = str(file_a.resolve())

    def flaky_insert(self: SQLiteFTS5Store, chunks):
        if chunks and chunks[0].abs_path == target_path:
            raise sqlite3.OperationalError("simulated insert failure")
        return original_insert(self, chunks)

    monkeypatch.setattr(SQLiteFTS5Store, "insert_chunks", flaky_insert)

    file_a.write_text("stable new content that should roll back\n", encoding="utf-8")
    file_b.write_text("other new content that should succeed\n", encoding="utf-8")

    summary = DefaultIndexer(cfg).index()
    assert summary.files_indexed == 1
    assert summary.files_errored == 1

    with SQLiteFTS5Store(cfg.workspace_root) as store:
        record = store.get_file_record(target_path)
        assert record is not None
        assert record.content_hash == original_record.content_hash

        content_rows = store.conn.execute(
            "SELECT content FROM chunks WHERE abs_path = ? ORDER BY chunk_index",
            (target_path,),
        ).fetchall()

    assert content_rows
    combined = "\n".join(row["content"] for row in content_rows)
    assert "stable old content" in combined
    assert "stable new content" not in combined


def test_missing_root_skips_stale_prune(
    tmp_path: Path, make_workspace_config, write_file
):
    external_root = tmp_path / "external"
    external_root.mkdir()

    cfg = make_workspace_config(
        {
            "knowledgebase": {
                "roots": [{"path": str(external_root), "recursive": True}],
            }
        },
    )

    local_file = write_file(
        cfg.workspace_root / "docs" / "local.txt", "local content\n"
    )
    external_file = write_file(external_root / "external.txt", "external content\n")

    first = DefaultIndexer(cfg).index()
    assert first.files_indexed == 2

    shutil.rmtree(external_root)

    second = DefaultIndexer(cfg).index()
    assert second.files_pruned == 0

    with SQLiteFTS5Store(cfg.workspace_root) as store:
        indexed = store.all_indexed_paths()

    assert str(local_file.resolve()) in indexed
    assert str(external_file.resolve()) in indexed


def test_workspace_command_search_disabled_returns_structured_error(
    make_workspace_config,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    cfg = make_workspace_config({"workspace": {"enabled": False}})
    monkeypatch.setattr("workspace.config.load_workspace_config", lambda: cfg)

    args = Namespace(
        workspace_action="search",
        query="needle",
        limit=None,
        path=None,
        glob=None,
        human=False,
    )

    with pytest.raises(SystemExit) as exc:
        workspace_command(args)

    assert exc.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"] == "Workspace is disabled (workspace.enabled = false)"


def test_workspace_command_wraps_unexpected_errors_as_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(
        "workspace.config.load_workspace_config",
        lambda: (_ for _ in ()).throw(ValueError("bad config")),
    )

    args = Namespace(
        workspace_action="search",
        query="needle",
        limit=None,
        path=None,
        glob=None,
        human=False,
    )

    with pytest.raises(SystemExit) as exc:
        workspace_command(args)

    assert exc.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {"error": "bad config", "error_type": "ValueError"}


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (
            ["hermes", "workspace", "search", "needle", "--human"],
            ("search", None, True),
        ),
        (["hermes", "workspace", "roots", "list", "--human"], ("roots", "list", True)),
    ],
)
def test_workspace_human_flag_parses_after_subcommands(
    argv: list[str],
    expected: tuple[str, str | None, bool],
    monkeypatch: pytest.MonkeyPatch,
):
    from hermes_cli import main as main_mod
    import workspace.commands as workspace_commands

    captured: dict[str, object] = {}

    def fake_workspace_command(args):
        captured["workspace_action"] = args.workspace_action
        captured["roots_action"] = getattr(args, "roots_action", None)
        captured["human"] = getattr(args, "human", False)

    monkeypatch.setattr("hermes_cli.config.get_container_exec_info", lambda: None)
    monkeypatch.setattr(workspace_commands, "workspace_command", fake_workspace_command)
    monkeypatch.setattr(sys, "argv", argv)

    main_mod.main()

    assert (
        captured["workspace_action"],
        captured["roots_action"],
        captured["human"],
    ) == expected
