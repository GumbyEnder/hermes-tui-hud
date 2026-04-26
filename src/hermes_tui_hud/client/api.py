"""HTTP client for the official Hermes Dashboard API (port 9119)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

from .models import (
    ActionStatus,
    CronJob,
    DashboardTheme,
    EnvVar,
    HermesSession,
    ModelInfo,
    OAuthProvider,
    SessionSearchResult,
    Skill,
    Status,
    Toolset,
    UsageAnalytics,
)


class HermesAPIError(RuntimeError):
    pass


class HermesDashboardClient:
    """Client for the official Hermes Dashboard REST API (FastAPI, port 9119).

    Auth: The dashboard uses an ephemeral session token injected into the SPA
    HTML as ``window.__HERMES_SESSION_TOKEN__``.  There is no /login endpoint.
    The client fetches the index page, extracts the token, and sends it via
    the ``X-Hermes-Session-Token`` header on every subsequent request.

    Public endpoints (/api/status, /api/model/info, etc.) do not require
    the session token.
    """

    _TOKEN_RE = re.compile(r'window\.__HERMES_SESSION_TOKEN__\s*=\s*"([^"]+)"')

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 10.0,
    ):
        self.base_url = (base_url or os.getenv("HERMES_HUD_BASE_URL") or "http://127.0.0.1:9119").rstrip("/")
        self.timeout = timeout
        self._session_token: str | None = os.getenv("HERMES_SESSION_TOKEN")
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    # ── Auth ──────────────────────────────────────────────────────────

    def _ensure_token(self) -> None:
        """Fetch the session token from the dashboard index page if not already known."""
        if self._session_token:
            return
        try:
            req = urllib.request.Request(f"{self.base_url}/", headers={"Accept": "text/html"})
            with self._opener.open(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            m = self._TOKEN_RE.search(html)
            if m:
                self._session_token = m.group(1)
            else:
                raise HermesAPIError("Could not extract session token from dashboard page")
        except urllib.error.URLError as exc:
            raise HermesAPIError(f"Cannot reach dashboard at {self.base_url}: {exc.reason}") from exc

    # ── Core HTTP ─────────────────────────────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> Any:
        if require_auth:
            self._ensure_token()
        url = f"{self.base_url}{path}"
        headers: dict[str, str] = {}
        if self._session_token:
            headers["X-Hermes-Session-Token"] = self._session_token
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("detail") or body.get("error") or body.get("message") or exc.reason
            except Exception:
                message = exc.reason
            raise HermesAPIError(f"{exc.code} {message}") from exc
        except urllib.error.URLError as exc:
            raise HermesAPIError(f"Network error: {exc.reason}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HermesAPIError("Invalid JSON response") from exc

    def get(self, path: str, require_auth: bool = True) -> Any:
        return self.request("GET", path, require_auth=require_auth)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, payload=payload)

    def put(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("PUT", path, payload=payload)

    def delete(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, payload=payload)

    # ── Status ────────────────────────────────────────────────────────

    def get_status(self) -> Status:
        data = self.get("/api/status", require_auth=False)
        return Status.from_api(data)

    def restart_gateway(self) -> dict[str, Any]:
        return self.post("/api/gateway/restart")

    def update_hermes(self) -> dict[str, Any]:
        return self.post("/api/hermes/update")

    def get_action_status(self, name: str, lines: int = 200) -> ActionStatus:
        data = self.get(f"/api/actions/{urllib.parse.quote(name)}/status?lines={int(lines)}")
        return ActionStatus.from_api(data)

    # ── Sessions ──────────────────────────────────────────────────────

    def list_sessions(self, limit: int = 20, offset: int = 0) -> tuple[list[HermesSession], int]:
        data = self.get(f"/api/sessions?limit={int(limit)}&offset={int(offset)}")
        sessions = [HermesSession.from_api(s) for s in data.get("sessions", [])]
        total = data.get("total", 0)
        return sessions, total

    def search_sessions(self, query: str, limit: int = 20) -> list[SessionSearchResult]:
        q = urllib.parse.quote(query)
        data = self.get(f"/api/sessions/search?q={q}&limit={int(limit)}")
        return [SessionSearchResult.from_api(r) for r in data.get("results", [])]

    def get_session(self, session_id: str) -> HermesSession:
        data = self.get(f"/api/sessions/{urllib.parse.quote(session_id)}")
        return HermesSession.from_api(data)

    def get_session_messages(self, session_id: str) -> dict[str, Any]:
        return self.get(f"/api/sessions/{urllib.parse.quote(session_id)}/messages")

    def delete_session(self, session_id: str) -> dict[str, Any]:
        return self.delete(f"/api/sessions/{urllib.parse.quote(session_id)}")

    # ── Config ────────────────────────────────────────────────────────

    def get_config(self) -> dict[str, Any]:
        return self.get("/api/config")

    def get_config_defaults(self) -> dict[str, Any]:
        return self.get("/api/config/defaults", require_auth=False)

    def get_config_schema(self) -> dict[str, Any]:
        return self.get("/api/config/schema", require_auth=False)

    def get_config_raw(self) -> str:
        data = self.get("/api/config/raw")
        return data.get("yaml", "") if isinstance(data, dict) else ""

    def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        return self.put("/api/config", {"config": config})

    def update_config_raw(self, yaml_text: str) -> dict[str, Any]:
        return self.put("/api/config/raw", {"yaml_text": yaml_text})

    def get_model_info(self) -> ModelInfo:
        data = self.get("/api/model/info", require_auth=False)
        return ModelInfo.from_api(data)

    # ── Env ───────────────────────────────────────────────────────────

    def list_env_vars(self) -> list[EnvVar]:
        data = self.get("/api/env")
        return [EnvVar.from_api(name, info) for name, info in data.items()]

    def set_env_var(self, key: str, value: str) -> dict[str, Any]:
        return self.put("/api/env", {"key": key, "value": value})

    def remove_env_var(self, key: str) -> dict[str, Any]:
        return self.delete("/api/env", {"key": key})

    def reveal_env_var(self, key: str) -> str:
        data = self.post("/api/env/reveal", {"key": key})
        return data.get("value", "")

    # ── OAuth ─────────────────────────────────────────────────────────

    def list_oauth_providers(self) -> list[OAuthProvider]:
        data = self.get("/api/providers/oauth")
        return [OAuthProvider.from_api(p) for p in data.get("providers", [])]

    def disconnect_oauth(self, provider_id: str) -> dict[str, Any]:
        return self.delete(f"/api/providers/oauth/{urllib.parse.quote(provider_id)}")

    def start_oauth(self, provider_id: str) -> dict[str, Any]:
        return self.post(f"/api/providers/oauth/{urllib.parse.quote(provider_id)}/start")

    def submit_oauth_code(self, provider_id: str, session_id: str, code: str) -> dict[str, Any]:
        return self.post(
            f"/api/providers/oauth/{urllib.parse.quote(provider_id)}/submit",
            {"session_id": session_id, "code": code},
        )

    def poll_oauth(self, provider_id: str, session_id: str) -> dict[str, Any]:
        return self.get(f"/api/providers/oauth/{urllib.parse.quote(provider_id)}/poll/{urllib.parse.quote(session_id)}")

    def cancel_oauth_session(self, session_id: str) -> dict[str, Any]:
        return self.delete(f"/api/providers/oauth/sessions/{urllib.parse.quote(session_id)}")

    # ── Skills ────────────────────────────────────────────────────────

    def list_skills(self) -> list[Skill]:
        data = self.get("/api/skills")
        if isinstance(data, list):
            return [Skill.from_api(s) for s in data]
        return []

    def toggle_skill(self, name: str, enabled: bool) -> dict[str, Any]:
        """Set a skill's enabled state.

        Args:
            name: Skill identifier
            enabled: Target state (True to enable, False to disable)
        """
        return self.put("/api/skills/toggle", {"name": name, "enabled": enabled})

    # ── Tools ─────────────────────────────────────────────────────────

    def list_toolsets(self) -> list[Toolset]:
        data = self.get("/api/tools/toolsets")
        if isinstance(data, list):
            return [Toolset.from_api(t) for t in data]
        return []

    # ── Logs ──────────────────────────────────────────────────────────

    def get_logs(
        self,
        file: str = "agent",
        lines: int = 100,
        level: str | None = None,
        component: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        params = [f"file={urllib.parse.quote(file)}", f"lines={int(lines)}"]
        if level:
            params.append(f"level={urllib.parse.quote(level)}")
        if component:
            params.append(f"component={urllib.parse.quote(component)}")
        if search:
            params.append(f"search={urllib.parse.quote(search)}")
        return self.get(f"/api/logs?{'&'.join(params)}")

    # ── Cron ──────────────────────────────────────────────────────────

    def list_cron_jobs(self) -> list[CronJob]:
        data = self.get("/api/cron/jobs")
        if isinstance(data, list):
            return [CronJob.from_api(j) for j in data]
        return []

    def get_cron_job(self, job_id: str) -> CronJob:
        data = self.get(f"/api/cron/jobs/{urllib.parse.quote(job_id)}")
        return CronJob.from_api(data)

    def create_cron_job(self, prompt: str, schedule: str, name: str | None = None, deliver: str | None = None) -> CronJob:
        payload: dict[str, Any] = {"prompt": prompt, "schedule": schedule}
        if name:
            payload["name"] = name
        if deliver:
            payload["deliver"] = deliver
        data = self.post("/api/cron/jobs", payload)
        return CronJob.from_api(data)

    def update_cron_job(self, job_id: str, **updates: Any) -> CronJob:
        data = self.put(f"/api/cron/jobs/{urllib.parse.quote(job_id)}", {"updates": updates})
        return CronJob.from_api(data)

    def pause_cron_job(self, job_id: str) -> CronJob:
        data = self.post(f"/api/cron/jobs/{urllib.parse.quote(job_id)}/pause")
        return CronJob.from_api(data)

    def resume_cron_job(self, job_id: str) -> CronJob:
        data = self.post(f"/api/cron/jobs/{urllib.parse.quote(job_id)}/resume")
        return CronJob.from_api(data)

    def trigger_cron_job(self, job_id: str) -> CronJob:
        data = self.post(f"/api/cron/jobs/{urllib.parse.quote(job_id)}/trigger")
        return CronJob.from_api(data)

    def delete_cron_job(self, job_id: str) -> dict[str, Any]:
        return self.delete(f"/api/cron/jobs/{urllib.parse.quote(job_id)}")

    # ── Analytics ─────────────────────────────────────────────────────

    def get_usage_analytics(self, days: int = 30) -> UsageAnalytics:
        data = self.get(f"/api/analytics/usage?days={int(days)}")
        return UsageAnalytics.from_api(data)

    # ── Dashboard ─────────────────────────────────────────────────────

    def list_themes(self) -> tuple[list[DashboardTheme], str]:
        data = self.get("/api/dashboard/themes", require_auth=False)
        themes = [DashboardTheme.from_api(t) for t in data.get("themes", [])]
        active = data.get("active", "")
        return themes, active

    def set_theme(self, name: str) -> dict[str, Any]:
        return self.put("/api/dashboard/theme", {"name": name})

    def list_plugins(self) -> list[dict[str, Any]]:
        data = self.get("/api/dashboard/plugins", require_auth=False)
        return data if isinstance(data, list) else []
    # ── Analytics+ Plugin ─────────────────────────────────────────────────

    def get_plugin_analytics_totals(self, days: int = 7) -> dict[str, Any]:
        data = self.get(f"/api/plugins/analytics/totals?days={int(days)}")
        return data if isinstance(data, dict) else {}

    def get_plugin_analytics_timeseries(self, days: int = 7) -> list[dict[str, Any]]:
        data = self.get(f"/api/plugins/analytics/timeseries?days={int(days)}")
        return data if isinstance(data, list) else []

    def get_plugin_analytics_model_efficiency(self, days: int = 7) -> list[dict[str, Any]]:
        data = self.get(f"/api/plugins/analytics/model-efficiency?days={int(days)}")
        return data if isinstance(data, list) else []

