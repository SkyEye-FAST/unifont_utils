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

from .base import Validator
from .glyphs import Glyph, ReplacePattern, SearchPattern


def is_app_dark(app: App) -> bool:
    """Return True if the given Textual `App` uses a dark theme.

    Args:
        app (App): Running Textual application.

    Returns:
        bool: True for dark theme, False otherwise.
    """
    theme = app.get_theme(app.theme)
    return bool(theme.dark) if theme else False


def _hex_index(index: int) -> str:
    """Return a two-character uppercase hexadecimal string for an index.

    Args:
        index (int): The numeric index to convert (e.g. column or row index).

    Returns:
        str: Two-character, zero-padded, uppercase hexadecimal representation.
    """
    return hex(index)[2:].rjust(2).upper()


def _color_by_index(index: int) -> str:
    """Return a color name for a header index.

    Args:
        index (int): Header index.

    Returns:
        str: Color name for styling.
    """
    return "auto" if index % 2 == 0 else ("green" if index > 9 else "red")


def _pixel_color(value: int, dark_theme: bool) -> str:
    """Return 'white' or 'black' for a pixel to contrast the theme.

    Args:
        value (int): Pixel value (0 or 1).
        dark_theme (bool): True when theme is dark.

    Returns:
        str: Chosen color name.
    """
    if value:
        return "white" if dark_theme else "black"
    return "black" if dark_theme else "white"


class EditWidget(Static, can_focus=True):
    """Focusable widget for viewing and editing a single `Glyph`.

    Attributes:
        cursor_x (int): Current cursor column (reactive).
        cursor_y (int): Current cursor row (reactive).
        glyph (Glyph): Glyph being edited.
    """

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
        """Initialize widget: render glyph and set focus."""
        self.render_glyph()
        self.focus()

    def watch_cursor_x(self) -> None:
        """Re-render when cursor position changes."""
        self.render_glyph()

    watch_cursor_y = watch_cursor_x

    def render_glyph(self) -> None:
        """Render the glyph grid, headers, and cursor state into the widget."""
        dark_theme = is_app_dark(self.app)
        width = self.glyph.width
        glyph = Text("\n  ")

        for col in range(width):
            glyph.append(_hex_index(col), style=f"{_color_by_index(col)} bold")
        glyph.append("\n")

        for row in range(16):
            glyph.append(f"{_hex_index(row)} ", style=f"{_color_by_index(row)} bold")
            for col in range(width):
                cursor_selected = self.cursor_x == col % width and self.cursor_y == row
                pixel_value = self.glyph.data[row * width + col]
                pixel_color = _pixel_color(pixel_value, dark_theme)
                block_foreground = "red" if cursor_selected else pixel_color
                glyph.append(
                    "⬥ " if cursor_selected else "  ", style=f"{block_foreground} on {pixel_color}"
                )
            glyph.append("\n")

        position = Text(
            f"Position: ({self.cursor_x}, {self.cursor_y})",
            justify="center",
            style="bold",
        )
        display_cp = Validator.code_point_display(self.glyph.code_point)
        panel = Panel(
            glyph,
            title=f"U+{display_cp} ({self.glyph.character})",
            subtitle=position,
        )

        self.update(Group(Text(self.glyph.unicode_name, justify="center", style="bold"), panel))

    def _get_index(self) -> int:
        """Return linear index into `glyph.data` for current cursor."""
        return self.cursor_y * self.glyph.width + self.cursor_x

    def _move_cursor(self, dx: int, dy: int) -> None:
        """Move cursor by (dx, dy), clamped to glyph bounds."""
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
        """Flip the pixel under the cursor and re-render."""
        index = self._get_index()
        self.glyph.update_data_at_index(index, int(not self.glyph.data[index]))
        self.render_glyph()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _handle_mouse_event(self, event, update_data: bool = False) -> None:
        """Handle mouse interactions; update cursor and optionally pixel data.

        Args:
            event: Textual mouse event with `x`, `y`, `button`, `ctrl`.
            update_data (bool): Write pixel changes when True.
        """
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
    """Widget to preview and apply replace patterns on a `Glyph`.

    Attributes:
        match_index (int): Selected match index (reactive).
        matches (list): Match positions in the glyph.
        glyph (Glyph): Glyph under inspection.
    """

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
            replace_pattern (ReplacePattern): The replacement pattern to apply.
        """
        super().__init__()
        self.glyph = glyph
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern
        self.matches = self.glyph.find_matches(search_pattern)

    def on_mount(self) -> None:
        """Render the glyph and request focus."""
        self.render_glyph()
        self.focus()

    def watch_match_index(self) -> None:
        """Re-render when the selected match index changes."""
        self.render_glyph()

    def render_glyph(self) -> None:
        """Render glyph with match highlights and replacement preview."""
        dark_theme = is_app_dark(self.app)
        width = self.glyph.width
        glyph = Text("\n  ")

        for col in range(width):
            glyph.append(_hex_index(col), style=f"{_color_by_index(col)} bold")
        glyph.append("\n")

        current_match = self.matches[self.match_index] if self.matches else None
        repl_height = self.replace_pattern.height
        repl_width = self.replace_pattern.width

        for row in range(16):
            glyph.append(f"{_hex_index(row)} ", style=f"{_color_by_index(row)} bold")
            for col in range(width):
                pixel_color = _pixel_color(self.glyph.data[row * width + col], dark_theme)

                if current_match:
                    start_row, start_col = current_match
                    within_match = (
                        start_row <= row < start_row + repl_height
                        and start_col <= col < start_col + repl_width
                    )
                    if within_match:
                        repl_value = self.replace_pattern.data[
                            (row - start_row) * repl_width + (col - start_col)
                        ]
                        repl_color = _pixel_color(repl_value, dark_theme)
                        if repl_value:
                            glyph.append("  ", style="green on green")
                            continue
                        glyph.append("  ", style=f"{repl_color} on {repl_color}")
                        continue

                glyph.append("  ", style=f"{pixel_color} on {pixel_color}")
            glyph.append("\n")

        match_index_text = Text(
            f"Matches ({self.match_index + 1} / {len(self.matches)})",
            justify="center",
            style="bold",
        )
        display_cp = Validator.code_point_display(self.glyph.code_point)
        panel = Panel(
            glyph,
            title=f"U+{display_cp} ({self.glyph.character})",
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
        """Apply replacement at the selected match and refresh matches."""
        if self.matches:
            match_pos = self.matches[self.match_index]
            self.glyph.apply_pattern(match_pos[0], match_pos[1], self.replace_pattern)
            self.render_glyph()
        self.matches = self.glyph.find_matches(self.search_pattern)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class GlyphEditor(App):
    """Textual app that hosts an `EditWidget` for editing one glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    BINDINGS = [("ctrl+d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(self, glyph: Glyph) -> None:
        """Initialize the editor application.

        Args:
            glyph (Glyph): The glyph instance to be edited by the app.
        """
        super().__init__()
        self.glyph = glyph
        self.edit_widget = None

    def action_toggle_dark(self) -> None:
        """Toggle the theme and refresh the edit widget if mounted."""
        self.theme = "textual-light" if is_app_dark(self) else "textual-dark"
        if self.edit_widget:
            self.edit_widget.render_glyph()

    def compose(self) -> ComposeResult:
        """Compose and yield child widgets for the application UI.

        Yields a `Header`, `Footer`, and an `EditWidget` bound to the app's
        glyph.
        """
        yield Header()
        yield Footer()
        self.edit_widget = EditWidget(self.glyph)
        yield self.edit_widget


class GlyphReplacer(App):
    """Textual app that hosts a `ReplaceWidget` for applying patterns."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    BINDINGS = [("ctrl+d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(
        self,
        glyph: Glyph,
        search_pattern: SearchPattern,
        replace_pattern: ReplacePattern,
    ) -> None:
        """Initialize the replacer application.

        Args:
            glyph (Glyph): The glyph instance to search and modify.
            search_pattern (SearchPattern): Pattern used to locate matches.
            replace_pattern (ReplacePattern): Pattern used to replace matches.
        """
        super().__init__()
        self.glyph = glyph
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern
        self.replace_widget = None

    def action_toggle_dark(self) -> None:
        """Toggle theme and refresh the replace widget if mounted."""
        self.theme = "textual-light" if is_app_dark(self) else "textual-dark"
        if self.replace_widget:
            self.replace_widget.render_glyph()

    def compose(self) -> ComposeResult:
        """Compose and yield the header/footer and the replace widget.

        Yields a `Header`, `Footer`, and a `ReplaceWidget` instance.
        """
        yield Header()
        yield Footer()
        self.replace_widget = ReplaceWidget(self.glyph, self.search_pattern, self.replace_pattern)
        yield self.replace_widget
