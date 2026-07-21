"""Cache colors used by the CustomTkinter interface."""

from __future__ import annotations

import customtkinter as ctk


class ThemeCache:
    """快取目前主題模式下，資料表格會用到的所有顏色。"""

    def __init__(self) -> None:
        # Defaults keep the cache usable before the first theme refresh.
        self.is_dark: bool = True
        self.text_color: str = "#FFFFFF"
        self.header_bg: str = "#1F2937"
        self.row_odd_bg: str = "#202A36"
        self.row_even_bg: str = "#283544"
        self.locked_final_weight_bg: str = "#573333"
        self.locked_entry_bg: str = "#3A3F46"
        self.chance_text_color: str = "#63D5FF"
        self.save_btn_normal_bg: str = "#2563EB"
        self.save_btn_disabled_bg: str = "#4B5563"
        self.entry_default_bg: str = "#374151"

    def get_theme_color(self, component: str, element: str, default: str = "#FFFFFF") -> str:
        """Return a color from the active CustomTkinter theme."""
        try:
            val = ctk.ThemeManager.theme[component][element]
            if isinstance(val, list):
                mode = ctk.get_appearance_mode().lower()
                return val[1] if mode == "dark" else val[0]
            return str(val)
        except Exception:
            return default

    def refresh(self) -> None:
        """Refresh cached colors after startup or a theme change."""
        self.is_dark = (ctk.get_appearance_mode().lower() == "dark")
        is_dark = self.is_dark

        self.text_color = self.get_theme_color("CTkLabel", "text_color")
        self.header_bg = "#1F2937" if is_dark else "#DDE6F0"
        self.row_odd_bg = "#202A36" if is_dark else "#F8FAFC"
        self.row_even_bg = "#283544" if is_dark else "#EEF3F8"
        self.locked_final_weight_bg = "#573333" if is_dark else "#F9DADA"
        self.locked_entry_bg = "#3A3F46" if is_dark else "#E5E7EB"
        self.chance_text_color = "#63D5FF" if is_dark else "#0369A1"
        self.save_btn_normal_bg = "#2563EB"
        self.save_btn_disabled_bg = "#4B5563"
        self.entry_default_bg = "#374151" if is_dark else "#FFFFFF"

    def row_bg(self, row_idx: int) -> str:
        """Return the alternating background color for a row."""
        return self.row_odd_bg if row_idx % 2 == 0 else self.row_even_bg
