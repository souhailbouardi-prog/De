from hermes_cli.tools_config import TOOL_CATEGORIES


def test_browser_firecrawl_provider_exposes_self_hosted_settings():
    providers = TOOL_CATEGORIES["browser"]["providers"]
    firecrawl = next(p for p in providers if p.get("browser_provider") == "firecrawl")

    env_keys = [item["key"] for item in firecrawl["env_vars"]]

    assert "FIRECRAWL_API_KEY" in env_keys
    assert "FIRECRAWL_API_URL" in env_keys
    assert "FIRECRAWL_BROWSER_TTL" in env_keys
    assert "self-hosted" in firecrawl["tag"].lower()
