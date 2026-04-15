from __future__ import annotations

from ..client.api import HermesAPIClient


def render_maintenance_text(client: HermesAPIClient) -> str:
    payload = client.check_updates(force=False)
    lines = ["Maintenance"]
    if payload.get("disabled"):
        lines.append("Update checks are disabled.")
    else:
        for key in ("webui", "agent"):
            block = payload.get(key) or {}
            if not isinstance(block, dict):
                continue
            lines.append(f"- {key}")
            lines.append(
                f"  branch={block.get('branch') or 'unknown'} behind={block.get('behind') or 0}"
            )
            lines.append(
                f"  current={block.get('current_sha') or 'unknown'} latest={block.get('latest_sha') or 'unknown'}"
            )
    lines.extend(
        [
            "",
            "Actions",
            "  u = force update check",
            "  w = apply webui update",
            "  a = apply agent update",
            "  c = cleanup stale sessions",
            "  z = cleanup zero-message sessions",
        ]
    )
    return "\n".join(lines)
