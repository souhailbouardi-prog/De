from gateway.session_query_service import SessionQueryService
from hermes_state import SessionDB


def _update_session_times(db: SessionDB, session_id: str, *, started_at: float, ended_at: float | None = None) -> None:
    db._execute_write(
        lambda conn: conn.execute(
            "UPDATE sessions SET started_at = ?, ended_at = ? WHERE id = ?",
            (started_at, ended_at, session_id),
        )
    )


def _update_message_timestamp(db: SessionDB, message_id: int, timestamp: float) -> None:
    db._execute_write(
        lambda conn: conn.execute(
            "UPDATE messages SET timestamp = ? WHERE id = ?",
            (timestamp, message_id),
        )
    )


def test_get_root_task_snapshots_returns_root_current_and_lineage(monkeypatch, tmp_path):
    hermes_home = tmp_path / ".hermes" / "profiles" / "coder"
    hermes_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    db = SessionDB(db_path=hermes_home / "state.db")
    try:
        db.create_session("sess_root", "cli")
        db.set_session_title("sess_root", "实现 Session Query")
        _update_session_times(db, "sess_root", started_at=100.0)

        db.create_session("sess_leaf", "cli", parent_session_id="sess_root")
        db.set_session_title("sess_leaf", "继续处理分页")
        _update_session_times(db, "sess_leaf", started_at=200.0)

        root_user_id = db.append_message(
            "sess_root",
            "user",
            "先把 dashboard session API 定下来",
        )
        _update_message_timestamp(db, root_user_id, 101.0)

        root_assistant_id = db.append_message(
            "sess_root",
            "assistant",
            "已经把 service 抽出来了",
        )
        _update_message_timestamp(db, root_assistant_id, 102.0)

        leaf_assistant_id = db.append_message(
            "sess_leaf",
            "assistant",
            "已经补齐分页游标语义",
        )
        _update_message_timestamp(db, leaf_assistant_id, 205.0)

        service = SessionQueryService(db=db)

        assert service.get_root_task_snapshots() == {
            "root_tasks": [
                {
                    "profile_id": "coder",
                    "root_session_id": "sess_root",
                    "current_session_id": "sess_leaf",
                    "root_session": {
                        "session_id": "sess_root",
                        "parent_session_id": None,
                        "title": "实现 Session Query",
                        "source": "cli",
                        "started_at": 100.0,
                        "ended_at": None,
                    },
                    "current_session": {
                        "session_id": "sess_leaf",
                        "parent_session_id": "sess_root",
                        "title": "继续处理分页",
                        "source": "cli",
                        "started_at": 200.0,
                        "ended_at": None,
                    },
                    "lineage": [
                        {
                            "session_id": "sess_root",
                            "parent_session_id": None,
                            "title": "实现 Session Query",
                            "source": "cli",
                            "started_at": 100.0,
                            "ended_at": None,
                        },
                        {
                            "session_id": "sess_leaf",
                            "parent_session_id": "sess_root",
                            "title": "继续处理分页",
                            "source": "cli",
                            "started_at": 200.0,
                            "ended_at": None,
                        },
                    ],
                    "initial_user_message": "先把 dashboard session API 定下来",
                    "latest_conversation_message": "已经补齐分页游标语义",
                    "last_activity_at": 205.0,
                }
            ]
        }
    finally:
        db.close()


def test_get_session_messages_page_uses_timestamp_and_id_cursor_for_stable_paging(monkeypatch, tmp_path):
    hermes_home = tmp_path / ".hermes" / "profiles" / "coder"
    hermes_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    db = SessionDB(db_path=hermes_home / "state.db")
    try:
        db.create_session("sess_page", "cli")

        message_ids = []
        for index in range(1, 6):
            message_id = db.append_message("sess_page", "assistant", f"message-{index}")
            _update_message_timestamp(db, message_id, 100.0)
            message_ids.append(message_id)

        service = SessionQueryService(db=db)

        first_page = service.get_session_messages_page("sess_page", limit=2)
        assert first_page == {
            "messages": [
                {
                    "id": message_ids[3],
                    "session_id": "sess_page",
                    "role": "assistant",
                    "content": "message-4",
                    "tool_name": None,
                    "reasoning": None,
                    "timestamp": 100.0,
                },
                {
                    "id": message_ids[4],
                    "session_id": "sess_page",
                    "role": "assistant",
                    "content": "message-5",
                    "tool_name": None,
                    "reasoning": None,
                    "timestamp": 100.0,
                },
            ],
            "has_more_before": True,
        }

        second_page = service.get_session_messages_page(
            "sess_page",
            limit=2,
            before_id=first_page["messages"][0]["id"],
            before_ts=first_page["messages"][0]["timestamp"],
        )
        assert second_page == {
            "messages": [
                {
                    "id": message_ids[1],
                    "session_id": "sess_page",
                    "role": "assistant",
                    "content": "message-2",
                    "tool_name": None,
                    "reasoning": None,
                    "timestamp": 100.0,
                },
                {
                    "id": message_ids[2],
                    "session_id": "sess_page",
                    "role": "assistant",
                    "content": "message-3",
                    "tool_name": None,
                    "reasoning": None,
                    "timestamp": 100.0,
                },
            ],
            "has_more_before": True,
        }

        third_page = service.get_session_messages_page(
            "sess_page",
            limit=2,
            before_id=second_page["messages"][0]["id"],
            before_ts=second_page["messages"][0]["timestamp"],
        )
        assert third_page == {
            "messages": [
                {
                    "id": message_ids[0],
                    "session_id": "sess_page",
                    "role": "assistant",
                    "content": "message-1",
                    "tool_name": None,
                    "reasoning": None,
                    "timestamp": 100.0,
                }
            ],
            "has_more_before": False,
        }
    finally:
        db.close()


def test_get_session_binding_returns_latest_leaf_and_lineage(monkeypatch, tmp_path):
    hermes_home = tmp_path / ".hermes" / "profiles" / "coder"
    hermes_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    db = SessionDB(db_path=hermes_home / "state.db")
    try:
        db.create_session("sess_root", "cli")
        db.set_session_title("sess_root", "实现 Session Query")
        _update_session_times(db, "sess_root", started_at=100.0)

        db.create_session("sess_mid", "cli", parent_session_id="sess_root")
        db.set_session_title("sess_mid", "继续处理分页")
        _update_session_times(db, "sess_mid", started_at=200.0)

        db.create_session("sess_leaf", "cli", parent_session_id="sess_mid")
        db.set_session_title("sess_leaf", "补 binding 测试")
        _update_session_times(db, "sess_leaf", started_at=300.0)

        service = SessionQueryService(db=db)

        assert service.get_session_binding("sess_mid", root_session_id="sess_root") == {
            "root_session_id": "sess_root",
            "current_session_id": "sess_leaf",
            "lineage": [
                {
                    "session_id": "sess_root",
                    "parent_session_id": None,
                    "title": "实现 Session Query",
                    "source": "cli",
                    "started_at": 100.0,
                    "ended_at": None,
                },
                {
                    "session_id": "sess_mid",
                    "parent_session_id": "sess_root",
                    "title": "继续处理分页",
                    "source": "cli",
                    "started_at": 200.0,
                    "ended_at": None,
                },
                {
                    "session_id": "sess_leaf",
                    "parent_session_id": "sess_mid",
                    "title": "补 binding 测试",
                    "source": "cli",
                    "started_at": 300.0,
                    "ended_at": None,
                },
            ],
        }
    finally:
        db.close()



def test_get_session_binding_returns_none_when_root_session_is_unrelated(monkeypatch, tmp_path):
    hermes_home = tmp_path / ".hermes" / "profiles" / "coder"
    hermes_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    db = SessionDB(db_path=hermes_home / "state.db")
    try:
        db.create_session("sess_root_a", "cli")
        db.create_session("sess_leaf_a", "cli", parent_session_id="sess_root_a")
        db.create_session("sess_root_b", "cli")

        service = SessionQueryService(db=db)

        assert service.get_session_binding("sess_leaf_a", root_session_id="sess_root_b") is None
    finally:
        db.close()
