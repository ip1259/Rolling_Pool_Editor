import sqlite3
from typing import Dict, Tuple, Optional, List


class CachedCategoryAccessor:
    """Provide dictionary-style access to cached localized text."""

    def __init__(self, table_name: str):
        self._table_name = table_name
        self._cache: Dict[str, str] = {}

    def __getitem__(self, text_id: str) -> str:
        """Return cached text or a visible missing-ID marker."""
        return self._cache.get(text_id, f"Missing_ID<{text_id}>")

    def _refresh_cache(self, conn: sqlite3.Connection, lang: str, fallback_lang: Optional[str]):
        """Reload one text category for the requested languages."""
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

                if primary_text != "%null%" and primary_text is not None:
                    self._cache[tid] = primary_text
                    continue

                if fallback_lang and len(row) > 2:
                    fallback_text = row[2]
                    if fallback_text != "%null%" and fallback_text is not None:
                        self._cache[tid] = fallback_text
                        continue

                self._cache[tid] = f"Null_Content<{tid}>"
        except sqlite3.OperationalError:
            # A language may be unavailable in older text databases.
            pass


class GameTextGuiManager:
    """Load and cache localized game text for the GUI."""

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
        """Return available database languages and their display names."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('PRAGMA table_info("menu_texts")')
                db_langs = [row[1]
                            for row in cursor.fetchall() if row[1] != 'id']
                return [(lang, self.LANGUAGE_MAP.get(lang, lang)) for lang in db_langs]
            except sqlite3.Error:
                return []


GameText = GameTextGuiManager(r"src\game_data\game_texts.db")
