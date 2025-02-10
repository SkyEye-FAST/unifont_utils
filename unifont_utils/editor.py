# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Editor"""

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from .glyphs import Glyph, ReplacePattern, SearchPattern


class EditWidget(Static, can_focus=True):
    """Widget to display and edit a Glyph."""

    cursor_x = reactive(0)
    cursor_y = reactive(0)
    glyph: Glyph

    BINDINGS = [
        ("w,up", "move_up", "Up"),
        ("s,down", "move_down", "Down"),
        ("a,left", "move_left", "Left"),
        ("d,right", "move_right", "Right"),
        ("space", "toggle_glyph", "Toggle 0/1"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, glyph: Glyph) -> None:
        """Create a new EditWidget.

        Args:
            glyph (Glyph): The glyph to edit.
        """
        super().__init__()
        self.glyph = glyph

    def on_mount(self) -> None:
        """Actions that are executed when the widget is mounted."""
        self.render_glyph()
        self.focus()

    def watch_cursor_x(self) -> None:
        """Watch for changes to the `cursor_x` or `cursor_y` attribute."""
        self.render_glyph()

    watch_cursor_y = watch_cursor_x

    def render_glyph(self) -> None:
        """Render the glyph with the current cursor position."""

        def get_color(i: int) -> str:
            """Get color based on index."""
            return "auto" if i % 2 == 0 else ("green" if i > 9 else "red")

        def get_pixel_color(value: int) -> str:
            if value:
                return "white" if self.app.dark else "black"
            return "black" if self.app.dark else "white"

        def get_block_style(is_cursor: bool, data_value: int) -> str:
            """Get style for the glyph block."""
            pixel = get_pixel_color(data_value)
            return f"{'red' if is_cursor else pixel} on {pixel}"

        def get_nums(i: int) -> str:
            """Get the hexadecimal representation of index."""
            return hex(i)[2:].rjust(2).upper()

        width = self.glyph.width
        glyph = Text("\n  ")
        # Columns
        for i in range(width):
            glyph.append(get_nums(i), style=f"{get_color(i)} bold")
        glyph.append("\n")

        for i in range(16):
            # Rows
            glyph.append(f"{get_nums(i)} ", style=f"{get_color(i)} bold")
            # Glyph pixel blocks
            for j in range(width):
                is_cursor = self.cursor_x == j % width and self.cursor_y == i
                block_style = get_block_style(is_cursor, self.glyph.data[i * width + j])
                char = "⬥ " if is_cursor else "  "
                glyph.append(char, style=block_style)
            glyph.append("\n")

        position = Text(
            f"Position: ({self.cursor_x}, {self.cursor_y})",
            justify="center",
            style="bold",
        )
        panel = Panel(
            glyph,
            title=f"U+{self.glyph.code_point} ({self.glyph.character})",
            subtitle=position,
        )

        self.update(Group(Text(self.glyph.unicode_name, justify="center", style="bold"), panel))

    def _get_index(self) -> int:
        """Get the index of the current cursor position."""
        return self.cursor_y * self.glyph.width + self.cursor_x

    def _move_cursor(self, dx: int, dy: int) -> None:
        """Move cursor by the given offsets."""
        self.cursor_x = min(max(0, self.cursor_x + dx), self.glyph.width - 1)
        self.cursor_y = min(max(0, self.cursor_y + dy), 15)

    def action_move_up(self) -> None:
        """Move the cursor up."""
        self._move_cursor(0, -1)

    def action_move_down(self) -> None:
        """Move the cursor down."""
        self._move_cursor(0, 1)

    def action_move_left(self) -> None:
        """Move the cursor left."""
        self._move_cursor(-1, 0)

    def action_move_right(self) -> None:
        """Move the cursor right."""
        self._move_cursor(1, 0)

    def action_toggle_glyph(self) -> None:
        """Toggle the glyph's visibility."""
        index = self._get_index()
        self.glyph.update_data_at_index(index, int(not self.glyph.data[index]))
        self.render_glyph()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _handle_mouse_event(self, event, update_data: bool = False) -> None:
        """Handle mouse events for click and movement."""
        grid_x = (event.x - 5) // 2
        grid_y = event.y - 4

        if 0 <= grid_x < self.glyph.width and 0 <= grid_y < 16:
            self.cursor_x = grid_x
            self.cursor_y = grid_y

            index = self._get_index()
            if update_data:
                if event.button == 1 and not event.ctrl:
                    self.glyph.update_data_at_index(index, 1)
                elif event.button == 3 or (event.button == 1 and event.ctrl):
                    self.glyph.update_data_at_index(index, 0)

            self.render_glyph()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle mouse click events."""
        self._handle_mouse_event(event, update_data=True)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Handle mouse move events."""
        self._handle_mouse_event(event, update_data=bool(event.button))


class ReplaceWidget(Static, can_focus=True):
    """Widget to display and edit a Glyph."""

    match_index = reactive(0)
    matches = []
    glyph: Glyph

    BINDINGS = [
        ("a,left", "prev", "Previous"),
        ("d,right", "next", "Next"),
        ("space", "apply", "Apply"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        glyph: Glyph,
        search_pattern: SearchPattern,
        replace_pattern: ReplacePattern,
    ) -> None:
        """Create a new ReplaceWidget.

        Args:
            glyph (Glyph): The glyph to edit.
            search_pattern (SearchPattern): The search pattern to match.
            replace_pattern (ReplacePattern): The replace pattern to apply.
        """
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
            return "auto" if i % 2 == 0 else ("green" if i > 9 else "red")

        def get_pixel_color(value: int) -> str:
            if value == 1:
                return "white" if self.app.dark else "black"
            return "black" if self.app.dark else "white"

        def get_block_style(i: int, j: int, current_match: tuple[int, int]) -> str:
            width = self.glyph.width
            h = self.replace_pattern.height
            w = self.replace_pattern.width
            x, y = current_match

            if current_match and x <= i < x + h and y <= j < y + w:
                pixel = self.replace_pattern.data[(i - x) * w + (j - y)]
                pixel_color = get_pixel_color(pixel)
                if pixel == 1:
                    return "green on green"
                return f"{pixel_color} on {pixel_color}"
            pixel_color = get_pixel_color(self.glyph.data[i * width + j])
            return f"{pixel_color} on {pixel_color}"

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

        self.update(Group(Text(self.glyph.unicode_name, justify="center", style="bold"), panel))

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


class GlyphEditor(App):
    """Main application for editing a glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    BINDINGS = [("ctrl+d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(self, glyph: Glyph) -> None:
        """Create a new GlyphEditor.

        Args:
            glyph (Glyph): The glyph to edit.
        """
        super().__init__()
        self.glyph = glyph
        self.edit_widget = None

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        if self.edit_widget:
            self.edit_widget.render_glyph()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        self.edit_widget = EditWidget(self.glyph)
        yield self.edit_widget


class GlyphReplacer(App):
    """Main application for replacing patterns in a glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    BINDINGS = [("ctrl+d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(
        self,
        glyph: Glyph,
        search_pattern: SearchPattern,
        replace_pattern: ReplacePattern,
    ) -> None:
        """Create a new GlyphReplacer.

        Args:
            glyph (Glyph): The glyph to edit.
            search_pattern (SearchPattern): The search pattern to match.
            replace_pattern (ReplacePattern): The replace pattern to apply.
        """
        super().__init__()
        self.glyph = glyph
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern
        self.replace_widget = None

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        if self.replace_widget:
            self.replace_widget.render_glyph()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        self.replace_widget = ReplaceWidget(self.glyph, self.search_pattern, self.replace_pattern)
        yield self.replace_widget
