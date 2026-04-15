from __future__ import annotations

from ..client.api import HermesAPIClient


def render_sessions_text(client: HermesAPIClient) -> str:
    sessions = client.list_sessions()
    if not sessions:
        return "No Hermes sessions found."
    lines = ["Sessions"]
    for session in sessions[:20]:
        lines.append(
            f"- {session.title} ({session.session_id}) profile={session.profile or 'default'} "
            f"messages={session.message_count} model={session.model or 'unknown'}"
        )
    return "\n".join(lines)
