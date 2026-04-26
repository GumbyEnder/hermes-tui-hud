"""Bordered panel with colored title bar — inherits from Vertical for auto-layout."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class Panel(Vertical):
    """A bordered vertical container with a colored title bar.

    Children yielded inside ``with Panel(...)`` appear below the title,
    stacked vertically.
    """

    def __init__(
        self,
        title: str | None = None,
        color: str = "#FF8C42",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.title = title
        self.panel_color = color
        self._title_widget: Static | None = None

    def compose(self) -> ComposeResult:
        if self.title:
            title_widget = Static(self.title, classes="panel-title")
            self._title_widget = title_widget
            yield title_widget
        # Children from the caller are automatically included because
        # we inherit from Vertical (they become part of this container).

    def on_mount(self) -> None:
        self.styles.border = ("round", self.panel_color)
        self.styles.padding = (0, 1)
        self.styles.background = "transparent"
        if self._title_widget:
            self._title_widget.styles.color = self.panel_color
            self._title_widget.styles.background = self.panel_color
            self._title_widget.styles.text_style = "bold"
            self._title_widget.styles.width = "100%"
            self._title_widget.styles.text_align = "center"
