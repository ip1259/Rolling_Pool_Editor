import sqlite3
from typing import Dict, Tuple, Optional, List


class CachedCategoryAccessor:
    """記憶體快取代理器，兼顧 Goods[ID] 語法與 GUI 絲滑度"""

    def __init__(self, table_name: str):
        self._table_name = table_name
        self._cache: Dict[str, str] = {}  # 儲存目前語系的所有文字快取

    def __getitem__(self, text_id: str) -> str:
        """直接從記憶體 Dict 查詢，零硬碟開銷"""
        return self._cache.get(text_id, f"Missing_ID<{text_id}>")

    def _refresh_cache(self, conn: sqlite3.Connection, lang: str, fallback_lang: Optional[str]):
        """當全域切換語系時，由 Manager 觸發此方法更新記憶體"""
        self._cache.clear()

        columns = ['id', f'"{lang}"']
        if fallback_lang:
            columns.append(f'"{fallback_lang}"')

        sql = f'SELECT {", ".join(columns)} FROM "{self._table_name}"'

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor.fetchall():
                tid = row[0]
                primary_text = row[1]

                # 1. 優先採用主要語系
                if primary_text != "%null%" and primary_text is not None:
                    self._cache[tid] = primary_text
                    continue

                # 2. 主要語系為空，嘗試採用回退語系
                if fallback_lang and len(row) > 2:
                    fallback_text = row[2]
                    if fallback_text != "%null%" and fallback_text is not None:
                        self._cache[tid] = fallback_text
                        continue

                # 3. 兩者皆空
                self._cache[tid] = f"Null_Content<{tid}>"
        except sqlite3.OperationalError:
            # 預防資料庫中不存在該語系欄位
            pass


class GameTextGuiManager:
    """專供 GUI 輔助程式使用的全域文本管理器"""

    # 語系與其原生名稱（Native Name）的對照表
    LANGUAGE_MAP = {
        "araae": "العربية",
        "deude": "Deutsch",
        "engus": "English",
        "frafr": "Français",
        "itait": "Italiano",
        "jpnjp": "日本語",
        "korkr": "한국어",
        "polpl": "Polski",
        "porbr": "Português (Brasil)",
        "rusru": "Русский",
        "spaar": "Español (Latinoamérica)",
        "spaes": "Español (España)",
        "thath": "ไทย",
        "zhocn": "简体中文",
        "zhotw": "繁體中文"
    }

    def __init__(self, db_path: str = "game_texts_split.db"):
        self.db_path = db_path
        self._current_lang = "engus"
        self._fallback_lang = "engus"

        # 實例化各分類的快取代理器
        self.Menu = CachedCategoryAccessor("menu_texts")
        self.Goods = CachedCategoryAccessor("goods_texts")
        self.Antique = CachedCategoryAccessor("antique_texts")
        self.AttachEffect = CachedCategoryAccessor("attacheffect_texts")

        self._accessors = [self.Menu, self.Goods,
                           self.Antique, self.AttachEffect]

    def change_language(self, lang: str, fallback_lang: Optional[str] = "engus"):
        """GUI 啟動或使用者切換語系時呼叫，自動刷新記憶體快取"""
        self._current_lang = lang
        self._fallback_lang = fallback_lang

        try:
            with sqlite3.connect(self.db_path) as conn:
                for accessor in self._accessors:
                    accessor._refresh_cache(conn, lang, fallback_lang)
            print(
                f"[GameText] 語系切換至: {self.get_current_lang_display()} (回退: {self.LANGUAGE_MAP.get(fallback_lang, fallback_lang)})")
        except sqlite3.Error as e:
            print(f"[GameText 錯誤] 無法載入資料庫: {e}")

    def get_current_lang_display(self) -> str:
        """獲取當前語系的人類可讀名稱"""
        return self.LANGUAGE_MAP.get(self._current_lang, self._current_lang)

    def get_available_languages_for_gui(self) -> List[Tuple[str, str]]:
        """
        自動掃描資料庫中實際擁有的語系欄位，並對照 MAP 傳回給 GUI 繪製下拉選單。
        傳回格式: [('engus', 'English'), ('zhotw', '繁體中文'), ...]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('PRAGMA table_info("menu_texts")')
                db_langs = [row[1]
                            for row in cursor.fetchall() if row[1] != 'id']
                return [(lang, self.LANGUAGE_MAP.get(lang, lang)) for lang in db_langs]
            except sqlite3.Error:
                return []


# 實例化全域物件
GameText = GameTextGuiManager(r"src\game_data\game_texts.db")
