"""
ThemeCache
==========
集中管理 CustomTkinter 主題相關顏色的計算與快取。

設計動機 (對應 plan.md「Theme Cache」章節)：
    - 原本每次 refresh_data_grid() 都會重新判斷 is_dark、重新組字串顏色。
    - 改為：只有在「主題切換 (Theme Changed)」時才呼叫 refresh() 重新計算一次，
      其餘畫面刷新 (Weight 修改、Filter 修改等) 一律直接讀取本物件的屬性，
      不再重新查詢 ctk.ThemeManager 或重新做條件判斷。

⚠️ 注意：本檔案不屬於 QML/.ui.qml 範疇，是純 Python/CustomTkinter 專案，
因此不套用 .ui.qml 的 Connections/onXxxx 相關規則。
"""

from __future__ import annotations

import customtkinter as ctk


class ThemeCache:
    """快取目前主題模式下，資料表格會用到的所有顏色。"""

    def __init__(self) -> None:
        # 給予安全的預設值，避免尚未呼叫 refresh() 前被存取時出錯
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
        """🚀 動態獲取 CustomTkinter 當前主題的顏色代碼，防範寫死色彩 (與原 App 邏輯相同)"""
        try:
            val = ctk.ThemeManager.theme[component][element]
            if isinstance(val, list):
                mode = ctk.get_appearance_mode().lower()
                return val[1] if mode == "dark" else val[0]
            return str(val)
        except Exception:
            return default

    def refresh(self) -> None:
        """在主題切換 (或程式啟動) 時呼叫，一次性重新計算所有顏色。"""
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
        """依照列的奇偶數回傳交錯色 (Zebra Row)。"""
        return self.row_odd_bg if row_idx % 2 == 0 else self.row_even_bg
