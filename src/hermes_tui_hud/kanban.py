"""
Kanban board parser for Hermes TUI HUD.

Loads kanban boards from the Obsidian vault, parses cards,
and provides status lookup for wiki backlink rendering.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, NamedTuple
from threading import RLock


class CardInfo(NamedTuple):
    id: str
    done: bool
    line: str
    column: str


class KanbanBoard:
    COLUMN_ORDER = ["backlog", "todo", "in progress", "review", "done"]

    def __init__(self, path: Path, vault_root: Path):
        self.path = path
        self.vault_root = vault_root
        self.name = path.stem
        self._cards: Dict[str, CardInfo] = {}
        self._last_mtime: float = 0.0
        self._lock = RLock()
        self._needs_reload: bool = True

    def _parse_column(self, line: str) -> Optional[str]:
        m = re.match(r'^##\s+(.+)', line.strip())
        if m:
            col = m.group(1).lower()
            col = re.sub(r'[^a-z ]', '', col).strip()
            return col
        return None

    def _parse_card(self, line: str, current_column: str) -> Optional[CardInfo]:
        m = re.match(r'^- \[(x| )\]\s+([A-Za-z0-9_.-]+)\s+—', line)
        if not m:
            return None
        status_char = m.group(1)
        card_id = m.group(2)
        done = (status_char == 'x')
        return CardInfo(id=card_id, done=done, line=line, column=current_column)

    def reload(self) -> None:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except Exception:
            return
        lines = raw.split('\n')
        cards: Dict[str, CardInfo] = {}
        current_column = "backlog"
        for line in lines:
            col = self._parse_column(line)
            if col:
                current_column = col
                continue
            card = self._parse_card(line, current_column)
            if card:
                cards[card.id] = card
        with self._lock:
            self._cards = cards
            self._last_mtime = self.path.stat().st_mtime

    def get_card_status(self, card_id: str) -> Optional[CardInfo]:
        with self._lock:
            return self._cards.get(card_id)

    def needs_reload(self) -> bool:
        try:
            mt = self.path.stat().st_mtime
            return mt > self._last_mtime
        except Exception:
            return False


class KanbanCache:
    def __init__(self, vault_root: Path = Path("/mnt/nas/Obsidian Vault")):
        self.vault_root = vault_root
        self.kanban_dir = vault_root / "Kanban"
        self._boards: Dict[str, KanbanBoard] = {}
        self._lock = RLock()
        self._last_scan: float = 0.0
        self.SCAN_INTERVAL = 300.0

    def _discover_boards(self) -> None:
        if not self.kanban_dir.exists():
            return
        now = time.time()
        if now - self._last_scan < self.SCAN_INTERVAL:
            try:
                dir_mtime = self.kanban_dir.stat().st_mtime
                if dir_mtime <= self._last_scan:
                    return
            except Exception:
                pass
        found: Dict[str, KanbanBoard] = {}
        for md_file in self.kanban_dir.glob("*.md"):
            board_name = md_file.stem
            if board_name in self._boards:
                found[board_name] = self._boards[board_name]
            else:
                board = KanbanBoard(md_file, self.vault_root)
                board.reload()
                found[board_name] = board
        with self._lock:
            self._boards = found
            self._last_scan = now

    def get_board(self, board_name: str) -> Optional[KanbanBoard]:
        self._discover_boards()
        with self._lock:
            if board_name in self._boards:
                return self._boards[board_name]
            low = board_name.lower()
            for name, board in self._boards.items():
                if low in name.lower() or name.lower() in low:
                    return board
        return None

    def get_card_status(self, board_name: str, card_id: str) -> Optional[CardInfo]:
        board = self.get_board(board_name)
        if board:
            if board.needs_reload():
                board.reload()
            return board.get_card_status(card_id)
        return None

    def refresh_all(self) -> None:
        with self._lock:
            for board in self._boards.values():
                board.reload()


_cache: Optional[KanbanCache] = None


def get_cache() -> KanbanCache:
    global _cache
    if _cache is None:
        _cache = KanbanCache()
    return _cache


def render_kanban_chip(card_info: CardInfo, board_name: str) -> str:
    if card_info.done:
        icon = "✓"
    else:
        icon = "◻"
    safe_board = urllib.parse.quote(board_name, safe="")
    link = f"kanban-open://{safe_board}/{card_info.id}"
    return f"[{icon} {card_info.id}]({link})"


def render_kanban_links(text: str, cache: Optional[KanbanCache] = None) -> str:
    if cache is None:
        cache = get_cache()
    pattern = re.compile(r'\[\[kanban:([^:\]]+):([^\]]+)\]\]')

    def replace(match):
        board_name = match.group(1).strip()
        card_id = match.group(2).strip()
        card_info = cache.get_card_status(board_name, card_id)
        if card_info:
            return render_kanban_chip(card_info, board_name)
        return f"[[? {card_id}]]"

    return pattern.sub(replace, text)


if __name__ == "__main__":
    cache = get_cache()
    test = "S1.1 [[kanban:Hermes Kanban — Sprint 1.5.0:S1.1]] and B1 [[kanban:Hermes Kanban — Sprint 1.5.0:B1]]"
    print(render_kanban_links(test, cache))
