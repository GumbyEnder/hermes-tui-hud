# Hermes TUI HUD
# Planning Outline

Date: 2026-04-15
Status: local planning document
Target repo: `https://github.com/GumbyEnder/hermes-tui-hud`

## Goal

Build a terminal-native Hermes operator console that carries over the strongest functional ideas from the dashboard work:

- agent/profile management
- session management
- gateway control
- cron/task control
- maintenance actions
- project and Kanban workflows
- notes and todos
- alerts and reporting
- memory inspection

This should not try to replicate the web dashboard visually. It should translate the same capabilities into terminal-native interaction patterns.

---

## 1. CLI Command Tree

The terminal product should have two layers:

- a command-oriented CLI for direct automation and scripting
- a full-screen TUI for interactive browsing and operations

The CLI should expose the same core objects the dashboard now works with.

### Top-Level Command Shape

```text
hermes-hud
  status
  alerts
  agents
  sessions
  gateway
  cron
  projects
  notes
  todos
  reports
  memory
  maintenance
  tui
```

### Command Tree

```text
hermes-hud status
  summary
  resources
  health

hermes-hud alerts
  list
  ack <id>
  ack-all

hermes-hud agents
  list
  show <profile>
  switch <profile>
  create <profile>
  clone <source> <target>
  delete <profile>
  config <profile>
  soul <profile>

hermes-hud sessions
  list [--profile <profile>] [--archived] [--pinned]
  show <session-id>
  rename <session-id> <title>
  export <session-id>
  pin <session-id>
  unpin <session-id>
  archive <session-id>
  unarchive <session-id>
  clear <session-id>
  delete <session-id>

hermes-hud gateway
  status [--profile <profile>]
  logs [--profile <profile>] [--lines <n>] [--follow]
  start [--profile <profile>]
  stop [--profile <profile>]
  restart [--profile <profile>]

hermes-hud cron
  list [--profile <profile>]
  add [--profile <profile>]
  run <job-id>
  pause <job-id>
  resume <job-id>
  delete <job-id>

hermes-hud projects
  list
  show <project-id>
  brief <project-id>
  kanban <project-id>
  add-card <project-id> <column>
  move-card <project-id> <card-id> <column>
  delete-card <project-id> <card-id>

hermes-hud notes
  show
  edit

hermes-hud todos
  list
  add
  done <todo-id>
  reopen <todo-id>
  delete <todo-id>

hermes-hud reports
  summary [--window 1h|24h|7d|30d]
  sessions [--window ...]
  costs [--window ...]
  models [--window ...]

hermes-hud memory
  summary
  entries
  search <query>
  providers

hermes-hud maintenance
  check-updates
  apply-update [webui|agent]
  cleanup-sessions
  cleanup-zero-message

hermes-hud tui
```

### CLI Design Principles

- Every TUI action should have a CLI equivalent where practical.
- Output should support:
  - human-readable tables by default
  - `--json` for scripting
- Actions should be profile-aware where needed.
- Dangerous actions should require confirmation unless `--yes` is passed.

---

## 2. Full-Screen TUI Layout

The TUI should be a real operator console, not a glorified menu tree.

Recommended stack:

- Python
- `textual` for the main TUI
- `$EDITOR` integration for config, soul, and notes editing

### Main Layout

```text
+--------------------------------------------------------------------------------+
| Hermes TUI HUD | Active: gollum | Model: ... | CPU ... | MEM ... | Alerts: 3 |
+----------------------+---------------------------------------------------------+
| Nav                  | Main Panel                                              |
|                      |                                                         |
| > Overview           | Selected view content                                  |
|   Agents             |                                                         |
|   Sessions           |                                                         |
|   Gateway            |                                                         |
|   Cron               |                                                         |
|   Projects           |                                                         |
|   Notes              |                                                         |
|   Todos              |                                                         |
|   Reports            |                                                         |
|   Memory             |                                                         |
|   Maintenance        |                                                         |
|                                                         +---------------------+
|                                                         | Context / Detail    |
|                                                         | selected item info  |
|                                                         | actions / help      |
+--------------------------------------------------------------------------------+
| Command: / filter | Hotkeys | status messages                                  |
+--------------------------------------------------------------------------------+
```

### Views

#### Overview

- top-line resources
- active profile
- recent alerts
- gateway state
- active cron count
- session count

#### Agents

- left list of profiles
- center tabbed content:
  - Overview
  - Sessions
  - Config
  - Cron
  - Gateway
- right detail/actions panel

#### Sessions

- searchable session list
- message/session metadata preview
- action shortcuts:
  - rename
  - pin
  - archive
  - export
  - delete

#### Gateway

- status indicators
- latest logs
- action buttons:
  - start
  - stop
  - restart
- follow-log mode

#### Cron

- cron table
- enabled/paused state
- last run / next run
- add/edit/run/pause/delete actions

#### Projects

- project list
- project brief viewer
- three-column Kanban board:
  - Todo
  - In Progress
  - Done
- quick add/move/delete card flow

#### Notes

- note preview
- edit in external editor or inline editor mode

#### Todos

- compact task list
- add / complete / reopen / delete

#### Reports

- time window switcher:
  - 1H
  - 24H
  - 7D
  - 30D
- headline stats
- sparklines / ASCII bars
- top models / top sessions / cost snapshots

#### Memory

- current Hermes memory summary
- search
- provider list
- future-ready provider breakdown

#### Maintenance

- update check
- update apply
- cleanup actions
- environment sanity info

### Interaction Model

- `j/k` or arrow keys for list movement
- `enter` to open/select
- `/` for search/filter
- `tab` / `shift+tab` for panel focus
- `g` then key for global navigation
- `:` for command entry
- `e` to edit file-backed content
- `r` to refresh current view

### TUI Design Principles

- one obvious focus target at a time
- all operator-critical actions visible without deep nesting
- readable in SSH over average terminals
- no dependency on mouse input

---

## 3. Phased Build Plan

Build this in layers so the terminal interface is useful early and doesn’t depend on finishing the entire TUI shell first.

### Phase 1: Core CLI Foundation

Deliver:

- repo scaffolding
- Python package structure
- command runner
- shared backend client layer
- `status`, `agents list`, `sessions list`, `gateway status`, `reports summary`

Why first:

- gives immediate scripting value
- establishes backend contract surface
- creates reusable service layer for later TUI work

Success criteria:

- CLI can read real Hermes data
- profile-aware commands work
- JSON output mode works

### Phase 2: Minimal TUI Shell

Deliver:

- Textual app shell
- nav rail
- top status bar
- command/footer bar
- working views for:
  - Overview
  - Agents
  - Sessions

Why:

- creates the real interaction model early
- covers the highest-value daily operator flows

Success criteria:

- can launch `hermes-hud tui`
- navigate between views
- inspect agents and sessions without crashes

### Phase 3: Agent Operations Parity

Deliver:

- agent profile switch/create/clone/delete
- per-agent config viewer/editor
- per-agent sessions actions
- gateway status/logs/actions
- cron list/add/run/pause/resume/delete

Why:

- this is the biggest dashboard-to-terminal value transfer

Success criteria:

- terminal can replace the web dashboard for routine agent ops

### Phase 4: Projects / Notes / Todos

Deliver:

- projects list/detail
- briefs viewer
- Kanban board
- notes editor
- todos workflow

Why:

- moves from pure ops into day-to-day operator workflow

Success criteria:

- project context and execution tracking are usable entirely in terminal

### Phase 5: Reporting / Alerts / Maintenance

Deliver:

- report windows
- ASCII trend views
- alert center
- update and cleanup actions

Why:

- rounds out the operator console

Success criteria:

- TUI supports both active operations and historical awareness

### Phase 6: Memory Provider Layer

Deliver:

- Hermes native memory inspection
- provider abstraction
- Honcho adapter
- future external memory adapters
- merged reporting with provider attribution

Why:

- this is strategically important but should not block core ops work

Success criteria:

- multiple memory systems can be viewed through one terminal UX
- provider-specific and merged stats are both available

---

## Recommended Technical Architecture

### Language / Framework

- Python
- `textual` for TUI
- `rich` for CLI tables and formatting
- `typer` or `click` for command tree

### Internal Modules

```text
hermes_tui_hud/
  app.py
  cli.py
  client/
    api.py
    models.py
  views/
    overview.py
    agents.py
    sessions.py
    gateway.py
    cron.py
    projects.py
    notes.py
    todos.py
    reports.py
    memory.py
    maintenance.py
  widgets/
    status_bar.py
    nav.py
    detail_panel.py
    tables.py
    sparklines.py
  services/
    agents.py
    sessions.py
    gateway.py
    cron.py
    projects.py
    notes.py
    reports.py
    memory.py
```

### Key Architectural Rule

Do not bind the TUI directly to raw API calls in widget code.

Instead:

- API client
- service layer
- view models
- TUI widgets

That will let the CLI and TUI share the same underlying logic.

---

## Suggested Immediate Next Move

Start with:

1. repo scaffold
2. shared backend client
3. CLI command tree skeleton
4. minimal TUI shell with `Overview`, `Agents`, and `Sessions`

That is the shortest path to something real and testable.
