from __future__ import annotations

from typing import Any


def render_projects_text(projects: list[dict[str, Any]], selected_project_id: str | None = None) -> str:
    lines = ["Projects"]
    if not projects:
        lines.append("No projects found.")
        return "\n".join(lines)
    for project in projects:
        pid = str(project.get("project_id") or project.get("id") or project.get("name") or "")
        marker = ">" if pid == selected_project_id else "-"
        lines.append(f"{marker} {project.get('name') or pid}")
        if project.get("path"):
            lines.append(f"  path={project['path']}")
        if project.get("description"):
            lines.append(f"  {project['description']}")
        kanban = project.get("kanban") or {}
        lines.append(
            f"  todo={len(kanban.get('todo') or [])} in_progress={len(kanban.get('in_progress') or [])} done={len(kanban.get('done') or [])}"
        )
    lines.extend(
        [
            "",
            "Actions",
            "  ] / [ = select project",
            "  N = add Kanban card",
            "  M = move Kanban card",
        ]
    )
    return "\n".join(lines)
