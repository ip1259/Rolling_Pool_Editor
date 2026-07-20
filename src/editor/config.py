"""Persistent user preferences for the editor."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "engus",
    "theme": "Dark",
    "filters": [],
}


class Config:
    def __init__(self, path: Path | None = None) -> None:
        base_dir = Path(os.environ.get("APPDATA", Path.home())) / "RollingPoolEditor"
        self.path = path or base_dir / "config.json"
        self.values = dict(DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        try:
            with self.path.open(encoding="utf-8") as config_file:
                loaded = json.load(config_file)
            if isinstance(loaded, dict):
                self.values.update(loaded)
        except (OSError, ValueError, TypeError):
            pass

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as config_file:
                json.dump(self.values, config_file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def update(self, **values: Any) -> None:
        self.values.update(values)
        self.save()
