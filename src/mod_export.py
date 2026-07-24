"""Export edited weights through the independent .NET regulation helper."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from game_param_res import EditableAttachEffectTableRecord, GameParamManager


BASE_SHA256 = "585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6"
HELPER_NAME = "NightreignRegulationHelper.exe"


class ModExportError(Exception):
    """Raised when the regulation helper rejects or cannot complete an export."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class NoModChangesError(ModExportError):
    """Raised when no editable weights have changed."""


class ModExporter:
    def __init__(
        self,
        game_param: GameParamManager,
        resource_root: Path | None = None,
        helper_path: Path | None = None,
    ) -> None:
        self.game_param = game_param
        self.resource_root = resource_root or self._default_resource_root()
        self.base_path = self.resource_root / "Grand Only" / "regulation.bin"
        self.helper_path = helper_path or self._default_helper_path()

    def export(
        self,
        mod_directory: str | os.PathLike[str],
        manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.game_param.validate_editable()
        manifest = manifest or self.build_manifest()
        output_path = Path(mod_directory).resolve() / "regulation.bin"

        if output_path == self.base_path.resolve():
            raise ModExportError("Output path must not overwrite the fixed base regulation.")
        if not self.base_path.is_file():
            raise ModExportError(f"Base regulation was not found: {self.base_path}")
        if not self.helper_path.is_file():
            raise ModExportError(f"Regulation helper was not found: {self.helper_path}")

        manifest_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                prefix="rolling-pool-editor-",
                delete=False,
            ) as manifest_file:
                json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)
                manifest_path = Path(manifest_file.name)

            command = [
                str(self.helper_path),
                "patch",
                "--base",
                str(self.base_path),
                "--changes",
                str(manifest_path),
                "--output",
                str(output_path),
            ]
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                creationflags=self._subprocess_creation_flags(),
            )
            result = self._parse_result(completed.stdout)
            if completed.returncode != 0 or not result.get("success"):
                message = str(result.get("message") or completed.stderr.strip()
                              or "Regulation helper failed.")
                code = result.get("code")
                raise ModExportError(
                    message,
                    int(code) if isinstance(code, int) else completed.returncode,
                )
            return result
        except OSError as error:
            raise ModExportError(str(error)) from error
        finally:
            if manifest_path is not None:
                try:
                    manifest_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def build_manifest(self) -> dict[str, Any]:
        changes = self.game_param.build_mod_changes()
        if not changes:
            raise NoModChangesError("No editable weights have been modified.")

        editable_table_ids = sorted(
            int(table_id)
            for table_id in EditableAttachEffectTableRecord.EDITABLE_TABLES
        )
        return {
            "formatVersion": 1,
            "baseSha256": BASE_SHA256,
            "param": "AttachEffectTableParam",
            "editableTableIds": editable_table_ids,
            "changes": changes,
        }

    def _default_helper_path(self) -> Path:
        packaged = self.resource_root / "NightreignRegulationHelper" / HELPER_NAME
        if packaged.is_file():
            return packaged

        development = (
            self.resource_root
            / "helper"
            / "NightreignRegulationHelper"
            / "bin"
            / "Release"
            / "net10.0"
            / HELPER_NAME
        )
        return development

    @staticmethod
    def _default_resource_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def _parse_result(stdout: str) -> dict[str, Any]:
        lines = [line for line in stdout.splitlines() if line.strip()]
        if not lines:
            raise ModExportError("Regulation helper returned no result.")
        try:
            result = json.loads(lines[-1])
        except json.JSONDecodeError as error:
            raise ModExportError("Regulation helper returned invalid JSON.") from error
        if not isinstance(result, dict):
            raise ModExportError("Regulation helper returned an invalid result.")
        return result

    @staticmethod
    def _subprocess_creation_flags() -> int:
        return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
