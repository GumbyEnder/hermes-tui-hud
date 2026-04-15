from __future__ import annotations

from ..client.api import HermesAPIClient


def render_overview_text(client: HermesAPIClient) -> str:
    summary = client.summary()
    resources = summary.get("resources", {})
    cpu = resources.get("cpu_percent", 0)
    memory = resources.get("memory", {})
    disk = resources.get("disk", {})
    profiles = summary.get("profiles", {}).get("profiles", [])
    sessions = summary.get("sessions", {}).get("sessions", [])
    alerts = summary.get("alerts", {}).get("events", [])
    return "\n".join(
        [
            "Hermes HUD Overview",
            f"CPU: {cpu}%",
            f"Memory: {memory.get('percent', 0)}%",
            f"Disk: {disk.get('percent', 0)}%",
            f"Profiles: {len(profiles)}",
            f"Sessions: {len(sessions)}",
            f"Recent alerts: {len(alerts)}",
        ]
    )
