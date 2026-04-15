from __future__ import annotations

import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import AgentProfile, HermesAlert, HermesSession


class HermesAPIError(RuntimeError):
    pass


class HermesAPIClient:
    def __init__(self, base_url: str | None = None, password: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or os.getenv("HERMES_HUD_BASE_URL") or "http://127.0.0.1:8787").rstrip("/")
        self.password = password if password is not None else os.getenv("HERMES_HUD_PASSWORD")
        self.timeout = timeout
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cookie_jar))
        self._logged_in = False

    def _headers(self, json_body: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def login(self) -> None:
        if self._logged_in or not self.password:
            return
        payload = json.dumps({"password": self.password}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/auth/login",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("error") or body.get("message") or exc.reason
            except Exception:
                message = exc.reason
            raise HermesAPIError(f"Login failed: {exc.code} {message}") from exc
        except urllib.error.URLError as exc:
            raise HermesAPIError(f"Network error: {exc.reason}") from exc
        data = json.loads(raw.decode("utf-8")) if raw else {}
        if not data.get("ok"):
            raise HermesAPIError("Login failed")
        self._logged_in = True

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        if self.password and path != "/api/auth/login":
            self.login()
        url = f"{self.base_url}{path}"
        data = None
        headers = self._headers(json_body=payload is not None)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("error") or body.get("message") or exc.reason
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
            raise HermesAPIError("Invalid JSON response from Hermes backend") from exc

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, payload=payload)

    def summary(self) -> dict[str, Any]:
        resources = self.get("/api/ops/resources")
        profiles = self.get("/api/profiles")
        sessions = self.get("/api/sessions")
        alerts = self.get("/api/ops/ledger")
        return {
            "resources": resources,
            "profiles": profiles,
            "sessions": sessions,
            "alerts": alerts,
        }

    def list_profiles(self) -> list[AgentProfile]:
        data = self.get("/api/profiles")
        return [AgentProfile.from_api(item) for item in data.get("profiles", [])]

    def list_sessions(self) -> list[HermesSession]:
        data = self.get("/api/sessions")
        return [HermesSession.from_api(item) for item in data.get("sessions", [])]

    def rename_session(self, session_id: str, title: str) -> dict[str, Any]:
        return self.post("/api/session/rename", {"session_id": session_id, "title": title})

    def delete_session(self, session_id: str) -> dict[str, Any]:
        return self.post("/api/session/delete", {"session_id": session_id})

    def clear_session(self, session_id: str) -> dict[str, Any]:
        return self.post("/api/session/clear", {"session_id": session_id})

    def pin_session(self, session_id: str, pinned: bool = True) -> dict[str, Any]:
        return self.post("/api/session/pin", {"session_id": session_id, "pinned": pinned})

    def archive_session(self, session_id: str, archived: bool = True) -> dict[str, Any]:
        return self.post("/api/session/archive", {"session_id": session_id, "archived": archived})

    def list_alerts(self, limit: int = 20) -> list[HermesAlert]:
        data = self.get(f"/api/ops/ledger?limit={urllib.parse.quote(str(limit))}")
        return [HermesAlert.from_api(item) for item in data.get("events", [])]

    def get_profile_content(self, name: str) -> dict[str, Any]:
        target = urllib.parse.quote(name)
        return self.get(f"/api/profile/content?name={target}")

    def switch_profile(self, name: str) -> dict[str, Any]:
        return self.post("/api/profile/switch", {"name": name})

    def save_text_file(self, path: str, content: str) -> dict[str, Any]:
        return self.post("/api/text-file/save", {"path": path, "content": content})

    def list_projects(self) -> list[dict[str, Any]]:
        data = self.get("/api/projects")
        return list(data.get("projects", []))

    def list_briefs(self) -> list[dict[str, Any]]:
        data = self.get("/api/ops/briefs")
        return list(data.get("briefs", []))

    def get_text_file(self, path: str) -> dict[str, Any]:
        target = urllib.parse.quote(path)
        return self.get(f"/api/text-file?path={target}")

    def update_project(self, project_id: str, **fields: Any) -> dict[str, Any]:
        payload = {"project_id": project_id, **fields}
        return self.post("/api/projects/update", payload)

    def get_notes(self) -> list[str]:
        data = self.get("/api/notes")
        return list(data.get("notes", []))

    def save_notes(self, content: str) -> dict[str, Any]:
        return self.post("/api/notes/save", {"content": content})

    def get_memory(self) -> dict[str, Any]:
        return self.get("/api/memory")

    def save_memory(self, section: str, content: str) -> dict[str, Any]:
        return self.post("/api/memory/write", {"section": section, "content": content})

    def get_costs(self) -> dict[str, Any]:
        return self.get("/api/ops/costs")

    def get_dialogs(self) -> dict[str, Any]:
        return self.get("/api/ops/dialogs")

    def get_resources(self) -> dict[str, Any]:
        return self.get("/api/ops/resources")

    def gateway_status(self, profile: str | None = None) -> dict[str, Any]:
        target = urllib.parse.quote(profile or "default")
        return self.get(f"/api/gateway/status?profile={target}")

    def gateway_logs(self, profile: str | None = None, lines: int = 120) -> dict[str, Any]:
        target = urllib.parse.quote(profile or "default")
        return self.get(f"/api/gateway/logs?profile={target}&lines={int(lines)}")

    def gateway_action(self, action: str, profile: str | None = None) -> dict[str, Any]:
        return self.post("/api/gateway/action", {"profile": profile or "default", "action": action})

    def list_cron_jobs(self) -> list[dict[str, Any]]:
        data = self.get("/api/crons")
        return list(data.get("jobs", []))

    def create_cron_job(self, prompt: str, schedule: str, name: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"prompt": prompt, "schedule": schedule}
        if name:
            payload["name"] = name
        return self.post("/api/crons/create", payload)

    def run_cron_job(self, job_id: str) -> dict[str, Any]:
        return self.post("/api/crons/run", {"job_id": job_id})

    def pause_cron_job(self, job_id: str) -> dict[str, Any]:
        return self.post("/api/crons/pause", {"job_id": job_id})

    def resume_cron_job(self, job_id: str) -> dict[str, Any]:
        return self.post("/api/crons/resume", {"job_id": job_id})

    def delete_cron_job(self, job_id: str) -> dict[str, Any]:
        return self.post("/api/crons/delete", {"job_id": job_id})

    def check_updates(self, force: bool = False) -> dict[str, Any]:
        return self.get("/api/updates/check?force=1" if force else "/api/updates/check")

    def apply_update(self, target: str) -> dict[str, Any]:
        return self.post("/api/updates/apply", {"target": target})

    def cleanup_sessions(self, zero_only: bool = False) -> dict[str, Any]:
        path = "/api/sessions/cleanup_zero_message" if zero_only else "/api/sessions/cleanup"
        return self.post(path, {})
