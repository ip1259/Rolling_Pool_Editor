"""GUI and game-text localization cache."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


LOCALE_DIRECTORY = Path(__file__).with_name("locales")
DEFAULT_LANGUAGE = "engus"


def _load_gui_localizations() -> Dict[str, Dict[str, str]]:
    """Load every GUI locale file so languages can be added without code changes."""
    locale_sources: Dict[str, Tuple[str | None, Dict[str, str]]] = {}
    for locale_path in LOCALE_DIRECTORY.glob("*.json"):
        with locale_path.open(encoding="utf-8") as locale_file:
            content = json.load(locale_file)
        if not isinstance(content, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in content.items()
        ):
            raise ValueError(f"Invalid GUI locale file: {locale_path}")
        base_language = content.pop("$extends", None)
        locale_sources[locale_path.stem] = (base_language, content)

    if DEFAULT_LANGUAGE not in locale_sources:
        raise RuntimeError(f"Missing default GUI locale: {DEFAULT_LANGUAGE}.json")

    localizations: Dict[str, Dict[str, str]] = {}

    def resolve(language: str, resolving: Tuple[str, ...] = ()) -> Dict[str, str]:
        if language in localizations:
            return localizations[language]
        if language in resolving or language not in locale_sources:
            raise ValueError(f"Invalid GUI locale inheritance: {language}")

        base_language, text = locale_sources[language]
        resolved_text = {}
        if base_language:
            resolved_text.update(resolve(base_language, resolving + (language,)))
        resolved_text.update(text)
        localizations[language] = resolved_text
        return resolved_text

    for language in locale_sources:
        resolve(language)
    return localizations


GUI_LOCALIZATION = _load_gui_localizations()


class LocalizationCache:
    """Caches GUI strings and localized names read from the game text database."""

    def __init__(self, game_text_module: Any) -> None:
        self._game_text = game_text_module
        self.current_lang: str = "zhotw"
        self._effect_name_cache: Dict[str, Tuple[str, str]] = {}
        self._cache_key: Tuple[str, str] = ("", "")

    def get_text(self, key: str) -> str:
        default_text = GUI_LOCALIZATION[DEFAULT_LANGUAGE].get(key, key)
        return GUI_LOCALIZATION.get(self.current_lang, {}).get(key, default_text)

    def set_language(self, lang_code: str) -> None:
        self.current_lang = lang_code

    def build_effect_name_cache(
        self, table_id: str, table_dict: Dict[str, Any], game_param_module: Any
    ) -> None:
        cache_key = (self.current_lang, table_id)
        if cache_key == self._cache_key and self._effect_name_cache:
            return

        new_cache: Dict[str, Tuple[str, str]] = {}
        for eff_id in table_dict.keys():
            eff_param = game_param_module.AttachEffect.get(eff_id)
            if not eff_param:
                new_cache[eff_id] = ("Unknown", "None")
                continue

            effect_name = self._game_text.AttachEffect[eff_param.attachTextId]
            filter_text = "None"
            filter_param = game_param_module.AttachEffectFilter.get(
                eff_param.attachFilterParamId
            )
            if filter_param:
                filter_text = self._game_text.AttachEffect[filter_param.filterTextId]

            new_cache[eff_id] = (effect_name, filter_text)

        self._effect_name_cache = new_cache
        self._cache_key = cache_key

    def invalidate(self) -> None:
        self._cache_key = ("", "")

    def get_effect_name_and_filter(self, eff_id: str) -> Tuple[str, str]:
        return self._effect_name_cache.get(eff_id, ("Unknown", "None"))
