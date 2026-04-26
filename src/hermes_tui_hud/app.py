"""Cyberpunk Hermes Dashboard TUI HUD  –  Status · Sessions · Model · Config
    Skills · Tools · Cron · Logs · Analytics · Env

Keybindings:  q=Quit  r=Refresh  /=Search  1-9/0=Tabs  t=ToggleSkill  e=EditConfig  Ctrl+S=Save
"""

from __future__ import annotations

import errno
from datetime import datetime, timezone

from textual.reactive import reactive
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from textual.widget import NoMatches

from .client.api import HermesDashboardClient
from .client.models import (
    CronJob, EnvVar, HermesSession, ModelInfo, SessionSearchResult,
    Skill, Status, Toolset, UsageAnalytics,
)

from .widgets import Panel

def _short_rel_time(iso: str | None) -> str:
    """Return compact relative time: 30s / 5m / 2h / 3D / 1W."""
    if not iso:
        return "-"
    try:
        # Hermes timestamps: ISO 8601, usually with microseconds and Z suffix
        # Normalize: replace Z with +00:00 for fromisoformat
        iso_norm = iso.replace("Z", "+00:00") if iso.endswith("Z") else iso
        dt = datetime.fromisoformat(iso_norm)
        # Make timezone-aware if naive (assume UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        secs = diff.total_seconds()
        if secs < 60:
            return f"{int(secs)}s"
        mins = secs / 60
        if mins < 60:
            return f"{int(mins)}m"
        hours = mins / 60
        if hours < 24:
            return f"{int(hours)}h"
        days = hours / 24
        if days < 7:
            return f"{int(days)}D"
        weeks = days / 7
        return f"{int(weeks)}W"
    except Exception:
        return "?"



# ─── Colors ─────────────────────────────────────────────────────────────
# ─── Theme Palettes ─────────────────────────────────────────────────────────
PALETTES = [
    # 0 — Neon Night (default cyberpunk)
    ("#00fff0", "#ff00ff", "#00ff41", "#ff0040", "#0a0a0f", "#12121a"),  # cyan, magenta, green, red, bg, panel
    # 1 — Vaporwave
    ("#ff71ce", "#01cdfe", "#05ffa1", "#b967ff", "#1a0b2e", "#2b102e"),
    # 2 — Matrix
    ("#00ff00", "#003300", "#008f11", "#00ff41", "#000000", "#001100"),
    # 3 — Amber CRT
    ("#ffb000", "#ff6b00", "#ffd000", "#ff4800", "#0f0a00", "#1a1208"),
    # 4 — ICE ICE BABY
    ("#00e5ff", "#00ffea", "#ffffff", "#00aaff", "#050a1a", "#0a1525"),
]

PALETTE_NAMES = ["Neon Night", "Vaporwave", "Matrix", "Amber CRT", "ICE ICE BABY"]

CYAN, MAGENTA, GREEN, RED, BG, PANEL = (
    "#00fff0", "#ff00ff", "#00ff41", "#ff0040", "#0a0a0f", "#12121a"
)

# ─── CodeBurn-inspired palette ─────────────────────────────────────────────
# Accent/secondary colors borrowed from CodeBurn TUI dashboard
# (redefines DIM from CodeBurn's '#555555')
DIM = "#666666"

# CodeBurn overview/panel highlight colors
CB_ORANGE = "#FF8C42"   #  primary accent
CB_GOLD   = "#FFD700"   #  totals / key numbers
CB_GREEN  = "#5BF58C"   #  healthy / success
CB_BLUE   = "#5B9EF5"   #  info / sessions
CB_RED    = "#F55B5B"   #  errors / over-limit
CB_MAGENTA= "#E05BF5"   #  models / special
CB_CYAN2  = "#5BF5E0"   #  tools / MCP secondary
CB_PURPLE = "#F55BE0"   #  mcp / distinct category
CB_AMBER  = "#F5A05B"   #  bash / system

# Per-pane / per-category color mapping (panel headers, table accents)
PANE_COLORS = {
    "status":   CB_ORANGE,
    "sessions": CB_BLUE,
    "model":    CB_MAGENTA,
    "config":   CB_GREEN,
    "skills":   CB_GREEN,
    "tools":    CB_CYAN2,
    "cron":     CB_AMBER,
    "logs":     DIM,
    "analytics": CB_PURPLE,
    "env":      CYAN,
    "commands": MAGENTA,
}

# Task / activity category colors (from CodeBurn CATEGORY_COLORS)
CATEGORY_COLORS = {
    "coding":           "#5B9EF5",   # blue
    "debugging":        "#F55B5B",   # red
    "feature":          "#5BF58C",   # green
    "refactoring":      "#F5E05B",   # yellow
    "testing":          "#E05BF5",   # magenta
    "exploration":      "#5BF5E0",   # cyan
    "planning":         "#7B9EF5",   # light blue
    "delegation":       "#F5C85B",   # gold
    "git":              "#CCCCCC",   # gray
    "build/deploy":     "#5BF5A0",   # light green
    "conversation":     "#888888",   # dim gray
    "brainstorming":    "#F55BE0",   # purple-pink
    "general":          "#666666",   # neutral
}

# Provider / model family colors (matches CodeBurn PROVIDER_COLORS)
PROVIDER_COLORS = {
    "claude":  "#FF8C42",   # orange
    "codex":   "#5BF5A0",   # green
    "cursor":  "#00B4D8",   # blue
    "opencode": "#A78BFA",  # purple
    "pi":      "#F472B6",  # pink
    "openai":  "#10a37f",  # official OpenAI green
    "anthropic": CB_ORANGE,
}


class CyberHeader(Static):
    version = reactive("")
    gateway_status = reactive("")
    session_count = reactive(0)
    model = reactive("")
    clock = reactive("")
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="cyber-header"):
            yield Label("", id="v")
            yield Label("", id="g")
            yield Label("", id="s")
            yield Label("", id="m")
            yield Label("", id="c")

    def watch_version(self, v): self._set("v", f"⟨ HERMES {v} ⟩")
    def watch_gateway_status(self, s):
        col = GREEN if s == "RUNNING" else RED
        self._set("g", f"[{col}]◉ {s}[/]")
    def watch_session_count(self, n):
        self._set("s", f"◉ SESSIONS: {n}")
    def watch_model(self, m):
        self._set("m", f"◉ MODEL: {m[:30]}")
    def watch_clock(self, t):
        self._set("c", f"[{CYAN}]◉ {t}[/]")

    def _set(self, eid: str, text: str) -> None:
        try:
            self.query_one(f"#{eid}", Label).update(text)
        except Exception:
            pass


class HomePane(Static):
    """HERMES home / splash screen — ASCII art, status snapshot, quick links."""

    def compose(self) -> ComposeResult:
        with Panel("⌨ HERMES HUD – Home", color=PANE_COLORS["status"]):
            yield Static(id="home-ascii")

    def on_mount(self) -> None:
        art = """[bold cyan]    .-----..-.         .-..-..-..-..-..-..-..-..-..-..-..-..-
    |.-.-.|\\            | { } { } { } { } { } { } { } { } { }
    |'-'-'|-.  .--.  .-|-. .-. .-. .-. .-. .-. .-. .-. .-. .-.
    .'   `-'  |  |  |  | | | | | | | | | | | | | | | | | | |
   .-.  .-.   '  `--'  `-' `-' `-' `-' `-' `-' `-' `-' `-'
   |  ||  |
   |  ||  |  [bold magenta]HERMES[/]  [dim]Project Manager[/]
   '--'--'  
[/]"""
        self.query_one("#home-ascii", Static).update(art)

        info = (
            "\n[bold]GitHub:[/]   https://github.com/GumbyEnder/hermes-tui-hud\n"
            "[bold]Profile:[/]  Frodo — Hermes Project Manager\n"
            "[bold]Palette:[/]  CodeBurn-inspired cyberpunk\n"
            "[bold]Keys:[/]     q=Quit  r=Refresh  /=Search  1-9/0=Tabs\n"
        )
        self.query_one("#home-ascii", Static).update(art + info)



class StatusPane(Static):
    def compose(self) -> ComposeResult:
        with Panel("Status", color=PANE_COLORS["status"]):
            with Vertical():
                for n in ("ver", "gw", "plat", "cfg", "env"):
                    yield Label("", id=f"st-{n}")

    def update_status(self, s: Status) -> None:
        self._upd("ver", f"Version       : {s.version}  ({s.release_date})")
        col = GREEN if s.gateway_running else RED
        st = "RUNNING" if s.gateway_running else "STOPPED"
        self._upd("gw", f"Gateway       : [{col}]{st}[/]  pid={s.gateway_pid or '-'}")
        plat = ", ".join(f"{n}={p.get('state','?')}" for n, p in s.gateway_platforms.items()) if s.gateway_platforms else "None"
        self._upd("plat", f"Platforms     : {plat}")
        self._upd("cfg", f"Config path   : {s.config_path}")
        self._upd("env", f"Environment   : {s.env_path}")

    def _upd(self, n: str, txt: str) -> None:
        try:
            self.query_one(f"#st-{n}", Label).update(txt)
        except Exception:
            pass


class SessionsPane(Static):
    def compose(self) -> ComposeResult:
        with Panel("Sessions", color=PANE_COLORS["sessions"]):
            with Vertical():
                yield Label("", id="sm")
                t = DataTable(id="st", zebra_stripes=True)
                t.add_columns("ID", "Model", "Plat", "In", "Out", "Cost", "Status", "Last Act", "Title")
                yield t
                yield Label("", id="sn")

    def update_sessions(self, sessions, total):
        t = self.query_one("#st", DataTable)
        t.clear()
        for s in sessions:
            cost = f"${s.estimated_cost_usd:.4f}" if s.estimated_cost_usd else "-"
            st = "ACTIVE" if s.is_active else "IDLE"
            col = GREEN if s.is_active else CYAN
            last = _short_rel_time(s.last_active) if s.last_active else "-"
            t.add_row(
                s.session_id[:12], s.model[:22], s.platform[:8],
                f"{s.input_tokens:>7,}", f"{s.output_tokens:>7,}", f"{cost:>9}",
                f"[{col}]{st}[/]", last, (s.title or "-")[:40],
            )
        self._upd("sm", f"Total: {total}  ·  showing {len(sessions)}")

    def update_search_results(self, results):
        t = self.query_one("#st", DataTable)
        t.clear()
        for r in results:
            t.add_row(
                r.session_id[:12], r.model[:22] if r.model else "-", "-",
                "-", "-", "-", f"[{MAGENTA}]MATCH[/]", r.snippet[:60],
            )
        self._upd("sm", f"Search: {len(results)}")

    def _upd(self, n, txt):
        try:
            self.query_one(f"#{n}", Label).update(txt)
        except Exception:
            pass


class ModelPane(Static):
    def compose(self) -> ComposeResult:
        with Panel("Model", color=PANE_COLORS["model"]):
            with ScrollableContainer():
                for n in ("name", "prov", "ctx", "maxo", "tools", "vision", "reason", "fam"):
                    yield Label("", id=f"md-{n}")

    def update_model(self, m: ModelInfo) -> None:
        self._upd("name", f"◉ Model   : {m.model}")
        self._upd("prov", f"◉ Provider: {m.provider}")
        self._upd("ctx", f"◉ Context : {m.effective_context_length:,d} (auto={m.auto_context_length} cfg={m.config_context_length})")
        self._upd("maxo", f"◉ Max out : {m.capabilities.max_output_tokens:,d}")
        c = m.capabilities
        yes, no = "[green]YES[/]", "[red]NO[/]"
        self._upd("tools", f"◉ Tools   : {yes if c.supports_tools else no}")
        self._upd("vision", f"◉ Vision  : {yes if c.supports_vision else no}")
        self._upd("reason", f"◉ Reason  : {yes if c.supports_reasoning else no}")
        self._upd("fam", f"◉ Family  : {c.model_family}")

    def _upd(self, n, txt):
        try:
            self.query_one(f"#md-{n}", Label).update(txt)
        except Exception:
            pass


class ConfigPane(Static):
    edit_mode = reactive(False)
    def compose(self) -> ComposeResult:
        # Display mode container
        with Panel("Config", color=PANE_COLORS["config"]):
            with Vertical(id="cfg-display"):
                yield RichLog(id="cl", wrap=True, markup=True, highlight=True)
            # Edit mode container (hidden by default)
            with Vertical(id="cfg-edit", classes="hidden"):
                yield TextArea(id="cfg-editor", language="yaml", show_line_numbers=True)

    def update_config(self, text: str) -> None:
        # If we're in edit mode, force back to display
        if self.edit_mode:
            self.edit_mode = False
        self._last_config_text = text or ""
        log = self.query_one("#cl", RichLog)
        log.clear()
        log.write(self._last_config_text)

    def get_editable_text(self) -> str:
        """Get current editor content for saving."""
        editor = self.query_one("#cfg-editor", TextArea)
        return editor.text




    def _watch_edit_mode(self, old: bool, new: bool) -> None:
        # Guard: don't run until widget is mounted and children exist
        if not self.is_mounted:
            return
        disp = self.query_one("#cfg-display", Vertical)
        edit = self.query_one("#cfg-edit", Vertical)
        disp.display = not new
        edit.display = new
        if new:
            # Enter edit mode — load current config into editor and give it focus
            editor = self.query_one("#cfg-editor", TextArea)
            editor.clear()
            editor.insert(self._last_config_text)
            editor.focus()
            self.app.notify("Editing config – Ctrl+S to save, Esc to cancel", timeout=3, anchor="bottom")
        else:
            # Exiting edit mode — clear editor and return focus to display
            editor = self.query_one("#cfg-editor", TextArea)
            editor.clear()
            editor.blur()

class SkillsPane(Static):
    BINDINGS = [Binding("t", "toggle_skill", "Toggle Skill")]
    def compose(self) -> ComposeResult:
        with Panel("Skills", color=PANE_COLORS["skills"]):
            with Vertical():
                t = DataTable(zebra_stripes=True, cursor_type="row")
                t.add_columns("Status", "Name", "Description")
                yield t

    def update_skills(self, skills: list[Skill]) -> None:
        t = self.query_one(DataTable)
        t.clear()
        for s in skills:
            st = "[green]ON[/]" if s.enabled else "[red]OFF[/]"
            t.add_row(st, s.name, (s.description or "-")[:60], key=s.name)

    def action_toggle_skill(self) -> None:
        """Toggle the currently selected skill in the skills tab."""
        table = self.query_one(DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx < 0:
            self.notify("No skill selected (use ↑↓ to pick)", severity="warning")
            return
        skill_name = table.get_row_at(row_idx)[1]
        status_cell = table.get_row_at(row_idx)[0]
        currently_on = status_cell.startswith("[green]")
        desired_state = not currently_on
        try:
            result = self.app.client.toggle_skill(skill_name, enabled=desired_state)
            new_state = result.get("enabled", desired_state)
            self.notify(f"Skill '{skill_name}' → {'ON' if new_state else 'OFF'}", timeout=3)
            try:
                new_label = "[green]ON[/]" if new_state else "[red]OFF[/]"
                table.update_cell(row_idx, 0, new_label)
            except Exception:
                pass
            self.app._do_refresh_skills()
        except Exception as exc:
            msg = str(exc)
            hint = f" ({exc.args[0][:60]})" if hasattr(exc, 'args') and exc.args else ""
            self.notify(f"Toggle failed: {msg}{hint}", severity="error", timeout=5)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Row selected — cursor_row already updates, no extra state needed."""
        pass


class ToolsPane(Static):
    BINDINGS = [Binding("t", "toggle_tool", "Toggle Tool")]
    def compose(self) -> ComposeResult:
        with Panel("Tools", color=PANE_COLORS["tools"]):
            with Vertical():
                t = DataTable(zebra_stripes=True)
                t.add_columns("Status", "Toolset", "Enabled", "Configured", "Tools")
                yield t

    def update_tools(self, toolsets: list[Toolset]) -> None:
        t = self.query_one(DataTable)
        t.clear()
        for ts in toolsets:
            if ts.configured and ts.enabled:
                st, en, cfg = "[green]OK[/]", "[green]ON[/]", "[green]OK[/]"
            elif ts.configured:
                st, en, cfg = "[magenta]ENABLED[/]", "[green]ON[/]", "[green]OK[/]"
            else:
                st, en, cfg = "[red]INACTIVE[/]", "[red]OFF[/]", "[red]NEEDS CFG[/]"
            tools_preview = ", ".join(ts.tools[:4])
            if len(ts.tools) > 4:
                tools_preview += f" +{len(ts.tools)-4}"
            t.add_row(st, ts.name[:20], en, cfg, tools_preview)


    def action_toggle_tool(self) -> None:
        """Toggle tool enabled state (not yet supported via API)."""
        table = self.query_one(DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx < 0:
            self.notify("No tool selected", severity="warning")
            return
        tool_name = table.get_row_at(row_idx)[1]
        self.notify(f"Tool '{tool_name}' toggle not supported yet (API endpoint missing)", severity="warning", timeout=5)

class CronPane(Static):
    BINDINGS = [Binding("t", "toggle_cron", "Toggle Cron Job")]
    def compose(self) -> ComposeResult:
        with Panel("Cron Jobs", color=PANE_COLORS["cron"]):
            with Vertical():
                t = DataTable(zebra_stripes=True)
                t.add_columns("Status", "JobID", "Name", "Schedule", "Last Run", "Status")
                yield t

    def update_cron(self, jobs: list[CronJob]) -> None:
        t = self.query_one(DataTable)
        t.clear()
        self.jobs = jobs
        for j in jobs:
            st = "[green]ON[/]" if j.enabled else "[red]OFF[/]"
            lr = (j.last_run or "-")[:19]
            ls = j.last_status or "-"
            col = GREEN if (j.last_status or "").lower() == "success" else RED if j.last_status else ""
            # Use schedule_display (human-friendly) if present, else fallback to raw schedule
            sched = j.schedule_display[:12] if j.schedule_display else (str(j.schedule)[:12] if j.schedule else "-")
            t.add_row(st, j.job_id[:12], j.name[:22], sched, lr, f"[{col}]{ls}[/]" if col else ls, key=j.job_id)


    def action_toggle_cron(self) -> None:
        """Toggle the enabled state of the selected cron job."""
        table = self.query_one(DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx < 0:
            self.notify("No cron job selected", severity="warning")
            return
        if not hasattr(self, 'jobs') or row_idx >= len(self.jobs):
            self.notify("Cron job data out of sync", severity="error")
            return
        job = self.jobs[row_idx]
        job_id = job.job_id
        desired_state = not job.enabled
        try:
            result = self.app.client.update_cron_job(job_id, enabled=desired_state)
            new_state = getattr(result, 'enabled', desired_state)
            self.notify(f"Cron job '{job.name[:30]}' → {'ON' if new_state else 'OFF'}", timeout=3)
            try:
                new_label = "[green]ON[/]" if new_state else "[red]OFF[/]"
                table.update_cell(row_idx, 0, new_label)
            except Exception:
                pass
            self.app._do_refresh_cron()
        except Exception as exc:
            msg = str(exc)
            hint = f" ({exc.args[0][:60]})" if hasattr(exc, 'args') and exc.args else ""
            self.notify(f"Cron toggle failed: {msg}{hint}", severity="error", timeout=5)

class LogsPane(Static):
    def compose(self) -> ComposeResult:
        with Panel("Logs", color=PANE_COLORS["logs"]):
            with Vertical():
                yield Label("Level: [cyan]INFO[/] [green]DEBUG[/] [yellow]WARN[/] [red]ERROR[/]", id="lh")
                yield RichLog(id="lv", wrap=True, markup=True, highlight=True)

    def append_log_line(self, line: str) -> None:
        log = self.query_one("#lv", RichLog)
        if "ERROR" in line or "FATAL" in line:
            log.write(f"[red]{line}[/]")
        elif "WARN" in line:
            log.write(f"[yellow]{line}[/]")
        elif "INFO" in line:
            log.write(f"[cyan]{line}[/]")
        elif "DEBUG" in line:
            log.write(f"[green dim]{line}[/]")
        else:
            log.write(line)

    def clear_logs(self) -> None:
        self.query_one("#lv", RichLog).clear()


class AnalyticsPane(Static):
    def compose(self) -> ComposeResult:
        with Vertical():
            # Totals panel
            with Panel("📊 Totals (7d)", color=CB_BLUE):
                yield Label("", id="totals")
            # Model breakdown panel
            with Panel("By Model", color=CB_MAGENTA):
                tm = DataTable(id="atm")
                tm.add_columns("Model", "In", "Out", "Cost")
                yield tm
            # Daily activity panel
            with Panel("Daily", color=CB_ORANGE):
                td = DataTable(id="atd")
                td.add_columns("Date", "In", "Out", "Sess", "Cost")
                yield td

    def update_analytics(self, a: UsageAnalytics) -> None:
        t = a.totals
        self._upd("totals",
            f"Totals ({a.period_days}d) – In: {t.get('input_tokens',0):,d}  "
            f"Out: {t.get('output_tokens',0):,d}  "
            f"Cost: ${t.get('estimated_cost',0):.2f}  Sessions: {t.get('sessions',0)}"
        )
        mt = self.query_one("#atm", DataTable); mt.clear()
        for m in a.by_model:
            mt.add_row(m.model[:28], f"{m.input_tokens:,d}", f"{m.output_tokens:,d}", f"${m.estimated_cost:.4f}")
        dt = self.query_one("#atd", DataTable); dt.clear()
        for d in a.daily[-14:]:
            dt.add_row(d.day, f"{d.input_tokens:,d}", f"{d.output_tokens:,d}", str(d.sessions), f"${d.estimated_cost:.4f}")

    def _upd(self, n, txt):
        try:
            self.query_one(f"#{n}", Label).update(txt)
        except Exception:
            pass


class EnvPane(Static):
    def compose(self) -> ComposeResult:
        with Panel("Environment", color=PANE_COLORS["env"]):
            with Vertical():
                t = DataTable(zebra_stripes=True)
                t.add_columns("Status", "Name", "Value", "Description")
                yield t

    def update_env(self, envs: list[EnvVar]) -> None:
        t = self.query_one(DataTable)
        t.clear()
        for e in envs:
            st = "[green]SET[/]" if e.is_set else "[gray]-[/]"
            val = "********" if e.is_password and e.is_set else (e.redacted_value or "-")
            desc = (e.description or "-")[:45]
            t.add_row(st, e.name[:20], val[:25], desc)


class CommandsPane(Static):
    """Display all keybindings in a sortable table."""
    def compose(self) -> ComposeResult:
        with Panel("Commands", color=PANE_COLORS["commands"]):
            with Vertical(id="cmd-container"):
                yield Label("⌨⟨ KEYBINDINGS ⟩", id="cmd-title")
                t = DataTable(zebra_stripes=True, id="cmd-table")
                t.add_columns("Key", "Action", "Description")
                yield t

    def on_mount(self) -> None:
        table = self.query_one("#cmd-table", DataTable)
        table.clear()
        for binding in self.app.BINDINGS:
            key = binding.key
            action = binding.action
            desc = binding.description or ""
            table.add_row(key, action, desc)


# ─── Main App ────────────────────────────────────────────────────────────


class CyberFooter(Footer):
    """Footer that displays current palette name alongside key hints."""
    palette_name: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        # Palette label on the left
        yield Label(f"PALETTE: {self.palette_name}", id="palette-label")
        # Include Footer's default key hints
        yield from super().compose()

    def watch_palette_name(self, name: str) -> None:
        try:
            self.query_one("#palette-label", Label).update(f"PALETTE: {name}")
        except NoMatches:
            pass  # Label not yet mounted; compose will set initial text


class HermesHUDApp(App):
    enable_mouse = False  # Disable mouse tracking to avoid ConPTY EIO crash on exit

    CSS = """
/* Palette variables — overridden via get_css_variables() */
$cyan: #00ffff;
$magenta: #ff00ff;
$green: #00ff00;
$red: #ff0000;
$bg: #000000;
$panel: #111111;


Screen { background: $bg; overflow: hidden; }

#cyber-header {
    dock: top;
    height: 3;
    background: $panel;
    border: solid $cyan;
    padding: 0 1; content-align: left middle;
}
#cyber-header Label { color: $cyan; text-style: bold; margin-right: 2; }

#tabs {
    height: 1fr;
    margin-top: 3;
    margin-bottom: 3;
    background: $bg;
}

TabPane {
    height: 1fr;
    background: $panel;
    padding: 1;
}
TabPane > * { height: 1fr; }
TabPane > Vertical > DataTable,
TabPane > DataTable { height: 1fr; }
TabPane > ScrollableContainer { height: 1fr; }
TabPane > Vertical > Label,
TabPane > Label { height: auto; }

DataTable {
    background: $panel;
    color: #e0e0e0;
}
DataTable > .datatable--cursor { background: $cyan; color: black; }
DataTable > .datatable--fixed { background: $panel; }
DataTable > .datatable--fixed-cursor { background: $cyan; color: black; }

Footer {
    dock: bottom;
    height: 3;
    background: $panel;
    color: $cyan;
}
#palette-label {
    color: $cyan;
    text-style: bold;
    dock: left;
    padding: 0 1;
}

#sm, #sn { color: #888; }
#lh { margin-bottom: 1; color: #666; }
#lv { height: 1fr; background: $panel; color: #e0e0e0; }
#cl { height: 1fr; background: $panel; color: #d0d0d0; }
#totals { color: $green; text-style: bold; margin-bottom: 1; }
#cfg-editor { height: 1fr; }
#cfg-display, #cfg-edit { height: 1fr; }
.hidden { display: none; }

#cmd-title {
    text-align: center;
    text-style: bold;
    margin: 1 0;
}
#cmd-container { height: 1fr; }
#cmd-table { height: 1fr; }
"""

    def _build_css(self) -> str:
        """Generate CSS string from current palette colors."""
        return f""""
    Screen {{ background: {BG}; overflow: hidden; }}

    #cyber-header {{
        dock: top;
        height: 3;
        background: {PANEL};
        border: solid {CYAN};
        padding: 0 1; content-align: left middle;
        }}
    #cyber-header Label {{ color: {CYAN}; text-style: bold; margin-right: 2; }}

    /* Main content area */
    #tabs {{
        height: 1fr;
        margin-top: 3;
        margin-bottom: 3;
        background: {BG};
    }}

    /* Ensure tab panes and children fill available space */
    TabPane {{
        height: 1fr;
        background: {PANEL};
        padding: 1;
    }}
    TabPane > * {{
        height: 1fr;
    }}
    TabPane > Vertical > DataTable,
    TabPane > DataTable {{
        height: 1fr;
    }}
    TabPane > ScrollableContainer {{
        height: 1fr;
    }}
    TabPane > Vertical > Label,
    TabPane > Label {{
        height: auto;
    }}

    /* DataTable styling (size controlled via parent) */
    DataTable {{
        background: {PANEL};
        color: #e0e0e0;
    }}
    DataTable > .datatable--cursor {{ background: {CYAN}; color: black; }}
    DataTable > .datatable--fixed {{ background: {PANEL}; }}
    DataTable > .datatable--fixed-cursor {{ background: {CYAN}; color: black; }}

    Footer {{
        dock: bottom;
        height: 3;
        background: {PANEL};
        color: {CYAN};
        }}
    #palette-label {{
        color: {CYAN};
        text-style: bold;
        dock: left;
        padding: 0 1;
    }}

    /* Misc */
    #sm, #sn {{ color: #888; }}
    #lh {{ margin-bottom: 1; color: #666; }}
    #lv {{ height: 1fr; background: {PANEL}; color: #e0e0e0; }}
    #cl {{ height: 1fr; background: {PANEL}; color: #d0d0d0; }}
    #totals {{ color: {GREEN}; text-style: bold; margin-bottom: 1; }}
    #cfg-editor {{ height: 1fr; }}
    #cfg-display, #cfg-edit {{ height: 1fr; }}
    .hidden {{ display: none; }}

    #cmd-title {{
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }}
    #cmd-container {{
        height: 1fr;
    }}
    #cmd-table {{
        height: 1fr;
    }}
    """



    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("/", "search", "Search"),
        *[Binding(str(i), f"tab_{i}", f"Tab {i}") for i in range(1, 10)],
        Binding("0", "tab_0", "Tab 0"),
        # Skills & Config
        Binding("e", "edit_config", "Edit Config"),
        Binding("ctrl+s", "save_config", "Save Config", priority=True),
        Binding("escape", "cancel_edit", "Cancel Edit"),
        Binding("ctrl+p", "cycle_palette", "Cycle Palette", priority=True),
    ]

    TITLE = "Hermes Agent HUD"
    SUB_TITLE = "[ Cyberpunk Console ]"

    def __init__(self, client: HermesDashboardClient) -> None:
        super().__init__()
        self.current_palette = 0
        self.client = client
        self._clock_timer = None
        self.search_mode = False
        self.search_query = ""
        self.sessions_offset = 0
        self.sessions_limit = 30
    def get_css_variables(self) -> dict:
        """Return CSS custom property values for current palette."""
        variables = super().get_css_variables()
        variables.update({
            "$cyan": CYAN,
            "$magenta": MAGENTA,
            "$green": GREEN,
            "$red": RED,
            "$bg": BG,
            "$panel": PANEL,
        })
        return variables

    def compose(self) -> ComposeResult:
        yield CyberHeader(id="cyber-header")
        with TabbedContent(id="tabs"):
            names = ["Home","Status","Sessions","Model","Config","Skills","Tools","Cron","Logs","Analytics","Env","Commands"]
            for i, name in enumerate(names):
                # Commands sits beyond the 10-numeric-slot limit; give it a unique non-numeric ID
                if name == "Commands":
                    tid = "commands-tab"
                else:
                    if i == 9:
                        tid = "tab_0"      # Analytics (10th tab) → numeric '0' slot
                    elif i < 9:
                        tid = f"tab_{i+1}" # Home..Tools → tab_1..tab_9
                    else:
                        tid = f"tab_{i}"   # Env (i=10) → tab_10 (no numeric binding, unique)
                pid = f"{name.lower()}-pane"
                with TabPane(name, id=tid):
                    match name:
                        case "Home":        yield HomePane(id=pid)
                        case "Status":      yield StatusPane(id=pid)
                        case "Sessions":    yield SessionsPane(id=pid)
                        case "Model":       yield ModelPane(id=pid)
                        case "Config":      yield ConfigPane(id=pid)
                        case "Skills":      yield SkillsPane(id=pid)
                        case "Tools":       yield ToolsPane(id=pid)
                        case "Cron":        yield CronPane(id=pid)
                        case "Logs":        yield LogsPane(id=pid)
                        case "Analytics":   yield AnalyticsPane(id=pid)
                        case "Env":         yield EnvPane(id=pid)
                        case "Commands":   yield CommandsPane(id="commands-pane")
        yield CyberFooter(id="cyber-footer")

    def on_mount(self) -> None:
        self._clock_timer = self.set_interval(1.0, self._tick)
        self.set_interval(30.0, self._auto_refresh)
        self._load_all()
        # Set initial palette name in footer
        try:
            self.query_one(CyberFooter).palette_name = PALETTE_NAMES[self.current_palette]
        except Exception:
            pass  # footer not mounted yet

    def on_unmount(self) -> None:
        if self._clock_timer:
            self._clock_timer.stop()

    def _tick(self) -> None:
        try:
            self.query_one(CyberHeader).clock = datetime.now().strftime("%H:%M:%S")
        except Exception:
            # Widget may not be mounted yet or already unmounted; ignore
            pass

    def _auto_refresh(self) -> None:
        self._load_status_sessions()

    def action_refresh(self) -> None:
        self._load_all()

    @work(exclusive=True, thread=True)
    def _load_all(self) -> None:
        self._do_refresh_status()
        self._do_refresh_sessions()
        self._do_refresh_model()
        self._do_refresh_config()
        self._do_refresh_skills()
        self._do_refresh_tools()
        self._do_refresh_cron()
        self._do_refresh_logs()
        self._do_refresh_analytics()
        self._do_refresh_env()

    @work(exclusive=True, thread=True)
    def _load_status_sessions(self) -> None:
        self._do_refresh_status()
        self._do_refresh_sessions()

    def _do_refresh_status(self) -> None:
        try:
            s = self.client.get_status()
            self.call_from_thread(self._update_status, s)
        except Exception:
            pass

    def _update_status(self, s: Status) -> None:
        h = self.query_one(CyberHeader)
        h.version = s.version
        h.gateway_status = "RUNNING" if s.gateway_running else "STOPPED"
        h.session_count = s.active_sessions
        h.model = next(iter(s.gateway_platforms.values()), {}).get("model", "unknown") if s.gateway_platforms else "unknown"
        self.query_one("#status-pane", StatusPane).update_status(s)

    def _do_refresh_sessions(self) -> None:
        try:
            sessions, total = self.client.list_sessions(self.sessions_limit, self.sessions_offset)
            self.call_from_thread(self._update_sessions, sessions, total)
        except Exception:
            pass

    def _update_sessions(self, sessions: list[HermesSession], total: int) -> None:
        self.query_one("#sessions-pane", SessionsPane).update_sessions(sessions, total)

    def _do_refresh_model(self) -> None:
        try:
            m = self.client.get_model_info()
            self.call_from_thread(self._update_model, m)
        except Exception:
            pass

    def _update_model(self, m: ModelInfo) -> None:
        self.query_one("#model-pane", ModelPane).update_model(m)

    def _do_refresh_config(self) -> None:
        try:
            txt = self.client.get_config_raw()
            self.call_from_thread(self._update_config, txt)
        except Exception:
            pass

    def _update_config(self, txt: str) -> None:
        self.query_one("#config-pane", ConfigPane).update_config(txt)

    def _do_refresh_skills(self) -> None:
        try:
            skills = self.client.list_skills()
            self.call_from_thread(self._update_skills, skills)
        except Exception:
            pass

    def _update_skills(self, skills: list[Skill]) -> None:
        self.query_one("#skills-pane", SkillsPane).update_skills(skills)

    def _do_refresh_tools(self) -> None:
        try:
            toolsets = self.client.list_toolsets()
            self.call_from_thread(self._update_tools, toolsets)
        except Exception:
            pass

    def _update_tools(self, toolsets: list[Toolset]) -> None:
        self.query_one("#tools-pane", ToolsPane).update_tools(toolsets)

    def _do_refresh_cron(self) -> None:
        try:
            jobs = self.client.list_cron_jobs()
            self.call_from_thread(self._update_cron, jobs)
        except Exception:
            pass

    def _update_cron(self, jobs: list[CronJob]) -> None:
        self.query_one("#cron-pane", CronPane).update_cron(jobs)

    def _do_refresh_logs(self) -> None:
        try:
            data = self.client.get_logs(file="agent", lines=50)
            lines = data.get("lines", [])
            self.call_from_thread(self._update_logs, lines)
        except Exception:
            pass

    def _update_logs(self, lines: list[str]) -> None:
        pane = self.query_one("#logs-pane", LogsPane)
        pane.clear_logs()
        for line in lines:
            pane.append_log_line(line)

    def _do_refresh_analytics(self) -> None:
        try:
            a = self.client.get_usage_analytics(30)
            self.call_from_thread(self._update_analytics, a)
        except Exception:
            pass

    def _update_analytics(self, a: UsageAnalytics) -> None:
        self.query_one("#analytics-pane", AnalyticsPane).update_analytics(a)

    def _do_refresh_env(self) -> None:
        try:
            envs = self.client.list_env_vars()
            self.call_from_thread(self._update_env, envs)
        except Exception:
            pass

    def _update_env(self, envs: list[EnvVar]) -> None:
        self.query_one("#env-pane", EnvPane).update_env(envs)

    # ── Actions ───────────────────────────────────────────────────────────

    def action_quit(self) -> None:
        self.exit()

    def action_search(self) -> None:
        if self.query_one(TabbedContent).active in ("tab_2", "tab_8"):
            self.search_mode = not self.search_mode
            self.notify("Type letters then ENTER · ESC to cancel" if self.search_mode else "Search off", timeout=2)

    # Skills & Config actions ────────────────────────────────────────────────


    def action_edit_config(self) -> None:
        """Enter config edit mode."""
        self.query_one("#config-pane", ConfigPane).edit_mode = True
        self.notify("Editing config – Ctrl+S to save, Esc to cancel", timeout=3)

    def action_save_config(self) -> None:
        """Save edited config."""
        pane = self.query_one("#config-pane", ConfigPane)
        if not pane.edit_mode:
            return
        new_yaml = pane.get_editable_text()
        try:
            self.client.update_config_raw(new_yaml)
            self.app.notify("Config saved successfully", timeout=2, anchor="bottom")
            # Update display immediately with new config text
            pane.update_config(new_yaml)
            pane.edit_mode = False
            # Also refresh in background to ensure consistency
            self._do_refresh_config()
        except Exception as exc:
            self.notify(f"Save failed: {exc}", severity="error")

    def action_cancel_edit(self) -> None:
        """Exit edit mode without saving."""
        pane = self.query_one("#config-pane", ConfigPane)
        pane.edit_mode = False
        self.notify("Edit cancelled", timeout=1)


    async def on_key(self, event) -> None:
        if self.search_mode and event.key.isprintable() and len(event.key) == 1:
            self.search_query += event.key
            self.notify(f"Search: {self.search_query}", timeout=2)
        elif self.search_mode and event.key == "enter":
            self.search_mode = False
            # TODO: implement actual search call here
            self.notify(f"Search '{self.search_query}' – not implemented yet", timeout=3)
            self.search_query = ""
        elif self.search_mode and event.key == "escape":
            self.search_mode = False
            self.notify("Search cancelled", timeout=1)
        elif event.key == "escape" and self.query_one(ConfigPane).edit_mode:
            self.action_cancel_edit()


    def action_cycle_palette(self) -> None:
        """Cycle to next cyberpunk palette."""
        global CYAN, MAGENTA, GREEN, RED, BG, PANEL
        self.current_palette = (self.current_palette + 1) % len(PALETTES)
        CYAN, MAGENTA, GREEN, RED, BG, PANEL = PALETTES[self.current_palette]
        # Update footer palette name
        try:
            self.query_one(CyberFooter).palette_name = PALETTE_NAMES[self.current_palette]
        except Exception:
            pass  # footer not mounted yet
        # Rebuild CSS with new colors

        self.refresh_css()
        self.notify(f"Palette: {PALETTE_NAMES[self.current_palette]}", timeout=1.5)

    def action_tab_1(self): self._set_active("tab_1")
    def action_tab_2(self): self._set_active("tab_2")
    def action_tab_3(self): self._set_active("tab_3")
    def action_tab_4(self): self._set_active("tab_4")
    def action_tab_5(self): self._set_active("tab_5")
    def action_tab_6(self): self._set_active("tab_6")
    def action_tab_7(self): self._set_active("tab_7")
    def action_tab_8(self): self._set_active("tab_8")
    def action_tab_9(self): self._set_active("tab_9")
    def action_tab_0(self): self._set_active("tab_0")

    def _set_active(self, tid: str) -> None:
        self.query_one(TabbedContent).active = tid

    @on(TabbedContent.TabActivated)
    def on_tab_activated(self, event):
        tid = event.tab.id
        if tid == "tab_2":
            self._load_status_sessions()
        elif tid == "tab_8":
            self._do_refresh_logs()


def run_app(args) -> None:
    """Launch the TUI HUD."""
    try:
        from textual.app import App  # noqa: F401
    except ImportError:
        import sys
        print("ERROR: textual is required. Install with: pip install textual", file=sys.stderr)
        raise SystemExit(1)

    from .client.api import HermesDashboardClient

    client = HermesDashboardClient(base_url=args.base_url, timeout=args.timeout)

    try:
        status = client.get_status()
    except Exception as exc:
        import sys
        print(f"ERROR: Cannot reach Hermes dashboard: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Connected to Hermes {status.version} (gateway {'running' if status.gateway_running else 'stopped'})")
    print("Launching TUI HUD…")
    app = HermesHUDApp(client)
    try:
        app.run()
    except OSError as e:
        # Suppress EIO crashes when terminal PTY is closed during shutdown
        # (ConPTY mouse-tracking flush issue on Windows / WSL; also seen on Linux when
        # the terminal emulator exits before the TUI restores terminal state)
        if e.errno != errno.EIO:
            raise
