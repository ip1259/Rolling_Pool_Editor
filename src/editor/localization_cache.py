"""
LocalizationCache
==================
對應 plan.md「Localization Cache」章節。

原本每一列 Row 在 refresh 時都要：
    GameText.AttachEffect[eff_param.attachTextId]
    GameText.AttachEffect[flt_p.filterTextId]
這類字典查詢；資料量一大 (1000~5000 筆) 時，這些查詢與中間運算會被重複執行。

改為：
    - 語言切換 / 表格切換時，一次性建立 {eff_id: (name, filter_text)} 的映射表 (effect_name_cache)。
    - 畫面 Refresh 只需要 dict.get()，不再重複組字串或重新查兩層字典。

⚠️ 不會修改 GameText / GameParam 既有 API，僅包一層快取。
"""

from __future__ import annotations

from typing import Dict, Tuple, Any


# --- GUI 介面專用多語言字典 (原封不動搬移自 main.py，內容 100% 相容) ---
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
        "th_chance": "出現機率",
        "th_edit": "修改期望值",
        "msg_success": "成功",
        "msg_err": "錯誤",
        "export_ok": "配置校驗通過，已成功還原輸出至 data/param/AttachEffectTableParam.csv",
        "reset_ok": "已重置所有編輯層數據至初始狀態。",
        "input_err": "請輸入有效的整數數值！",
        "lock_err": "該項初始最終權重為 0，已被系統鎖定，無法修改！",
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
        "th_chance": "出现概率",
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
        "th_chance": "Chance Rate",
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


class LocalizationCache:
    """管理 GUI 靜態文字，以及 GameText 查詢結果的快取。"""

    def __init__(self, game_text_module: Any) -> None:
        self._game_text = game_text_module
        self.current_lang: str = "zhotw"

        # eff_id -> (effect_name, filter_text)
        self._effect_name_cache: Dict[str, Tuple[str, str]] = {}
        self._cache_key: Tuple[str, str] = ("", "")  # (lang, table_id)

    # ---------------- GUI 靜態文字 ----------------
    def get_text(self, key: str) -> str:
        return GUI_LOCALIZATION.get(self.current_lang, GUI_LOCALIZATION.get("engus", {})).get(key, key)

    def set_language(self, lang_code: str) -> None:
        self.current_lang = lang_code

    # ---------------- effect name / filter text 快取 ----------------
    def build_effect_name_cache(self, table_id: str, table_dict: Dict[str, Any],
                                 game_param_module: Any) -> None:
        """
        依目前語言 + 目前 table_id，一次性建立 eff_id -> (name, filter_text) 映射表。
        僅在「語言切換」或「表格切換」時需要重建；Weight 修改不需要重建。
        """
        cache_key = (self.current_lang, table_id)
        if cache_key == self._cache_key and self._effect_name_cache:
            return  # 已經是最新快取，不需要重建

        new_cache: Dict[str, Tuple[str, str]] = {}
        for eff_id in table_dict.keys():
            eff_param = game_param_module.AttachEffect.get(eff_id)
            if not eff_param:
                new_cache[eff_id] = ("Unknown", "None")
                continue

            eff_name = self._game_text.AttachEffect[eff_param.attachTextId]

            f_text = "None"
            flt_p = game_param_module.AttachEffectFilter.get(eff_param.attachFilterParamId)
            if flt_p:
                f_text = self._game_text.AttachEffect[flt_p.filterTextId]

            new_cache[eff_id] = (eff_name, f_text)

        self._effect_name_cache = new_cache
        self._cache_key = cache_key

    def invalidate(self) -> None:
        """強制讓下一次 build_effect_name_cache 重新建立 (例如語言剛切換完)。"""
        self._cache_key = ("", "")

    def get_effect_name_and_filter(self, eff_id: str) -> Tuple[str, str]:
        return self._effect_name_cache.get(eff_id, ("Unknown", "None"))
