from __future__ import annotations

import re


def render_notes_todos_text(lines: list[str]) -> str:
    output = ["Notes / Todos"]
    todos = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-*]\s+\[( |x|X)\]\s+", stripped):
            todos.append(stripped)
    output.append(f"Notes lines: {len(lines)}")
    output.append(f"Todos: {len(todos)}")
    output.append("")
    output.append("Recent todos")
    if todos:
        for item in todos[-8:]:
            output.append(f"- {item}")
    else:
        output.append("No todo items found in ~/.hermes/notes.md")
    output.extend(
        [
            "",
            "Actions",
            "  + = add todo",
            "  E = edit notes",
        ]
    )
    return "\n".join(output)
