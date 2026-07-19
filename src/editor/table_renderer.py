"""Pure Canvas renderer for the chance-weight table."""

from __future__ import annotations

from typing import List, Tuple

import tkinter as tk


_COLUMN_RATIOS = (0.12, 0.48, 0.14, 0.14, 0.12)


def _column_edges(width: int) -> List[int]:
    edges = [0]
    for ratio in _COLUMN_RATIOS[:-1]:
        edges.append(round(edges[-1] + width * ratio))
    edges.append(width)
    return edges


def edit_bounds(width: int) -> Tuple[int, int, int]:
    edges = _column_edges(width)
    left, right = edges[4], edges[5]
    return left, right - 36, right


def draw_header(canvas: tk.Canvas, headers: List[str], width: int, height: int, theme) -> None:
    edges = _column_edges(width)
    canvas.create_rectangle(0, 0, width, height,
                            fill=theme.header_bg, outline="")
    for index, header in enumerate(headers):
        left, right = edges[index], edges[index + 1]
        canvas.create_rectangle(left, 0, right, height,
                                outline=theme.row_even_bg)
        canvas.create_text(
            (left + right) // 2, height // 2, text=header, fill=theme.text_color,
            font=("Helvetica", 12, "bold"), width=max(right - left - 12, 1), justify="center",
        )


def draw_row(canvas: tk.Canvas, record, row_index: int, effect_name: str,
             chance_float: float, is_locked: bool, y: int, width: int,
             height: int, theme) -> None:
    edges = _column_edges(width)
    row_bg = theme.row_bg(row_index)
    final_bg = theme.locked_final_weight_bg if record.final_chance_weight == 0 else row_bg
    border = theme.row_even_bg if row_index % 2 == 0 else theme.row_odd_bg
    values = (
        (record.attachEffectId, row_bg, theme.text_color, "center"),
        (effect_name, row_bg, theme.text_color, "left"),
        (str(record.final_chance_weight), final_bg, theme.text_color, "center"),
        (f"{chance_float * 100:.2f}%", row_bg,
         theme.chance_text_color, "center"),
    )
    for index, (text, bg, color, anchor) in enumerate(values):
        left, right = edges[index], edges[index + 1]
        canvas.create_rectangle(
            left, y, right, y + height, fill=bg, outline=border, tags="row")
        canvas.create_text(
            left + 8 if anchor == "left" else (left + right) // 2,
            y + height // 2, text=text, fill=color, font=("Helvetica", 12),
            anchor="w" if anchor == "left" else "center", justify=anchor,
            width=max(right - left - 16, 1), tags="row",
        )

    left, save_left, right = edit_bounds(width)
    canvas.create_rectangle(left, y, right, y + height,
                            fill=row_bg, outline=border, tags="row")
    if is_locked:
        canvas.create_rectangle(left + 4, y + 10, save_left - 4, y + height - 10,
                                fill=theme.locked_entry_bg, outline="", tags="row")
    else:
        canvas.create_rectangle(left + 4, y + 10, save_left - 4, y + height - 10,
                                fill=theme.entry_default_bg, outline="", tags="row")
    button_bg = theme.save_btn_disabled_bg if is_locked else theme.save_btn_normal_bg
    canvas.create_rectangle(save_left + 2, y + 10, right - 4, y + height - 10,
                            fill=button_bg, outline="", tags="row")
    canvas.create_text((save_left + right) // 2, y + height // 2, text="✔",
                       fill=theme.text_color, font=("Helvetica", 11, "bold"), tags="row")
