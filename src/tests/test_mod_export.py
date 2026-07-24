from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_ROOT.parent
sys.path.insert(0, str(SRC_ROOT))

from game_param_res import GameParam  # noqa: E402
from mod_export import ModExporter, NoModChangesError  # noqa: E402


class ModExporterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        GameParam.reset_editable()
        self.helper_path = (
            PROJECT_ROOT
            / "helper"
            / "NightreignRegulationHelper"
            / "bin"
            / "Release"
            / "net10.0"
            / "NightreignRegulationHelper.exe"
        )
        self.exporter = ModExporter(
            GameParam,
            resource_root=PROJECT_ROOT,
            helper_path=self.helper_path,
        )

    def tearDown(self) -> None:
        GameParam.reset_editable()

    def test_manifest_rejects_no_changes(self) -> None:
        with self.assertRaises(NoModChangesError):
            self.exporter.build_manifest()

    def test_manifest_only_contains_modified_editable_row(self) -> None:
        record = GameParam.EditableAttachEffectTable["100"]["7000000"]
        record.update_weight(100)

        manifest = self.exporter.build_manifest()

        self.assertEqual(1, len(manifest["changes"]))
        self.assertEqual(
            {
                "id": 100,
                "attachEffectId": 7_000_000,
                "occurrence": 0,
                "expectedChanceWeight": 52,
                "expectedChanceWeightDlc": -1,
                "chanceWeight": 100,
                "chanceWeightDlc": -1,
            },
            manifest["changes"][0],
        )

    def test_manifest_never_includes_non_editable_table(self) -> None:
        non_editable_record = next(
            record
            for table_id, table in GameParam.EditableAttachEffectTable.items()
            if table_id not in {
                "100", "110", "200", "210", "300", "310",
                "2000000", "2100000", "2200000", "3000000",
            }
            for record in table.values()
            if record.origin_chance_weight > 0
        )
        non_editable_record.update_weight(
            non_editable_record.final_chance_weight + 1
        )

        with self.assertRaises(NoModChangesError):
            self.exporter.build_manifest()

    def test_export_produces_verified_regulation(self) -> None:
        if not self.helper_path.is_file():
            self.skipTest("Release helper has not been built.")

        record = GameParam.EditableAttachEffectTable["100"]["7000000"]
        record.update_weight(100)

        with tempfile.TemporaryDirectory(
            prefix="rolling-pool-editor-tests-"
        ) as output_directory:
            result = self.exporter.export(output_directory)
            output_path = Path(output_directory) / "regulation.bin"

            self.assertTrue(result["success"])
            self.assertEqual(1, result["details"]["modifiedCount"])
            self.assertTrue(output_path.is_file())


if __name__ == "__main__":
    unittest.main()
