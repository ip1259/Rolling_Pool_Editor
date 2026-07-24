import sqlite3
import csv
import os
from dataclasses import dataclass

class ParamDict(dict):
    def __getitem__(self, key): return super().__getitem__(str(key))
    def get(self, key, default=None): return super().get(str(key), default)
    def __contains__(self, key): return super().__contains__(str(key))
    def keys(self): return super().keys()


@dataclass(frozen=True)
class AttachEffectFilterCategory:
    ID: str
    textId: str
    category: str


@dataclass(frozen=True)
class AttachEffectFilter:
    ID: str
    filterTextId: str
    attachEffectFilterCategory: str


@dataclass(frozen=True)
class AttachEffectFilterSubCategory:
    ID: str
    textId: str
    filterCategory: str


@dataclass(frozen=True)
class AttachEffect:
    ID: str
    attachTextId: str
    attachFilterParamId: str
    passiveSpEffectId_1: str


@dataclass(frozen=True)
class AttachEffectTable:
    ID: str
    Name: str
    unknown_0: str
    attachEffectId: str
    chanceWeight: int
    chanceWeight_dlc: int


@dataclass(frozen=True)
class SpEffectParam:
    ID: str
    spCategory: str


class EditableAttachEffectTableRecord:
    """Mutable weight record used by the editor."""
    EDITABLE_TABLES = set(["100", "110", "200", "210", "300", "310",
                           "2000000", "2100000", "2200000", "3000000"])

    def __init__(self, ID: str, Name: str, unknown_0: str, attachEffectId: str, chanceWeight: int, chanceWeight_dlc: int):
        self._ID = ID
        self._Name = Name
        self._unknown_0 = unknown_0
        self._attachEffectId = attachEffectId
        self._chanceWeight = chanceWeight
        self._chanceWeight_dlc = chanceWeight_dlc
        self._originalChanceWeight = chanceWeight
        self._originalChanceWeightDlc = chanceWeight_dlc
        self._originWeight = chanceWeight if chanceWeight_dlc == -1 else chanceWeight_dlc

    @property
    def ID(self) -> str: return self._ID
    @property
    def Name(self) -> str: return self._Name
    @property
    def unknown_0(self) -> str: return self._unknown_0
    @property
    def attachEffectId(self) -> str: return self._attachEffectId
    @property
    def chanceWeight(self) -> int: return self._chanceWeight
    @property
    def chanceWeight_dlc(self) -> int: return self._chanceWeight_dlc
    @property
    def original_chance_weight(self) -> int: return self._originalChanceWeight
    @property
    def original_chance_weight_dlc(self) -> int: return self._originalChanceWeightDlc

    @property
    def final_chance_weight(self) -> int:
        """Return the DLC weight when present, otherwise the base weight."""
        if self._chanceWeight_dlc == -1:
            return self._chanceWeight
        return self._chanceWeight_dlc

    @property
    def origin_chance_weight(self) -> int:
        return self._originWeight

    @property
    def is_modified(self) -> bool:
        return self.final_chance_weight != self._originWeight

    def update_weight(self, value: int):
        """Update both weight fields when the record has a DLC override."""
        if self._originWeight == 0:
            raise PermissionError(
                f"❌ 修改失敗：項目 (Table: {self._ID}, Effect: {self._attachEffectId}) "
                f"最終權重為 0，此項已被鎖定，不能修改！"
            )

        target_value = int(value)
        if self._chanceWeight_dlc != -1:
            self._chanceWeight = target_value
            self._chanceWeight_dlc = target_value
        else:
            self._chanceWeight = target_value


class GameParamManager:
    def __init__(self, db_path: str = "game_data/game_param.db"):
        self._db_path = db_path

        self.AttachEffectFilterCategory = ParamDict()
        self.AttachEffectFilter = ParamDict()
        self.AttachEffectFilterSubCategory = ParamDict()
        self.AttachEffect = ParamDict()
        self.AttachEffectTable = ParamDict()
        self.EditableAttachEffectTable = ParamDict()
        self.SpEffect = ParamDict()
        self._editable_chance_map = dict()

        self._raw_table_rows = []
        self._editable_table_order = []

        self.reload()

    @property
    def editable_chance_map(self):
        return self._editable_chance_map

    def reload(self):
        """從 SQLite 資料庫讀取數據並建立初始快取"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT ID, textId, category FROM AttachEffectFilterCategoryParam")
            self.AttachEffectFilterCategory = ParamDict({r["ID"]: AttachEffectFilterCategory(
                r["ID"], r["textId"], r["category"]) for r in cursor.fetchall()})
            cursor.execute(
                "SELECT ID, filterTextId, attachEffectFilterCategory FROM AttachEffectFilterParam")
            self.AttachEffectFilter = ParamDict({r["ID"]: AttachEffectFilter(
                r["ID"], r["filterTextId"], r["attachEffectFilterCategory"]) for r in cursor.fetchall()})
            cursor.execute(
                "SELECT ID, textId, filterCategory FROM AttachEffectFilterSubCategoryParam")
            self.AttachEffectFilterSubCategory = ParamDict({r["ID"]: AttachEffectFilterSubCategory(
                r["ID"], r["textId"], r["filterCategory"]) for r in cursor.fetchall()})
            cursor.execute(
                "SELECT ID, attachTextId, attachFilterParamId, passiveSpEffectId_1 FROM AttachEffectParam")
            self.AttachEffect = ParamDict({r["ID"]: AttachEffect(
                r["ID"], r["attachTextId"], r["attachFilterParamId"], r['passiveSpEffectId_1']) for r in cursor.fetchall()})
            cursor.execute(
                "SELECT ID, spCategory FROM SpEffectParam")
            self.SpEffect = ParamDict({r["ID"]: SpEffectParam(
                r["ID"], r["spCategory"]) for r in cursor.fetchall()})

            # row_id preserves the source CSV order.
            cursor.execute(
                "SELECT ID, Name, unknown_0, attachEffectId, chanceWeight, chanceWeight_dlc FROM AttachEffectTableParam ORDER BY row_id")

            self._raw_table_rows = [dict(row) for row in cursor.fetchall()]

            # Duplicate keys remain in _raw_table_rows but are hidden from the GUI map.
            self.AttachEffectTable.clear()
            for row in self._raw_table_rows:
                t_id = str(row["ID"])
                eff_id = str(row["attachEffectId"])
                c_weight = row["chanceWeight"] if row["chanceWeight"] is not None else 0
                c_weight_dlc = row["chanceWeight_dlc"] if row["chanceWeight_dlc"] is not None else 0
                unk_0 = str(row["unknown_0"]
                            ) if row["unknown_0"] is not None else ""

                item = AttachEffectTable(
                    t_id, row["Name"], unk_0, eff_id, c_weight, c_weight_dlc)
                if t_id not in self.AttachEffectTable:
                    self.AttachEffectTable[t_id] = ParamDict()
                self.AttachEffectTable[t_id][eff_id] = item

            self.reset_editable()

        except sqlite3.OperationalError as e:
            print(f"⚠️ 讀取資料庫失敗: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def reset_editable(self):
        """Rebuild editable records while preserving duplicate rows for export."""
        self.EditableAttachEffectTable.clear()
        self._editable_table_order.clear()
        self._editable_chance_map.clear()

        seen_keys = set()

        for row in self._raw_table_rows:
            t_id = str(row["ID"])
            eff_id = str(row["attachEffectId"])
            key = (t_id, eff_id)

            c_weight = row["chanceWeight"] if row["chanceWeight"] is not None else 0
            c_weight_dlc = row["chanceWeight_dlc"] if row["chanceWeight_dlc"] is not None else 0
            unk_0 = str(row["unknown_0"]
                        ) if row["unknown_0"] is not None else ""

            record = EditableAttachEffectTableRecord(
                ID=t_id, Name=row["Name"], unknown_0=unk_0, attachEffectId=eff_id,
                chanceWeight=c_weight, chanceWeight_dlc=c_weight_dlc
            )

            if t_id not in self._editable_chance_map:
                self._editable_chance_map[t_id] = {}

            if key not in seen_keys:
                if t_id not in self.EditableAttachEffectTable:
                    self.EditableAttachEffectTable[t_id] = ParamDict()
                self.EditableAttachEffectTable[t_id][eff_id] = record
                seen_keys.add(key)
            else:
                pass

            # Export uses this complete ordered list, including duplicate keys.
            self._editable_table_order.append(record)

        for k in self._editable_chance_map.keys():
            self.update_chance_rate_map(k)

        print("編輯層與物理序列已完成再初始化（含 unknown_0 與幽靈項隔離機制）。")

    def update_chance_rate_map(self, id):
        total_weight = sum(
            rcrd.final_chance_weight for rcrd in self.EditableAttachEffectTable[id].values())
        for eid, rcrd in self.EditableAttachEffectTable[id].items():
            self._editable_chance_map[id][eid] = float(
                rcrd.final_chance_weight/total_weight) if total_weight != 0 else 0

    def validate_editable(self) -> bool:
        """Validate constraints required before export."""
        target_id = "3000000"
        if target_id in self.EditableAttachEffectTable:
            non_zero_items = [
                item for item in self.EditableAttachEffectTable[target_id].values()
                if item.final_chance_weight != 0
            ]
            if len(non_zero_items) < 3:
                raise ValueError(
                    f"❌ 導出失敗！ID 為 {target_id} 的群組中，"
                    f"最終權重非 0 的數量僅有 {len(non_zero_items)} 筆，不能小於 3 筆！"
                )
        return True

    def build_mod_changes(self) -> list[dict]:
        """Return modified editable rows with stable duplicate occurrences."""
        changes = []
        occurrences = {}

        for record in self._editable_table_order:
            identity = (record.ID, record.attachEffectId)
            occurrence = occurrences.get(identity, 0)
            occurrences[identity] = occurrence + 1

            if record.ID not in EditableAttachEffectTableRecord.EDITABLE_TABLES:
                continue
            if not record.is_modified:
                continue

            changes.append({
                "id": int(record.ID),
                "attachEffectId": int(record.attachEffectId),
                "occurrence": occurrence,
                "expectedChanceWeight": record.original_chance_weight,
                "expectedChanceWeightDlc": record.original_chance_weight_dlc,
                "chanceWeight": record.chanceWeight,
                "chanceWeightDlc": record.chanceWeight_dlc,
            })

        return changes

    def export_editable_to_csv(self, output_path: str = "data/param/AttachEffectTableParam.csv"):
        """透過物理清單平鋪輸出，保證輸出檔案的行數、欄位順序與重複項完整性"""
        self.validate_editable()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, mode='w', encoding='utf-8-sig', newline='') as f:
            # Smithbox expects this field order.
            fieldnames = ["ID", "Name", "unknown_0",
                          "attachEffectId", "chanceWeight", "chanceWeight_dlc"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for item in self._editable_table_order:
                writer.writerow({
                    "ID": item.ID,
                    "Name": item.Name,
                    "unknown_0": item.unknown_0,
                    "attachEffectId": item.attachEffectId,
                    "chanceWeight": item.chanceWeight,
                    "chanceWeight_dlc": item.chanceWeight_dlc
                })
        print(f"💾 配置校驗通過，已依原 CSV 完整佈局還原輸出：{output_path}")

    def import_editable_from_csv(self, csv_path: str) -> int:
        """Import weights into existing editable records by table and effect IDs."""
        updated_tables = set()
        updated_count = 0
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            required = {"ID", "attachEffectId",
                        "chanceWeight", "chanceWeight_dlc"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(
                    "CSV must include ID, attachEffectId, chanceWeight, and chanceWeight_dlc columns.")
            for row in reader:
                table_id, effect_id = str(
                    row["ID"]), str(row["attachEffectId"])
                record = self.EditableAttachEffectTable.get(
                    table_id, {}).get(effect_id)
                if (table_id not in EditableAttachEffectTableRecord.EDITABLE_TABLES
                        or record is None
                        or record.origin_chance_weight == 0):
                    continue
                dlc_weight = int(row["chanceWeight_dlc"])
                record.update_weight(
                    dlc_weight if dlc_weight != -1 else int(row["chanceWeight"]))
                updated_tables.add(table_id)
                updated_count += 1
        for table_id in updated_tables:
            self.update_chance_rate_map(table_id)
        return updated_count

    def apply_table_changes_to_others(self, source_table_id: str) -> int:
        """Apply changed source weights to matching filters in every other table.

        Increased weights still target the highest Effect ID. Decreased weights
        target every matching Effect ID less than or equal to the source ID.
        """
        TARGET_TABLES = EditableAttachEffectTableRecord.EDITABLE_TABLES
        source_table = self.EditableAttachEffectTable.get(source_table_id, {})
        changes = [record for record in source_table.values()
                   if record.origin_chance_weight > 0
                   and record.final_chance_weight != record.origin_chance_weight]
        touched_tables = set()
        applied_count = 0
        for target_table_id, target_table in self.EditableAttachEffectTable.items():
            if target_table_id == source_table_id or str(target_table_id) not in TARGET_TABLES:
                continue
            for source in changes:
                source_effect = self.AttachEffect.get(source.attachEffectId)
                if source_effect is None:
                    continue
                candidates = []
                for target in target_table.values():
                    target_effect = self.AttachEffect.get(
                        target.attachEffectId)
                    if (target.origin_chance_weight > 0 and target_effect is not None
                            and target_effect.attachFilterParamId == source_effect.attachFilterParamId):
                        candidates.append(target)
                if not candidates:
                    continue
                source_effect_id = int(source.attachEffectId)
                if source.final_chance_weight > source.origin_chance_weight:
                    targets = [max(candidates, key=lambda item: int(
                        item.attachEffectId))]
                else:
                    targets = [item for item in candidates if int(
                        item.attachEffectId) <= source_effect_id]
                    if not targets:
                        continue
                for target in targets:
                    target.update_weight(source.final_chance_weight)
                    touched_tables.add(target_table_id)
                    print(
                        f"touched table:{target_table_id}, Effect ID:{target.attachEffectId}")
                    applied_count += 1
        for table_id in touched_tables:
            self.update_chance_rate_map(table_id)
        return applied_count

    def set_unmodified_editable_records_to_one(self, table_id: str) -> int:
        """Set untouched, non-locked records to one in one editable table."""
        if table_id not in EditableAttachEffectTableRecord.EDITABLE_TABLES:
            return 0
        changed_count = 0
        for record in self.EditableAttachEffectTable.get(table_id, {}).values():
            if record.origin_chance_weight > 0 and record.final_chance_weight == record.origin_chance_weight:
                record.update_weight(1)
                changed_count += 1
        if changed_count:
            self.update_chance_rate_map(table_id)
        return changed_count

    def auto_configure_all_tables(self, active_filter_ids) -> int:
        """Apply automatic weights to untouched records in every editable table."""
        changed_count = 0
        touched_tables = set()

        for table_id, table in self.EditableAttachEffectTable.items():
            if table_id not in EditableAttachEffectTableRecord.EDITABLE_TABLES:
                continue

            eligible = [record for record in table.values()
                        if record.origin_chance_weight > 0 and not record.is_modified]
            filtered_groups = {}

            for record in eligible:
                effect = self.AttachEffect.get(record.attachEffectId)
                if effect is None or effect.attachFilterParamId not in active_filter_ids:
                    if record.final_chance_weight != 1:
                        record.update_weight(1)
                        changed_count += 1
                        touched_tables.add(table_id)
                    continue
                filtered_groups.setdefault(effect.attachFilterParamId, []).append(record)

            for records in filtered_groups.values():
                records.sort(key=lambda item: int(item.attachEffectId), reverse=True)
                highest_effect = self.AttachEffect[records[0].attachEffectId]
                sp_effect = self.SpEffect.get(highest_effect.passiveSpEffectId_1)
                sp_category = sp_effect.spCategory if sp_effect is not None else ""

                for index, record in enumerate(records):
                    if sp_category == "10":
                        target_weight = (record.final_chance_weight + 300
                                         if index == 0 else 1)
                    elif sp_category == "20":
                        target_weight = record.final_chance_weight + max(0, 300 - index * 50)
                    else:
                        target_weight = record.final_chance_weight + 300

                    if target_weight != record.final_chance_weight:
                        record.update_weight(target_weight)
                        changed_count += 1
                        touched_tables.add(table_id)

        for table_id in touched_tables:
            self.update_chance_rate_map(table_id)
        return changed_count

GameParam = GameParamManager(r"src\game_data\game_param.db")
