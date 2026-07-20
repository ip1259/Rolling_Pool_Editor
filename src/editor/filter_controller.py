"""Build and manage the collapsible effect-filter tree."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set

import customtkinter as ctk


class FilterController:
    def __init__(self, parent_frame: ctk.CTkBaseClass, game_param_module: Any,
                 game_text_module: Any, on_change: Callable[[], None],
                 initial_filters: Set[str] | None = None) -> None:
        self._parent_frame = parent_frame
        self._game_param = game_param_module
        self._game_text = game_text_module
        self._on_change = on_change
        self._block_filter_event = False
        self._initial_filters = set(initial_filters or ())

        # 新增：標記是否為首次建立，用來判定是否套用預設摺疊狀態
        self._is_first_build = True

        self.sub_cat_vars: Dict[str, ctk.BooleanVar] = {}
        self.filter_vars: Dict[str, ctk.BooleanVar] = {}
        self.filter_to_sub_map: Dict[str, str] = {}
        self.sub_to_filters_map: Dict[str, List[str]] = {}

        # 大分類的狀態與 UI 參考[cite: 1]
        self.collapsed_categories: Set[str] = set()
        self._category_frames: Dict[str, ctk.CTkFrame] = {}
        self._category_buttons: Dict[str, ctk.CTkButton] = {}
        self._category_titles: Dict[str, str] = {}

        # 中分類的狀態與 UI 參考[cite: 1]
        self.collapsed_sub_categories: Set[str] = set()
        self._sub_category_frames: Dict[str, ctk.CTkFrame] = {}
        self._sub_category_buttons: Dict[str, ctk.CTkButton] = {}

    def build_tree(self) -> None:
        """Rebuild the tree while preserving selected filters and collapsed groups."""
        selected_filters = (self.get_active_filter_ids() if self.filter_vars
                            else self._initial_filters)
        for widget in self._parent_frame.winfo_children():
            widget.destroy()

        self.sub_cat_vars.clear()
        self.filter_vars.clear()
        self.filter_to_sub_map.clear()
        self.sub_to_filters_map.clear()
        self._category_frames.clear()
        self._category_buttons.clear()
        self._category_titles.clear()
        self._sub_category_frames.clear()
        self._sub_category_buttons.clear()

        # 新增：如果是首次執行，將所有分類預設加入摺疊清單
        if self._is_first_build:
            self.collapsed_categories = set(
                self._game_param.AttachEffectFilterCategory.keys())
            self.collapsed_sub_categories = set(
                self._game_param.AttachEffectFilterSubCategory.keys())
            self._is_first_build = False

        category_to_subs: Dict[str, List[str]] = {}
        for sub_id, sub_param in self._game_param.AttachEffectFilterSubCategory.items():
            category_to_subs.setdefault(
                sub_param.filterCategory, []).append(sub_id)

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
            category_button.grid(
                row=row, column=0, sticky="ew", padx=2, pady=(8, 2))
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

                sub_header_frame = ctk.CTkFrame(
                    content, fg_color="transparent")
                sub_header_frame.grid(
                    row=content_row, column=0, sticky="ew", padx=20, pady=2)
                content_row += 1

                sub_toggle_btn = ctk.CTkButton(
                    sub_header_frame, text="", font=("Helvetica", 12, "bold"), width=20, height=20,
                    fg_color="transparent", hover_color=("#E5E7EB", "#374151"), text_color="#337AB7",
                    command=lambda s=sub_id: self._toggle_sub_category(s),
                )
                sub_toggle_btn.pack(side="left", padx=(0, 5))
                self._sub_category_buttons[sub_id] = sub_toggle_btn
                self._update_sub_category_button(sub_id)

                sub_checkbox = ctk.CTkCheckBox(
                    sub_header_frame, text=self._game_text.Menu[sub_param.textId],
                    font=("Helvetica", 12, "bold"), variable=sub_var,
                    command=lambda s=sub_id: self._on_sub_category_toggled(s),
                )
                sub_checkbox.pack(side="left")

                sub_content = ctk.CTkFrame(content, fg_color="transparent")
                sub_content.grid(row=content_row, column=0, sticky="ew")
                sub_content.grid_columnconfigure(0, weight=1)
                self._sub_category_frames[sub_id] = sub_content
                content_row += 1

                filter_row = 0
                for filter_id in filter_ids:
                    filter_param = self._game_param.AttachEffectFilter[filter_id]
                    filter_var = ctk.BooleanVar(
                        value=filter_id in selected_filters)
                    self.filter_vars[filter_id] = filter_var
                    filter_checkbox = ctk.CTkCheckBox(
                        sub_content, text=self._game_text.AttachEffect[filter_param.filterTextId],
                        font=("Helvetica", 11), variable=filter_var,
                        command=lambda f=filter_id: self._on_filter_toggled(f),
                    )

                    # 修改：將原本的 padx=40 加大至 (60, 20)，使得最後的子元素再往右退多一點[cite: 1]
                    # tuple 格式 (left_padding, right_padding) 確保不會因過度推擠造成右側裁切
                    filter_checkbox.grid(
                        row=filter_row, column=0, sticky="w", padx=(60, 20), pady=1)
                    filter_row += 1

                # 初始檢查是否需要隱藏中分類內容
                if sub_id in self.collapsed_sub_categories:
                    sub_content.grid_remove()

            # 初始檢查是否需要隱藏大分類內容
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

    def _toggle_sub_category(self, sub_id: str) -> None:
        if sub_id in self.collapsed_sub_categories:
            self.collapsed_sub_categories.remove(sub_id)
            self._sub_category_frames[sub_id].grid()
        else:
            self.collapsed_sub_categories.add(sub_id)
            self._sub_category_frames[sub_id].grid_remove()
        self._update_sub_category_button(sub_id)

    def _update_sub_category_button(self, sub_id: str) -> None:
        icon = "▶" if sub_id in self.collapsed_sub_categories else "▼"
        self._sub_category_buttons[sub_id].configure(text=icon)

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
        self.sub_cat_vars[sub_id].set(
            all(self.filter_vars[f_id].get() for f_id in sibling_ids))
        self._block_filter_event = False
        self._on_change()

    def get_active_filter_ids(self) -> Set[str]:
        return {filter_id for filter_id, var in self.filter_vars.items() if var.get()}

    def clear_all_filters(self) -> None:
        """Clear every checkbox and refresh the displayed table once."""
        self._block_filter_event = True
        for variable in self.sub_cat_vars.values():
            variable.set(False)
        for variable in self.filter_vars.values():
            variable.set(False)
        self._block_filter_event = False
        self._on_change()
