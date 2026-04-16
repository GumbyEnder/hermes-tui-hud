from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .app import run_tui
from .client.api import HermesAPIClient, HermesAPIError
from .views import render_agents_text, render_overview_text, render_sessions_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-hud", description="Hermes terminal operator console")
    parser.add_argument("--base-url", default=None, help="Hermes Web UI base URL")
    parser.add_argument("--password", default=None, help="Hermes Web UI password")
    parser.add_argument("--json", action="store_true", help="Emit JSON where possible")

    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show status information")
    status_sub = status.add_subparsers(dest="status_command", required=True)
    status_sub.add_parser("summary", help="Summary of resources, profiles, sessions, and alerts")

    agents = sub.add_parser("agents", help="Agent/profile operations")
    agents_sub = agents.add_subparsers(dest="agents_command", required=True)
    agents_sub.add_parser("list", help="List profiles")

    sessions = sub.add_parser("sessions", help="Session operations")
    sessions_sub = sessions.add_subparsers(dest="sessions_command", required=True)
    sessions_sub.add_parser("list", help="List sessions")
    sessions_search = sessions_sub.add_parser("search", help="Search sessions by title or content")
    sessions_search.add_argument("query", help="Search query")
    sessions_search.add_argument("--depth", type=int, default=24, help="Message depth for content search")
    sessions_export = sessions_sub.add_parser("export", help="Export a session to JSON")
    sessions_export.add_argument("session_id", help="Session id")
    sessions_export.add_argument("--dest", default="/tmp", help="Destination directory")

    gateway = sub.add_parser("gateway", help="Gateway operations")
    gateway_sub = gateway.add_subparsers(dest="gateway_command", required=True)
    gateway_status = gateway_sub.add_parser("status", help="Show gateway status")
    gateway_status.add_argument("--profile", default=None, help="Profile name")
    gateway_logs = gateway_sub.add_parser("logs", help="Show gateway logs")
    gateway_logs.add_argument("--profile", default=None, help="Profile name")
    gateway_logs.add_argument("--lines", type=int, default=120, help="Number of log lines")
    for action in ("start", "stop", "restart"):
        gateway_action = gateway_sub.add_parser(action, help=f"{action.title()} gateway service")
        gateway_action.add_argument("--profile", default=None, help="Profile name")

    cron = sub.add_parser("cron", help="Cron operations")
    cron_sub = cron.add_subparsers(dest="cron_command", required=True)
    cron_sub.add_parser("list", help="List cron jobs")
    cron_add = cron_sub.add_parser("add", help="Create a cron job")
    cron_add.add_argument("--prompt", required=True, help="Prompt text")
    cron_add.add_argument("--schedule", required=True, help="Cron schedule expression")
    cron_add.add_argument("--name", default=None, help="Optional job name")
    for action in ("run", "pause", "resume", "delete"):
        cron_action = cron_sub.add_parser(action, help=f"{action.title()} a cron job")
        cron_action.add_argument("job_id", help="Cron job id")

    maintenance = sub.add_parser("maintenance", help="Maintenance actions")
    maintenance_sub = maintenance.add_subparsers(dest="maintenance_command", required=True)
    maintenance_check = maintenance_sub.add_parser("check-updates", help="Check for updates")
    maintenance_check.add_argument("--force", action="store_true", help="Force re-check")
    maintenance_apply = maintenance_sub.add_parser("apply-update", help="Apply update")
    maintenance_apply.add_argument("target", choices=["webui", "agent"], help="Update target")
    maintenance_sub.add_parser("cleanup-sessions", help="Cleanup stale untitled empty sessions")
    maintenance_sub.add_parser("cleanup-zero-message", help="Cleanup all zero-message sessions")

    sub.add_parser("tui", help="Launch the full-screen TUI")
    return parser


def _client(args: argparse.Namespace) -> HermesAPIClient:
    return HermesAPIClient(base_url=args.base_url, password=args.password)


def _emit_json(payload: Any) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _confirm(prompt: str) -> bool:
    response = input(f"{prompt} [y/N]: ").strip().lower()
    return response in {"y", "yes"}


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


def _cron_job_label(job: dict[str, Any]) -> str:
    return str(job.get("name") or job.get("id") or "unnamed job")


def _print_gateway_status(payload: dict[str, Any]) -> None:
    print("Gateway Status")
    print(f"Profile: {payload.get('profile') or 'default'}")
    print(f"Service: {payload.get('service') or 'unknown'}")
    print(f"Installed: {bool(payload.get('installed'))}")
    print(f"Active: {bool(payload.get('active'))}")
    print(f"Enabled: {bool(payload.get('enabled'))}")
    if payload.get("status"):
        print(f"Status: {payload['status']}")
    if payload.get("message"):
        print(f"Message: {payload['message']}")


def _print_cron_jobs(jobs: list[dict[str, Any]]) -> None:
    if not jobs:
        print("No cron jobs found.")
        return
    print("Cron Jobs")
    for job in jobs:
        print(f"- {_cron_job_label(job)} ({job.get('id') or 'no-id'})")
        print(f"  schedule={_cron_schedule_label(job)} enabled={job.get('enabled', True)}")
        print(f"  last={job.get('last_run_at') or job.get('last_run') or job.get('last_status') or job.get('state') or 'pending'}")
        if job.get("prompt"):
            print(f"  prompt={job['prompt']}")


def _print_update_summary(payload: dict[str, Any]) -> None:
    if payload.get("disabled"):
        print("Update checks are disabled.")
        return
    print("Update Summary")
    for key in ("webui", "agent"):
        block = payload.get(key) or {}
        if not isinstance(block, dict):
            continue
        print(f"- {key}")
        print(f"  branch={block.get('branch') or 'unknown'} behind={block.get('behind') or 0}")
        print(f"  current={block.get('current_sha') or 'unknown'} latest={block.get('latest_sha') or 'unknown'}")


def _print_session_search(results: list[dict[str, Any]], query: str) -> None:
    if not results:
        print(f"No sessions matched: {query}")
        return
    print(f"Session Search · {query}")
    for session in results:
        flags = []
        if session.get("pinned"):
            flags.append("pinned")
        if session.get("archived"):
            flags.append("archived")
        match = session.get("match_type") or "match"
        print(f"- {session.get('title') or 'Untitled'} ({session.get('session_id') or 'no-id'})")
        print(f"  profile={session.get('profile') or 'default'} model={session.get('model') or 'unknown'} match={match}")
        if flags:
            print(f"  flags={', '.join(flags)}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = _client(args)
    try:
        if args.command == "status" and args.status_command == "summary":
            if args.json:
                return _emit_json(client.summary())
            print(render_overview_text(client))
            return 0

        if args.command == "agents" and args.agents_command == "list":
            if args.json:
                return _emit_json([profile.__dict__ for profile in client.list_profiles()])
            print(render_agents_text(client))
            return 0

        if args.command == "sessions" and args.sessions_command == "list":
            if args.json:
                return _emit_json([session.__dict__ for session in client.list_sessions()])
            print(render_sessions_text(client))
            return 0

        if args.command == "sessions" and args.sessions_command == "search":
            payload = client.search_sessions(args.query, content=True, depth=args.depth)
            if args.json:
                return _emit_json(payload)
            _print_session_search(payload, args.query)
            return 0

        if args.command == "sessions" and args.sessions_command == "export":
            target = client.export_session(args.session_id, dest_dir=args.dest)
            if args.json:
                return _emit_json({"ok": True, "path": str(target)})
            print(f"Exported session to {target}")
            return 0

        if args.command == "gateway":
            if args.gateway_command == "status":
                payload = client.gateway_status(profile=args.profile)
                if args.json:
                    return _emit_json(payload)
                _print_gateway_status(payload)
                return 0

            if args.gateway_command == "logs":
                payload = client.gateway_logs(profile=args.profile, lines=args.lines)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("logs") or "")
                return 0

            if args.gateway_command in {"start", "stop", "restart"}:
                payload = client.gateway_action(args.gateway_command, profile=args.profile)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Gateway {args.gateway_command} requested.")
                return 0

        if args.command == "cron":
            if args.cron_command == "list":
                jobs = client.list_cron_jobs()
                if args.json:
                    return _emit_json(jobs)
                _print_cron_jobs(jobs)
                return 0

            if args.cron_command == "add":
                payload = client.create_cron_job(prompt=args.prompt, schedule=args.schedule, name=args.name)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or "Cron job created.")
                return 0

            if args.cron_command == "run":
                payload = client.run_cron_job(args.job_id)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Cron job {args.job_id} run requested.")
                return 0

            if args.cron_command == "pause":
                payload = client.pause_cron_job(args.job_id)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Cron job {args.job_id} paused.")
                return 0

            if args.cron_command == "resume":
                payload = client.resume_cron_job(args.job_id)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Cron job {args.job_id} resumed.")
                return 0

            if args.cron_command == "delete":
                if not _confirm(f"Delete cron job {args.job_id}?"):
                    print("Cancelled.")
                    return 0
                payload = client.delete_cron_job(args.job_id)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Cron job {args.job_id} deleted.")
                return 0

        if args.command == "maintenance":
            if args.maintenance_command == "check-updates":
                payload = client.check_updates(force=args.force)
                if args.json:
                    return _emit_json(payload)
                _print_update_summary(payload)
                return 0

            if args.maintenance_command == "apply-update":
                if not _confirm(f"Apply update to {args.target}?"):
                    print("Cancelled.")
                    return 0
                payload = client.apply_update(args.target)
                if args.json:
                    return _emit_json(payload)
                print(payload.get("message") or f"Update requested for {args.target}.")
                return 0

            if args.maintenance_command == "cleanup-sessions":
                if not _confirm("Cleanup stale untitled empty sessions?"):
                    print("Cancelled.")
                    return 0
                payload = client.cleanup_sessions(zero_only=False)
                if args.json:
                    return _emit_json(payload)
                print(f"Cleaned {payload.get('cleaned', 0)} sessions.")
                return 0

            if args.maintenance_command == "cleanup-zero-message":
                if not _confirm("Cleanup all zero-message sessions?"):
                    print("Cancelled.")
                    return 0
                payload = client.cleanup_sessions(zero_only=True)
                if args.json:
                    return _emit_json(payload)
                print(f"Cleaned {payload.get('cleaned', 0)} sessions.")
                return 0

        if args.command == "tui":
            return run_tui(client)
    except HermesAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
