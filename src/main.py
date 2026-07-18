import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Set

# 匯入您提供的底層資源模組
from game_param_res import GameParam, EditableAttachEffectTableRecord
from game_trext_res import GameText

# --- GUI 介面專用多語言字典 (新增警告文本) ---
GUI_LOCALIZATION = {
    "zhotw": {
        "title": "遊戲機率權重修改工具 (chanceWeight Editor)",
        "setting_panel": "系統設定",
        "lang_select": "介面與遊戲語系:",
        "theme_select": "外觀主題模式:",
        "table_select": "選擇參數表格 ID:",
        "filter_panel": "效果標籤過濾器",
        "data_panel": "參數編輯工作區",
        "btn_export": "💾 檢查並匯出 CSV 參數檔",
        "btn_reset": "🔄 重置本次所有修改",
        "th_eff_id": "效果 ID",
        "th_eff_name": "效果名稱 (遊戲文本)",
        "th_filter": "所屬標籤",
        "th_raw_w": "原始權重",
        "th_dlc_w": "DLC 權重",
        "th_final_w": "最終權重",
        "th_edit": "修改期望值",
        "msg_success": "成功",
        "msg_err": "錯誤",
        "export_ok": "配置校驗通過，已成功還原輸出至 data/param/AttachEffectTableParam.csv",
        "reset_ok": "已重置所有編輯層數據至初始狀態。",
        "input_err": "請輸入有效的整數數值！",
        "lock_err": "該項最終權重為 0，已被系統鎖定，無法修改！",
        "warn_3000000": "⚠️ 核心警告：ID 3000000 群組中最終權重非 0 的數量僅有 {count} 筆，將導致無法匯出！(必須至少 3 筆)"
    },
    "zhocn": {
        "title": "游戏概率权重修改工具 (chanceWeight Editor)",
        "setting_panel": "系统设置",
        "lang_select": "界面与游戏语系:",
        "theme_select": "外观主题模式:",
        "table_select": "选择参数表格 ID:",
        "filter_panel": "效果标签过滤器",
        "data_panel": "参数编辑工作区",
        "btn_export": "💾 检查并导出 CSV 参数档",
        "btn_reset": "🔄 重置本次所有修改",
        "th_eff_id": "效果 ID",
        "th_eff_name": "效果名称 (游戏文本)",
        "th_filter": "所属标签",
        "th_raw_w": "原始权重",
        "th_dlc_w": "DLC 权重",
        "th_final_w": "最终权重",
        "th_edit": "修改期望值",
        "msg_success": "成功",
        "msg_err": "错误",
        "export_ok": "配置校验通过，已成功还原输出至 data/param/AttachEffectTableParam.csv",
        "reset_ok": "已重置所有编辑层数据至初始状态。",
        "input_err": "请输入有效的整数数值！",
        "lock_err": "该项最终权重为 0，已被系统锁定，无法修改！",
        "warn_3000000": "⚠️ 核心警告：ID 3000000 群组中最终权重非 0 的数量仅有 {count} 笔，将导致无法导出！(必须至少 3 笔)"
    },
    "engus": {
        "title": "Game Chance Weight Editor (chanceWeight Tool)",
        "setting_panel": "System Settings",
        "lang_select": "UI & Game Language:",
        "theme_select": "Appearance Theme:",
        "table_select": "Select Table ID:",
        "filter_panel": "Effect Tag Filter",
        "data_panel": "Parameter Editor Workspace",
        "btn_export": "💾 Validate & Export CSV",
        "btn_reset": "🔄 Reset All Current Changes",
        "th_eff_id": "Effect ID",
        "th_eff_name": "Effect Name (Game Text)",
        "th_filter": "Associated Tag",
        "th_raw_w": "Raw Weight",
        "th_dlc_w": "DLC Weight",
        "th_final_w": "Final Weight",
        "th_edit": "New Weight Value",
        "msg_success": "Success",
        "msg_err": "Error",
        "export_ok": "Validation passed! Successfully exported to data/param/AttachEffectTableParam.csv",
        "reset_ok": "All editable records have been restored to initial state.",
        "input_err": "Please enter a valid integer value!",
        "lock_err": "This item is locked (Final Weight is 0) and cannot be modified!",
        "warn_3000000": "⚠️ Core Warning: Group 3000000 has only {count} non-zero final weights. Export will FAIL! (Min 3 required)"
    }
}


class ChanceWeightEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 預設語系與主題設定
        self.current_gui_lang = "zhotw"
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # 初始化外部文本資料庫 (預設載入繁中)
        GameText.change_language(self.current_gui_lang)

        # 允許修改的特定 Table ID 列表
        self.allowed_table_ids = ["100", "110", "200", "210",
                                  "300", "310", "2000000", "2100000", "2200000", "3000000"]
        self.selected_table_id = self.allowed_table_ids[0]

        # 過濾器事件阻斷鎖 (防止中分類批次改寫小分類時造成重複重繪)
        self._block_filter_event = False

        # 儲存過濾器 Checkbox 元件與其布林變數的結構
        # 中分類 ID -> BooleanVar
        self.sub_cat_vars: Dict[str, ctk.BooleanVar] = {}
        # 小分類 ID -> BooleanVar
        self.filter_vars: Dict[str, ctk.BooleanVar] = {}
        self.filter_to_sub_map: Dict[str, str] = {}       # 小分類 ID -> 中分類 ID
        self.sub_to_filters_map: Dict[str,
                                      List[str]] = {}  # 中分類 ID -> 小分類 ID 列表

        # 配置視窗基本屬性
        self.title(GUI_LOCALIZATION[self.current_gui_lang]["title"])
        self.geometry("1400x850")
        self.minsize(1200, 750)

        # 建構 GUI 版面
        self._setup_layout()

        # 動態載入過濾器樹狀結構
        self._build_filter_tree_widgets()

        # 載入主資料表格與實時警告檢測
        self.refresh_data_grid()

    def _get_text(self, key: str) -> str:
        """獲取當前本地化的 GUI 介面文字"""
        return GUI_LOCALIZATION.get(self.current_gui_lang, GUI_LOCALIZATION["engus"]).get(key, key)

    def _setup_layout(self):
        """配置主視窗網格佈局 (左側控制面板 + 右側參數編輯區)"""
        self.grid_columnconfigure(0, weight=1, minsize=350)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # ================= 左側控制面板 =================
        self.left_panel = ctk.CTkFrame(self, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(4, weight=1)  # 讓過濾器滾動框吃滿剩餘高度

        # 區塊 1: 系統設定區
        self.setting_title = ctk.CTkLabel(self.left_panel, text=self._get_text(
            "setting_panel"), font=("Helvetica", 16, "bold"), anchor="w")
        self.setting_title.grid(
            row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        self.setting_box = ctk.CTkFrame(
            self.left_panel, fg_color="transparent")
        self.setting_box.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        self.setting_box.grid_columnconfigure(1, weight=1)

        # 語言切換
        self.lbl_lang = ctk.CTkLabel(
            self.setting_box, text=self._get_text("lang_select"), anchor="w")
        self.lbl_lang.grid(row=0, column=0, sticky="w", pady=5)
        self.combo_lang = ctk.CTkOptionMenu(self.setting_box, values=[
                                            "繁體中文 (zhotw)", "简体中文 (zhocn)", "English (engus)"], command=self._on_language_changed)
        self.combo_lang.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)

        # 主題切換
        self.lbl_theme = ctk.CTkLabel(
            self.setting_box, text=self._get_text("theme_select"), anchor="w")
        self.lbl_theme.grid(row=1, column=0, sticky="w", pady=5)
        self.combo_theme = ctk.CTkOptionMenu(self.setting_box, values=[
                                             "Dark", "Light", "System"], command=lambda m: ctk.set_appearance_mode(m))
        self.combo_theme.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        # Table ID 切換
        self.lbl_table = ctk.CTkLabel(self.setting_box, text=self._get_text(
            "table_select"), anchor="w", font=("Helvetica", 12, "bold"))
        self.lbl_table.grid(row=2, column=0, sticky="w", pady=(15, 5))
        self.combo_table = ctk.CTkOptionMenu(
            self.setting_box, values=self.allowed_table_ids, command=self._on_table_id_changed)
        self.combo_table.grid(row=2, column=1, sticky="ew",
                              padx=(10, 0), pady=(15, 5))

        # 區塊 2: 滾動過濾器區 (Scrollable Frame)
        self.lbl_filter_title = ctk.CTkLabel(self.left_panel, text=self._get_text(
            "filter_panel"), font=("Helvetica", 14, "bold"), anchor="w")
        self.lbl_filter_title.grid(
            row=3, column=0, sticky="ew", padx=15, pady=(20, 5))

        self.filter_scroll = ctk.CTkScrollableFrame(
            self.left_panel, label_text="")
        self.filter_scroll.grid(
            row=4, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.filter_scroll.grid_columnconfigure(0, weight=1)

        # ================= 右側參數編輯區 =================
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)  # 讓資料表格吃滿高度

        # 頂部標題與功能按鈕
        self.top_ctrl_frame = ctk.CTkFrame(
            self.right_panel, fg_color="transparent")
        self.top_ctrl_frame.grid(
            row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.top_ctrl_frame.grid_columnconfigure(0, weight=1)

        self.lbl_data_title = ctk.CTkLabel(
            self.top_ctrl_frame, text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}", font=("Helvetica", 16, "bold"), anchor="w")
        self.lbl_data_title.grid(row=0, column=0, sticky="w")

        self.btn_reset = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text(
            "btn_reset"), fg_color="#D9534F", hover_color="#C9302C", command=self._on_reset_clicked)
        self.btn_reset.grid(row=0, column=1, padx=5, sticky="e")

        self.btn_export = ctk.CTkButton(self.top_ctrl_frame, text=self._get_text(
            "btn_export"), fg_color="#5CB85C", hover_color="#4CAE4C", font=("Helvetica", 12, "bold"), command=self._on_export_clicked)
        self.btn_export.grid(row=0, column=2, padx=5, sticky="e")

        # 實時警告標籤列 (預設隱藏，橫跨整個右側頂部)
        self.lbl_warning = ctk.CTkLabel(self.right_panel, text="", font=(
            "Helvetica", 12, "bold"), fg_color="#3A1F1F", text_color="#D9534F", height=32, corner_radius=4, anchor="w", padx=10)
        self.lbl_warning.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        self.lbl_warning.grid_remove()  # 初始隱藏

        # 中央主數據滾動框 (DataGrid)
        self.data_scroll = ctk.CTkScrollableFrame(self.right_panel)
        self.data_scroll.grid(
            row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_filter_tree_widgets(self):
        """建構過濾器樹狀結構[cite: 1, 3]"""
        self.sub_cat_vars.clear()
        self.filter_vars.clear()
        self.filter_to_sub_map.clear()
        self.sub_to_filters_map.clear()

        cat_to_sub_list: Dict[str, List[str]] = {}
        for sub_id, sub_param in GameParam.AttachEffectFilterSubCategory.items():

            c_id = sub_param.filterCategory
            cat_to_sub_list.setdefault(c_id, []).append(sub_id)

        for flt_id, flt_param in GameParam.AttachEffectFilter.items():

            s_id = flt_param.attachEffectFilterCategory
            self.sub_to_filters_map.setdefault(s_id, []).append(flt_id)
            self.filter_to_sub_map[flt_id] = s_id

        current_row = 0
        for cat_id, cat_param in GameParam.AttachEffectFilterCategory.items():

            lbl_cat = ctk.CTkLabel(self.filter_scroll, text=f"■ {GameText.Menu[cat_param.textId]}", font=(
                "Helvetica", 13, "bold"), anchor="w", text_color="#337AB7")
            lbl_cat.grid(row=current_row, column=0,
                         sticky="w", padx=5, pady=(10, 2))
            current_row += 1

            sub_ids = cat_to_sub_list.get(cat_id, [])
            for s_id in sub_ids:
                sub_param = GameParam.AttachEffectFilterSubCategory[s_id]
                s_var = ctk.BooleanVar(value=False)
                self.sub_cat_vars[s_id] = s_var

                chk_sub = ctk.CTkCheckBox(self.filter_scroll, text=GameText.Menu[sub_param.textId], font=("Helvetica", 12, "bold"), variable=s_var,
                                          command=lambda s=s_id: self._on_sub_category_toggled(s))
                chk_sub.grid(row=current_row, column=0,
                             sticky="w", padx=20, pady=2)
                current_row += 1

                flt_ids = self.sub_to_filters_map.get(s_id, [])
                for f_id in flt_ids:
                    flt_param = GameParam.AttachEffectFilter[f_id]
                    f_var = ctk.BooleanVar(value=False)
                    self.filter_vars[f_id] = f_var

                    chk_flt = ctk.CTkCheckBox(self.filter_scroll, text=GameText.AttachEffect[flt_param.filterTextId], font=("Helvetica", 11), variable=f_var,
                                              command=lambda f=f_id: self._on_filter_toggled(f))
                    chk_flt.grid(row=current_row, column=0,
                                 sticky="w", padx=40, pady=1)
                    current_row += 1

    def _check_global_warnings(self):
        """實時監控全域異常狀態 (針對 3000000 進行即時警告)"""
        target_id = "3000000"
        if target_id in GameParam.EditableAttachEffectTable:

            non_zero_items = [
                item for item in GameParam.EditableAttachEffectTable[target_id].values()
                if item.final_chance_weight != 0
            ]
            count = len(non_zero_items)
            if count < 3:
                # 觸發警告：動態組合當前語系的警告訊息
                warn_text = self._get_text("warn_3000000").format(count=count)
                self.lbl_warning.configure(text=warn_text)
                self.lbl_warning.grid()  # 讓元件顯示
                return

        # 若條件正常，將警告標籤隱藏並釋放排版空間
        self.lbl_warning.grid_remove()

    def _on_sub_category_toggled(self, sub_id: str):
        """中分類連動小分類"""
        if self._block_filter_event:
            return
        self._block_filter_event = True
        target_status = self.sub_cat_vars[sub_id].get()
        for f_id in self.sub_to_filters_map.get(sub_id, []):
            self.filter_vars[f_id].set(target_status)
        self._block_filter_event = False
        self.refresh_data_grid()

    def _on_filter_toggled(self, filter_id: str):
        """小分類連動中分類"""
        if self._block_filter_event:
            return
        parent_sub_id = self.filter_to_sub_map.get(filter_id)
        if not parent_sub_id:
            return
        self._block_filter_event = True
        all_siblings = self.sub_to_filters_map.get(parent_sub_id, [])
        is_all_checked = all(
            self.filter_vars[f_id].get() for f_id in all_siblings)
        self.sub_cat_vars[parent_sub_id].set(is_all_checked)
        self._block_filter_event = False
        self.refresh_data_grid()

    def _on_language_changed(self, selected_lang_str: str):
        """全域語言切換"""
        if "zhotw" in selected_lang_str:
            self.current_gui_lang = "zhotw"
        elif "zhocn" in selected_lang_str:
            self.current_gui_lang = "zhocn"
        else:
            self.current_gui_lang = "engus"

        GameText.change_language(self.current_gui_lang)

        self.title(self._get_text("title"))
        self.setting_title.configure(text=self._get_text("setting_panel"))
        self.lbl_lang.configure(text=self._get_text("lang_select"))
        self.lbl_theme.configure(text=self._get_text("theme_select"))
        self.lbl_table.configure(text=self._get_text("table_select"))
        self.lbl_filter_title.configure(text=self._get_text("filter_panel"))
        self.lbl_data_title.configure(
            text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}")
        self.btn_reset.configure(text=self._get_text("btn_reset"))
        self.btn_export.configure(text=self._get_text("btn_export"))

        # 刷新所有動態元件的文字
        for widget in self.filter_scroll.winfo_children():
            widget.destroy()
        self._build_filter_tree_widgets()
        self.refresh_data_grid()

    def _on_table_id_changed(self, table_id: str):
        self.selected_table_id = table_id
        self.lbl_data_title.configure(
            text=f"{self._get_text('data_panel')} - Table ID: {self.selected_table_id}")
        self.refresh_data_grid()

    def get_active_filter_ids(self) -> Set[str]:
        return {f_id for f_id, var in self.filter_vars.items() if var.get()}

    def refresh_data_grid(self):
        """根據篩選與當前表 ID 渲染工作區，並附加實時全域狀態檢測[cite: 1, 3]"""
        for widget in self.data_scroll.winfo_children():
            widget.destroy()

        # 執行實時全域安全檢查
        self._check_global_warnings()

        active_filters = self.get_active_filter_ids()
        is_empty_set = (len(active_filters) == 0)

        table_dict = GameParam.EditableAttachEffectTable.get(
            self.selected_table_id, {})

        display_records: List[EditableAttachEffectTableRecord] = []
        for eff_id, record in table_dict.items():

            eff_param = GameParam.AttachEffect.get(eff_id)
            if not eff_param:
                if is_empty_set:
                    display_records.append(record)
                continue
            filter_param_id = eff_param.attachFilterParamId
            if is_empty_set or (filter_param_id in active_filters):
                display_records.append(record)

        # 欄位配置
        headers = [
            self._get_text("th_eff_id"), self._get_text("th_eff_name"),
            self._get_text("th_filter"), self._get_text("th_raw_w"),
            self._get_text("th_dlc_w"), self._get_text("th_final_w"),
            self._get_text("th_edit")
        ]
        for col_idx, h_text in enumerate(headers):
            lbl_h = ctk.CTkLabel(self.data_scroll, text=h_text, font=(
                "Helvetica", 12, "bold"), fg_color="#222222", height=30, anchor="center")
            lbl_h.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=1)

        self.data_scroll.grid_columnconfigure(0, weight=1)
        self.data_scroll.grid_columnconfigure(1, weight=3)
        self.data_scroll.grid_columnconfigure(2, weight=2)
        self.data_scroll.grid_columnconfigure(3, weight=1)
        self.data_scroll.grid_columnconfigure(4, weight=1)
        self.data_scroll.grid_columnconfigure(5, weight=1)
        self.data_scroll.grid_columnconfigure(6, weight=2)

        # 繪製資料列[cite: 1, 2, 3]
        for row_idx, rec in enumerate(display_records, start=1):

            lbl_id = ctk.CTkLabel(
                self.data_scroll, text=rec.attachEffectId, anchor="center")
            lbl_id.grid(row=row_idx, column=0, sticky="ew", padx=1, pady=1)

            eff_param = GameParam.AttachEffect.get(rec.attachEffectId)
            g_text = GameText.AttachEffect[eff_param.attachTextId] if eff_param else "Unknown"
            lbl_name = ctk.CTkLabel(
                self.data_scroll, text=g_text, anchor="w", padx=5)
            lbl_name.grid(row=row_idx, column=1, sticky="ew", padx=1, pady=1)

            f_text = "None"
            if eff_param:
                flt_p = GameParam.AttachEffectFilter.get(
                    eff_param.attachFilterParamId)
                if flt_p:
                    f_text = GameText.AttachEffect[flt_p.filterTextId]
            lbl_tag = ctk.CTkLabel(
                self.data_scroll, text=f_text, anchor="center", text_color="#A0A0A0")
            lbl_tag.grid(row=row_idx, column=2, sticky="ew", padx=1, pady=1)

            lbl_raw = ctk.CTkLabel(self.data_scroll, text=str(
                rec.chanceWeight), anchor="center")
            lbl_raw.grid(row=row_idx, column=3, sticky="ew", padx=1, pady=1)

            lbl_dlc = ctk.CTkLabel(self.data_scroll, text=str(
                rec.chanceWeight_dlc), anchor="center")
            lbl_dlc.grid(row=row_idx, column=4, sticky="ew", padx=1, pady=1)

            fw = rec.final_chance_weight
            fw_color = "#D9534F" if fw == 0 else "transparent"
            lbl_fw = ctk.CTkLabel(self.data_scroll, text=str(
                fw), anchor="center", fg_color=fw_color)
            lbl_fw.grid(row=row_idx, column=5, sticky="ew", padx=1, pady=1)

            # 修改元件區塊
            edit_frame = ctk.CTkFrame(self.data_scroll, fg_color="transparent")
            edit_frame.grid(row=row_idx, column=6, sticky="ew", padx=1, pady=1)
            edit_frame.grid_columnconfigure(0, weight=1)

            entry_val = ctk.CTkEntry(
                edit_frame, height=24, font=("Helvetica", 11))
            entry_val.insert(0, str(fw))
            entry_val.grid(row=0, column=0, sticky="ew", padx=(2, 2))

            btn_save = ctk.CTkButton(edit_frame, text="✔", width=28, height=24, fg_color="#337AB7", hover_color="#286090",
                                     command=lambda r=rec, e=entry_val: self._on_save_row_weight(r, e))
            btn_save.grid(row=0, column=1, padx=(0, 2))

            # 🚀 重點功能加入：為 Entry 元件綁定鍵盤 Enter 鍵，實現快速儲存
            entry_val.bind("<Return>", lambda event, r=rec,
                           e=entry_val: self._on_save_row_weight(r, e))

            if fw == 0:
                entry_val.configure(state="disabled")
                btn_save.configure(state="disabled")

    def _on_save_row_weight(self, record: EditableAttachEffectTableRecord, entry_widget: ctk.CTkEntry):
        """儲存特定欄位權重修改"""
        input_str = entry_widget.get().strip()
        try:
            val = int(input_str)
            record.update_weight(val)

            # 儲存後立即更新介面與重新檢測全域警告
            self.refresh_data_grid()
        except ValueError:
            messagebox.showerror(self._get_text("msg_err"),
                                 self._get_text("input_err"))
        except PermissionError as pe:
            messagebox.showerror(self._get_text("msg_err"), str(pe))

    def _on_reset_clicked(self):
        GameParam.reset_editable()
        self.refresh_data_grid()
        messagebox.showinfo(self._get_text("msg_success"),
                            self._get_text("reset_ok"))

    def _on_export_clicked(self):
        try:
            GameParam.export_editable_to_csv()
            messagebox.showinfo(self._get_text(
                "msg_success"), self._get_text("export_ok"))
        except (ValueError, PermissionError) as e:
            messagebox.showerror(self._get_text("msg_err"), str(e))


if __name__ == "__main__":
    app = ChanceWeightEditorApp()
    app.mainloop()
