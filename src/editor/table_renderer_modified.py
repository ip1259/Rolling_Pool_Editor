"""
TableRenderer
=============
對應 plan.md「Header Renderer」「Row Renderer」「Widget 更新策略」「Entry 更新」
「Save Button」章節。

核心優化策略：
    1. Header 只在語言/主題切換時重建文字與顏色，Weight 修改完全不動 Header。
    2. Row 的每一個欄位在 configure() 前都會先比對「快取的舊值」，
       只有值真的改變才呼叫 configure() / delete()+insert()，
       避免「800 rows × 7 labels = 5600 次 configure」這種暴力刷新。
    3. Save 按鈕與 Entry 的 <Return> 綁定，只在 Object Pool 建立元件當下綁定一次，
       之後每次渲染只更新一個「可變狀態容器 (state dict)」裡的 record 參照，
       不再重複呼叫 configure(command=...) / bind() / unbind()。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

import customtkinter as ctk
import tkinter as tk


# ============================================================
# Header Renderer
# ============================================================

def configure_header_columns(frame: ctk.CTkBaseClass) -> None:
    """套用與資料列一致的欄寬比例，確保 Header 與 Row 對齊。"""
    frame.grid_columnconfigure((0, 3, 4, 5, 6), weight=1)
    frame.grid_columnconfigure(1, weight=3)
    frame.grid_columnconfigure(2, weight=2)
    frame.grid_columnconfigure(7, weight=2)


def build_header_labels(frame: ctk.CTkBaseClass, headers: List[str],
                        header_bg: str, text_color: str) -> List[ctk.CTkLabel]:
    """第一次建立 Header Label (僅執行一次)。"""
    labels = []
    for col_idx, h_text in enumerate(headers):
        lbl_h = ctk.CTkLabel(frame, text=h_text, font=("Helvetica", 12, "bold"),
                             fg_color=header_bg, text_color=text_color, corner_radius=0)
        lbl_h.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=2)
        labels.append(lbl_h)
    configure_header_columns(frame)
    return labels


def update_header_labels(labels: List[ctk.CTkLabel], headers: List[str],
                         header_bg: str, text_color: str) -> None:
    """語言切換 / 主題切換時呼叫，更新既有 Header Label 的文字與顏色。"""
    for lbl_h, h_text in zip(labels, headers):
        lbl_h.configure(text=h_text, fg_color=header_bg, text_color=text_color)


# ============================================================
# Row Renderer / Object Pool
# ============================================================

def create_row_widgets(canvas: tk.Canvas, on_save: Callable[[Any, ctk.CTkEntry], None]) -> Dict[str, Any]:
    """
    建立一列 (Row) 的 Widget 群組，掛載於傳入的 canvas 上 (VirtualTable 專用)。

    - "_row_frame": 該列的容器 Frame，供 VirtualTable 以 create_window 貼上 Canvas。
    - "_state": 可變狀態容器，只存放「目前此 slot 代表的 record」，
                讓 Save 按鈕 / Entry 的 <Return> 綁定只需要建立一次。
    - "_cache": 上一次渲染時各欄位的值，供差異比對使用。
    """
    row_frame = ctk.CTkFrame(canvas, fg_color="transparent", corner_radius=0)
    configure_header_columns(row_frame)

    lbl_id = ctk.CTkLabel(row_frame, font=("Helvetica", 12), corner_radius=0)
    lbl_id.grid(row=0, column=0, sticky="ew", padx=1, pady=1)

    lbl_name = ctk.CTkLabel(row_frame, font=(
        "Helvetica", 12), anchor="w", justify="left", corner_radius=0)
    lbl_name.grid(row=0, column=1, sticky="ew", padx=1, pady=1)

    lbl_tag = ctk.CTkLabel(row_frame, font=("Helvetica", 12), corner_radius=0)
    lbl_tag.grid(row=0, column=2, sticky="ew", padx=1, pady=1)

    lbl_raw = ctk.CTkLabel(row_frame, font=("Helvetica", 12), corner_radius=0)
    lbl_raw.grid(row=0, column=3, sticky="ew", padx=1, pady=1)

    lbl_dlc = ctk.CTkLabel(row_frame, font=("Helvetica", 12), corner_radius=0)
    lbl_dlc.grid(row=0, column=4, sticky="ew", padx=1, pady=1)

    lbl_final = ctk.CTkLabel(row_frame, font=(
        "Helvetica", 12, "bold"), corner_radius=0)
    lbl_final.grid(row=0, column=5, sticky="ew", padx=1, pady=1)

    lbl_chance = ctk.CTkLabel(row_frame, font=(
        "Helvetica", 12, "bold"), corner_radius=0)
    lbl_chance.grid(row=0, column=6, sticky="ew", padx=1, pady=1)

    edit_frame = ctk.CTkFrame(
        row_frame, fg_color="transparent", corner_radius=0)
    edit_frame.grid_columnconfigure(0, weight=1)
    edit_frame.grid(row=0, column=7, sticky="ew", padx=1, pady=1)

    entry = ctk.CTkEntry(edit_frame, font=("Helvetica", 12), height=28)
    entry.grid(row=0, column=0, sticky="nsew", padx=(2, 2), pady=1)

    save_btn = ctk.CTkButton(edit_frame, text="✔", width=30, height=28,
                             font=("Helvetica", 12, "bold"),
                             fg_color=getattr(theme if False else type("x", (), {})(), "save_btn_normal_bg", "#337AB7"), hover_color="#286090")
    save_btn.grid(row=0, column=1, padx=(2, 2), pady=1, sticky="nsew")

    # --- 驗證：只允許輸入數字與開頭負號 (取代每次 try/except int()) ---
    def _validate_digits(proposed: str) -> bool:
        if proposed in ("", "-"):
            return True
        body = proposed[1:] if proposed.startswith("-") else proposed
        return body.isdigit()

    vcmd = row_frame.register(_validate_digits)
    entry.configure(validate="key", validatecommand=(vcmd, "%P"))

    # --- 穩定 callback：只建立一次，往後只更新 state["record"] ---
    state: Dict[str, Any] = {"record": None}

    def _handle_save(event=None):
        rec = state.get("record")
        if rec is None:
            return
        on_save(rec, entry)

    save_btn.configure(command=_handle_save)
    entry.bind("<Return>", _handle_save)

    return {
        "_row_frame": row_frame,
        "_state": state,
        "_cache": {},
        "id": lbl_id,
        "name": lbl_name,
        "tag": lbl_tag,
        "raw_w": lbl_raw,
        "dlc_w": lbl_dlc,
        "final_w": lbl_final,
        "chance": lbl_chance,
        "edit_frame": edit_frame,
        "entry": entry,
        "save_btn": save_btn,
    }


def _set_if_changed(cache: Dict[str, Any], key: str, new_value: Any, apply_fn: Callable[[], None]) -> None:
    """差異比對核心：值沒變就完全不呼叫 apply_fn (也就是不呼叫 configure())。"""
    if cache.get(key) != new_value:
        apply_fn()
        cache[key] = new_value


def render_row(
    widgets: Dict[str, Any],
    record: Any,
    row_index: int,
    *,
    theme,
    eff_name: str,
    filter_text: str,
    chance_float: float,
    is_locked: bool,
) -> None:
    """
    將第 row_index 筆資料填入 widgets。所有欄位皆先比對快取，值不同才 configure()。
    """
    cache = widgets["_cache"]
    widgets["_state"]["record"] = record

    row_bg = theme.row_bg(row_index)
    fw = record.final_chance_weight
    fw_bg = theme.locked_final_weight_bg if fw == 0 else row_bg
    chance_display = f"{chance_float * 100:.2f}%"

    lbl_id = widgets["id"]
    _set_if_changed(cache, "id_text_bg", (record.attachEffectId, row_bg),
                    lambda: lbl_id.configure(text=record.attachEffectId, fg_color=row_bg))

    lbl_name = widgets["name"]
    _set_if_changed(cache, "name_text_bg", (eff_name, row_bg),
                    lambda: lbl_name.configure(text=eff_name, fg_color=row_bg))

    lbl_tag = widgets["tag"]
    _set_if_changed(cache, "tag_text_bg", (filter_text, row_bg, theme.tag_text_color),
                    lambda: lbl_tag.configure(text=filter_text, fg_color=row_bg,
                                              text_color=theme.tag_text_color))

    lbl_raw = widgets["raw_w"]
    _set_if_changed(cache, "raw_w", (record.chanceWeight, row_bg),
                    lambda: lbl_raw.configure(text=str(record.chanceWeight), fg_color=row_bg))

    lbl_dlc = widgets["dlc_w"]
    _set_if_changed(cache, "dlc_w", (record.chanceWeight_dlc, row_bg),
                    lambda: lbl_dlc.configure(text=str(record.chanceWeight_dlc), fg_color=row_bg))

    lbl_final = widgets["final_w"]
    _set_if_changed(cache, "final_w", (fw, fw_bg),
                    lambda: lbl_final.configure(text=str(fw), fg_color=fw_bg))

    lbl_chance = widgets["chance"]
    _set_if_changed(cache, "chance", (chance_display, row_bg, theme.chance_text_color),
                    lambda: lbl_chance.configure(text=chance_display, fg_color=row_bg,
                                                 text_color=theme.chance_text_color))

    edit_frame = widgets["edit_frame"]
    _set_if_changed(cache, "edit_frame_bg", row_bg,
                    lambda: edit_frame.configure(fg_color=row_bg))

    # --- Entry：值或鎖定狀態不同才 delete + insert / 改變外觀 ---
    entry = widgets["entry"]
    if cache.get("entry_value") != fw or cache.get("entry_locked") != is_locked:
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, str(fw))
        if is_locked:
            entry.configure(state="disabled", fg_color=theme.locked_entry_bg)
        else:
            # 修正既有小瑕疵：解鎖後應還原為預設底色，避免殘留鎖定時的深色底
            entry.configure(fg_color=theme.entry_default_bg)
        cache["entry_value"] = fw
        cache["entry_locked"] = is_locked

    save_btn = widgets["save_btn"]
    _set_if_changed(cache, "locked", is_locked,
                    lambda: save_btn.configure(
                        state="disabled" if is_locked else "normal",
                        fg_color=theme.save_btn_disabled_bg if is_locked else theme.save_btn_normal_bg))


def hide_row(widgets: Dict[str, Any]) -> None:
    """slot 被回收 (不再代表任何資料) 時呼叫，清空快取確保下次強制重繪。"""
    widgets["_state"]["record"] = None
    widgets["_cache"].clear()
