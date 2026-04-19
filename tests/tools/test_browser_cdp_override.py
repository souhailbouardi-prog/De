from unittest.mock import Mock, patch


HOST = "example-host"
PORT = 9223
WS_URL = f"ws://{HOST}:{PORT}/devtools/browser/abc123"
HTTP_URL = f"http://{HOST}:{PORT}"
VERSION_URL = f"{HTTP_URL}/json/version"


class TestResolveCdpOverride:
    def test_keeps_full_devtools_websocket_url(self):
        from tools.browser_tool import _resolve_cdp_override

        assert _resolve_cdp_override(WS_URL) == WS_URL

    def test_resolves_http_discovery_endpoint_to_websocket(self):
        from tools.browser_tool import _resolve_cdp_override

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = _resolve_cdp_override(HTTP_URL)

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_resolves_bare_ws_hostport_to_discovery_websocket(self):
        from tools.browser_tool import _resolve_cdp_override

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = _resolve_cdp_override(f"ws://{HOST}:{PORT}")

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_falls_back_to_raw_url_when_discovery_fails(self):
        from tools.browser_tool import _resolve_cdp_override

        with patch("tools.browser_tool.requests.get", side_effect=RuntimeError("boom")):
            assert _resolve_cdp_override(HTTP_URL) == HTTP_URL

    def test_normalizes_provider_returned_http_cdp_url_when_creating_session(self, monkeypatch):
        import tools.browser_tool as browser_tool

        provider = Mock()
        provider.create_session.return_value = {
            "session_name": "cloud-session",
            "bb_session_id": "bu_123",
            "cdp_url": "https://cdp.browser-use.example/session",
            "features": {"browser_use": True},
        }

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        monkeypatch.setattr(browser_tool, "_active_sessions", {})
        monkeypatch.setattr(browser_tool, "_session_last_activity", {})
        monkeypatch.setattr(browser_tool, "_start_browser_cleanup_thread", lambda: None)
        monkeypatch.setattr(browser_tool, "_update_session_activity", lambda task_id: None)
        monkeypatch.setattr(browser_tool, "_get_cdp_override", lambda: "")
        monkeypatch.setattr(browser_tool, "_get_cloud_provider", lambda: provider)

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            session_info = browser_tool._get_session_info("task-browser-use")

        assert session_info["cdp_url"] == WS_URL
        provider.create_session.assert_called_once_with("task-browser-use")
        mock_get.assert_called_once_with(
            "https://cdp.browser-use.example/session/json/version",
            timeout=10,
        )


class TestGetCdpOverride:
    def test_prefers_env_var_over_config(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.setenv("BROWSER_CDP_URL", HTTP_URL)
        monkeypatch.setattr(
            browser_tool,
            "read_raw_config",
            lambda: {"browser": {"cdp_url": "http://config-host:9222"}},
            raising=False,
        )

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = browser_tool._get_cdp_override()

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_uses_config_browser_cdp_url_when_env_missing(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("hermes_cli.config.read_raw_config", return_value={"browser": {"cdp_url": HTTP_URL}}), \
             patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = browser_tool._get_cdp_override()

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_raw_override_prefers_env_over_config(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.setenv("BROWSER_CDP_URL", HTTP_URL)
        with patch("hermes_cli.config.read_raw_config", return_value={"browser": {"cdp_url": "http://config-host:9222"}}):
            assert browser_tool._get_raw_cdp_override() == HTTP_URL

    def test_raw_override_reads_config_when_env_missing(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        with patch("hermes_cli.config.read_raw_config", return_value={"browser": {"cdp_url": HTTP_URL}}):
            assert browser_tool._get_raw_cdp_override() == HTTP_URL


class TestCdpEndpointReachable:
    def test_http_endpoint_uses_actual_host(self):
        from tools.browser_tool import _cdp_endpoint_reachable

        response = Mock()
        response.raise_for_status.return_value = None
        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            assert _cdp_endpoint_reachable(HTTP_URL) is True
        mock_get.assert_called_once_with(VERSION_URL, timeout=2.0)

    def test_http_endpoint_returns_false_when_actual_host_unreachable(self):
        from tools.browser_tool import _cdp_endpoint_reachable

        with patch("tools.browser_tool.requests.get", side_effect=RuntimeError("boom")):
            assert _cdp_endpoint_reachable("http://unreachable.invalid:9333") is False

    def test_full_websocket_endpoint_uses_real_websocket_handshake(self):
        from tools.browser_tool import _cdp_endpoint_reachable

        fake_conn = Mock()
        fake_conn.__enter__ = Mock(return_value=fake_conn)
        fake_conn.__exit__ = Mock(return_value=False)
        with patch("websockets.sync.client.connect", return_value=fake_conn) as mock_conn:
            assert _cdp_endpoint_reachable(WS_URL) is True
        mock_conn.assert_called_once_with(WS_URL, open_timeout=2.0, close_timeout=2.0)