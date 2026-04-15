from __future__ import annotations

from ..client.api import HermesAPIClient


def render_gateway_text(client: HermesAPIClient, profile: str | None = None) -> str:
    payload = client.gateway_status(profile=profile)
    lines = [
        "Gateway",
        f"Profile: {payload.get('profile') or profile or 'default'}",
        f"Service: {payload.get('service') or 'unknown'}",
        f"Installed: {bool(payload.get('installed'))}",
        f"Active: {bool(payload.get('active'))}",
        f"Enabled: {bool(payload.get('enabled'))}",
    ]
    if payload.get("message"):
        lines.append(f"Message: {payload['message']}")
    if payload.get("status"):
        lines.extend(["", payload["status"]])
    lines.extend(
        [
            "",
            "Actions",
            "  s = start gateway",
            "  x = stop gateway",
            "  t = restart gateway",
            "  l = show recent gateway logs",
        ]
    )
    return "\n".join(lines)
