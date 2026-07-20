"""Canvas-rendered virtual table with a single temporary editor."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, List, Optional, Tuple


class VirtualTable(tk.Frame):
    def __init__(
        self,
        master,
        *,
        row_height: int,
        draw_header: Callable[[tk.Canvas, List[str], int, int, object], None],
        draw_row: Callable[[tk.Canvas, int, int, int, int, object], None],
        edit_bounds: Callable[[int], Tuple[int, int, int, int]],
        header_column_at: Callable[[int, int], int],
        on_header_click: Callable[[int], None],
        can_edit: Callable[[int], bool],
        edit_value: Callable[[int], str],
        on_save: Callable[[int, str], None],
        on_zero: Callable[[int], None],
    ) -> None:
        super().__init__(master, bd=0, highlightthickness=0)
        self.row_height = row_height
        self.header_height = 40
        self._draw_header = draw_header
        self._draw_row = draw_row
        self._edit_bounds = edit_bounds
        self._header_column_at = header_column_at
        self._on_header_click = on_header_click
        self._can_edit = can_edit
        self._edit_value = edit_value
        self._on_save = on_save
        self._on_zero = on_zero
        self._headers: List[str] = []
        self._theme = None
        self._total_rows = 0
        self._editor: Optional[tk.Entry] = None
        self._editor_window: Optional[int] = None
        self._editing_index: Optional[int] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header_canvas = tk.Canvas(self, height=self.header_height, bd=0, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, sticky="ew")
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollincrement=row_height)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=16)
        self.vsb.grid(row=0, column=1, rowspan=2, sticky="ns")
        self.canvas.configure(yscrollcommand=self._on_yscroll)

        self.header_canvas.bind("<Configure>", lambda _event: self._redraw_header())
        self.header_canvas.bind("<Button-1>", self._on_header_clicked)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

    def set_theme(self, theme) -> None:
        self._theme = theme
        self.configure(bg=theme.row_bg(0))
        self.header_canvas.configure(bg=theme.header_bg)
        self.canvas.configure(bg=theme.row_bg(0))
        self.vsb.configure(troughcolor=theme.row_bg(0), highlightthickness=0, bd=0)
        self._redraw_header()
        self.request_refresh()

    def set_headers(self, headers: List[str]) -> None:
        self._headers = headers
        self._redraw_header()

    def set_row_count(self, total_rows: int) -> None:
        self._total_rows = total_rows
        self.canvas.configure(scrollregion=(0, 0, max(self.canvas.winfo_width(), 1), max(total_rows * self.row_height, 1)))
        self._close_editor()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self._theme is None:
            return
        self._redraw_header()
        self.canvas.delete("row")
        width = max(self.canvas.winfo_width(), 1)
        first, last = self._visible_range()
        for index in range(first, last + 1):
            self._draw_row(self.canvas, index, index * self.row_height, width, self.row_height, self._theme)

    def _redraw_header(self) -> None:
        if self._theme is None:
            return
        self.header_canvas.delete("all")
        self._draw_header(self.header_canvas, self._headers, max(self.header_canvas.winfo_width(), 1), self.header_height, self._theme)

    def _visible_range(self) -> Tuple[int, int]:
        if self._total_rows == 0:
            return 0, -1
        top, bottom = self.canvas.yview()
        first = max(0, int(top * self._total_rows) - 1)
        last = min(self._total_rows - 1, int(bottom * self._total_rows) + 1)
        return first, last

    def _on_canvas_configure(self, event) -> None:
        self.canvas.configure(scrollregion=(0, 0, event.width, max(self._total_rows * self.row_height, 1)))
        self.request_refresh()

    def _on_header_clicked(self, event) -> None:
        self._on_header_click(self._header_column_at(event.x, self.header_canvas.winfo_width()))

    def _on_yscroll(self, first, last) -> None:
        self.vsb.set(first, last)
        self.request_refresh()

    def _on_canvas_click(self, event) -> None:
        if self._theme is None:
            return
        index = int(self.canvas.canvasy(event.y) // self.row_height)
        if not 0 <= index < self._total_rows:
            return
        edit_left, save_left, zero_left, edit_right = self._edit_bounds(self.canvas.winfo_width())
        x = self.canvas.canvasx(event.x)
        if x < edit_left or x > edit_right:
            return
        if x >= zero_left and self._can_edit(index):
            self._close_editor()
            self._on_zero(index)
        elif x >= save_left and index == self._editing_index:
            self._save_editor()
        elif x < save_left and self._can_edit(index):
            self._show_editor(index, edit_left, save_left)

    def _show_editor(self, index: int, edit_left: int, save_left: int) -> None:
        self._close_editor()
        self._editing_index = index
        self._editor = tk.Entry(
            self.canvas, justify="center", font=("Helvetica", 12), relief="flat", bd=0,
            bg=self._theme.entry_default_bg, fg=self._theme.text_color,
            insertbackground=self._theme.text_color,
        )
        self._editor.bind("<Return>", lambda _event: self._save_editor())
        self._editor.bind("<Escape>", lambda _event: self._close_editor())
        self._editor.insert(0, self._edit_value(index))
        x = (edit_left + save_left) // 2
        y = index * self.row_height + self.row_height // 2
        self._editor_window = self.canvas.create_window(
            x, y, window=self._editor, width=max(save_left - edit_left - 8, 20), height=28, tags="editor")
        self._editor.focus_set()

    def _save_editor(self) -> None:
        if self._editor is None or self._editing_index is None:
            return
        self._on_save(self._editing_index, self._editor.get().strip())

    def _close_editor(self) -> None:
        if self._editor_window is not None:
            self.canvas.delete(self._editor_window)
        if self._editor is not None:
            self._editor.destroy()
        self._editor = None
        self._editor_window = None
        self._editing_index = None

    def _bind_mousewheel(self, _event=None) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, _event=None) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event) -> None:
        self._close_editor()
        self.canvas.yview_scroll((-1 if event.delta > 0 else 1) * 3, "units")

    def _on_mousewheel_linux(self, event) -> None:
        self._close_editor()
        self.canvas.yview_scroll(-3 if event.num == 4 else 3, "units")
