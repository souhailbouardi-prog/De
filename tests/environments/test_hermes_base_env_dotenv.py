import importlib
import sys
import types
from pathlib import Path


def _stub_module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def _load_base_env_module(monkeypatch):
    class _BaseEnv:
        pass

    class _BaseEnvConfig:
        pass

    class _ScoredDataGroup:
        pass

    class _ScoredDataItem:
        pass

    class _APIServerConfig:
        pass

    class _ServerBaseline:
        pass

    class _ServerManager:
        pass

    class _AgentResult:
        pass

    class _HermesAgentLoop:
        pass

    class _ToolContext:
        pass

    stub_modules = {
        "environments.patches": _stub_module(
            "environments.patches",
            apply_patches=lambda: None,
        ),
        "atroposlib": _stub_module("atroposlib"),
        "atroposlib.envs": _stub_module("atroposlib.envs"),
        "atroposlib.envs.base": _stub_module(
            "atroposlib.envs.base",
            BaseEnv=_BaseEnv,
            BaseEnvConfig=_BaseEnvConfig,
            ScoredDataGroup=_ScoredDataGroup,
            ScoredDataItem=_ScoredDataItem,
        ),
        "atroposlib.envs.server_handling": _stub_module("atroposlib.envs.server_handling"),
        "atroposlib.envs.server_handling.server_manager": _stub_module(
            "atroposlib.envs.server_handling.server_manager",
            APIServerConfig=_APIServerConfig,
            ServerBaseline=_ServerBaseline,
            ServerManager=_ServerManager,
        ),
        "atroposlib.type_definitions": _stub_module(
            "atroposlib.type_definitions",
            Item=object,
        ),
        "environments.agent_loop": _stub_module(
            "environments.agent_loop",
            AgentResult=_AgentResult,
            HermesAgentLoop=_HermesAgentLoop,
        ),
        "environments.tool_context": _stub_module(
            "environments.tool_context",
            ToolContext=_ToolContext,
        ),
        "tools.budget_config": _stub_module(
            "tools.budget_config",
            DEFAULT_RESULT_SIZE_CHARS=1,
            DEFAULT_TURN_BUDGET_CHARS=1,
            DEFAULT_PREVIEW_SIZE_CHARS=1,
        ),
        "model_tools": _stub_module(
            "model_tools",
            get_tool_definitions=lambda *args, **kwargs: [],
        ),
        "toolset_distributions": _stub_module(
            "toolset_distributions",
            sample_toolsets_from_distribution=lambda *args, **kwargs: [],
        ),
    }

    stub_modules["atroposlib"].envs = stub_modules["atroposlib.envs"]
    stub_modules["atroposlib.envs"].base = stub_modules["atroposlib.envs.base"]
    stub_modules["atroposlib.envs"].server_handling = stub_modules["atroposlib.envs.server_handling"]
    stub_modules["atroposlib.envs.server_handling"].server_manager = stub_modules[
        "atroposlib.envs.server_handling.server_manager"
    ]

    for name, module in stub_modules.items():
        monkeypatch.setitem(sys.modules, name, module)

    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)

    module_name = "environments.hermes_base_env"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_load_repo_dotenv_falls_back_to_latin1(monkeypatch, tmp_path):
    module = _load_base_env_module(monkeypatch)
    env_path = tmp_path / ".env"

    calls = []

    def fake_load_dotenv(*, dotenv_path, encoding=None, **kwargs):
        calls.append((Path(dotenv_path), encoding))
        if encoding == "utf-8":
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad byte")
        return True

    monkeypatch.setattr(module, "load_dotenv", fake_load_dotenv)

    module._load_repo_dotenv(env_path)

    assert calls == [
        (env_path, "utf-8"),
        (env_path, "latin-1"),
    ]


def test_hermes_base_env_uses_repo_dotenv_helper():
    source = (
        Path(__file__).resolve().parents[2] / "environments" / "hermes_base_env.py"
    ).read_text(encoding="utf-8")

    assert "def _load_repo_dotenv(path: Path) -> None:" in source
    assert "_load_repo_dotenv(_env_path)" in source
