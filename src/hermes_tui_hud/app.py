"""TUI HUD application — placeholder for v0.2 full build."""


def run_app(args) -> None:
    """Launch the interactive TUI HUD."""
    try:
        from textual.app import App
    except ImportError:
        print("ERROR: textual is required for TUI mode. Install with: pip install textual", file=__import__("sys").stderr)
        raise SystemExit(1)

    from .client.api import HermesDashboardClient

    client = HermesDashboardClient(base_url=args.base_url, timeout=args.timeout)

    # Quick smoke test before launching TUI
    try:
        status = client.get_status()
    except Exception as exc:
        print(f"ERROR: Cannot reach Hermes dashboard: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)

    print(f"Connected to Hermes {status.version} (gateway {'running' if status.gateway_running else 'stopped'})")
    print("TUI HUD not yet built — use CLI subcommands for now.")
    print("  hermes-hud status|sessions|config|model|cron|skills|tools|logs|env|analytics|oauth")
