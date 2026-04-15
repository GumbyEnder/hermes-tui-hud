from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AgentProfile:
    name: str
    model: str | None = None
    provider: str | None = None
    is_active: bool = False
    is_default: bool = False
    gateway_running: bool = False
    path: str | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "AgentProfile":
        return cls(
            name=str(payload.get("name") or "unknown"),
            model=payload.get("model"),
            provider=payload.get("provider"),
            is_active=bool(payload.get("is_active")),
            is_default=bool(payload.get("is_default")),
            gateway_running=bool(payload.get("gateway_running")),
            path=payload.get("path"),
        )


@dataclass(slots=True)
class HermesSession:
    session_id: str
    title: str
    profile: str | None = None
    model: str | None = None
    message_count: int = 0
    updated_at: float = 0.0

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "HermesSession":
        return cls(
            session_id=str(payload.get("session_id") or ""),
            title=str(payload.get("title") or "Untitled session"),
            profile=payload.get("profile"),
            model=payload.get("model"),
            message_count=int(payload.get("message_count") or 0),
            updated_at=float(payload.get("updated_at") or payload.get("created_at") or 0),
        )


@dataclass(slots=True)
class HermesAlert:
    title: str
    event_type: str | None = None
    project: str | None = None
    ts: float = 0.0

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "HermesAlert":
        return cls(
            title=str(payload.get("title") or payload.get("summary") or payload.get("event") or "event"),
            event_type=payload.get("type"),
            project=payload.get("project"),
            ts=float(payload.get("ts") or 0),
        )
