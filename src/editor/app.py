"""Main CustomTkinter application for editing rolling-pool weights."""

from __future__ import annotations

import os
from typing import List, Set, Tuple

import customtkinter as ctk
from tkinter import messagebox, filedialog

from game_param_res import GameParam, EditableAttachEffectTableRecord
from game_trext_res import GameText

from .theme_cache import ThemeCache
from .localization_cache import LocalizationCache
from .filter_controller import FilterController
from .config import Config
from .warning_controller import WarningController
from .virtual_table import VirtualTable
from . import table_renderer as tr


class ChanceWeightEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = Config()
        available_languages = {
            code for code, _name in GameText.get_available_languages_for_gui()
        }
        configured_language = self.config.values.get("language", "engus")
        self.current_gui_lang = (configured_language
                                 if isinstance(configured_language, str)
                                 and configured_language in available_languages else "engus")
        configured_theme = self.config.values.get("theme", "Dark")
        self.current_theme = configured_theme if configured_theme in ("Dark", "Light") else "Dark"
        configured_filters = self.config.values.get("filters", [])
        if not isinstance(configured_filters, list):
            configured_filters = []
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")

        GameText.change_language(self.current_gui_lang)

        self.allowed_table_ids = ["100", "110", "200", "210",
                                  "300", "310", "2000000", "2100000", "2200000", "3000000"]
        self.selected_table_id = self.allowed_table_ids[0]

        # Locked records are identified from their original weights at startup.
        self.initially_locked_records: Set[Tuple[str, str]] = set()
        self._record_initial_locks()

        self.theme = ThemeCache()
        self.theme.refresh()
        self.loc = LocalizationCache(GameText)
        self.loc.set_language(self.current_gui_lang)

        self.title(self._get_text("title"))
        self.geometry("1500x900")
        self.minsize(1280, 750)

        self._current_display_records: List[EditableAttachEffectTableRecord] = []
        self._sort_column = None
        self._sort_reverse = False

        self._setup_layout()

        # The filter tree requires the frame created by _setup_layout().
        self.filter_controller = FilterController(
            self.filter_scroll, GameParam, GameText, on_change=self._on_filters_changed,
            initial_filters=set(configured_filters))
        self.filter_controller.build_tree()
        self._update_auto_configure_button_state()

        self.warning_controller = WarningController(self.lbl_warning, self._get_text)

        self.refresh_data_grid()

    def _record_initial_locks(self):
        """在初始化時，掃描並記錄哪些資料原本就是 0 權重，進行永久鎖定"""
        for t_id, table_dict in GameParam.EditableAttachEffectTable.items():
            for eff_id, record in table_dict.items():
                if record.final_chance_weight == 0:
                    self.initially_locked_records.add((t_id, eff_id))

    def _get_text(self, key: str) -> str:
        return self.loc.get_text(key)

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1, minsize=350)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(4, weight=1)

        self.setting_title = ctk.CTkLabel(self.left_panel, text=self._get_text(
            "setting_panel"), font=("Helvetica", 16, "bold"), anchor="w")
        self.setting_title.grid(
            row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        self.setting_box = ctk.CTkFrame(
            self.left_panel, fg_color="transparent")
        self.setting_box.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        self.setting_box.grid_columnconfigure(1, weight=1)

        self.lbl_lang = ctk.CTkLabel(
            self.setting_box, text=self._get_text("lang_select"), anchor="w")
        self.lbl_lang.grid(row=0, column=0, sticky="w", pady=5)

        db_langs = GameText.get_available_languages_for_gui()
        lang_options = [f"{name} ({code})" for code, name in db_langs] if db_langs else [
            "繁體中文 (zhotw)"]

        self.combo_lang = ctk.CTkOptionMenu(
            self.setting_box, values=lang_options, command=self._on_language_changed)
        self.combo_lang.grid(row=0, column=1, sticky="ew",
                             padx=(10, 0), pady=5)

        current_native = GameText.LANGUAGE_MAP.get(
            self.current_gui_lang, self.current_gui_lang)
        default_option = f"{current_native} ({self.current_gui_lang})"
        if default_option in lang_options:
            self.combo_lang.set(default_option)

        self.lbl_theme = ctk.CTkLabel(
            self.setting_box, text=self._get_text("theme_select"), anchor="w")
        self.lbl_theme.grid(row=1, column=0, sticky="w", pady=5)

        self.combo_theme = ctk.CTkOptionMenu(
            self.setting_box, values=["Dark", "Light"], command=self._on_theme_changed)
        self.combo_theme.grid(
            row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.combo_theme.set(self.current_theme)

        self.lbl_table = ctk.CTkLabel(self.setting_box, text=self._get_text(
            "table_select"), anchor="w", font=("Helvetica", 12, "bold"))
        self.lbl_table.grid(row=2, column=0, sticky="w", pady=(15, 5))
        self.combo_table = ctk.CTkOptionMenu(
            self.setting_box, values=self.allowed_table_ids, command=self._on_table_id_changed)
        self.combo_table.grid(row=2, column=1, sticky="ew",
                              padx=(10, 0), pady=(15, 5))

        self.filter_header = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.filter_header.grid(row=3, column=0, sticky="ew", padx=15, pady=(20, 5))
        self.filter_header.grid_columnconfigure(0, weight=1)
        self.lbl_filter_title = ctk.CTkLabel(self.filter_header, text=self._get_text(
            "filter_panel"), font=("Helvetica", 14, "bold"), anchor="w")
        self.lbl_filter_title.grid(row=0, column=0, sticky="w")
        self.btn_clear_filters = ctk.CTkButton(
            self.filter_header, text=self._get_text("btn_clear_filters"), width=100, height=26,
            command=self._on_clear_filters_clicked)
        self.btn_clear_filters.grid(row=0, column=1, sticky="e")

        self.filter_scroll = ctk.CTkScrollableFrame(
            self.left_panel, label_text="")
        self.filter_scroll.grid(
            row=4, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.filter_scroll.grid_columnconfigure(0, weight=1)

        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)

        self.top_ctrl_frame = ctk.CTkFrame(
            self.right_panel, fg_color="transparent")
        self.top_ctrl_frame.grid(
            row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.top_ctrl_frame.grid_columnconfigure(0, weight=1)

        self.lbl_data_title = ctk.CTkLabel(
            self.top_ctrl_frame, text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}", font=("Helvetica", 16, "bold"), anchor="w")
        self.lbl_data_title.grid(row=0, column=0, sticky="w")

        self.btn_reset = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text("btn_reset"),
                                       fg_color=("#D9534F", "#C9302C"), hover_color=("#C9302C", "#A9201C"),
                                       command=self._on_reset_clicked)
        self.btn_reset.grid(row=0, column=1, padx=5, sticky="e")

        self.btn_increase_filtered = ctk.CTkButton(
            self.top_ctrl_frame, text=self._get_text("btn_increase_filtered"),
            command=self._on_increase_filtered_clicked)
        self.btn_increase_filtered.grid(row=1, column=1, padx=5, pady=(4, 0), sticky="e")

        self.btn_zero_unmodified = ctk.CTkButton(
            self.top_ctrl_frame, text=self._get_text("btn_set_unmodified_one"),
            fg_color=("#7C3AED", "#6D28D9"), hover_color=("#6D28D9", "#5B21B6"),
            command=self._on_zero_unmodified_clicked)
        self.btn_zero_unmodified.grid(row=1, column=2, padx=5, pady=(4, 0), sticky="e")

        self.btn_apply = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text("btn_apply"),
                                       command=self._on_apply_clicked)
        self.btn_apply.grid(row=1, column=3, padx=5, pady=(4, 0), sticky="e")

        self.btn_import = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text("btn_import"),
                                        command=self._on_import_clicked)
        self.btn_import.grid(row=1, column=4, padx=5, pady=(4, 0), sticky="e")

        self.btn_export = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text("btn_export"),
                                        fg_color=("#5CB85C", "#4CAE4C"), hover_color=("#4CAE4C", "#398439"),
                                        font=("Helvetica", 12, "bold"), command=self._on_export_clicked)
        self.btn_export.grid(row=0, column=2, padx=5, sticky="e")

        self.btn_auto_configure = ctk.CTkButton(
            self.top_ctrl_frame, text=self._get_text("btn_auto_configure"),
            state="disabled", command=self._on_auto_configure_clicked)
        self.btn_auto_configure.grid(row=0, column=3, padx=5, sticky="e")

        self.lbl_warning = ctk.CTkLabel(self.right_panel, text="", font=("Helvetica", 12, "bold"),
                                        fg_color=("#F2DEDE", "#3A1F1F"), text_color=("#A94442", "#D9534F"),
                                        height=32, corner_radius=4, anchor="w", padx=10)
        self.lbl_warning.grid(
            row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        self.lbl_warning.grid_remove()

        self.table_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(0, weight=1)

        self.virtual_table = VirtualTable(
            self.table_container,
            row_height=56,
            draw_header=tr.draw_header,
            draw_row=self._draw_canvas_row,
            edit_bounds=tr.edit_bounds,
            header_column_at=tr.column_at,
            on_header_click=self._on_header_sort,
            can_edit=self._can_edit_canvas_row,
            edit_value=self._canvas_edit_value,
            on_save=self._on_save_canvas_weight,
            on_zero=self._on_zero_canvas_weight,
        )
        self.virtual_table.grid(row=0, column=0, sticky="nsew")
        self.virtual_table.set_theme(self.theme)

    def _current_headers_text(self) -> List[str]:
        headers = [
            self._get_text("th_eff_id"), self._get_text("th_eff_name"),
            self._get_text("th_final_w"),
            self._get_text("th_chance"), self._get_text("th_edit"),
        ]
        if self._sort_column is not None:
            headers[self._sort_column] += " ▼" if self._sort_reverse else " ▲"
        return headers

    def _refresh_header(self):
        """Header 只在語言/主題切換時呼叫，Weight 修改不會觸發。"""
        self.virtual_table.set_headers(self._current_headers_text())

    def _on_theme_changed(self, mode: str):
        """主題切換：重新計算 ThemeCache，並更新 Header 與目前可視列的顏色。"""
        ctk.set_appearance_mode(mode)
        self.current_theme = mode
        self.config.update(theme=mode)
        self.theme.refresh()
        self._refresh_header()
        self.virtual_table.set_theme(self.theme)
        self.warning_controller.check(GameParam)

    def _on_language_changed(self, selected_lang_str: str):
        """Reload interface and game text after a language change."""
        try:
            if "(" in selected_lang_str and selected_lang_str.endswith(")"):
                code = selected_lang_str.split("(")[-1].rstrip(")")
            else:
                code = selected_lang_str
        except Exception:
            return

        self.current_gui_lang = code
        self.config.update(language=code)
        self.loc.set_language(code)

        GameText.change_language(code)
        self.loc.invalidate()

        self.title(self._get_text("title"))
        self.setting_title.configure(text=self._get_text("setting_panel"))
        self.lbl_lang.configure(text=self._get_text("lang_select"))
        self.lbl_theme.configure(text=self._get_text("theme_select"))
        self.lbl_table.configure(text=self._get_text("table_select"))
        self.lbl_filter_title.configure(text=self._get_text("filter_panel"))
        self.btn_clear_filters.configure(text=self._get_text("btn_clear_filters"))

        self.lbl_data_title.configure(
            text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}"
        )
        self.btn_reset.configure(text=self._get_text("btn_reset"))
        self.btn_increase_filtered.configure(text=self._get_text("btn_increase_filtered"))
        self.btn_zero_unmodified.configure(text=self._get_text("btn_set_unmodified_one"))
        self.btn_apply.configure(text=self._get_text("btn_apply"))
        self.btn_import.configure(text=self._get_text("btn_import"))
        self.btn_export.configure(text=self._get_text("btn_export"))
        self.btn_auto_configure.configure(text=self._get_text("btn_auto_configure"))

        self._refresh_header()

        # Filter labels depend on the current game-text language.
        self.filter_controller.build_tree()

        self.refresh_data_grid()

    def _on_table_id_changed(self, table_id: str):
        self.selected_table_id = table_id
        self.lbl_data_title.configure(
            text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}")
        self.refresh_data_grid()

    def get_active_filter_ids(self) -> Set[str]:
        return self.filter_controller.get_active_filter_ids()

    def _on_filters_changed(self):
        active_filters = self.get_active_filter_ids()
        self.config.update(filters=sorted(active_filters, key=int))
        self._update_auto_configure_button_state()
        self.refresh_data_grid()

    def _update_auto_configure_button_state(self):
        state = "normal" if self.get_active_filter_ids() else "disabled"
        self.btn_auto_configure.configure(state=state)

    def _on_clear_filters_clicked(self):
        self.filter_controller.clear_all_filters()

    def _build_display_records(self) -> List[EditableAttachEffectTableRecord]:
        active_filters = self.get_active_filter_ids()
        is_empty_set = (len(active_filters) == 0)
        table_dict = GameParam.EditableAttachEffectTable.get(self.selected_table_id, {})

        display_records: List[EditableAttachEffectTableRecord] = []
        for eff_id, record in table_dict.items():
            eff_param = GameParam.AttachEffect.get(eff_id)
            if not eff_param:
                if is_empty_set:
                    display_records.append(record)
                continue
            if is_empty_set or (eff_param.attachFilterParamId in active_filters):
                display_records.append(record)
        return display_records

    def refresh_data_grid(self):
        """Refresh the visible records and their calculated chance rates."""
        self.warning_controller.check(GameParam)

        table_dict = GameParam.EditableAttachEffectTable.get(self.selected_table_id, {})
        self.loc.build_effect_name_cache(self.selected_table_id, table_dict, GameParam)

        display_records = self._build_display_records()
        self._current_display_records = display_records

        table_chance_dict = GameParam.editable_chance_map.get(self.selected_table_id, {})
        self._current_chance_map = table_chance_dict

        if self._sort_column is not None:
            display_records.sort(key=self._sort_key, reverse=self._sort_reverse)

        self._refresh_header()
        self.virtual_table.set_row_count(len(display_records))

    def _draw_canvas_row(self, canvas, idx: int, y: int, width: int, height: int, theme):
        """Draw one visible row for the virtual table."""
        if idx >= len(self._current_display_records):
            return
        record = self._current_display_records[idx]

        eff_name, _filter_text = self.loc.get_effect_name_and_filter(record.attachEffectId)
        chance_float = self._current_chance_map.get(record.attachEffectId, 0.0)
        is_locked = (self.selected_table_id, record.attachEffectId) in self.initially_locked_records

        tr.draw_row(canvas, record, idx, eff_name, chance_float, is_locked,
                    y, width, height, theme)

    def _can_edit_canvas_row(self, idx: int) -> bool:
        if idx >= len(self._current_display_records):
            return False
        record = self._current_display_records[idx]
        return (self.selected_table_id, record.attachEffectId) not in self.initially_locked_records

    def _canvas_edit_value(self, idx: int) -> str:
        return str(self._current_display_records[idx].final_chance_weight)

    def _on_header_sort(self, column: int) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self.refresh_data_grid()

    def _sort_key(self, record: EditableAttachEffectTableRecord):
        if self._sort_column == 0:
            return int(record.attachEffectId)
        if self._sort_column == 1:
            return self.loc.get_effect_name_and_filter(record.attachEffectId)[0]
        if self._sort_column == 3:
            return self._current_chance_map.get(record.attachEffectId, 0.0)
        return record.final_chance_weight

    def _on_save_canvas_weight(self, idx: int, input_str: str):
        if idx >= len(self._current_display_records):
            return
        record = self._current_display_records[idx]
        try:
            val = int(input_str)
            record.update_weight(val)
            GameParam.update_chance_rate_map(record.ID)

            self.refresh_data_grid()

        except ValueError:
            messagebox.showerror(self._get_text("msg_err"),
                                 self._get_text("input_err"))
        except PermissionError as pe:
            messagebox.showerror(self._get_text("msg_err"), str(pe))

    def _on_zero_canvas_weight(self, idx: int):
        if not self._can_edit_canvas_row(idx):
            return
        record = self._current_display_records[idx]
        try:
            record.update_weight(1)
            GameParam.update_chance_rate_map(record.ID)
            self.refresh_data_grid()
        except PermissionError as error:
            messagebox.showerror(self._get_text("msg_err"), str(error))

    def _on_increase_filtered_clicked(self):
        editable_records = [record for index, record in enumerate(self._current_display_records)
                            if self._can_edit_canvas_row(index)]
        if not editable_records:
            return
        if not messagebox.askyesno(self._get_text("btn_increase_filtered"),
                                   self._get_text("increase_filtered_confirm").format(count=len(editable_records))):
            return
        for record in editable_records:
            record.update_weight(record.final_chance_weight + 100)
        GameParam.update_chance_rate_map(self.selected_table_id)
        self.refresh_data_grid()
        messagebox.showinfo(self._get_text("msg_success"),
                            self._get_text("increase_filtered_ok").format(count=len(editable_records)))

    def _on_reset_clicked(self):
        GameParam.reset_editable()
        self.refresh_data_grid()
        messagebox.showinfo(self._get_text("msg_success"),
                            self._get_text("reset_ok"))

    def _on_zero_unmodified_clicked(self):
        if not messagebox.askyesno(
                self._get_text("btn_set_unmodified_one"),
                self._get_text("set_unmodified_one_confirm").format(table_id=self.selected_table_id)):
            return
        count = GameParam.set_unmodified_editable_records_to_one(self.selected_table_id)
        self.refresh_data_grid()
        messagebox.showinfo(
            self._get_text("msg_success"),
            self._get_text("set_unmodified_one_ok").format(count=count))

    def _on_auto_configure_clicked(self):
        if not self.get_active_filter_ids():
            return
        if not messagebox.askyesno(
                self._get_text("btn_auto_configure"),
                self._get_text("auto_configure_confirm")):
            return
        count = GameParam.auto_configure_all_tables(self.get_active_filter_ids())
        self.refresh_data_grid()
        messagebox.showinfo(
            self._get_text("msg_success"),
            self._get_text("auto_configure_ok").format(count=count))

    def _on_import_clicked(self):
        file_path = filedialog.askopenfilename(filetypes=[
            (self._get_text("file_csv"), "*.csv"), (self._get_text("file_all"), "*.*")],
            title=self._get_text("btn_import"))
        if not file_path:
            return
        try:
            count = GameParam.import_editable_from_csv(file_path)
            self.refresh_data_grid()
            messagebox.showinfo(self._get_text("msg_success"), self._get_text("import_ok").format(count=count))
        except (OSError, ValueError, PermissionError) as error:
            messagebox.showerror(self._get_text("msg_err"), str(error))

    def _on_apply_clicked(self):
        if not messagebox.askyesno(self._get_text("btn_apply"), self._get_text("apply_confirm")):
            return
        try:
            count = GameParam.apply_table_changes_to_others(self.selected_table_id)
            self.refresh_data_grid()
            messagebox.showinfo(self._get_text("msg_success"), self._get_text("apply_ok").format(count=count))
        except (ValueError, PermissionError) as error:
            messagebox.showerror(self._get_text("msg_err"), str(error))

    def _on_export_clicked(self):
        root_path = os.path.dirname(os.path.abspath(__file__))
        root_path = os.path.dirname(root_path)
        extract_dir = os.path.join(root_path, "extract")

        try:
            os.makedirs(extract_dir, exist_ok=True)
        except Exception:
            extract_dir = root_path

        default_filename = "AttachEffectTableParam.csv"

        file_path = filedialog.asksaveasfilename(
            initialdir=extract_dir,
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[(self._get_text("file_csv"), "*.csv"), (self._get_text("file_all"), "*.*")],
            title=self._get_text("btn_export")
        )

        if not file_path:
            return

        try:
            GameParam.export_editable_to_csv(file_path)

            msg_title = self._get_text("msg_success")
            msg_body = f"配置校驗通過！檔案已成功匯出至：\n{file_path}"
            messagebox.showinfo(msg_title, msg_body)

        except (ValueError, PermissionError) as e:
            messagebox.showerror(self._get_text("msg_err"), str(e))
