"""Build and manage the collapsible effect-filter tree."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set

import customtkinter as ctk


class FilterController:
    def __init__(self, parent_frame: ctk.CTkBaseClass, game_param_module: Any,
                 game_text_module: Any, on_change: Callable[[], None]) -> None:
        self._parent_frame = parent_frame
        self._game_param = game_param_module
        self._game_text = game_text_module
        self._on_change = on_change
        self._block_filter_event = False

        self.sub_cat_vars: Dict[str, ctk.BooleanVar] = {}
        self.filter_vars: Dict[str, ctk.BooleanVar] = {}
        self.filter_to_sub_map: Dict[str, str] = {}
        self.sub_to_filters_map: Dict[str, List[str]] = {}
        self.collapsed_categories: Set[str] = set()
        self._category_frames: Dict[str, ctk.CTkFrame] = {}
        self._category_buttons: Dict[str, ctk.CTkButton] = {}
        self._category_titles: Dict[str, str] = {}

    def build_tree(self) -> None:
        """Rebuild the tree while preserving selected filters and collapsed groups."""
        selected_filters = self.get_active_filter_ids()
        for widget in self._parent_frame.winfo_children():
            widget.destroy()

        self.sub_cat_vars.clear()
        self.filter_vars.clear()
        self.filter_to_sub_map.clear()
        self.sub_to_filters_map.clear()
        self._category_frames.clear()
        self._category_buttons.clear()
        self._category_titles.clear()

        category_to_subs: Dict[str, List[str]] = {}
        for sub_id, sub_param in self._game_param.AttachEffectFilterSubCategory.items():
            category_to_subs.setdefault(sub_param.filterCategory, []).append(sub_id)

        for filter_id, filter_param in self._game_param.AttachEffectFilter.items():
            sub_id = filter_param.attachEffectFilterCategory
            self.sub_to_filters_map.setdefault(sub_id, []).append(filter_id)
            self.filter_to_sub_map[filter_id] = sub_id

        row = 0
        for category_id, category_param in self._game_param.AttachEffectFilterCategory.items():
            title = self._game_text.Menu[category_param.textId]
            self._category_titles[category_id] = title
            category_button = ctk.CTkButton(
                self._parent_frame, text="", font=("Helvetica", 13, "bold"), anchor="w",
                height=28, fg_color="transparent", hover_color=("#E5E7EB", "#374151"),
                text_color="#337AB7", command=lambda c=category_id: self._toggle_category(c),
            )
            category_button.grid(row=row, column=0, sticky="ew", padx=2, pady=(8, 2))
            self._category_buttons[category_id] = category_button
            self._update_category_button(category_id)
            row += 1

            content = ctk.CTkFrame(self._parent_frame, fg_color="transparent")
            content.grid(row=row, column=0, sticky="ew")
            content.grid_columnconfigure(0, weight=1)
            self._category_frames[category_id] = content
            row += 1

            content_row = 0
            for sub_id in category_to_subs.get(category_id, []):
                sub_param = self._game_param.AttachEffectFilterSubCategory[sub_id]
                filter_ids = self.sub_to_filters_map.get(sub_id, [])
                sub_var = ctk.BooleanVar(
                    value=bool(filter_ids) and all(filter_id in selected_filters for filter_id in filter_ids))
                self.sub_cat_vars[sub_id] = sub_var
                sub_checkbox = ctk.CTkCheckBox(
                    content, text=self._game_text.Menu[sub_param.textId],
                    font=("Helvetica", 12, "bold"), variable=sub_var,
                    command=lambda s=sub_id: self._on_sub_category_toggled(s),
                )
                sub_checkbox.grid(row=content_row, column=0, sticky="w", padx=20, pady=2)
                content_row += 1

                for filter_id in filter_ids:
                    filter_param = self._game_param.AttachEffectFilter[filter_id]
                    filter_var = ctk.BooleanVar(value=filter_id in selected_filters)
                    self.filter_vars[filter_id] = filter_var
                    filter_checkbox = ctk.CTkCheckBox(
                        content, text=self._game_text.AttachEffect[filter_param.filterTextId],
                        font=("Helvetica", 11), variable=filter_var,
                        command=lambda f=filter_id: self._on_filter_toggled(f),
                    )
                    filter_checkbox.grid(row=content_row, column=0, sticky="w", padx=40, pady=1)
                    content_row += 1

            if category_id in self.collapsed_categories:
                content.grid_remove()

    def _toggle_category(self, category_id: str) -> None:
        if category_id in self.collapsed_categories:
            self.collapsed_categories.remove(category_id)
            self._category_frames[category_id].grid()
        else:
            self.collapsed_categories.add(category_id)
            self._category_frames[category_id].grid_remove()
        self._update_category_button(category_id)

    def _update_category_button(self, category_id: str) -> None:
        icon = "▶" if category_id in self.collapsed_categories else "▼"
        self._category_buttons[category_id].configure(
            text=f"{icon} {self._category_titles[category_id]}")

    def _on_sub_category_toggled(self, sub_id: str) -> None:
        if self._block_filter_event:
            return
        self._block_filter_event = True
        selected = self.sub_cat_vars[sub_id].get()
        for filter_id in self.sub_to_filters_map.get(sub_id, []):
            self.filter_vars[filter_id].set(selected)
        self._block_filter_event = False
        self._on_change()

    def _on_filter_toggled(self, filter_id: str) -> None:
        if self._block_filter_event:
            return
        sub_id = self.filter_to_sub_map.get(filter_id)
        if not sub_id:
            return
        self._block_filter_event = True
        sibling_ids = self.sub_to_filters_map.get(sub_id, [])
        self.sub_cat_vars[sub_id].set(all(self.filter_vars[f_id].get() for f_id in sibling_ids))
        self._block_filter_event = False
        self._on_change()

    def get_active_filter_ids(self) -> Set[str]:
        return {filter_id for filter_id, var in self.filter_vars.items() if var.get()}
