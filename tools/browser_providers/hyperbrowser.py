"""Hyperbrowser cloud browser provider (direct API key only)."""

import logging
import os
import uuid
from typing import Any, Dict, Optional

import requests

from tools.browser_providers.base import CloudBrowserProvider

logger = logging.getLogger(__name__)

# Official API host and paths — see https://hyperbrowser.ai/docs/api-reference/create-new-session
_DEFAULT_API_BASE = "https://api.hyperbrowser.ai"


def _api_base() -> str:
    return os.environ.get("HYPERBROWSER_API_BASE_URL", _DEFAULT_API_BASE).rstrip("/")


def _create_session_url() -> str:
    return f"{_api_base()}/api/session"


def _stop_session_url(session_id: str) -> str:
    return f"{_api_base()}/api/session/{session_id}/stop"


class HyperbrowserProvider(CloudBrowserProvider):
    """Hyperbrowser (https://hyperbrowser.ai) cloud browser backend."""

    def provider_name(self) -> str:
        return "Hyperbrowser"

    def is_configured(self) -> bool:
        return self._get_config_or_none() is not None

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _get_config_or_none(self) -> Optional[Dict[str, Any]]:
        api_key = os.environ.get("HYPERBROWSER_API_KEY")
        if api_key:
            return {"api_key": api_key}
        return None

    def _get_config(self) -> Dict[str, Any]:
        config = self._get_config_or_none()
        if config is None:
            raise ValueError(
                "Hyperbrowser requires the HYPERBROWSER_API_KEY environment variable."
            )
        return config

    def _load_yaml_hyperbrowser_cfg(self) -> Dict[str, Any]:
        try:
            from hermes_cli.config import read_raw_config

            cfg = read_raw_config()
            browser = cfg.get("browser")
            if isinstance(browser, dict):
                hb = browser.get("hyperbrowser")
                if isinstance(hb, dict):
                    return dict(hb)
        except Exception as e:
            logger.debug("Could not read browser.hyperbrowser from config: %s", e)
        return {}

    def _bool_setting(
        self,
        env_key: str,
        default: bool,
        yaml_cfg: Dict[str, Any],
        yaml_key: str,
    ) -> bool:
        if env_key in os.environ:
            return os.environ[env_key].strip().lower() not in ("false", "0", "no", "")
        if yaml_key in yaml_cfg:
            val = yaml_cfg[yaml_key]
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() not in ("false", "0", "no", "")
        return default

    def _optional_str(
        self,
        env_key: str,
        yaml_cfg: Dict[str, Any],
        yaml_key: str,
    ) -> Optional[str]:
        raw = os.environ.get(env_key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
        if yaml_key in yaml_cfg and yaml_cfg[yaml_key] is not None:
            s = str(yaml_cfg[yaml_key]).strip()
            if s:
                return s
        return None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(self, task_id: str) -> Dict[str, object]:
        config = self._get_config()
        yaml_cfg = self._load_yaml_hyperbrowser_cfg()

        use_stealth = self._bool_setting(
            "HYPERBROWSER_STEALTH", True, yaml_cfg, "stealth"
        )
        use_proxy = self._bool_setting(
            "HYPERBROWSER_PROXY", True, yaml_cfg, "proxy"
        )
        solve_captchas = self._bool_setting(
            "HYPERBROWSER_SOLVE_CAPTCHAS", True, yaml_cfg, "solve_captchas"
        )
        proxy_country = self._optional_str(
            "HYPERBROWSER_PROXY_COUNTRY", yaml_cfg, "proxy_country"
        )
        profile_id = self._optional_str(
            "HYPERBROWSER_PROFILE_ID", yaml_cfg, "profile_id"
        )

        payload: Dict[str, Any] = {
            "useStealth": use_stealth,
            "useProxy": use_proxy,
            "solveCaptchas": solve_captchas,
            "acceptCookies": True,
            "screen": {"width": 1920, "height": 1080},
        }
        if proxy_country:
            payload["proxyCountry"] = proxy_country
        if profile_id:
            # OpenAPI: CreateSessionProfile uses nested `profile.id`, not `profileId`.
            payload["profile"] = {"id": profile_id}

        headers = {
            "x-api-key": config["api_key"],
            "Content-Type": "application/json",
        }

        response = requests.post(
            _create_session_url(),
            headers=headers,
            json=payload,
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"Failed to create Hyperbrowser session: "
                f"{response.status_code} {response.text}"
            )

        session_data = response.json()
        session_name = f"hermes_{task_id}_{uuid.uuid4().hex[:8]}"

        features_enabled = {
            "stealth": use_stealth,
            "proxy": use_proxy,
            "solve_captchas": solve_captchas,
            "accept_cookies": True,
            "proxy_country": bool(proxy_country),
            "profile": bool(profile_id),
        }
        feature_str = ", ".join(k for k, v in features_enabled.items() if v)
        logger.info(
            "Created Hyperbrowser session %s with features: %s",
            session_name,
            feature_str,
        )

        return {
            "session_name": session_name,
            "bb_session_id": session_data["id"],
            "cdp_url": session_data["wsEndpoint"],
            "live_url": session_data.get("liveUrl"),
            "features": features_enabled,
        }

    def close_session(self, session_id: str) -> bool:
        try:
            config = self._get_config()
        except ValueError:
            logger.warning(
                "Cannot close Hyperbrowser session %s — missing credentials",
                session_id,
            )
            return False

        try:
            response = requests.put(
                _stop_session_url(session_id),
                headers={
                    "x-api-key": config["api_key"],
                },
                timeout=10,
            )
            if 200 <= response.status_code < 300:
                logger.debug("Successfully closed Hyperbrowser session %s", session_id)
                return True
            logger.warning(
                "Failed to close Hyperbrowser session %s: HTTP %s - %s",
                session_id,
                response.status_code,
                response.text[:200],
            )
            return False
        except Exception as e:
            logger.error(
                "Exception closing Hyperbrowser session %s: %s",
                session_id,
                e,
                exc_info=True,
            )
            return False

    def emergency_cleanup(self, session_id: str) -> None:
        config = self._get_config_or_none()
        if config is None:
            logger.warning(
                "Cannot emergency-cleanup Hyperbrowser session %s — missing credentials",
                session_id,
            )
            return
        try:
            requests.put(
                _stop_session_url(session_id),
                headers={
                    "x-api-key": config["api_key"],
                },
                timeout=5,
            )
        except Exception as e:
            logger.debug(
                "Emergency cleanup failed for Hyperbrowser session %s: %s",
                session_id,
                e,
            )
