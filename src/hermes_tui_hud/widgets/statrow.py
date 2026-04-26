from textual.app import ComposeResult
"""Key‑value row(s) with optional color highlighting — CodeBurn Overview style."""

from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static


class StatItem(Widget):
    """A single label→value pair with independent color control."""

    def __init__(
        self,
        label: str,
        value: str,
        *,
        value_color: str = "#e0e0e0",
        label_color: str = "#888888",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.label_text = label
        self.value_text = value
        self.value_color = value_color
        self.label_color = label_color

    def compose(self) -> ComposeResult:
        # Wrap label+value in a horizontal container; parent StatRow can also be Horizontal
        with Horizontal(classes="stat-item-inner"):
            lbl = Static(self.label_text, classes="stat-label")
            lbl.styles.color = self.label_color
            yield lbl
            val = Static(self.value_text, classes="stat-value")
            val.styles.color = self.value_color
            val.styles.text_style = "bold"
            yield val


class StatRow(Widget):
    """A horizontal row that stacks StatItem widgets."""

    def __init__(
        self,
        *items: StatItem,
        align: str = "center",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.items = items
        self.align = align

    def compose(self) -> ComposeResult:
        row = Horizontal(classes="stat-row")
        row.styles.align = (self.align, "center")
        row.styles.height = 1
        for item in self.items:
            yield item
