"""Color badge / tag widget — compact categorical label with background."""

from textual.widgets import Static


class ColorBadge(Static):
    """A small rectangular badge showing a label with a background color.

    Example:
        ColorBadge("success", bg="#5BF58C", fg="black")
    """

    def __init__(
        self,
        label: str,
        *,
        bg: str = "#5BF58C",
        fg: str = "#000000",
        bold: bool = True,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(label, id=id, classes=classes)
        self.bg_color = bg
        self.fg_color = fg
        self.bold = bold

    def on_mount(self) -> None:
        self.styles.background = self.bg_color
        self.styles.color = self.fg_color
        if self.bold:
            self.styles.text_style = "bold"
        self.styles.margin = (0, 1)
        self.styles.padding = (0, 1)


class CategoryBadge(ColorBadge):
    """Badge that maps a task category to its CodeBurn color automatically."""

    # Category → color mapping from CodeBurn CATEGORY_COLORS
    _COLORS = {
        "coding": "#5B9EF5",
        "debugging": "#F55B5B",
        "feature": "#5BF58C",
        "refactoring": "#F5E05B",
        "testing": "#E05BF5",
        "exploration": "#5BF5E0",
        "planning": "#7B9EF5",
        "delegation": "#F5C85B",
        "git": "#CCCCCC",
        "build/deploy": "#5BF5A0",
        "conversation": "#888888",
        "brainstorming": "#F55BE0",
        "general": "#666666",
    }

    def __init__(self, category: str, **kwargs) -> None:
        color = self._COLORS.get(category.lower(), "#888888")
        super().__init__(category, bg=color, fg="#000000", **kwargs)
