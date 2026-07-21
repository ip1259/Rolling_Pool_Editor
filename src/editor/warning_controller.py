"""Display validation warnings for editable rolling pools."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk


class WarningController:
    TARGET_TABLE_ID = "3000000"
    MIN_NON_ZERO_COUNT = 3

    def __init__(self, warning_label: ctk.CTkLabel, get_text: Callable[[str], str]) -> None:
        self._label = warning_label
        self._get_text = get_text

    def check(self, game_param_module: Any) -> None:
        target_id = self.TARGET_TABLE_ID
        table = game_param_module.EditableAttachEffectTable
        if target_id in table:
            non_zero_items = [
                item for item in table[target_id].values()
                if item.final_chance_weight != 0
            ]
            count = len(non_zero_items)
            if count < self.MIN_NON_ZERO_COUNT:
                warn_text = self._get_text("warn_3000000").format(count=count)
                self._label.configure(text=warn_text)
                self._label.grid()
                return
        self._label.grid_remove()
