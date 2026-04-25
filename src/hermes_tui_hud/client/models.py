"""Typed dataclass models for Hermes Dashboard API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Status:
    """Response from GET /api/status."""
    version: str = ""
    release_date: str = ""
    hermes_home: str = ""
    config_path: str = ""
    env_path: str = ""
    config_version: int = 0
    latest_config_version: int = 0
    gateway_running: bool = False
    gateway_pid: Optional[int] = None
    gateway_health_url: Optional[str] = None
    gateway_state: Optional[str] = None
    gateway_platforms: dict[str, Any] = field(default_factory=dict)
    gateway_exit_reason: Optional[str] = None
    gateway_updated_at: Optional[str] = None
    active_sessions: int = 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Status:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HermesSession:
    """Session object from GET /api/sessions or GET /api/sessions/{id}."""
    session_id: str = ""
    title: str = ""
    model: str = ""
    platform: str = ""
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    last_active: Optional[str] = None
    is_active: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    api_call_count: int = 0
    message_count: int = 0
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> HermesSession:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SessionSearchResult:
    """Result item from GET /api/sessions/search."""
    session_id: str = ""
    snippet: str = ""
    role: Optional[str] = None
    source: Optional[str] = None
    model: Optional[str] = None
    session_started: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SessionSearchResult:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ModelCapabilities:
    """Model capabilities from GET /api/model/info."""
    supports_tools: bool = False
    supports_vision: bool = False
    supports_reasoning: bool = False
    context_window: int = 0
    max_output_tokens: int = 0
    model_family: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ModelCapabilities:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ModelInfo:
    """Response from GET /api/model/info."""
    model: str = ""
    provider: str = ""
    auto_context_length: int = 0
    config_context_length: int = 0
    effective_context_length: int = 0
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ModelInfo:
        caps = data.get("capabilities", {})
        return cls(
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            auto_context_length=data.get("auto_context_length", 0),
            config_context_length=data.get("config_context_length", 0),
            effective_context_length=data.get("effective_context_length", 0),
            capabilities=ModelCapabilities.from_api(caps) if caps else ModelCapabilities(),
        )


@dataclass
class CronJob:
    """Cron job from /api/cron/jobs endpoints."""
    job_id: str = ""
    name: str = ""
    prompt: str = ""
    schedule: str = ""
    deliver: str = ""
    enabled: bool = True
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    next_run: Optional[str] = None
    schedule_display: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> CronJob:
        # Map API keys to dataclass field names
        field_map = {
            "id": "job_id",
            "last_run_at": "last_run",
            "next_run_at": "next_run",
        }
        mapped = {}
        for k, v in data.items():
            field_name = field_map.get(k, k)
            if field_name in cls.__dataclass_fields__:
                mapped[field_name] = v
        return cls(**mapped)


@dataclass
class Skill:
    """Skill from GET /api/skills."""
    name: str = ""
    description: str = ""
    enabled: bool = True

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Skill:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Toolset:
    """Toolset from GET /api/tools/toolsets."""
    name: str = ""
    label: str = ""
    description: str = ""
    enabled: bool = False
    available: bool = False
    configured: bool = False
    tools: list[str] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Toolset:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EnvVar:
    """Environment variable from GET /api/env."""
    name: str = ""
    is_set: bool = False
    redacted_value: Optional[str] = None
    description: str = ""
    url: Optional[str] = None
    category: str = ""
    is_password: bool = False
    tools: list[str] = field(default_factory=list)
    advanced: bool = False

    @classmethod
    def from_api(cls, name: str, data: dict[str, Any]) -> EnvVar:
        return cls(name=name, **{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DailyUsage:
    """Daily usage row from GET /api/analytics/usage."""
    day: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    sessions: int = 0
    api_calls: int = 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DailyUsage:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ModelUsage:
    """Per-model usage row from GET /api/analytics/usage."""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    sessions: int = 0
    api_calls: int = 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ModelUsage:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class UsageAnalytics:
    """Response from GET /api/analytics/usage."""
    daily: list[DailyUsage] = field(default_factory=list)
    by_model: list[ModelUsage] = field(default_factory=list)
    totals: dict[str, Any] = field(default_factory=dict)
    period_days: int = 30
    skills: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> UsageAnalytics:
        return cls(
            daily=[DailyUsage.from_api(d) for d in data.get("daily", [])],
            by_model=[ModelUsage.from_api(m) for m in data.get("by_model", [])],
            totals=data.get("totals", {}),
            period_days=data.get("period_days", 30),
            skills=data.get("skills", {}),
        )


@dataclass
class OAuthProvider:
    """OAuth provider from GET /api/providers/oauth."""
    id: str = ""
    name: str = ""
    flow: str = ""
    cli_command: str = ""
    docs_url: str = ""
    logged_in: bool = False
    source: Optional[str] = None
    source_label: str = ""
    token_preview: str = ""
    expires_at: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> OAuthProvider:
        status = data.get("status", {})
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            flow=data.get("flow", ""),
            cli_command=data.get("cli_command", ""),
            docs_url=data.get("docs_url", ""),
            logged_in=status.get("logged_in", False),
            source=status.get("source"),
            source_label=status.get("source_label", ""),
            token_preview=status.get("token_preview", ""),
            expires_at=status.get("expires_at"),
        )


@dataclass
class DashboardTheme:
    """Theme from GET /api/dashboard/themes."""
    name: str = ""
    label: str = ""
    description: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DashboardTheme:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ActionStatus:
    """Action status from GET /api/actions/{name}/status."""
    name: str = ""
    running: bool = False
    exit_code: Optional[int] = None
    pid: Optional[int] = None
    lines: list[str] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ActionStatus:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
