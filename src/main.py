"""
ChanceWeightEditorApp - 進入點

實際邏輯已依照 plan.md 重構計畫拆分至 editor/ 套件：
    editor/theme_cache.py         主題色彩快取
    editor/localization_cache.py  GUI 文字字典 + GameText 查詢快取
    editor/filter_controller.py   過濾器樹狀結構與父子連動邏輯
    editor/warning_controller.py  3000000 群組警告檢查
    editor/virtual_table.py       Canvas 虛擬捲動表格 (Object Pool recycler)
    editor/table_renderer.py      Header / Row 渲染與差異比對 configure()
    editor/app.py                 ChanceWeightEditorApp 主視窗組裝

與 GameParam / GameText 既有 API 完全相容，未做任何修改。
"""

from editor.app import ChanceWeightEditorApp


if __name__ == "__main__":
    app = ChanceWeightEditorApp()
    app.mainloop()
