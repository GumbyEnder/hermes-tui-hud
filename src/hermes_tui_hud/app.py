from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .client import HermesAPIClient
from .client.api import HermesAPIError

SPLASH_ART = r"""
██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗
██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝
███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗
██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║
██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝

   A G E N T   O P E R A T O R   C O N S O L E
""".strip("\n")

THEMES: dict[str, dict[str, str]] = {
    "matrix": {
        "name": "Matrix",
        "brand": "HERMES // MATRIX",
        "tagline": "green phosphor signal deck",
        "hero_title": "Signal Matrix",
        "hero_subtitle": "Operator link live",
        "splash_title": "Boot Sequence // Matrix",
        "splash_subtitle": "Signal sync",
        "screen_bg": "#020604",
        "nav_bg": "#06100b",
        "workspace_bg": "#040907",
        "main_bg": "#040b07",
        "detail_bg": "#07100b",
        "header_bg": "#07110c",
        "status_bg": "#08120d",
        "accent": "#8cf7ac",
        "accent_soft": "#84b694",
        "select_bg": "#143121",
        "text": "#d8f9e1",
        "muted": "#8fc9a2",
        "warn": "#e0c36a",
        "info": "#8ab2ff",
        "border": "#173424",
        "hero_border": "#204d31",
        "marker": "▸",
    },
    "amber": {
        "name": "Amber CRT",
        "brand": "HERMES // AMBER",
        "tagline": "warm phosphor operator console",
        "hero_title": "Amber Console",
        "hero_subtitle": "CRT link steady",
        "splash_title": "Boot Sequence // Amber CRT",
        "splash_subtitle": "Phosphor warmup",
        "screen_bg": "#090603",
        "nav_bg": "#120b05",
        "workspace_bg": "#0c0804",
        "main_bg": "#110a05",
        "detail_bg": "#140d07",
        "header_bg": "#140b05",
        "status_bg": "#160d05",
        "accent": "#ffb44d",
        "accent_soft": "#d69b45",
        "select_bg": "#3a2410",
        "text": "#ffe0b3",
        "muted": "#d7a96d",
        "warn": "#ffd37a",
        "info": "#f6bf74",
        "border": "#4a2e14",
        "hero_border": "#6d431f",
        "marker": "▸",
    },
    "crt-blue": {
        "name": "Phosphor Blue",
        "brand": "HERMES // BLUE",
        "tagline": "radar-clean ops display",
        "hero_title": "Blue Watchfloor",
        "hero_subtitle": "Status net stable",
        "splash_title": "Boot Sequence // Phosphor Blue",
        "splash_subtitle": "Waveguide align",
        "screen_bg": "#030611",
        "nav_bg": "#050b17",
        "workspace_bg": "#040913",
        "main_bg": "#06101a",
        "detail_bg": "#08131f",
        "header_bg": "#06101b",
        "status_bg": "#07131e",
        "accent": "#7ad9ff",
        "accent_soft": "#73b7d4",
        "select_bg": "#15304d",
        "text": "#d7f3ff",
        "muted": "#8ec3d9",
        "warn": "#9fd4ff",
        "info": "#8ac4ff",
        "border": "#17344e",
        "hero_border": "#1d486a",
        "marker": "▣",
    },
    "vault-tec": {
        "name": "Vault-Tec",
        "brand": "HERMES // VAULT-TEC",
        "tagline": "retro-future shelter ops",
        "hero_title": "Vault Console",
        "hero_subtitle": "Containment online",
        "splash_title": "Boot Sequence // Vault-Tec",
        "splash_subtitle": "Shelter systems ready",
        "screen_bg": "#07110a",
        "nav_bg": "#0d1a10",
        "workspace_bg": "#08140c",
        "main_bg": "#0b170e",
        "detail_bg": "#0f1d12",
        "header_bg": "#102011",
        "status_bg": "#0d1c10",
        "accent": "#f4d64b",
        "accent_soft": "#cdb55f",
        "select_bg": "#254124",
        "text": "#fff0a9",
        "muted": "#d5c77d",
        "warn": "#ffd966",
        "info": "#9ee4a2",
        "border": "#496134",
        "hero_border": "#8c9d3a",
        "marker": "◆",
    },
    "mother": {
        "name": "Mother",
        "brand": "HERMES // MOTHER",
        "tagline": "cold shipmind oversight",
        "hero_title": "MU-TH-UR Deck",
        "hero_subtitle": "supervision active",
        "splash_title": "Boot Sequence // Mother",
        "splash_subtitle": "corporate monitor online",
        "screen_bg": "#080707",
        "nav_bg": "#120d0d",
        "workspace_bg": "#0f0c0c",
        "main_bg": "#130f0f",
        "detail_bg": "#181212",
        "header_bg": "#150f0f",
        "status_bg": "#130d0d",
        "accent": "#d94b4b",
        "accent_soft": "#d3a258",
        "select_bg": "#311919",
        "text": "#f2dfcf",
        "muted": "#c1a190",
        "warn": "#ffbf69",
        "info": "#c9b59f",
        "border": "#563535",
        "hero_border": "#8b3d3d",
        "marker": "◉",
    },
    "netrunner": {
        "name": "Netrunner",
        "brand": "HERMES // NETRUNNER",
        "tagline": "high-voltage deck access",
        "hero_title": "Runner Grid",
        "hero_subtitle": "trace line masked",
        "splash_title": "Boot Sequence // Netrunner",
        "splash_subtitle": "deck uplink established",
        "screen_bg": "#04070d",
        "nav_bg": "#07121a",
        "workspace_bg": "#061019",
        "main_bg": "#09151f",
        "detail_bg": "#0b1824",
        "header_bg": "#09131d",
        "status_bg": "#08111a",
        "accent": "#35f0ff",
        "accent_soft": "#8edbe0",
        "select_bg": "#14394d",
        "text": "#d9fbff",
        "muted": "#87cbd1",
        "warn": "#ff7bf0",
        "info": "#76b8ff",
        "border": "#1d4c5d",
        "hero_border": "#22b7c8",
        "marker": "▶",
    },
    "neonwave": {
        "name": "Neonwave",
        "brand": "HERMES // NEONWAVE",
        "tagline": "synth horizon operator deck",
        "hero_title": "Neonwave Deck",
        "hero_subtitle": "night grid locked in",
        "splash_title": "Boot Sequence // Neonwave",
        "splash_subtitle": "horizon glow stable",
        "screen_bg": "#11081d",
        "nav_bg": "#1b0d2d",
        "workspace_bg": "#140b24",
        "main_bg": "#1a1030",
        "detail_bg": "#201238",
        "header_bg": "#1c0f31",
        "status_bg": "#180d2b",
        "accent": "#ff4fd8",
        "accent_soft": "#ff9ef1",
        "select_bg": "#48215f",
        "text": "#ffe6fb",
        "muted": "#d7a8e6",
        "warn": "#6ef2ff",
        "info": "#8ab7ff",
        "border": "#5b2f77",
        "hero_border": "#ff4fd8",
        "marker": "✦",
    },
}

THEME_STATE_PATH = Path.home() / ".hermes" / "tui-hud-theme.txt"
LAYOUT_STATE_PATH = Path.home() / ".hermes" / "tui-hud-layout.txt"
EFFECTS_STATE_PATH = Path.home() / ".hermes" / "tui-hud-effects.txt"

EFFECT_MODES: dict[str, dict[str, Any]] = {
    "full": {"name": "Full FX", "box": box.HEAVY, "show_splash_art": True, "show_tagline": True, "flatten": False},
    "minimal": {"name": "Minimal", "box": box.ROUNDED, "show_splash_art": False, "show_tagline": True, "flatten": False},
    "off": {"name": "Low Noise Ops", "box": box.MINIMAL, "show_splash_art": False, "show_tagline": False, "flatten": True},
}


def run_tui(client: HermesAPIClient | None = None) -> int:
    client = client or HermesAPIClient()
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container, Horizontal, Vertical
        from textual.screen import ModalScreen
        from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static, TextArea
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The full-screen TUI requires 'textual'. Install project dependencies first with "
            "'pip install -e .'"
        ) from exc

    class PromptScreen(ModalScreen[str | None]):
        CSS = """
        PromptScreen {
          align: center middle;
          background: rgba(0, 0, 0, 0.72);
        }
        #prompt-shell {
          width: 84;
          max-width: 92;
          height: auto;
          border: round #6bcf8d;
          background: #0b1610;
          padding: 1 2;
        }
        #prompt-actions {
          height: auto;
          margin-top: 1;
        }
        #prompt-actions Button {
          margin-right: 1;
        }
        """

        def __init__(self, title: str, placeholder: str = "", value: str = "") -> None:
            super().__init__()
            self.title = title
            self.placeholder = placeholder
            self.value = value

        def compose(self) -> ComposeResult:
            with Container(id="prompt-shell"):
                yield Label(self.title, id="prompt-title")
                yield Input(value=self.value, placeholder=self.placeholder, id="prompt-input")
                with Horizontal(id="prompt-actions"):
                    yield Button("OK", variant="success", id="prompt-ok")
                    yield Button("Cancel", variant="default", id="prompt-cancel")

        def on_mount(self) -> None:
            self.query_one(Input).focus()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            self.dismiss(event.value.strip() or None)

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "prompt-ok":
                value = self.query_one(Input).value.strip()
                self.dismiss(value or None)
            else:
                self.dismiss(None)

    class TextEditorScreen(ModalScreen[str | None]):
        CSS = """
        TextEditorScreen {
          align: center middle;
          background: rgba(0, 0, 0, 0.78);
        }
        #editor-shell {
          width: 140;
          max-width: 96%;
          height: 34;
          border: round #d6aa45;
          background: #11100b;
          padding: 1 2;
        }
        #editor-text {
          height: 1fr;
          margin-top: 1;
        }
        #editor-actions {
          height: auto;
          margin-top: 1;
        }
        #editor-actions Button {
          margin-right: 1;
        }
        """

        def __init__(self, title: str, content: str) -> None:
            super().__init__()
            self.title = title
            self.content = content

        def compose(self) -> ComposeResult:
            with Container(id="editor-shell"):
                yield Label(self.title)
                yield TextArea(self.content, id="editor-text")
                with Horizontal(id="editor-actions"):
                    yield Button("Save", variant="success", id="editor-save")
                    yield Button("Cancel", variant="default", id="editor-cancel")

        def on_mount(self) -> None:
            self.query_one(TextArea).focus()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "editor-save":
                self.dismiss(self.query_one(TextArea).text)
            else:
                self.dismiss(None)

    class HelpScreen(ModalScreen[None]):
        CSS = """
        HelpScreen {
          align: center middle;
          background: rgba(0, 0, 0, 0.82);
        }
        #help-shell {
          width: 120;
          max-width: 96%;
          height: 34;
          border: round #6bcf8d;
          background: #09110d;
          padding: 1 2;
        }
        """

        def compose(self) -> ComposeResult:
            help_text = Text()
            rows = [
                ("Global", "r refresh   g theme   G effects   L/ctrl+l layout   h help   q quit"),
                ("Navigation", "] / [ select item"),
                ("Sessions", "f search   k filter   j export   e rename   p pin   m archive   c clear   d delete"),
                ("Agents", "o switch active   v config   y soul"),
                ("Gateway", "s start   x stop   t restart   l logs"),
                ("Projects", "v open   e edit   y browse path   b up dir   p cycle entry   n add card   m move card"),
                ("Notes", "] / [ select todo   p done/open   d delete   m reorder   n add   e edit notes"),
                ("Ops", "u refresh   w update webui   a update agent   z zero cleanup"),
            ]
            for title, body in rows:
                help_text.append(f"{title:10}", style="bold #8cf7ac")
                help_text.append(body + "\n", style="#d8f9e1")
            yield Container(
                Static(Panel(help_text, title="Hermes HUD Help", border_style="#346d93")),
                id="help-shell",
            )

        def on_key(self, event) -> None:
            self.dismiss(None)

    class HermesHUDApp(App[None]):
        TITLE = "HERO — Hermes Executive Relay Operations"

        CSS = """
        Screen {
          layout: vertical;
          background: #020604;
          color: #d8f9e1;
        }
        Header {
          background: #07110c;
          color: #e7ffed;
          text-style: bold;
        }
        #chrome {
          height: 1fr;
        }
        #nav-rail {
          width: 26;
          min-width: 24;
          background: #06100b;
          border-right: heavy #173424;
          padding: 1 0;
        }
        #brand {
          height: auto;
          padding: 0 1 1 2;
          color: #8cf7ac;
          text-style: bold;
        }
        #nav {
          height: 1fr;
          background: transparent;
        }
        #top-nav {
          display: none;
          height: 3;
          padding: 0 2 1 2;
        }
        #top-nav Button {
          min-width: 0;
          width: auto;
          margin-right: 1;
        }
        #workspace {
          width: 1fr;
          background: #040907;
        }
        #hero {
          height: 4;
          padding: 1 2;
          border-bottom: heavy #173424;
          background: #08110c;
        }
        #content-shell {
          height: 1fr;
        }
        #main-pane {
          width: 3fr;
          padding: 1;
          border-right: heavy #173424;
          background: #040b07;
        }
        #detail-pane {
          width: 2fr;
          padding: 1;
          background: #07100b;
        }
        #main-content, #detail-content {
          height: 1fr;
        }
        #status-bar {
          height: 1;
          padding: 0 1;
          background: #08120d;
          color: #84b694;
        }
        ListView {
          background: transparent;
          border: none;
          height: 1fr;
        }
        ListItem {
          padding: 0 1 0 2;
          color: #8fc9a2;
        }
        ListItem.-highlight {
          background: #143121;
          color: #f0fff3;
          text-style: bold;
        }
        Footer {
          background: #08120d;
          color: #8fc9a2;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
            ("h", "show_help", "Help"),
            ("right_square_bracket", "next_item", "Next"),
            ("left_square_bracket", "prev_item", "Prev"),
            ("right", "next_section", "Next Section"),
            ("left", "prev_section", "Prev Section"),
            ("g", "cycle_theme", "Theme"),
            ("G", "cycle_effects", "Effects"),
            ("shift+g", "cycle_effects", "Effects"),
            ("shift+l", "cycle_layout", "Layout"),
            ("L", "cycle_layout", "Layout"),
            ("ctrl+l", "cycle_layout", "Layout"),
            ("f", "search_sessions", "Search"),
            ("k", "cycle_session_filter", "Filter"),
            ("i", "cycle_time_window", "Window"),
            ("j", "export_session", "Export"),
            ("o", "activate_agent", "Switch"),
            ("v", "preview", "Preview"),
            ("y", "preview_alt", "Alt"),
            ("b", "back_up", "Up"),
            ("s", "gateway_start", "Start"),
            ("x", "gateway_stop", "Stop"),
            ("t", "gateway_restart", "Restart"),
            ("l", "gateway_logs", "Logs"),
            ("u", "maintenance_check", "Check"),
            ("w", "maintenance_apply_webui", "WebUI"),
            ("a", "maintenance_apply_agent", "Agent"),
            ("c", "clear_or_cleanup", "Clear"),
            ("z", "cleanup_zero", "Zero"),
            ("n", "context_add", "Add"),
            ("e", "context_edit_or_run", "Edit/Run"),
            ("p", "toggle_flag", "Pin/Pause"),
            ("d", "context_delete", "Delete"),
            ("m", "move_context", "Move"),
        ]

        profiles: list[dict[str, Any]]
        sessions: list[dict[str, Any]]
        projects: list[dict[str, Any]]
        briefs: list[dict[str, Any]]
        notes_lines: list[str]
        selected_agent_name: str | None
        selected_session_id: str | None
        selected_project_id: str | None
        maintenance_cache: dict[str, Any] | None
        memory_cache: dict[str, Any] | None
        reports_cache: dict[str, Any] | None
        overview_cache: dict[str, Any] | None
        cron_cache: list[dict[str, Any]] | None
        gateway_cache: dict[str, dict[str, Any]]
        profile_content_cache: dict[str, dict[str, Any]]
        session_query: str
        session_filter: str
        report_window: str
        session_search_results: list[dict[str, Any]] | None
        project_browser_path: str
        selected_project_entry_rel: str | None
        hud_theme: str
        hud_effects: str
        layout_mode: str
        show_splash: bool
        loading_views: set[str]
        status_message: str
        last_refresh_label: str | None
        selected_todo_line_index: int | None

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="chrome"):
                with Vertical(id="nav-rail"):
                    yield Static("", id="brand")
                    yield ListView(
                        ListItem(Label("Overview"), id="nav-overview"),
                        ListItem(Label("Agents"), id="nav-agents"),
                        ListItem(Label("Sessions"), id="nav-sessions"),
                        ListItem(Label("Gateway"), id="nav-gateway"),
                        ListItem(Label("Cron"), id="nav-cron"),
                        ListItem(Label("Projects"), id="nav-projects"),
                        ListItem(Label("Notes/Todos"), id="nav-notes"),
                        ListItem(Label("Memory"), id="nav-memory"),
                        ListItem(Label("Reports"), id="nav-reports"),
                        ListItem(Label("Token Spend"), id="nav-token-spend"),
                        ListItem(Label("Maintenance"), id="nav-maintenance"),
                        id="nav",
                    )
                with Vertical(id="workspace"):
                    with Horizontal(id="top-nav"):
                        yield Button("Overview", id="topnav-nav-overview")
                        yield Button("Agents", id="topnav-nav-agents")
                        yield Button("Sessions", id="topnav-nav-sessions")
                        yield Button("Gateway", id="topnav-nav-gateway")
                        yield Button("Cron", id="topnav-nav-cron")
                        yield Button("Projects", id="topnav-nav-projects")
                        yield Button("Notes", id="topnav-nav-notes")
                        yield Button("Memory", id="topnav-nav-memory")
                        yield Button("Reports", id="topnav-nav-reports")
                        yield Button("Spend", id="topnav-nav-token-spend")
                        yield Button("Maint", id="topnav-nav-maintenance")
                    yield Static("", id="hero")
                    with Container(id="content-shell"):
                        with Container(id="main-pane"):
                            yield Static("", id="main-content")
                        with Container(id="detail-pane"):
                            yield Static("", id="detail-content")
            yield Static("", id="status-bar")
            yield Footer()

        def on_mount(self) -> None:
            self.profiles = []
            self.sessions = []
            self.projects = []
            self.briefs = []
            self.notes_lines = []
            self.selected_agent_name = None
            self.selected_session_id = None
            self.selected_project_id = None
            self.maintenance_cache = None
            self.memory_cache = None
            self.reports_cache = None
            self.overview_cache = None
            self.cron_cache = None
            self.gateway_cache = {}
            self.profile_content_cache = {}
            self.session_query = ""
            self.session_filter = "all"
            self.report_window = "24h"
            self.session_search_results = None
            self.project_browser_path = "."
            self.selected_project_entry_rel = None
            self.hud_theme = self._load_saved_theme()
            self.hud_effects = self._load_saved_effects()
            self.layout_mode = self._load_saved_layout()
            self.show_splash = True
            self.loading_views = set()
            self.status_message = "Booting Hermes Agent HUD..."
            self.last_refresh_label = None
            self.selected_todo_line_index = None
            self.query_one(ListView).index = 0
            self._apply_theme()
            self._apply_layout()
            self._set_status("Booting Hermes Agent HUD...")
            self._render_current()
            self.set_timer(3.2, self._finish_boot)

        def _finish_boot(self) -> None:
            self.show_splash = False
            self._queue_load("shell", force=True, status="Loading Hermes state...")
            self._queue_load("overview", force=True)
            self._render_current()

        def _theme(self) -> dict[str, str]:
            return THEMES[getattr(self, "hud_theme", "matrix")]

        def _effects(self) -> dict[str, Any]:
            return EFFECT_MODES[getattr(self, "hud_effects", "full")]

        def _apply_theme(self) -> None:
            theme = self._theme()
            effects = self._effects()
            self.screen.styles.background = theme["screen_bg"]
            self.query_one(Header).styles.background = theme["header_bg"]
            self.query_one(Header).styles.color = theme["accent"]
            self.query_one(Footer).styles.background = theme["status_bg"]
            self.query_one(Footer).styles.color = theme["muted"]
            nav_bg = theme["screen_bg"] if effects["flatten"] else theme["nav_bg"]
            workspace_bg = theme["screen_bg"] if effects["flatten"] else theme["workspace_bg"]
            main_bg = theme["screen_bg"] if effects["flatten"] else theme["main_bg"]
            detail_bg = theme["screen_bg"] if effects["flatten"] else theme["detail_bg"]
            header_bg = theme["screen_bg"] if effects["flatten"] else theme["header_bg"]
            status_bg = theme["screen_bg"] if effects["flatten"] else theme["status_bg"]
            self.query_one("#nav-rail", Vertical).styles.background = nav_bg
            self.query_one("#workspace", Vertical).styles.background = workspace_bg
            self.query_one("#hero", Static).styles.background = theme["header_bg"]
            self.query_one("#hero", Static).styles.border_bottom = ("heavy", theme["border"])
            self.query_one("#main-pane", Container).styles.background = main_bg
            self.query_one("#main-pane", Container).styles.border_right = ("heavy", theme["border"])
            self.query_one("#detail-pane", Container).styles.background = detail_bg
            self.query_one("#hero", Static).styles.background = header_bg
            self.query_one("#status-bar", Static).styles.background = status_bg
            brand = self.query_one("#brand", Static)
            brand.styles.color = theme["accent"]
            brand.styles.background = nav_bg
            brand.update(self._brand_renderable())
            top_nav = self.query_one("#top-nav", Horizontal)
            top_nav.styles.background = nav_bg
            for child in top_nav.children:
                if isinstance(child, Button):
                    child.styles.background = theme["nav_bg"]
                    child.styles.color = theme["muted"]
                    child.styles.border = ("round", theme["border"])
            nav = self.query_one(ListView)
            nav.styles.background = nav_bg
            for item in nav.children:
                item.styles.color = theme["muted"]
            self.refresh()

        def _saved_layout_label(self) -> str:
            effective = self._effective_layout_mode()
            layout_mode = getattr(self, "layout_mode", "wide")
            if effective != layout_mode:
                return f"{layout_mode} (auto->{effective})"
            return effective

        def _effective_layout_mode(self) -> str:
            try:
                width = int(self.size.width)
            except Exception:
                width = 160
            if width < 145:
                return "stacked"
            return getattr(self, "layout_mode", "wide")

        def _apply_layout(self) -> None:
            effective = self._effective_layout_mode()
            chrome = self.query_one("#chrome", Horizontal)
            nav_rail = self.query_one("#nav-rail", Vertical)
            workspace = self.query_one("#workspace", Vertical)
            content = self.query_one("#content-shell", Container)
            main = self.query_one("#main-pane", Container)
            detail = self.query_one("#detail-pane", Container)
            theme = self._theme()
            if effective == "stacked":
                chrome.styles.layout = "vertical"
                nav_rail.styles.width = "1fr"
                nav_rail.styles.height = 4
                nav_rail.styles.border_right = None
                nav_rail.styles.border_bottom = ("heavy", theme["border"])
                self.query_one("#top-nav", Horizontal).styles.display = "block"
                self.query_one("#nav", ListView).styles.display = "none"
                workspace.styles.width = "1fr"
                workspace.styles.height = "1fr"
                content.styles.layout = "vertical"
                main.styles.width = None
                detail.styles.width = None
                main.styles.height = "2fr"
                detail.styles.height = "1fr"
                main.styles.border_right = None
                main.styles.border_bottom = ("heavy", theme["border"])
            else:
                chrome.styles.layout = "horizontal"
                nav_rail.styles.width = 26
                nav_rail.styles.height = "1fr"
                nav_rail.styles.border_bottom = None
                nav_rail.styles.border_right = ("heavy", theme["border"])
                self.query_one("#top-nav", Horizontal).styles.display = "none"
                self.query_one("#nav", ListView).styles.display = "block"
                workspace.styles.width = "1fr"
                workspace.styles.height = "1fr"
                content.styles.layout = "horizontal"
                main.styles.width = "3fr"
                detail.styles.width = "2fr"
                main.styles.height = None
                detail.styles.height = None
                main.styles.border_bottom = None
                main.styles.border_right = ("heavy", theme["border"])
            detail.styles.border_top = None
            self.refresh()

        def _load_saved_layout(self) -> str:
            try:
                saved = LAYOUT_STATE_PATH.read_text(encoding="utf-8").strip()
                if saved in {"wide", "stacked"}:
                    return saved
            except OSError:
                pass
            return "wide"

        def _save_layout(self) -> None:
            try:
                LAYOUT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
                LAYOUT_STATE_PATH.write_text(self.layout_mode, encoding="utf-8")
            except OSError:
                pass

        def on_resize(self, event) -> None:
            self._apply_layout()
            self._render_status_bar()

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            self._ensure_view_data(self._current_view())
            self._render_current()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            button_id = event.button.id or ""
            if button_id.startswith("topnav-"):
                target = button_id.removeprefix("topnav-")
                nav = self.query_one(ListView)
                ids = [getattr(item, "id", "") for item in nav.children]
                if target in ids:
                    nav.index = ids.index(target)
                    self._ensure_view_data(target)
                    self._render_current()
                    self._set_status(f"Active view: {target.removeprefix('nav-')}")

        def action_refresh(self) -> None:
            self._queue_load("shell", force=True, status="Refreshing Hermes state...")
            current = self._current_view()
            if current == "nav-overview":
                self._queue_load("overview", force=True)
            elif current == "nav-agents":
                profile_name = self.selected_agent_name
                if profile_name:
                    self._queue_load(f"profile:{profile_name}", force=True)
            elif current == "nav-gateway":
                self._queue_load(f"gateway:{self._gateway_profile_name()}", force=True)
            elif current == "nav-cron":
                self._queue_load("cron", force=True)
            elif current == "nav-maintenance":
                self._queue_load("maintenance", force=True)
            elif current == "nav-memory":
                self._queue_load("memory", force=True)
            elif current == "nav-reports":
                self._queue_load("reports", force=True)
            self._render_current()

        def action_show_help(self) -> None:
            self.push_screen(HelpScreen())

        async def action_cycle_layout(self) -> None:
            self.layout_mode = "stacked" if self.layout_mode == "wide" else "wide"
            self._save_layout()
            self._apply_layout()
            self._render_current()
            self._set_status(f"Layout: {self._saved_layout_label()}")

        async def action_cycle_theme(self) -> None:
            names = list(THEMES.keys())
            idx = names.index(self.hud_theme)
            self.hud_theme = names[(idx + 1) % len(names)]
            self._save_theme()
            self._apply_theme()
            self._apply_layout()
            self._render_current()
            self._set_status(f"Theme: {THEMES[self.hud_theme]['name']}")

        async def action_cycle_effects(self) -> None:
            names = list(EFFECT_MODES.keys())
            idx = names.index(self.hud_effects) if self.hud_effects in names else 0
            self.hud_effects = names[(idx + 1) % len(names)]
            self._save_effects()
            self._apply_theme()
            self._apply_layout()
            self._render_current()
            self._set_status(f"Effects: {self._effects()['name']}")

        async def action_search_sessions(self) -> None:
            if self._current_view() != "nav-sessions":
                self._set_status("Open Sessions first.")
                return
            query = await self._prompt("Session search", placeholder="title or content", value=self.session_query)
            self.session_query = query or ""
            self.session_search_results = None
            if self.session_query:
                try:
                    self.session_search_results = client.search_sessions(self.session_query, content=True, depth=24)
                except HermesAPIError as exc:
                    self._set_status(str(exc))
                    return
            visible = self._visible_sessions()
            if visible:
                self.selected_session_id = str(visible[0].get("session_id") or self.selected_session_id or "")
            self._render_current()
            if self.session_query:
                self._set_status(f"Session search: {len(visible)} matches")
            else:
                self._set_status("Session search: off")

        def action_cycle_session_filter(self) -> None:
            if self._current_view() != "nav-sessions":
                self._set_status("Open Sessions first.")
                return
            order = ["all", "open", "pinned", "archived", "recent"]
            idx = order.index(self.session_filter) if self.session_filter in order else 0
            self.session_filter = order[(idx + 1) % len(order)]
            visible = self._visible_sessions()
            if visible:
                self.selected_session_id = str(visible[0].get("session_id") or self.selected_session_id or "")
            self._render_current()
            self._set_status(f"Session filter: {self.session_filter}")

        def action_cycle_time_window(self) -> None:
            if self._current_view() not in {"nav-reports", "nav-token-spend"}:
                self._set_status("Open Reports or Token Spend first.")
                return
            order = ["24h", "7d", "30d", "all"]
            idx = order.index(self.report_window) if self.report_window in order else 0
            self.report_window = order[(idx + 1) % len(order)]
            self._render_current()
            self._set_status(f"Time window: {self.report_window}")

        def action_export_session(self) -> None:
            if self._current_view() != "nav-sessions":
                self._set_status("Open Sessions first.")
                return
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            try:
                target = client.export_session(str(session["session_id"]))
                self._set_status(f"Exported session to {target}")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def action_next_item(self) -> None:
            view = self._current_view()
            if view in {"nav-agents", "nav-gateway"}:
                self._cycle_agent(1)
            elif view == "nav-projects":
                self._cycle_project(1)
            elif view == "nav-sessions":
                self._cycle_session(1)
            elif view == "nav-notes":
                self._cycle_todo(1)

        def action_next_section(self) -> None:
            self._select_nav_offset(1)

        def action_prev_section(self) -> None:
            self._select_nav_offset(-1)

        def action_prev_item(self) -> None:
            view = self._current_view()
            if view in {"nav-agents", "nav-gateway"}:
                self._cycle_agent(-1)
            elif view == "nav-projects":
                self._cycle_project(-1)
            elif view == "nav-sessions":
                self._cycle_session(-1)
            elif view == "nav-notes":
                self._cycle_todo(-1)

        def _select_nav_offset(self, direction: int) -> None:
            nav = self.query_one(ListView)
            count = len(nav.children)
            if count == 0:
                return
            current = nav.index or 0
            nav.index = (current + direction) % count
            self._ensure_view_data(self._current_view())
            self._render_current()

        def action_activate_agent(self) -> None:
            if self._current_view() != "nav-agents":
                self._set_status("Open Agents first.")
                return
            profile = self._selected_profile()
            if not profile:
                self._set_status("No agent selected.")
                return
            try:
                client.switch_profile(profile["name"])
                self._refresh_side_state()
                self._render_current()
                self._set_status(f"Switched active profile to {profile['name']}")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def action_preview(self) -> None:
            view = self._current_view()
            if view == "nav-agents":
                self._preview_profile_file("config")
            elif view == "nav-projects":
                self._preview_project_file()
            elif view == "nav-memory":
                self._preview_memory_user()
            elif view == "nav-reports":
                self._preview_reports_models()
            elif view == "nav-token-spend":
                self._preview_reports_models()
            else:
                self._set_status("No preview action for this pane.")

        async def action_preview_alt(self) -> None:
            view = self._current_view()
            if view == "nav-agents":
                self._preview_profile_file("soul")
            elif view == "nav-projects":
                await self._browse_project_path()
            else:
                self._set_status("No alternate preview action for this pane.")

        def action_back_up(self) -> None:
            if self._current_view() != "nav-projects":
                self._set_status("Open Projects first.")
                return
            self._project_up()

        def action_gateway_start(self) -> None:
            self._gateway_action("start")

        def action_gateway_stop(self) -> None:
            self._gateway_action("stop")

        def action_gateway_restart(self) -> None:
            self._gateway_action("restart")

        def action_gateway_logs(self) -> None:
            profile_name = self._gateway_profile_name()
            try:
                payload = client.gateway_logs(profile=profile_name, lines=120)
                logs = payload.get("logs") or "No gateway logs returned."
                self.query_one("#detail-content", Static).update(
                    Panel(Syntax(logs, "log", theme="ansi_dark", line_numbers=False), title=f"Gateway Logs · {profile_name}")
                )
                self._set_status(f"Loaded gateway logs for {profile_name}")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def action_maintenance_check(self) -> None:
            if self._current_view() == "nav-maintenance":
                self._load_maintenance(force=True)
                self._render_current()
                self._set_status("Update status refreshed")
            elif self._current_view() in {"nav-memory", "nav-reports"}:
                self._load_memory_reports(force=True)
                self._render_current()
                self._set_status("Memory/reporting refreshed")
            else:
                self._set_status("Open Maintenance or Memory / Reports first.")

        def action_maintenance_apply_webui(self) -> None:
            self._maintenance_apply("webui")

        def action_maintenance_apply_agent(self) -> None:
            self._maintenance_apply("agent")

        def action_clear_or_cleanup(self) -> None:
            if self._current_view() == "nav-sessions":
                self._clear_selected_session()
            elif self._current_view() == "nav-maintenance":
                self._cleanup_sessions(False)
            else:
                self._set_status("No clear action for this pane.")

        def action_cleanup_zero(self) -> None:
            if self._current_view() != "nav-maintenance":
                self._set_status("Open Maintenance first.")
                return
            self._cleanup_sessions(True)

        async def action_context_add(self) -> None:
            view = self._current_view()
            if view == "nav-cron":
                await self._cron_add()
            elif view == "nav-projects":
                await self._kanban_add()
            elif view == "nav-notes":
                await self._todo_add()
            else:
                self._set_status("No add action for this pane.")

        async def action_context_edit_or_run(self) -> None:
            view = self._current_view()
            if view == "nav-cron":
                await self._cron_run()
            elif view == "nav-notes":
                await self._notes_edit()
            elif view == "nav-sessions":
                await self._rename_selected_session()
            elif view == "nav-projects":
                await self._edit_project_brief()
            elif view == "nav-memory":
                await self._edit_memory()
            else:
                self._set_status("No edit action for this pane.")

        async def action_toggle_flag(self) -> None:
            view = self._current_view()
            if view == "nav-cron":
                await self._cron_toggle()
            elif view == "nav-sessions":
                self._toggle_session_pin()
            elif view == "nav-projects":
                self._cycle_project_entry(1)
            elif view == "nav-notes":
                self._toggle_todo_done()
            else:
                self._set_status("No toggle action for this pane.")

        async def action_context_delete(self) -> None:
            view = self._current_view()
            if view == "nav-cron":
                await self._cron_delete()
            elif view == "nav-sessions":
                self._delete_selected_session()
            elif view == "nav-notes":
                self._delete_selected_todo()
            else:
                self._set_status("No delete action for this pane.")

        async def action_move_context(self) -> None:
            view = self._current_view()
            if view == "nav-projects":
                await self._kanban_move()
            elif view == "nav-sessions":
                self._toggle_session_archive()
            elif view == "nav-notes":
                await self._move_selected_todo()
            else:
                self._set_status("No move action for this pane.")

        def _current_view(self) -> str:
            nav = self.query_one(ListView)
            return nav.highlighted_child.id if nav.highlighted_child else "nav-overview"

        def _set_status(self, message: str) -> None:
            self.status_message = message
            self._render_status_bar()

        def _render_status_bar(self) -> None:
            theme = self._theme()
            status = Text()
            status.append(getattr(self, "status_message", None) or "Ready", style=theme["text"])
            status.append("  ")
            status.append(f"theme: {theme['name']}", style=theme["accent_soft"])
            status.append("  ")
            status.append(f"fx: {self._effects()['name']}", style=theme["accent_soft"])
            status.append("  ")
            status.append(f"layout: {self._saved_layout_label()}", style=theme["info"])
            if getattr(self, "loading_views", None):
                status.append("  ")
                status.append(f"loading: {', '.join(sorted(self.loading_views))}", style=theme["warn"])
            if getattr(self, "last_refresh_label", None):
                status.append("  ")
                status.append(f"last refresh: {self.last_refresh_label}", style=theme["muted"])
            self.query_one("#status-bar", Static).update(status)

        async def _prompt(self, label: str, placeholder: str = "", value: str = "") -> str | None:
            return await self.push_screen_wait(PromptScreen(label, placeholder=placeholder, value=value))

        async def _edit_text(self, title: str, content: str) -> str | None:
            return await self.push_screen_wait(TextEditorScreen(title, content))

        def _refresh_side_state(self) -> None:
            try:
                self.profiles = [
                    {
                        "name": profile.name,
                        "model": profile.model,
                        "provider": profile.provider,
                        "is_active": profile.is_active,
                        "is_default": profile.is_default,
                        "gateway_running": profile.gateway_running,
                        "path": profile.path,
                    }
                    for profile in client.list_profiles()
                ]
            except HermesAPIError:
                self.profiles = []
            if self.profiles:
                active = next((profile["name"] for profile in self.profiles if profile.get("is_active")), None)
                self.selected_agent_name = self.selected_agent_name or active or self.profiles[0]["name"]
            else:
                self.selected_agent_name = None

            try:
                self.sessions = client.get("/api/sessions").get("sessions", [])
            except HermesAPIError:
                self.sessions = []
            if self.sessions:
                ids = [str(session.get("session_id") or "") for session in self.sessions if session.get("session_id")]
                self.selected_session_id = self.selected_session_id if self.selected_session_id in ids else (ids[0] if ids else None)
            else:
                self.selected_session_id = None

            try:
                self.projects = client.list_projects()
            except HermesAPIError:
                self.projects = []
            if self.projects:
                ids = [self._project_id(project) for project in self.projects]
                self.selected_project_id = self.selected_project_id if self.selected_project_id in ids else ids[0]
            else:
                self.selected_project_id = None

            try:
                self.briefs = client.list_briefs()
            except HermesAPIError:
                self.briefs = []

            try:
                self.notes_lines = client.get_notes()
            except HermesAPIError:
                self.notes_lines = []

        def _snapshot_side_state(self) -> dict[str, Any]:
            profiles = [
                {
                    "name": profile.name,
                    "model": profile.model,
                    "provider": profile.provider,
                    "is_active": profile.is_active,
                    "is_default": profile.is_default,
                    "gateway_running": profile.gateway_running,
                    "path": profile.path,
                }
                for profile in client.list_profiles()
            ]
            sessions = client.get("/api/sessions").get("sessions", [])
            projects = client.list_projects()
            briefs = client.list_briefs()
            notes_lines = client.get_notes()
            return {
                "profiles": profiles,
                "sessions": sessions,
                "projects": projects,
                "briefs": briefs,
                "notes_lines": notes_lines,
            }

        def _apply_side_state(self, payload: dict[str, Any]) -> None:
            self.profiles = payload.get("profiles", [])
            self.sessions = payload.get("sessions", [])
            self.projects = payload.get("projects", [])
            self.briefs = payload.get("briefs", [])
            self.notes_lines = payload.get("notes_lines", [])

            if self.profiles:
                active = next((profile["name"] for profile in self.profiles if profile.get("is_active")), None)
                self.selected_agent_name = self.selected_agent_name or active or self.profiles[0]["name"]
            else:
                self.selected_agent_name = None

            if self.sessions:
                ids = [str(session.get("session_id") or "") for session in self.sessions if session.get("session_id")]
                self.selected_session_id = self.selected_session_id if self.selected_session_id in ids else (ids[0] if ids else None)
            else:
                self.selected_session_id = None

            if self.projects:
                ids = [self._project_id(project) for project in self.projects]
                self.selected_project_id = self.selected_project_id if self.selected_project_id in ids else ids[0]
            else:
                self.selected_project_id = None

        def _queue_load(self, key: str, force: bool = False, status: str | None = None) -> None:
            if key in self.loading_views:
                return
            if status:
                self._set_status(status)
            self.loading_views.add(key)
            self._render_status_bar()
            self.run_worker(self._load_data(key, force=force), group="hud-load", exclusive=False)

        async def _load_data(self, key: str, force: bool = False) -> None:
            try:
                payload = await asyncio.to_thread(self._fetch_data, key, force)
                self._apply_loaded_data(key, payload)
            except HermesAPIError as exc:
                self._load_failed(key, str(exc))
            except Exception as exc:
                self._load_failed(key, f"Unexpected error: {exc}")

        def _load_failed(self, key: str, message: str) -> None:
            self.loading_views.discard(key)
            self._set_status(message)
            self._render_current()

        def _apply_loaded_data(self, key: str, payload: Any) -> None:
            self.loading_views.discard(key)
            if key == "shell":
                self._apply_side_state(payload)
            elif key == "overview":
                self.overview_cache = payload
            elif key.startswith("profile:"):
                self.profile_content_cache[key.split(":", 1)[1]] = payload
            elif key.startswith("gateway:"):
                self.gateway_cache[key.split(":", 1)[1]] = payload
            elif key == "cron":
                self.cron_cache = payload
            elif key == "maintenance":
                self.maintenance_cache = payload
            elif key == "memory":
                self.memory_cache = payload
            elif key == "reports":
                self.reports_cache = payload
            self.last_refresh_label = datetime.now().strftime("%H:%M:%S")
            self._render_current()
            self._render_status_bar()

        def _fetch_data(self, key: str, force: bool = False) -> Any:
            if key == "shell":
                return self._snapshot_side_state()
            if key == "overview":
                return {
                    "resources": client.get_resources(),
                    "alerts": client.list_alerts(limit=8),
                }
            if key.startswith("profile:"):
                return client.get_profile_content(key.split(":", 1)[1])
            if key.startswith("gateway:"):
                return client.gateway_status(profile=key.split(":", 1)[1])
            if key == "cron":
                return client.list_cron_jobs()
            if key == "maintenance":
                return client.check_updates(force=force)
            if key == "memory":
                return client.get_memory()
            if key == "reports":
                return {
                    "resources": client.get_resources(),
                    "costs": client.get_costs(),
                    "dialogs": client.get_dialogs(),
                    "sessions": self.sessions or client.get("/api/sessions").get("sessions", []),
                }
            return None

        def _ensure_view_data(self, view_id: str) -> None:
            if view_id == "nav-overview" and self.overview_cache is None:
                self._queue_load("overview")
            elif view_id == "nav-agents":
                profile_name = self.selected_agent_name
                if profile_name and profile_name not in self.profile_content_cache:
                    self._queue_load(f"profile:{profile_name}")
            elif view_id == "nav-gateway":
                profile_name = self._gateway_profile_name()
                if profile_name not in self.gateway_cache:
                    self._queue_load(f"gateway:{profile_name}")
            elif view_id == "nav-cron" and self.cron_cache is None:
                self._queue_load("cron")
            elif view_id == "nav-maintenance" and self.maintenance_cache is None:
                self._queue_load("maintenance")
            elif view_id == "nav-memory" and self.memory_cache is None:
                self._queue_load("memory")
            elif view_id == "nav-reports" and self.reports_cache is None:
                self._queue_load("reports")

        def _selected_profile(self) -> dict[str, Any] | None:
            return next((profile for profile in self.profiles if profile.get("name") == self.selected_agent_name), None)

        def _selected_session(self) -> dict[str, Any] | None:
            return next((session for session in self.sessions if str(session.get("session_id") or "") == self.selected_session_id), None)

        def _selected_project(self) -> dict[str, Any] | None:
            return next((project for project in self.projects if self._project_id(project) == self.selected_project_id), None)

        def _project_id(self, project: dict[str, Any]) -> str:
            return str(project.get("project_id") or project.get("id") or project.get("name") or "")

        def _todo_items(self) -> list[dict[str, Any]]:
            items: list[dict[str, Any]] = []
            for idx, line in enumerate(self.notes_lines):
                stripped = line.strip()
                if stripped.startswith("- [") or stripped.startswith("* ["):
                    items.append(
                        {
                            "line_index": idx,
                            "text": stripped,
                            "done": "[x]" in stripped.lower(),
                        }
                    )
            return items

        def _selected_todo(self) -> dict[str, Any] | None:
            items = self._todo_items()
            if not items:
                self.selected_todo_line_index = None
                return None
            if self.selected_todo_line_index is not None:
                match = next((item for item in items if item["line_index"] == self.selected_todo_line_index), None)
                if match:
                    return match
            self.selected_todo_line_index = items[0]["line_index"]
            return items[0]

        def _cycle_agent(self, direction: int) -> None:
            if not self.profiles:
                self._set_status("No profiles available")
                return
            names = [profile["name"] for profile in self.profiles]
            current = names.index(self.selected_agent_name) if self.selected_agent_name in names else 0
            self.selected_agent_name = names[(current + direction) % len(names)]
            if self.selected_agent_name and self.selected_agent_name not in self.profile_content_cache:
                self._queue_load(f"profile:{self.selected_agent_name}")
            self._render_current()

        def _cycle_project(self, direction: int) -> None:
            if not self.projects:
                self._set_status("No projects available")
                return
            ids = [self._project_id(project) for project in self.projects]
            current = ids.index(self.selected_project_id) if self.selected_project_id in ids else 0
            self.selected_project_id = ids[(current + direction) % len(ids)]
            self.project_browser_path = "."
            self.selected_project_entry_rel = None
            self._render_current()

        def _cycle_session(self, direction: int) -> None:
            visible_sessions = self._visible_sessions()
            if not visible_sessions:
                self._set_status("No sessions available")
                return
            ids = [str(session.get("session_id") or "") for session in visible_sessions if session.get("session_id")]
            current = ids.index(self.selected_session_id) if self.selected_session_id in ids else 0
            self.selected_session_id = ids[(current + direction) % len(ids)]
            self._render_current()

        def _cycle_todo(self, direction: int) -> None:
            items = self._todo_items()
            if not items:
                self._set_status("No todos available")
                return
            indices = [item["line_index"] for item in items]
            current = indices.index(self.selected_todo_line_index) if self.selected_todo_line_index in indices else 0
            self.selected_todo_line_index = indices[(current + direction) % len(indices)]
            self._render_current()

        def _preview_profile_file(self, kind: str) -> None:
            profile = self._selected_profile()
            if not profile:
                self._set_status("No profile selected")
                return
            try:
                content = self.profile_content_cache.get(profile["name"])
                if not content:
                    self._queue_load(f"profile:{profile['name']}", status=f"Loading {kind} for {profile['name']}...")
                    self._set_status(f"Loading {kind} for {profile['name']}...")
                    return
                key = "config" if kind == "config" else "soul"
                path_key = "config_path" if kind == "config" else "soul_path"
                body = content.get(key) or f"No {key} content found."
                title = content.get(path_key) or f"{profile['name']} {key}"
                language = "yaml" if kind == "config" else "markdown"
                self.query_one("#detail-content", Static).update(
                    Panel(Syntax(body, language, theme="ansi_dark", line_numbers=True), title=title)
                )
                self._set_status(f"Loaded {key} for {profile['name']}")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _gateway_profile_name(self) -> str:
            return self.selected_agent_name or self._active_profile_name() or "default"

        def _gateway_action(self, action: str) -> None:
            if self._current_view() not in {"nav-gateway", "nav-agents"}:
                self._set_status("Open Gateway or Agents first.")
                return
            profile_name = self._gateway_profile_name()
            try:
                payload = client.gateway_action(action, profile=profile_name)
                self._set_status(payload.get("message") or f"Gateway {action} requested for {profile_name}")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _load_maintenance(self, force: bool = False) -> None:
            if self.maintenance_cache is not None and not force:
                return
            self._queue_load("maintenance", force=force)

        def _maintenance_apply(self, target: str) -> None:
            if self._current_view() != "nav-maintenance":
                self._set_status("Open Maintenance first.")
                return
            try:
                payload = client.apply_update(target)
                self._set_status(payload.get("message") or f"Update requested for {target}")
                self.maintenance_cache = None
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _cleanup_sessions(self, zero_only: bool) -> None:
            try:
                payload = client.cleanup_sessions(zero_only=zero_only)
                self._set_status(
                    f"Cleaned {payload.get('cleaned', 0)} {'zero-message ' if zero_only else ''}sessions"
                )
                self._refresh_side_state()
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _cron_add(self) -> None:
            prompt = await self._prompt("Cron prompt", placeholder="What should Hermes do?")
            if not prompt:
                self._set_status("Cancelled")
                return
            schedule = await self._prompt("Cron schedule", placeholder="0 * * * *")
            if not schedule:
                self._set_status("Cancelled")
                return
            name = await self._prompt("Cron name", placeholder="Optional")
            try:
                client.create_cron_job(prompt=prompt, schedule=schedule, name=name or None)
                self._set_status("Cron job created")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _cron_run(self) -> None:
            job_id = await self._prompt("Cron job id")
            if not job_id:
                self._set_status("Cancelled")
                return
            try:
                payload = client.run_cron_job(job_id)
                self._set_status(payload.get("message") or f"Cron job {job_id} run requested")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _cron_toggle(self) -> None:
            job_id = await self._prompt("Cron job id")
            if not job_id:
                self._set_status("Cancelled")
                return
            try:
                jobs = client.list_cron_jobs()
                match = next((job for job in jobs if str(job.get("id") or "") == job_id), None)
                if not match:
                    self._set_status(f"Cron job {job_id} not found")
                    return
                if match.get("enabled") is False:
                    client.resume_cron_job(job_id)
                    self._set_status(f"Cron job {job_id} resumed")
                else:
                    client.pause_cron_job(job_id)
                    self._set_status(f"Cron job {job_id} paused")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _cron_delete(self) -> None:
            job_id = await self._prompt("Cron job id")
            if not job_id:
                self._set_status("Cancelled")
                return
            try:
                client.delete_cron_job(job_id)
                self._set_status(f"Cron job {job_id} deleted")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _toggle_session_pin(self) -> None:
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            try:
                client.pin_session(str(session["session_id"]), not bool(session.get("pinned")))
                self._refresh_side_state()
                self._render_current()
                self._set_status(f"{'Pinned' if not session.get('pinned') else 'Unpinned'} session")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _toggle_session_archive(self) -> None:
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            try:
                client.archive_session(str(session["session_id"]), not bool(session.get("archived")))
                self._refresh_side_state()
                self._render_current()
                self._set_status(f"{'Archived' if not session.get('archived') else 'Unarchived'} session")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _delete_selected_session(self) -> None:
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            try:
                client.delete_session(str(session["session_id"]))
                self._refresh_side_state()
                self._render_current()
                self._set_status("Session deleted")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _clear_selected_session(self) -> None:
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            try:
                client.clear_session(str(session["session_id"]))
                self._refresh_side_state()
                self._render_current()
                self._set_status("Session cleared")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _rename_selected_session(self) -> None:
            session = self._selected_session()
            if not session or not session.get("session_id"):
                self._set_status("No session selected")
                return
            title = await self._prompt("Session title", value=str(session.get("title") or "Untitled"))
            if not title:
                self._set_status("Cancelled")
                return
            try:
                client.rename_session(str(session["session_id"]), title)
                self._refresh_side_state()
                self._render_current()
                self._set_status("Session renamed")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _match_briefs_for_project(self, project: dict[str, Any] | None) -> list[dict[str, Any]]:
            if not project:
                return []
            needle_name = str(project.get("name") or "").lower()
            needle_path = str(project.get("path") or "").lower()
            matches: list[dict[str, Any]] = []
            for brief in self.briefs:
                hay = " ".join([
                    str(brief.get("title") or ""),
                    str(brief.get("path") or ""),
                    str(brief.get("summary") or ""),
                ]).lower()
                if needle_name and needle_name in hay:
                    matches.append(brief)
                    continue
                if needle_path and needle_path in hay:
                    matches.append(brief)
            return matches[:6]

        def _project_root(self) -> Path | None:
            project = self._selected_project()
            if not project or not project.get("path"):
                return None
            try:
                return Path(str(project["path"])).expanduser().resolve()
            except Exception:
                return None

        def _project_entries(self) -> list[dict[str, Any]]:
            root = self._project_root()
            if not root or not root.exists() or not root.is_dir():
                return []
            try:
                target = (root / self.project_browser_path).resolve()
                if root not in target.parents and target != root:
                    return []
                if not target.exists() or not target.is_dir():
                    return []
                entries = []
                for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:25]:
                    entries.append(
                        {
                            "name": entry.name,
                            "is_dir": entry.is_dir(),
                            "path": str(entry),
                            "rel": str(entry.relative_to(root)),
                        }
                    )
                return entries
            except Exception:
                return []

        def _selected_project_entry(self) -> dict[str, Any] | None:
            entries = self._project_entries()
            if not entries:
                return None
            if self.selected_project_entry_rel:
                match = next((entry for entry in entries if entry["rel"] == self.selected_project_entry_rel), None)
                if match:
                    return match
            self.selected_project_entry_rel = entries[0]["rel"]
            return entries[0]

        def _cycle_project_entry(self, direction: int) -> None:
            if self._current_view() != "nav-projects":
                self._set_status("Open Projects first.")
                return
            entries = self._project_entries()
            if not entries:
                self._set_status("No project files in this path")
                return
            rels = [entry["rel"] for entry in entries]
            current = rels.index(self.selected_project_entry_rel) if self.selected_project_entry_rel in rels else 0
            self.selected_project_entry_rel = rels[(current + direction) % len(rels)]
            self._render_current()
            entry = self._selected_project_entry()
            if entry:
                self._set_status(f"Selected {entry['rel']}")

        def _project_up(self) -> None:
            current = Path(self.project_browser_path)
            if str(current) in {".", ""}:
                self._set_status("Already at project root")
                return
            parent = str(current.parent)
            self.project_browser_path = "." if parent in {"", "."} else parent
            self.selected_project_entry_rel = None
            self._render_current()
            self._set_status(f"Browsing {self.project_browser_path}")

        def _preview_project_file(self) -> None:
            root = self._project_root()
            if not root:
                self._set_status("No project path available")
                return
            target = self._selected_project_entry()
            if not target:
                matches = self._match_briefs_for_project(self._selected_project())
                if matches:
                    self._preview_project_brief()
                    return
                self._set_status("No previewable text file in current project path")
                return
            if target["is_dir"]:
                rel = target["rel"]
                self.project_browser_path = rel or "."
                self.selected_project_entry_rel = None
                self._render_current()
                self._set_status(f"Entered {rel}")
                return
            if Path(target["path"]).suffix.lower() not in {".md", ".markdown", ".txt", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"}:
                self._set_status("Selected file is not previewable text")
                return
            try:
                payload = client.get_text_file(target["path"])
                content = str(payload.get("content") or "")
                self.query_one("#detail-content", Static).update(
                    Panel(Markdown(content) if Path(target["path"]).suffix.lower() in {".md", ".markdown"} else Syntax(content, "text", theme="ansi_dark"), title=str(payload.get("path") or target["rel"]))
                )
                self._set_status(f"Previewing {target['rel']}")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _browse_project_path(self) -> None:
            root = self._project_root()
            if not root:
                self._set_status("No project path available")
                return
            value = await self._prompt("Project browser path", placeholder="., src, docs", value=self.project_browser_path)
            if value is None:
                self._set_status("Cancelled")
                return
            candidate = value or "."
            target = (root / candidate).resolve()
            if root not in target.parents and target != root:
                self._set_status("Path outside selected project")
                return
            if not target.exists() or not target.is_dir():
                self._set_status("Directory not found")
                return
            self.project_browser_path = candidate
            self.selected_project_entry_rel = None
            self._render_current()
            self._set_status(f"Browsing {candidate}")

        def _preview_reports_models(self) -> None:
            self._load_memory_reports(force=False)
            reports = self.reports_cache or {}
            costs = reports.get("costs") or {}
            rows = list((costs.get("by_model") or [])[:8])
            table = Table(expand=True)
            table.add_column("Model", style="#d7f6df")
            table.add_column("Sessions", justify="right", style="#8ab2ff")
            table.add_column("Cost", justify="right", style="#e0c36a")
            if rows:
                for row in rows:
                    table.add_row(str(row.get("model") or "unknown"), str(row.get("sessions") or 0), f"${float(row.get('estimated_cost') or 0):.3f}")
            else:
                table.add_row("No model cost data", "-", "-")
            self.query_one("#detail-content", Static).update(Panel(table, title="Top Models", border_style="#346d93"))
            self._set_status("Loaded model cost detail")

        def _preview_project_brief(self, raw_summary: bool = False) -> None:
            project = self._selected_project()
            matches = self._match_briefs_for_project(project)
            if not project or not matches:
                self._set_status("No matching brief found for selected project")
                return
            brief = matches[0]
            if raw_summary or not brief.get("path"):
                body = brief.get("summary") or "No brief summary available."
                self.query_one("#detail-content", Static).update(
                    Panel(Markdown(str(body)), title=str(brief.get("title") or "Brief"))
                )
                self._set_status("Loaded brief summary")
                return
            try:
                payload = client.get_text_file(str(brief["path"]))
                self.query_one("#detail-content", Static).update(
                    Panel(Markdown(payload.get("content") or ""), title=str(payload.get("path") or brief["path"]))
                )
                self._set_status("Loaded project brief")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _edit_project_brief(self) -> None:
            selected_entry = self._selected_project_entry()
            if selected_entry and not selected_entry["is_dir"]:
                ext = Path(selected_entry["path"]).suffix.lower()
                if ext in {".md", ".markdown", ".txt", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"}:
                    try:
                        payload = client.get_text_file(selected_entry["path"])
                    except HermesAPIError as exc:
                        self._set_status(str(exc))
                        return
                    updated = await self._edit_text(
                        str(payload.get("path") or selected_entry["rel"]),
                        str(payload.get("content") or ""),
                    )
                    if updated is None:
                        self._set_status("Cancelled")
                        return
                    try:
                        client.save_text_file(str(payload.get("path") or selected_entry["path"]), updated)
                        self._set_status(f"Saved {selected_entry['rel']}")
                        self._preview_project_file()
                    except HermesAPIError as exc:
                        self._set_status(str(exc))
                    return
            project = self._selected_project()
            matches = self._match_briefs_for_project(project)
            if not project or not matches or not matches[0].get("path"):
                self._set_status("No editable brief found for selected project")
                return
            brief = matches[0]
            try:
                payload = client.get_text_file(str(brief["path"]))
            except HermesAPIError as exc:
                self._set_status(str(exc))
                return
            updated = await self._edit_text(str(payload.get("path") or brief["path"]), str(payload.get("content") or ""))
            if updated is None:
                self._set_status("Cancelled")
                return
            try:
                client.save_text_file(str(payload.get("path") or brief["path"]), updated)
                self._set_status("Project brief saved")
                self._preview_project_brief()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _todo_add(self) -> None:
            text = await self._prompt("New todo", placeholder="Ship gateway log viewer")
            if not text:
                self._set_status("Cancelled")
                return
            lines = list(self.notes_lines)
            lines.append(f"- [ ] {text}")
            try:
                client.save_notes("\n".join(lines))
                self.notes_lines = lines
                self._set_status("Todo added")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _toggle_todo_done(self) -> None:
            selected = self._selected_todo()
            if not selected:
                self._set_status("No todo selected")
                return
            idx = selected["line_index"]
            line = self.notes_lines[idx]
            if "[x]" in line.lower():
                updated = line.replace("[x]", "[ ]").replace("[X]", "[ ]")
            else:
                updated = line.replace("[ ]", "[x]")
            lines = list(self.notes_lines)
            lines[idx] = updated
            try:
                client.save_notes("\n".join(lines))
                self.notes_lines = lines
                self._set_status("Todo updated")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _delete_selected_todo(self) -> None:
            selected = self._selected_todo()
            if not selected:
                self._set_status("No todo selected")
                return
            lines = list(self.notes_lines)
            del lines[selected["line_index"]]
            try:
                client.save_notes("\n".join(lines))
                self.notes_lines = lines
                self.selected_todo_line_index = None
                self._set_status("Todo deleted")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _move_selected_todo(self) -> None:
            selected = self._selected_todo()
            if not selected:
                self._set_status("No todo selected")
                return
            direction = await self._prompt("Move todo", placeholder="up | down")
            if direction not in {"up", "down"}:
                self._set_status("Cancelled")
                return
            items = self._todo_items()
            item_pos = next((i for i, item in enumerate(items) if item["line_index"] == selected["line_index"]), None)
            if item_pos is None:
                self._set_status("Todo not found")
                return
            swap_pos = item_pos - 1 if direction == "up" else item_pos + 1
            if swap_pos < 0 or swap_pos >= len(items):
                self._set_status("Cannot move further")
                return
            a = items[item_pos]["line_index"]
            b = items[swap_pos]["line_index"]
            lines = list(self.notes_lines)
            lines[a], lines[b] = lines[b], lines[a]
            try:
                client.save_notes("\n".join(lines))
                self.notes_lines = lines
                self.selected_todo_line_index = b
                self._set_status(f"Todo moved {direction}")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _notes_edit(self) -> None:
            current = "\n".join(self.notes_lines)
            updated = await self._edit_text("Edit Hermes Notes", current)
            if updated is None:
                self._set_status("Cancelled")
                return
            try:
                client.save_notes(updated)
                self.notes_lines = updated.splitlines()
                self._set_status("Notes saved")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _edit_memory(self) -> None:
            self._load_memory_reports(force=False)
            current = str((self.memory_cache or {}).get("memory") or "")
            updated = await self._edit_text("Edit Live Memory", current)
            if updated is None:
                self._set_status("Cancelled")
                return
            try:
                client.save_memory("memory", updated)
                self.memory_cache = None
                self._load_memory_reports(force=True)
                self._render_current()
                self._set_status("Memory saved")
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _preview_memory_user(self) -> None:
            self._load_memory_reports(force=False)
            if not self.memory_cache:
                self._set_status("No memory payload loaded")
                return
            content = str(self.memory_cache.get("user") or "No USER.md content.")
            title = str(self.memory_cache.get("user_path") or "USER.md")
            self.query_one("#detail-content", Static).update(
                Panel(Markdown(content), title=title, border_style="#346d93")
            )
            self._set_status("Loaded USER.md")

        async def _kanban_add(self) -> None:
            project = self._selected_project()
            if not project or not project.get("project_id"):
                self._set_status("No project selected")
                return
            title = await self._prompt("Kanban title", placeholder="Integrate Honcho reporting")
            if not title:
                self._set_status("Cancelled")
                return
            detail = await self._prompt("Kanban detail", placeholder="Optional detail") or ""
            kanban = normalize_kanban(project.get("kanban"))
            card_id = f"{project['project_id']}-{len(kanban['todo']) + len(kanban['in_progress']) + len(kanban['done']) + 1}"
            kanban["todo"].append({"id": card_id, "title": title, "detail": detail})
            try:
                client.update_project(project["project_id"], kanban=kanban)
                self._refresh_side_state()
                self._set_status(f"Kanban card {card_id} added")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        async def _kanban_move(self) -> None:
            project = self._selected_project()
            if not project or not project.get("project_id"):
                self._set_status("No project selected")
                return
            card_id = await self._prompt("Kanban card id")
            if not card_id:
                self._set_status("Cancelled")
                return
            target = await self._prompt("Target column", placeholder="todo | in_progress | done")
            if target not in {"todo", "in_progress", "done"}:
                self._set_status("Invalid target column")
                return
            kanban = normalize_kanban(project.get("kanban"))
            card = None
            for column in ("todo", "in_progress", "done"):
                for entry in list(kanban[column]):
                    if str(entry.get("id")) == card_id:
                        card = dict(entry)
                        kanban[column].remove(entry)
                        break
                if card:
                    break
            if not card:
                self._set_status(f"Card {card_id} not found")
                return
            kanban[target].append(card)
            try:
                client.update_project(project["project_id"], kanban=kanban)
                self._refresh_side_state()
                self._set_status(f"Moved card {card_id} to {target}")
                self._render_current()
            except HermesAPIError as exc:
                self._set_status(str(exc))

        def _load_memory_reports(self, force: bool = False) -> None:
            if (self.memory_cache is None or force):
                self._queue_load("memory", force=force)
            if (self.reports_cache is None or force):
                self._queue_load("reports", force=force)

        def _hero_renderable(self) -> Panel:
            theme = self._theme()
            effects = self._effects()
            active_profile = self._active_profile_name()
            nav_name = self._current_view().removeprefix("nav-").replace("-", " ").title()
            text = Text()
            text.append(theme["hero_title"], style=f"bold {theme['accent']}")
            text.append("  ")
            text.append(f"View: {nav_name}", style=theme["text"])
            text.append("  ")
            text.append(f"Active: {active_profile}", style=theme["warn"])
            text.append("  ")
            text.append(f"Profiles: {len(self.profiles)}", style=theme["info"])
            text.append("  ")
            text.append(f"Sessions: {len(self.sessions)}", style=theme["info"])
            text.append("  ")
            text.append(f"Theme: {theme['name']}", style=theme["accent_soft"])
            text.append("  ")
            text.append(f"FX: {effects['name']}", style=theme["accent_soft"])
            text.append("  ")
            text.append(f"Layout: {self._saved_layout_label()}", style=theme["info"])
            if effects["show_tagline"]:
                text.append("\n")
                text.append(theme["hero_subtitle"], style=theme["muted"])
            if self.loading_views:
                text.append("  ")
                text.append("Loading…", style=theme["warn"])
            return self._panel(
                text,
                title=theme["brand"],
                subtitle=theme["tagline"] if effects["show_tagline"] else "Hermes TUI HUD",
                border=theme["hero_border"],
            )

        def _load_saved_theme(self) -> str:
            try:
                saved = THEME_STATE_PATH.read_text(encoding="utf-8").strip()
                if saved in THEMES:
                    return saved
            except OSError:
                pass
            return "matrix"

        def _load_saved_effects(self) -> str:
            try:
                saved = EFFECTS_STATE_PATH.read_text(encoding="utf-8").strip()
                if saved in EFFECT_MODES:
                    return saved
            except OSError:
                pass
            return "full"

        def _save_theme(self) -> None:
            try:
                THEME_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
                THEME_STATE_PATH.write_text(self.hud_theme, encoding="utf-8")
            except OSError:
                pass

        def _save_effects(self) -> None:
            try:
                EFFECTS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
                EFFECTS_STATE_PATH.write_text(self.hud_effects, encoding="utf-8")
            except OSError:
                pass

        def _brand_renderable(self) -> Text:
            theme = self._theme()
            effects = self._effects()
            text = Text()
            text.append("HERMES HERO", style=f"bold {theme['accent']}")
            if effects["show_tagline"]:
                text.append("\n")
                text.append("Hermes Executive Relay Operations", style=theme["accent_soft"])
            return text

        def _render_top_nav_buttons(self) -> None:
            theme = self._theme()
            current = self._current_view()
            marker = theme.get("marker", "▸")
            top_nav = self.query_one("#top-nav", Horizontal)
            for child in top_nav.children:
                if not isinstance(child, Button):
                    continue
                target = (child.id or "").removeprefix("topnav-")
                label = target.removeprefix("nav-").replace("-", " ").title()
                if target == "nav-token-spend":
                    label = "Spend"
                elif target == "nav-maintenance":
                    label = "Maint"
                if target == current:
                    child.label = f"{marker} {label}"
                    child.styles.background = theme["accent"]
                    child.styles.color = theme["screen_bg"]
                    child.styles.border = ("round", theme["accent"])
                else:
                    child.label = label
                    child.styles.background = theme["nav_bg"]
                    child.styles.color = theme["muted"]
                    child.styles.border = ("round", theme["border"])

        def _panel(self, content: Any, *, title: str | None = None, subtitle: str | None = None, border: str | None = None) -> Panel:
            theme = self._theme()
            effects = self._effects()
            border_style = border or theme["border"]
            title_text = Text(title or "", style=f"bold {theme['accent']}") if title else None
            subtitle_text = Text(subtitle or "", style=theme["accent_soft"]) if subtitle else None
            return Panel(content, title=title_text, subtitle=subtitle_text, border_style=border_style, box=effects["box"])

        def _splash_main(self) -> Panel:
            theme = self._theme()
            effects = self._effects()
            if effects["show_splash_art"]:
                art = Text("HERMES HERO\n", style=f"bold {theme['accent']}")
                art.append("Hermes Executive Relay Operations\n\n", style=theme["accent_soft"])
                art.append(theme["tagline"], style=theme["text"])
                art.append("\n\nPreparing relay, memory, sessions, and operator state...", style=theme["muted"])
            else:
                art = Text("HERMES HERO\n", style=f"bold {theme['accent']}")
                art.append("Hermes Executive Relay Operations", style=theme["accent_soft"])
            return self._panel(art, title=theme["splash_title"], subtitle=theme["splash_subtitle"], border=theme["hero_border"])

        def _splash_detail(self) -> Panel:
            theme = self._theme()
            effects = self._effects()
            body = "Loading profiles, sessions, projects, notes, and operator state."
            if effects["show_tagline"]:
                body += "\n\nThis splash stays up briefly so boot-time backend calls do not feel like a freeze."
            msg = Text(body, style=theme["text"])
            return self._panel(msg, title="Boot Sequence", subtitle=effects["name"], border=theme["info"])

        def _overview_main(self) -> Panel:
            if not self.overview_cache:
                return Panel("Loading overview data...", title="System Overview", border_style="#2a7f4f")
            resources = self.overview_cache.get("resources", {})
            memory = resources.get("memory", {})
            disk = resources.get("disk", {})
            table = Table.grid(padding=(0, 2))
            table.add_column(style="bold #8bf2a4")
            table.add_column(style="#d7f6df")
            table.add_row("CPU", f"{resources.get('cpu_percent', 0)}%")
            table.add_row("Memory", f"{memory.get('percent', 0)}%")
            table.add_row("Disk", f"{disk.get('percent', 0)}%")
            table.add_row("Profiles", str(len(self.profiles)))
            table.add_row("Sessions", str(len(self.sessions)))
            table.add_row("Projects", str(len(self.projects)))
            return Panel(table, title="System Overview", border_style="#2a7f4f")

        def _overview_detail(self) -> Panel:
            if not self.overview_cache:
                return Panel("Loading alert feed...", title="Recent Alerts", border_style="#346d93")
            alerts = self.overview_cache.get("alerts", [])
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Event", style="#d7f6df")
            table.add_column("Project", style="#8ab2ff")
            if alerts:
                for alert in alerts:
                    title = getattr(alert, "title", None) or str(alert.get("title") if isinstance(alert, dict) else "Event")
                    project = getattr(alert, "project", None) if not isinstance(alert, dict) else alert.get("project")
                    table.add_row(title, project or "-")
            else:
                table.add_row("No recent ops events", "-")
            return Panel(table, title="Recent Alerts", border_style="#346d93")

        def _agents_main(self) -> Panel:
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Sel", width=3, style="#e0c36a")
            table.add_column("Agent", style="#d7f6df")
            table.add_column("Model", style="#8ab2ff")
            table.add_column("Flags", style="#8bf2a4")
            for profile in self.profiles:
                flags = []
                if profile.get("is_active"):
                    flags.append("active")
                if profile.get("is_default"):
                    flags.append("default")
                if profile.get("gateway_running"):
                    flags.append("gateway")
                table.add_row(
                    ">" if profile.get("name") == self.selected_agent_name else "",
                    str(profile.get("name") or "unknown"),
                    str(profile.get("model") or "unknown"),
                    ", ".join(flags) or "-",
                )
            help_text = Text("\n] / [ select    o switch active    v config    y soul    s/x/t/l gateway", style="#84b694")
            return Panel(Group(table, help_text), title="Agents", border_style="#2a7f4f")

        def _agents_detail(self) -> Panel:
            profile = self._selected_profile()
            if not profile:
                return Panel("No profile selected", title="Agent Detail", border_style="#7f4a2a")
            content = self.profile_content_cache.get(profile["name"])
            if not content:
                self._ensure_view_data("nav-agents")
                return Panel("Loading selected profile...", title="Agent Detail", border_style="#346d93")
            meta = Table.grid(padding=(0, 1))
            meta.add_column(style="bold #8bf2a4")
            meta.add_column(style="#d7f6df")
            meta.add_row("Name", str(profile.get("name") or "unknown"))
            meta.add_row("Provider", str(profile.get("provider") or "unknown"))
            meta.add_row("Model", str(profile.get("model") or "unknown"))
            meta.add_row("Path", str(profile.get("path") or "unknown"))
            meta.add_row("Gateway", "running" if profile.get("gateway_running") else "stopped")
            soul_preview = (content.get("soul") or "").splitlines()[:8]
            config_preview = (content.get("config") or "").splitlines()[:8]
            group = Group(
                meta,
                Text(""),
                Text("SOUL.md", style="bold #e0c36a"),
                Text("\n".join(soul_preview) or "No SOUL.md found", style="#d7f6df"),
                Text(""),
                Text("config.yaml", style="bold #8ab2ff"),
                Text("\n".join(config_preview) or "No config.yaml found", style="#d7f6df"),
            )
            return Panel(group, title=f"Selected · {profile['name']}", border_style="#346d93")

        def _visible_sessions(self) -> list[dict[str, Any]]:
            if self.session_query.strip():
                if self.session_search_results is not None:
                    base = self.session_search_results
                else:
                    query = self.session_query.strip().lower()
                    base = [
                        session
                        for session in self.sessions
                        if query in " ".join(
                            [
                                str(session.get("title") or ""),
                                str(session.get("profile") or ""),
                                str(session.get("model") or ""),
                            ]
                        ).lower()
                    ]
            else:
                base = self.sessions

            if self.session_filter == "open":
                return [session for session in base if not session.get("archived")]
            if self.session_filter == "pinned":
                return [session for session in base if session.get("pinned")]
            if self.session_filter == "archived":
                return [session for session in base if session.get("archived")]
            if self.session_filter == "recent":
                return list(base[:8])
            return list(base)

        def _sessions_main(self) -> Panel:
            visible_sessions = self._visible_sessions()
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Sel", width=3, style="#e0c36a")
            table.add_column("Title", style="#d7f6df")
            table.add_column("Profile", style="#8ab2ff")
            table.add_column("Tokens", justify="right", style="#e0c36a")
            table.add_column("Cost", justify="right", style="#8bf2a4")
            table.add_column("Flags", style="#8bf2a4")
            for session in visible_sessions[:30]:
                flags = []
                if session.get("pinned"):
                    flags.append("pinned")
                if session.get("archived"):
                    flags.append("archived")
                table.add_row(
                    ">" if str(session.get("session_id") or "") == self.selected_session_id else "",
                    str(session.get("title") or "Untitled"),
                    str(session.get("profile") or "default"),
                    str(session_token_total(session)),
                    f"${session_cost_value(session):.3f}",
                    ", ".join(flags) or "-",
                )
            if not visible_sessions:
                table.add_row("", "No sessions match search", "-", "-", "-", "-")
            visible_cost = sum(session_cost_value(session) for session in visible_sessions)
            visible_tokens = sum(session_token_total(session) for session in visible_sessions)
            help_text = Text(
                f"\nVisible tokens: {visible_tokens}    Visible cost: ${visible_cost:.3f}"
                f"\n] / [ select    f search={self.session_query or 'off'}    k filter={self.session_filter}    j export    e rename    p pin    m archive    c clear    d delete",
                style="#84b694",
            )
            return Panel(Group(table, help_text), title="Sessions", border_style="#2a7f4f")

        def _sessions_detail(self) -> Panel:
            session = self._selected_session()
            if not session:
                return Panel("No session selected", title="Session Detail", border_style="#7f4a2a")
            table = Table.grid(padding=(0, 1))
            table.add_column(style="bold #8bf2a4")
            table.add_column(style="#d7f6df")
            table.add_row("Title", str(session.get("title") or "Untitled"))
            table.add_row("ID", str(session.get("session_id") or "n/a"))
            table.add_row("Profile", str(session.get("profile") or "default"))
            table.add_row("Model", str(session.get("model") or "unknown"))
            table.add_row("Messages", str(session.get("message_count") or 0))
            table.add_row("Input Tokens", str(int(session.get("input_tokens") or 0)))
            table.add_row("Output Tokens", str(int(session.get("output_tokens") or 0)))
            table.add_row("Total Tokens", str(session_token_total(session)))
            table.add_row("Est. Cost", f"${session_cost_value(session):.3f}")
            table.add_row("Pinned", str(bool(session.get("pinned"))))
            table.add_row("Archived", str(bool(session.get("archived"))))
            if session.get("match_type"):
                table.add_row("Match", str(session.get("match_type")))
            excerpt = (
                session.get("excerpt")
                or session.get("match_excerpt")
                or session.get("snippet")
                or session.get("summary")
                or ""
            )
            if excerpt:
                return Panel(Group(table, Text(""), Text("Excerpt", style="bold #e0c36a"), Text(str(excerpt), style="#d7f6df")), title="Selected Session", border_style="#346d93")
            return Panel(table, title="Selected Session", border_style="#346d93")

        def _gateway_main(self) -> Panel:
            profile_name = self._gateway_profile_name()
            payload = self.gateway_cache.get(profile_name)
            if not payload:
                self._ensure_view_data("nav-gateway")
                return Panel(f"Loading gateway status for {profile_name}...", title="Gateway", border_style="#2a7f4f")
            table = Table.grid(padding=(0, 2))
            table.add_column(style="bold #8bf2a4")
            table.add_column(style="#d7f6df")
            table.add_row("Profile", str(payload.get("profile") or profile_name))
            table.add_row("Service", str(payload.get("service") or "unknown"))
            table.add_row("Installed", str(bool(payload.get("installed"))))
            table.add_row("Active", str(bool(payload.get("active"))))
            table.add_row("Enabled", str(bool(payload.get("enabled"))))
            if payload.get("message"):
                table.add_row("Message", str(payload.get("message")))
            help_text = Text("\ns start  x stop  t restart  l logs", style="#84b694")
            return Panel(Group(table, help_text), title="Gateway", border_style="#2a7f4f")

        def _gateway_detail(self) -> Panel:
            profile_name = self._gateway_profile_name()
            return Panel(
                Text(
                    f"Gateway commands are scoped to the selected profile.\n\nCurrent profile: {profile_name}\n\n"
                    "Use Agents or ]/[ to change scope before starting, stopping, or reading logs.",
                    style="#d7f6df",
                ),
                title="Gateway Scope",
                border_style="#346d93",
            )

        def _cron_main(self) -> Panel:
            jobs = self.cron_cache
            if jobs is None:
                self._ensure_view_data("nav-cron")
                return Panel("Loading cron jobs...", title="Cron", border_style="#2a7f4f")
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("ID", style="#8ab2ff")
            table.add_column("Name", style="#d7f6df")
            table.add_column("Schedule", style="#8bf2a4")
            table.add_column("Enabled", style="#e0c36a")
            for job in jobs[:20]:
                schedule = job.get("schedule_display") or job.get("schedule") or "manual"
                if isinstance(schedule, dict):
                    schedule = schedule.get("display") or schedule.get("expr") or schedule.get("kind") or str(schedule)
                table.add_row(str(job.get("id") or "n/a"), str(job.get("name") or "unnamed"), str(schedule), str(job.get("enabled", True)))
            help_text = Text("\nn add  e run  p pause/resume  d delete", style="#84b694")
            return Panel(Group(table, help_text), title="Cron", border_style="#2a7f4f")

        def _cron_detail(self) -> Panel:
            return Panel(
                Text("Cron controls target the active Hermes profile.\nUse add/run/pause/delete through modal prompts.", style="#d7f6df"),
                title="Cron Detail",
                border_style="#346d93",
            )

        def _projects_main(self) -> Panel:
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Sel", width=3, style="#e0c36a")
            table.add_column("Project", style="#d7f6df")
            table.add_column("Path", style="#8ab2ff")
            table.add_column("Cards", justify="right", style="#8bf2a4")
            for project in self.projects:
                kanban = normalize_kanban(project.get("kanban"))
                total = len(kanban["todo"]) + len(kanban["in_progress"]) + len(kanban["done"])
                table.add_row(
                    ">" if self._project_id(project) == self.selected_project_id else "",
                    str(project.get("name") or self._project_id(project)),
                    str(project.get("path") or "-"),
                    str(total),
                )
            help_text = Text("\n] / [ select    v open file/brief    e edit selected text file or brief    y browse path    b up dir    p cycle entry    n add card    m move card", style="#84b694")
            return Panel(Group(table, help_text), title="Projects", border_style="#2a7f4f")

        def _projects_detail(self) -> Panel:
            project = self._selected_project()
            if not project:
                return Panel("No project selected", title="Project Detail", border_style="#7f4a2a")
            kanban = normalize_kanban(project.get("kanban"))
            matches = self._match_briefs_for_project(project)
            entries = self._project_entries()
            table = Table(expand=True)
            table.add_column("Todo", style="#d7f6df")
            table.add_column("In Progress", style="#8ab2ff")
            table.add_column("Done", style="#8bf2a4")
            max_rows = max(len(kanban["todo"]), len(kanban["in_progress"]), len(kanban["done"]), 1)
            for idx in range(max_rows):
                row = []
                for column in ("todo", "in_progress", "done"):
                    if idx < len(kanban[column]):
                        card = kanban[column][idx]
                        row.append(f"{card.get('id')}\n{card.get('title')}")
                    else:
                        row.append("")
                table.add_row(*row)
            header = Text()
            header.append(str(project.get("name") or "Project"), style="bold #e0c36a")
            header.append(f"\n{project.get('path') or ''}", style="#84b694")
            if project.get("description"):
                header.append(f"\n\n{project.get('description')}", style="#d7f6df")
            if matches:
                header.append("\n\nBriefs:", style="bold #8bf2a4")
                for brief in matches:
                    header.append(f"\n- {brief.get('title') or brief.get('path')}", style="#d7f6df")
            browser = Table(expand=True, box=None, pad_edge=False)
            browser.add_column("Project Files", style="#d7f6df")
            browser.add_column("Type", width=8, style="#8ab2ff")
            if entries:
                for entry in entries[:12]:
                    browser.add_row(
                        f"{'>' if entry['rel'] == self.selected_project_entry_rel else ' '} {entry['rel']}",
                        "dir" if entry["is_dir"] else "file",
                    )
            else:
                browser.add_row("(no entries)", "-")
            footer = Text(
                f"\nBrowser path: {self.project_browser_path}\n"
                "p cycle file/dir    v open file / enter dir    y browse directory    b up dir    e edit selected text file or matched brief",
                style="#84b694",
            )
            return Panel(Group(header, Text(""), browser, Text(""), table, footer), title="Project Board", border_style="#346d93")

        def _notes_main(self) -> Panel:
            todos = self._todo_items()
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Sel", width=3, style="#e0c36a")
            table.add_column("Todo", style="#d7f6df")
            table.add_column("State", width=10, style="#8bf2a4")
            for todo in todos[-15:]:
                state = "done" if todo["done"] else "open"
                table.add_row(">" if todo["line_index"] == self.selected_todo_line_index else "", todo["text"], state)
            if not todos:
                table.add_row("", "No todo items in notes", "-")
            help_text = Text("\n] / [ select    p toggle done    d delete todo    m move todo    n add todo    e edit notes", style="#84b694")
            return Panel(Group(table, help_text), title="Notes / Todos", border_style="#2a7f4f")

        def _notes_detail(self) -> Panel:
            text = "\n".join(self.notes_lines[-40:]) or "No notes content."
            selected = self._selected_todo()
            if selected:
                group = Group(
                    Text("Selected Todo", style="bold #e0c36a"),
                    Text(selected["text"], style="#d7f6df"),
                    Text(""),
                    Markdown(text),
                )
                return Panel(group, title="~/.hermes/notes.md", border_style="#346d93")
            return Panel(Markdown(text), title="~/.hermes/notes.md", border_style="#346d93")

        def _memory_main(self) -> Panel:
            self._load_memory_reports(force=False)
            memory = self.memory_cache or {}
            if not memory:
                return Panel("Loading live memory...", title="Live Memory", border_style="#2a7f4f")
            memory_block = str(memory.get("memory") or "")
            preview = "\n".join(memory_block.splitlines()[:14]) or "No memory content found."
            help_text = Text("\ne edit MEMORY.md    v preview USER.md    u refresh memory", style="#84b694")
            return Panel(Group(Text(preview, style="#d7f6df"), help_text), title="Live Memory", border_style="#2a7f4f")

        def _memory_detail(self) -> Panel:
            self._load_memory_reports(force=False)
            memory = self.memory_cache or {}
            if not memory:
                return Panel("Loading memory detail...", title="Memory Detail", border_style="#346d93")
            user_preview = "\n".join(str(memory.get("user") or "").splitlines()[:18]) or "No USER.md content."
            table = Table.grid(padding=(0, 1))
            table.add_column(style="bold #8bf2a4")
            table.add_column(style="#d7f6df")
            table.add_row("Memory Path", str(memory.get("memory_path") or "n/a"))
            table.add_row("User Path", str(memory.get("user_path") or "n/a"))
            return Panel(Group(table, Text(""), Markdown(user_preview)), title="Memory Detail", border_style="#346d93")

        def _reports_main(self) -> Panel:
            self._load_memory_reports(force=False)
            reports = self.reports_cache or {}
            if not reports:
                return Panel("Loading reports...", title="Reports", border_style="#2a7f4f")
            resources = reports.get("resources") or {}
            costs = reports.get("costs") or {}
            dialogs = reports.get("dialogs") or {}
            sessions = filter_sessions_by_window(reports.get("sessions") or [], self.report_window)
            total_cost = sum(session_cost_value(session) for session in sessions)
            total_input = sum(int(session.get("input_tokens") or 0) for session in sessions)
            total_output = sum(int(session.get("output_tokens") or 0) for session in sessions)
            total_tokens = total_input + total_output
            by_model = list((costs.get("by_model") or [])[:5])
            spend_table = Table(expand=True, box=None, pad_edge=False)
            spend_table.add_column("Model", style="#d7f6df")
            spend_table.add_column("Tokens", justify="right", style="#e0c36a")
            spend_table.add_column("Cost", justify="right", style="#8bf2a4")
            if by_model:
                for row in by_model:
                    model_tokens = int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)
                    spend_table.add_row(
                        str(row.get("model") or "unknown"),
                        str(model_tokens),
                        f"${float(row.get('estimated_cost') or 0):.3f}",
                    )
            else:
                spend_table.add_row("No model spend data", "-", "-")
            table = Table.grid(padding=(0, 1))
            table.add_column(style="bold #8bf2a4")
            table.add_column(style="#d7f6df")
            table.add_row("CPU", f"{resources.get('cpu_percent', 0)}%")
            table.add_row("Memory", f"{(resources.get('memory') or {}).get('percent', 0)}%")
            table.add_row("Disk", f"{(resources.get('disk') or {}).get('percent', 0)}%")
            table.add_row("Sessions", str(len(sessions)))
            table.add_row("Input Tokens", str(total_input))
            table.add_row("Output Tokens", str(total_output))
            table.add_row("Total Tokens", str(total_tokens))
            table.add_row("Estimated Cost", f"${total_cost:.3f}")
            table.add_row("Dialog Roots", str(len(dialogs.get("roots") or [])))
            lines = [
                table,
                Text(""),
                Text(f"Window: {self.report_window}", style="#84b694"),
                Text(""),
                Text("Top Spend", style="bold #e0c36a"),
                spend_table,
                Text(""),
                Text("Press I to change time window · V for top models · U to refresh reports", style="#84b694"),
            ]
            return Panel(Group(*lines), title="Reports", border_style="#2a7f4f")

        def _reports_detail(self) -> Panel:
            self._load_memory_reports(force=False)
            reports = self.reports_cache or {}
            if not reports:
                return Panel("Loading reporting detail...", title="Reporting Detail", border_style="#346d93")
            costs = reports.get("costs") or {}
            dialogs = reports.get("dialogs") or {}
            top_models = list((costs.get("by_model") or [])[:5])
            by_provider = list((costs.get("by_provider") or costs.get("by_platform") or [])[:5])
            lines = [Text("Top Models", style="bold #e0c36a")]
            if top_models:
                for row in top_models:
                    model_tokens = int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)
                    lines.append(Text(f"- {row.get('model') or 'unknown'}  {model_tokens} tok  ${float(row.get('estimated_cost') or 0):.3f}", style="#d7f6df"))
            else:
                lines.append(Text("No model cost data available.", style="#d7f6df"))
            lines.extend([Text(""), Text("Providers / Platforms", style="bold #8bf2a4")])
            if by_provider:
                for row in by_provider:
                    label = row.get("provider") or row.get("platform") or row.get("name") or "unknown"
                    provider_tokens = int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)
                    lines.append(Text(f"- {label}  {provider_tokens} tok  ${float(row.get('estimated_cost') or 0):.3f}", style="#d7f6df"))
            else:
                lines.append(Text("No provider-level spend data.", style="#d7f6df"))
            roots = list((dialogs.get("roots") or [])[:4])
            lines.extend([Text(""), Text("Dialog Roots", style="bold #8ab2ff")])
            if roots:
                for root in roots:
                    lines.append(Text(f"- {root.get('title') or 'Untitled'} · {root.get('model') or 'unknown'}", style="#d7f6df"))
            else:
                lines.append(Text("No dialog graph data.", style="#d7f6df"))
            return Panel(Group(*lines), title="Reporting Detail", border_style="#346d93")

        def _token_spend_main(self) -> Panel:
            self._load_memory_reports(force=False)
            reports = self.reports_cache or {}
            if not reports:
                return Panel("Loading token spend...", title="Token Spend", border_style="#2a7f4f")
            sessions = reports.get("sessions") or []
            rows = spend_history_rows(sessions, self.report_window)
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Bucket", style="#d7f6df")
            table.add_column("Tokens", justify="right", style="#e0c36a")
            table.add_column("Cost", justify="right", style="#8bf2a4")
            table.add_column("Spend Graph", style="#8ab2ff")
            max_cost = max((float(row["cost"]) for row in rows), default=0.0)
            for row in rows:
                table.add_row(
                    str(row["label"]),
                    str(int(row["tokens"])),
                    f"${float(row['cost']):.3f}",
                    spark_bar(float(row["cost"]), max_cost),
                )
            if not rows:
                table.add_row("No spend data", "-", "-", "··················")
            filtered = filter_sessions_by_window(sessions, self.report_window)
            total_cost = sum(session_cost_value(session) for session in filtered)
            total_tokens = sum(session_token_total(session) for session in filtered)
            summary = Text(
                f"Window: {self.report_window}    Sessions: {len(filtered)}    Tokens: {total_tokens}    Cost: ${total_cost:.3f}\n"
                "Press I to change time window.",
                style="#84b694",
            )
            return Panel(Group(table, Text(""), summary), title="Token Spend", border_style="#2a7f4f")

        def _token_spend_detail(self) -> Panel:
            self._load_memory_reports(force=False)
            reports = self.reports_cache or {}
            if not reports:
                return Panel("Loading token spend detail...", title="Token Spend Detail", border_style="#346d93")
            sessions = reports.get("sessions") or []
            filtered = filter_sessions_by_window(sessions, self.report_window)
            by_profile: dict[str, dict[str, Any]] = {}
            by_provider: dict[str, dict[str, Any]] = {}
            for session in filtered:
                profile = str(session.get("profile") or "default")
                provider = str(session.get("provider") or session.get("platform") or infer_provider_from_model(str(session.get("model") or "")) or "unknown")
                for bucket, key in ((by_profile, profile), (by_provider, provider)):
                    row = bucket.setdefault(key, {"tokens": 0, "cost": 0.0, "sessions": 0})
                    row["tokens"] += session_token_total(session)
                    row["cost"] += session_cost_value(session)
                    row["sessions"] += 1

            lines: list[Any] = [Text(f"Window: {self.report_window}", style="#84b694"), Text("")]
            lines.append(Text("By Profile", style="bold #e0c36a"))
            if by_profile:
                for key, row in sorted(by_profile.items(), key=lambda item: item[1]["cost"], reverse=True)[:8]:
                    lines.append(Text(f"- {key}  {row['tokens']} tok  ${row['cost']:.3f}  {row['sessions']} sess", style="#d7f6df"))
            else:
                lines.append(Text("No profile spend data.", style="#d7f6df"))
            lines.extend([Text(""), Text("By Provider", style="bold #8bf2a4")])
            if by_provider:
                for key, row in sorted(by_provider.items(), key=lambda item: item[1]["cost"], reverse=True)[:8]:
                    lines.append(Text(f"- {key}  {row['tokens']} tok  ${row['cost']:.3f}  {row['sessions']} sess", style="#d7f6df"))
            else:
                lines.append(Text("No provider spend data.", style="#d7f6df"))
            return Panel(Group(*lines), title="Token Spend Detail", border_style="#346d93")

        def _maintenance_main(self) -> Panel:
            if self.maintenance_cache is None:
                message = Text(
                    "Maintenance data is now lazy-loaded.\n\nPress U to run an update check.\n"
                    "This avoids the old blocking pause when you open the pane.",
                    style="#d7f6df",
                )
                return Panel(message, title="Maintenance", border_style="#2a7f4f")
            payload = self.maintenance_cache
            table = Table(expand=True, box=None, pad_edge=False)
            table.add_column("Target", style="#d7f6df")
            table.add_column("Branch", style="#8ab2ff")
            table.add_column("Behind", justify="right", style="#8bf2a4")
            table.add_column("Current", style="#84b694")
            if payload.get("disabled"):
                table.add_row("updates", "disabled", "-", "-")
            else:
                for key in ("webui", "agent"):
                    block = payload.get(key) or {}
                    table.add_row(
                        key,
                        str(block.get("branch") or "unknown"),
                        str(block.get("behind") or 0),
                        str(block.get("current_sha") or "unknown")[:12],
                    )
            help_text = Text("\nu check  w webui  a agent  c cleanup  z zero cleanup", style="#84b694")
            return Panel(Group(table, help_text), title="Maintenance", border_style="#2a7f4f")

        def _maintenance_detail(self) -> Panel:
            return Panel(
                Text("Use this pane for update checks and cleanup flows. Mutating actions run live against Hermes.", style="#d7f6df"),
                title="Maintenance Detail",
                border_style="#346d93",
            )

        def _render_current(self) -> None:
            main_widget = self.query_one("#main-content", Static)
            detail_widget = self.query_one("#detail-content", Static)
            hero_widget = self.query_one("#hero", Static)
            top_nav_widget = self.query_one("#top-nav", Horizontal)

            if self.show_splash:
                theme = self._theme()
                top_nav_widget.styles.display = "none"
                hero_widget.update(
                    self._panel(
                        Text(f"Initializing {theme['brand']}...", style=theme["accent"]),
                        title=theme["hero_title"],
                        subtitle=theme["hero_subtitle"],
                        border=theme["hero_border"],
                    )
                )
                main_widget.update(self._splash_main())
                detail_widget.update(self._splash_detail())
                return

            self._ensure_view_data(self._current_view())
            if self._effective_layout_mode() == "stacked":
                top_nav_widget.styles.display = "block"
            self._render_top_nav_buttons()
            hero_widget.update(self._hero_renderable())
            selected_id = self._current_view()
            try:
                if selected_id == "nav-agents":
                    main_renderable = self._agents_main()
                    detail_renderable = self._agents_detail()
                elif selected_id == "nav-sessions":
                    main_renderable = self._sessions_main()
                    detail_renderable = self._sessions_detail()
                elif selected_id == "nav-gateway":
                    main_renderable = self._gateway_main()
                    detail_renderable = self._gateway_detail()
                elif selected_id == "nav-cron":
                    main_renderable = self._cron_main()
                    detail_renderable = self._cron_detail()
                elif selected_id == "nav-projects":
                    main_renderable = self._projects_main()
                    detail_renderable = self._projects_detail()
                elif selected_id == "nav-notes":
                    main_renderable = self._notes_main()
                    detail_renderable = self._notes_detail()
                elif selected_id == "nav-memory":
                    main_renderable = self._memory_main()
                    detail_renderable = self._memory_detail()
                elif selected_id == "nav-reports":
                    main_renderable = self._reports_main()
                    detail_renderable = self._reports_detail()
                elif selected_id == "nav-token-spend":
                    main_renderable = self._token_spend_main()
                    detail_renderable = self._token_spend_detail()
                elif selected_id == "nav-maintenance":
                    main_renderable = self._maintenance_main()
                    detail_renderable = self._maintenance_detail()
                else:
                    main_renderable = self._overview_main()
                    detail_renderable = self._overview_detail()
                main_widget.update(main_renderable)
                detail_widget.update(detail_renderable)
                self._set_status(f"Active view: {selected_id.removeprefix('nav-')}")
            except HermesAPIError as exc:
                main_widget.update(Panel(str(exc), title="Backend Error", border_style="#aa4444"))
                detail_widget.update(Panel("Hermes request failed.", border_style="#aa4444"))
                self._set_status(str(exc))

        def _active_profile_name(self) -> str:
            active = next((profile["name"] for profile in self.profiles if profile.get("is_active")), None)
            return active or self.selected_agent_name or (self.profiles[0]["name"] if self.profiles else "default")

    HermesHUDApp().run()
    return 0


def normalize_kanban(input_value: Any) -> dict[str, list[dict[str, Any]]]:
    data = input_value if isinstance(input_value, dict) else {}
    return {
        "todo": list(data.get("todo") or []),
        "in_progress": list(data.get("in_progress") or []),
        "done": list(data.get("done") or []),
    }


def session_token_total(session: dict[str, Any]) -> int:
    return int(session.get("input_tokens") or 0) + int(session.get("output_tokens") or 0)


def session_cost_value(session: dict[str, Any]) -> float:
    return float(session.get("estimated_cost") or 0.0)


def session_timestamp(session: dict[str, Any]) -> datetime | None:
    raw = session.get("updated_at") or session.get("created_at") or session.get("ts")
    if raw in (None, "", 0):
        return None
    try:
        value = float(raw)
        if value > 1_000_000_000_000:
            value = value / 1000.0
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except Exception:
        return None


def filter_sessions_by_window(sessions: list[dict[str, Any]], window: str) -> list[dict[str, Any]]:
    if window == "all":
        return list(sessions)
    now = datetime.now(timezone.utc)
    seconds = {"24h": 24 * 3600, "7d": 7 * 24 * 3600, "30d": 30 * 24 * 3600}.get(window, 24 * 3600)
    filtered: list[dict[str, Any]] = []
    for session in sessions:
        ts = session_timestamp(session)
        if ts is None:
            continue
        if (now - ts).total_seconds() <= seconds:
            filtered.append(session)
    return filtered


def spend_history_rows(sessions: list[dict[str, Any]], window: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    buckets: dict[str, dict[str, Any]] = {}
    use_hourly = window == "24h"
    for session in filter_sessions_by_window(sessions, window):
        ts = session_timestamp(session)
        if ts is None:
            continue
        if use_hourly:
            label = ts.astimezone().strftime("%m-%d %H:00")
        else:
            label = ts.astimezone().strftime("%Y-%m-%d")
        row = buckets.setdefault(label, {"label": label, "tokens": 0, "cost": 0.0, "sessions": 0})
        row["tokens"] += session_token_total(session)
        row["cost"] += session_cost_value(session)
        row["sessions"] += 1

    rows = list(buckets.values())
    rows.sort(key=lambda row: row["label"])
    if window == "24h":
        return rows[-24:]
    if window == "7d":
        return rows[-7:]
    if window == "30d":
        return rows[-30:]
    return rows[-30:]


def spark_bar(value: float, max_value: float, width: int = 18) -> str:
    if max_value <= 0:
        return "·" * width
    filled = max(1 if value > 0 else 0, int(round((value / max_value) * width)))
    filled = min(width, filled)
    return "█" * filled + "·" * (width - filled)


def infer_provider_from_model(model: str) -> str:
    lower = model.lower()
    if "openai" in lower or "gpt" in lower:
        return "openai"
    if "claude" in lower or "anthropic" in lower:
        return "anthropic"
    if "grok" in lower or "xai" in lower:
        return "xai"
    if "gemini" in lower or "google" in lower:
        return "google"
    if "deepseek" in lower:
        return "deepseek"
    if "mistral" in lower:
        return "mistral"
    return "unknown"
