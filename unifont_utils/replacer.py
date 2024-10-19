# -*- encoding: utf-8 -*-
"""Unifont Utils - Replacer"""

from typing import Tuple

from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

from .glyphs import Glyph, SearchPattern, ReplacePattern


class ReplaceWidget(Static, can_focus=True):
    """Widget to display and edit a Glyph."""

    match_index = reactive(0)
    matches = []
    glyph: Glyph

    BINDINGS = [
        ("a,left", "prev", "Previous Match"),
        ("d,right", "next", "Next Match"),
        ("space", "apply", "Apply"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        glyph: Glyph,
        search_pattern: SearchPattern,
        replace_pattern: ReplacePattern,
    ) -> None:
        super().__init__()
        self.glyph = glyph
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern
        self.matches = self.glyph.find_matches(search_pattern)

    def on_mount(self) -> None:
        """Actions that are executed when the widget is mounted."""
        self.render_glyph()
        self.focus()

    def watch_match_index(self) -> None:
        """Watch for changes to the `match_index` attribute."""
        self.render_glyph()

    def render_glyph(self) -> None:
        """Render the glyph with the current cursor position."""

        def get_color(i: int) -> str:
            """Get color based on index."""
            return "white" if i % 2 == 0 else ("green" if i > 9 else "red")

        def get_block_style(i: int, j: int, current_match: Tuple[int, int]) -> str:

            width = self.glyph.width
            h = self.replace_pattern.height
            w = self.replace_pattern.width
            x, y = current_match

            if current_match and x <= i < x + h and y <= j < y + w:
                pixel = self.replace_pattern.data[(i - x) * w + (j - y)]
                if pixel == 1:
                    return "green on green"
                return "black on black"
            return (
                "white on white"
                if self.glyph.data[i * width + j] == 1
                else "black on black"
            )

        def get_nums(i: int) -> str:
            """Get the hexadecimal representation of index."""
            return hex(i)[2:].rjust(2).upper()

        width = self.glyph.width
        glyph = Text("\n  ")
        # Columns
        for i in range(width):
            glyph.append(get_nums(i), style=f"{get_color(i)} bold")
        glyph.append("\n")

        current_match = self.matches[self.match_index]

        for i in range(16):
            # Rows
            glyph.append(f"{get_nums(i)} ", style=f"{get_color(i)} bold")
            for j in range(width):
                block_style = get_block_style(i, j, current_match)
                glyph.append("  ", style=block_style)
            glyph.append("\n")

        match_index_text = Text(
            f"Matches ({self.match_index + 1} / {len(self.matches)})",
            justify="center",
            style="bold",
        )
        panel = Panel(
            glyph,
            title=f"U+{self.glyph.code_point} ({self.glyph.character})",
            subtitle=match_index_text,
        )

        self.update(
            Group(Text(self.glyph.unicode_name, justify="center", style="bold"), panel)
        )

    def action_prev(self) -> None:
        """Move the cursor to the previous match."""
        if self.matches:
            self.match_index = (self.match_index - 1) % len(self.matches)

    def action_next(self) -> None:
        """Move the cursor to the next match."""
        if self.matches:
            self.match_index = (self.match_index + 1) % len(self.matches)

    def action_apply(self) -> None:
        """Apply the replacement to the glyph at the current match."""
        if self.matches:
            match_pos = self.matches[self.match_index]
            self.glyph.apply_pattern(match_pos[0], match_pos[1], self.replace_pattern)
            self.render_glyph()
        self.matches = self.glyph.find_matches(self.search_pattern)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class GlyphReplacer(App):
    """Main application for editing a glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    def __init__(
        self,
        glyph: Glyph,
        search_pattern: SearchPattern,
        replace_pattern: ReplacePattern,
    ) -> None:
        super().__init__()
        self.glyph = glyph
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ReplaceWidget(self.glyph, self.search_pattern, self.replace_pattern)
