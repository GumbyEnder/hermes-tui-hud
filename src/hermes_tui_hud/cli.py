"""CLI entry point for hermes-hud."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .client.api import HermesDashboardClient, HermesAPIError


def _client(args: argparse.Namespace) -> HermesDashboardClient:
    return HermesDashboardClient(base_url=args.base_url, timeout=args.timeout)


def _fmt_json(obj) -> str:
    """Pretty-print an object as JSON, handling dataclasses."""
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return json.dumps(asdict(obj), indent=2, default=str)
    if isinstance(obj, list):
        return json.dumps(
            [asdict(i) if hasattr(i, "__dataclass_fields__") else i for i in obj],
            indent=2, default=str,
        )
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2, default=str)
    return str(obj)


def cmd_status(args: argparse.Namespace) -> None:
    c = _client(args)
    s = c.get_status()
    print(f"Hermes {s.version}  gateway={'RUNNING' if s.gateway_running else 'STOPPED'}  "
          f"pid={s.gateway_pid or '-'}  sessions={s.active_sessions}")
    if s.gateway_state:
        print(f"  state: {s.gateway_state}")
    if s.gateway_platforms:
        for name, state in s.gateway_platforms.items():
            print(f"  {name}: {state.get('state', '?')}")


def cmd_sessions(args: argparse.Namespace) -> None:
    c = _client(args)
    if args.search:
        results = c.search_sessions(args.search, limit=args.limit)
        for r in results:
            print(f"  {r.session_id[:12]}  {r.role or '?':8s}  {r.snippet[:80]}")
        return
    sessions, total = c.list_sessions(limit=args.limit, offset=args.offset)
    print(f"Sessions ({total} total, showing {len(sessions)}):")
    for s in sessions:
        cost = f"${s.estimated_cost_usd:.4f}" if s.estimated_cost_usd else "-"
        active = "*" if s.is_active else " "
        print(f"  {active} {s.session_id[:12]}  {s.model[:30]:30s}  "
              f"in={s.input_tokens:>8d} out={s.output_tokens:>8d}  {cost:>10s}  "
              f"{(s.title or '-')[:50]}")


def cmd_session_detail(args: argparse.Namespace) -> None:
    c = _client(args)
    s = c.get_session(args.session_id)
    print(_fmt_json(s))


def cmd_session_messages(args: argparse.Namespace) -> None:
    c = _client(args)
    data = c.get_session_messages(args.session_id)
    for msg in data.get("messages", []):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        print(f"[{role}] {str(content)[:200]}")


def cmd_config(args: argparse.Namespace) -> None:
    c = _client(args)
    if args.raw:
        print(c.get_config_raw())
    elif args.schema:
        print(_fmt_json(c.get_config_schema()))
    elif args.defaults:
        print(_fmt_json(c.get_config_defaults()))
    else:
        print(_fmt_json(c.get_config()))


def cmd_model(args: argparse.Namespace) -> None:
    c = _client(args)
    m = c.get_model_info()
    print(f"Model:     {m.model}")
    print(f"Provider:  {m.provider}")
    print(f"Context:   {m.effective_context_length:,d} tokens (auto={m.auto_context_length:,d} config={m.config_context_length:,d})")
    caps = m.capabilities
    print(f"Tools:     {'yes' if caps.supports_tools else 'no'}  "
          f"Vision: {'yes' if caps.supports_vision else 'no'}  "
          f"Reasoning: {'yes' if caps.supports_reasoning else 'no'}")
    print(f"Family:    {caps.model_family}  Max output: {caps.max_output_tokens:,d}")


def cmd_cron(args: argparse.Namespace) -> None:
    c = _client(args)
    jobs = c.list_cron_jobs()
    if not jobs:
        print("No cron jobs.")
        return
    for j in jobs:
        state = "ON " if j.enabled else "OFF"
        last = j.last_status or "-"
        print(f"  [{state}] {j.job_id[:12]}  {j.name[:30]:30s}  "
              f"schedule={j.schedule}  last={last}")


def cmd_skills(args: argparse.Namespace) -> None:
    c = _client(args)
    skills = c.list_skills()
    if not skills:
        print("No skills found.")
        return
    for s in skills:
        state = "ON " if s.enabled else "OFF"
        print(f"  [{state}] {s.name:40s}  {s.description[:60]}")


def cmd_tools(args: argparse.Namespace) -> None:
    c = _client(args)
    toolsets = c.list_toolsets()
    if not toolsets:
        print("No toolsets found.")
        return
    for t in toolsets:
        state = "ON " if t.enabled else "OFF"
        cfg = "ok" if t.configured else "NEEDS CONFIG"
        print(f"  [{state}] {t.name:25s}  {cfg:12s}  tools: {', '.join(t.tools[:5])}")


def cmd_logs(args: argparse.Namespace) -> None:
    c = _client(args)
    data = c.get_logs(file=args.file, lines=args.lines, level=args.level,
                      component=args.component, search=args.search)
    for line in data.get("lines", []):
        print(line)


def cmd_env(args: argparse.Namespace) -> None:
    c = _client(args)
    envs = c.list_env_vars()
    for e in envs:
        state = "SET" if e.is_set else "   "
        val = e.redacted_value or "-"
        print(f"  [{state}] {e.name:35s}  {val:20s}  {e.description[:50]}")


def cmd_analytics(args: argparse.Namespace) -> None:
    c = _client(args)
    a = c.get_usage_analytics(days=args.days)
    print(f"Usage analytics (last {a.period_days} days):")
    print(f"  Totals: in={a.totals.get('input_tokens', 0):,d}  "
          f"out={a.totals.get('output_tokens', 0):,d}  "
          f"est_cost=${a.totals.get('estimated_cost', 0):.2f}  "
          f"sessions={a.totals.get('sessions', 0)}")
    print()
    if a.by_model:
        print("  By model:")
        for m in a.by_model:
            print(f"    {m.model[:40]:40s}  in={m.input_tokens:,d}  out={m.output_tokens:,d}  "
                  f"${m.estimated_cost:.2f}")


def cmd_oauth(args: argparse.Namespace) -> None:
    c = _client(args)
    providers = c.list_oauth_providers()
    if not providers:
        print("No OAuth providers configured.")
        return
    for p in providers:
        state = "IN " if p.logged_in else "OUT"
        print(f"  [{state}] {p.name:20s}  flow={p.flow:12s}  source={p.source_label or '-'}")


def cmd_tui(args: argparse.Namespace) -> None:
    from .app import run_app
    run_app(args)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="hermes-hud",
        description="Hermes Agent TUI HUD — terminal operator console",
    )
    parser.add_argument("--version", action="version", version=f"hermes-hud {__version__}")
    parser.add_argument("--base-url", default=None, help="Dashboard API base URL (default: http://127.0.0.1:9119)")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")

    sub = parser.add_subparsers(dest="command", help="Subcommand")

    # status
    p_status = sub.add_parser("status", help="Gateway & server status")
    p_status.set_defaults(func=cmd_status)

    # sessions
    p_sess = sub.add_parser("sessions", help="List and search sessions")
    p_sess.add_argument("--limit", type=int, default=20)
    p_sess.add_argument("--offset", type=int, default=0)
    p_sess.add_argument("--search", "-s", help="FTS5 search query")
    p_sess.set_defaults(func=cmd_sessions)

    # session detail
    p_detail = sub.add_parser("session", help="Session detail / messages")
    p_detail.add_argument("session_id")
    p_detail.add_argument("--messages", "-m", action="store_true", help="Show messages")
    p_detail.set_defaults(func=cmd_session_detail)

    # config
    p_cfg = sub.add_parser("config", help="View Hermes config")
    p_cfg.add_argument("--raw", action="store_true", help="Raw YAML")
    p_cfg.add_argument("--schema", action="store_true", help="Config schema")
    p_cfg.add_argument("--defaults", action="store_true", help="Default values")
    p_cfg.set_defaults(func=cmd_config)

    # model
    p_model = sub.add_parser("model", help="Current model info")
    p_model.set_defaults(func=cmd_model)

    # cron
    p_cron = sub.add_parser("cron", help="Cron jobs")
    p_cron.set_defaults(func=cmd_cron)

    # skills
    p_skills = sub.add_parser("skills", help="List skills")
    p_skills.set_defaults(func=cmd_skills)

    # tools
    p_tools = sub.add_parser("tools", help="List toolsets")
    p_tools.set_defaults(func=cmd_tools)

    # logs
    p_logs = sub.add_parser("logs", help="Agent/gateway logs")
    p_logs.add_argument("--file", default="agent", choices=["agent", "errors", "gateway"])
    p_logs.add_argument("--lines", type=int, default=100)
    p_logs.add_argument("--level", default=None)
    p_logs.add_argument("--component", default=None)
    p_logs.add_argument("--search", default=None)
    p_logs.set_defaults(func=cmd_logs)

    # env
    p_env = sub.add_parser("env", help="Environment variables")
    p_env.set_defaults(func=cmd_env)

    # analytics
    p_analytics = sub.add_parser("analytics", help="Usage analytics")
    p_analytics.add_argument("--days", type=int, default=30)
    p_analytics.set_defaults(func=cmd_analytics)

    # oauth
    p_oauth = sub.add_parser("oauth", help="OAuth providers")
    p_oauth.set_defaults(func=cmd_oauth)

    # tui
    p_tui = sub.add_parser("tui", help="Launch interactive TUI HUD")
    p_tui.set_defaults(func=cmd_tui)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except HermesAPIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
