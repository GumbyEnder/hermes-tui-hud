"""Horizontal bar chart / progress indicator — CodeBurn-inspired."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive


class HBar(Widget):
    """A horizontal bar used to visualize a value within a range.

    Args:
        value: Current value (0 – max).
        max: Maximum value for scaling (default 100).
        width: Bar length in character cells.
        color: Fill color (default gold).
        empty_color: Color of the unfilled portion.
        show_label: If True, show “value / max” to the right of the bar.

    Example:
        HBar(value=75, max=100, width=30, color="#FFD700")
    """

    value: reactive[float] = reactive(0.0)
    max: reactive[float] = reactive(100.0)
    width: reactive[int] = reactive(20)
    color: reactive[str] = reactive("#FFD700")
    empty_color: reactive[str] = reactive("#666666")
    show_label: reactive[bool] = reactive(False)

    class Changed(Message):
        """Posted when :attr:`value` changes."""

        def __init__(self, bar: "HBar") -> None:
            super().__init__()
            self.bar = bar

    def __init__(
        self,
        value: float = 0.0,
        max: float = 100.0,
        width: int = 20,
        color: str = "#FFD700",
        empty_color: str = "#666666",
        show_label: bool = False,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        # Clamp value to [0, max]
        self.value = max(0.0, min(value, max))
        self.max = max if max > 0 else 1.0
        self.width = max(1, width)
        self.color = color
        self.empty_color = empty_color
        self.show_label = show_label

    def render(self) -> str:
        if self.max == 0:
            ratio = 0.0
        else:
            ratio = self.value / self.max

        filled = int(round(ratio * self.width))
        empty = max(0, self.width - filled)

        # Build the bar: filled (█) + empty (░)
        bar_filled = "█" * filled
        bar_empty = "░" * empty
        from rich.text import Text

        text = Text()
        if filled:
            text.append(bar_filled, style=self.color)
        if empty:
            text.append(bar_empty, style=self.empty_color)
        if self.show_label:
            label = f" {self.value:.0f}/{self.max:.0f}"
            text.append(label, style=self.color)
        return text.plain

    def watch_value(self, old: float, new: float) -> None:
        self.post_message(self.Changed(self))
