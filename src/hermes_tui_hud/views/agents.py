from __future__ import annotations

from ..client.api import HermesAPIClient


def render_agents_text(client: HermesAPIClient) -> str:
    profiles = client.list_profiles()
    if not profiles:
        return "No agent profiles found."
    lines = ["Agents"]
    for profile in profiles:
        flags: list[str] = []
        if profile.is_active:
            flags.append("active")
        if profile.is_default:
            flags.append("default")
        if profile.gateway_running:
            flags.append("gateway")
        suffix = f" [{' | '.join(flags)}]" if flags else ""
        lines.append(f"- {profile.name}{suffix}")
        lines.append(f"  model={profile.model or 'unknown'} provider={profile.provider or 'unknown'}")
        if profile.path:
            lines.append(f"  path={profile.path}")
    return "\n".join(lines)
