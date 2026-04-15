from __future__ import annotations

import json
from typing import Any

from ..client.api import HermesAPIClient


def _cron_schedule_label(job: dict[str, Any]) -> str:
    value = job.get("schedule_display") or job.get("schedule")
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, dict):
        for key in ("display", "expr", "kind"):
            if isinstance(value.get(key), str) and value.get(key):
                return str(value[key])
        return json.dumps(value, ensure_ascii=False)
    return "manual"


def render_cron_text(client: HermesAPIClient) -> str:
    jobs = client.list_cron_jobs()
    lines = ["Cron Jobs"]
    if not jobs:
        lines.append("No cron jobs found.")
    else:
        for job in jobs[:20]:
            lines.append(f"- {job.get('name') or job.get('id') or 'unnamed job'}")
            lines.append(
                f"  id={job.get('id') or 'n/a'} enabled={job.get('enabled', True)} schedule={_cron_schedule_label(job)}"
            )
            lines.append(
                f"  last={job.get('last_run_at') or job.get('last_run') or job.get('last_status') or job.get('state') or 'pending'}"
            )
    lines.extend(
        [
            "",
            "Actions",
            "  n = create cron job",
            "  p = pause/resume selected by id prompt",
            "  d = delete selected by id prompt",
            "  e = execute selected by id prompt",
        ]
    )
    return "\n".join(lines)
