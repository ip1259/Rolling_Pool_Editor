import sqlite3
import csv
import os
from dataclasses import dataclass

# --- I. 智慧型防呆字典 ---


class ParamDict(dict):
    def __getitem__(self, key): return super().__getitem__(str(key))
    def get(self, key, default=None): return super().get(str(key), default)
    def __contains__(self, key): return super().__contains__(str(key))
    def keys(self): return super().keys()


# --- II. 唯讀資料結構 (Data Containers) ---
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


@dataclass(frozen=True)
class AttachEffectTable:
    ID: str
    Name: str
    unknown_0: str  # 已同步加回
    attachEffectId: str
    chanceWeight: int
    chanceWeight_dlc: int


# --- III. 專屬可編輯資料結構 ---
class EditableAttachEffectTableRecord:
    """專供 GUI 編輯使用的資料包，封裝了特殊的權重特判與同步規則"""
    EDITABLE_TABLES = set(["100", "110", "200", "210", "300", "310",
                           "2000000", "2100000", "2200000", "3000000"])

    def __init__(self, ID: str, Name: str, unknown_0: str, attachEffectId: str, chanceWeight: int, chanceWeight_dlc: int):
        self._ID = ID
        self._Name = Name
        self._unknown_0 = unknown_0  # 唯讀留存，確保輸出完整性
        self._attachEffectId = attachEffectId
        self._chanceWeight = chanceWeight
        self._chanceWeight_dlc = chanceWeight_dlc
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
    def final_chance_weight(self) -> int:
        """動態計算最終權重"""
        if self._chanceWeight_dlc == -1:
            return self._chanceWeight
        return self._chanceWeight_dlc

    @property
    def origin_chance_weight(self) -> int:
        return self._originWeight

    def update_weight(self, value: int):
        """修改權重方法 (包含鎖定與聯動規則)"""
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


# --- IV. 核心管理類別 (GameParamManager) ---
class GameParamManager:
    def __init__(self, db_path: str = "game_data/game_param.db"):
        self._db_path = db_path

        self.AttachEffectFilterCategory = ParamDict()
        self.AttachEffectFilter = ParamDict()
        self.AttachEffectFilterSubCategory = ParamDict()
        self.AttachEffect = ParamDict()
        self.AttachEffectTable = ParamDict()
        self.EditableAttachEffectTable = ParamDict()
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

            # 1~4 基礎表加載
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
                "SELECT ID, attachTextId, attachFilterParamId FROM AttachEffectParam")
            self.AttachEffect = ParamDict({r["ID"]: AttachEffect(
                r["ID"], r["attachTextId"], r["attachFilterParamId"]) for r in cursor.fetchall()})

            # 5. 載入 AttachEffectTableParam (依 row_id 排序以維持 CSV 原始順序)
            # 查詢中加入了 unknown_0
            cursor.execute(
                "SELECT ID, Name, unknown_0, attachEffectId, chanceWeight, chanceWeight_dlc FROM AttachEffectTableParam ORDER BY row_id")

            self._raw_table_rows = [dict(row) for row in cursor.fetchall()]

            # 建立唯讀字典 (重複項在此處自然被後續資料覆蓋，GUI 看不到幽靈重複項)
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

            # 同步初始化編輯層
            self.reset_editable()

        except sqlite3.OperationalError as e:
            print(f"⚠️ 讀取資料庫失敗: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def reset_editable(self):
        """重置編輯層：將唯一項暴露給 GUI，並默默將幽靈重複項封存於物理序列"""
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

            # 建立獨立的編輯層物件
            record = EditableAttachEffectTableRecord(
                ID=t_id, Name=row["Name"], unknown_0=unk_0, attachEffectId=eff_id,
                chanceWeight=c_weight, chanceWeight_dlc=c_weight_dlc
            )

            if t_id not in self._editable_chance_map:
                self._editable_chance_map[t_id] = {}

            if key not in seen_keys:
                # 唯一項：塞入 GUI 可見的巢狀字典
                if t_id not in self.EditableAttachEffectTable:
                    self.EditableAttachEffectTable[t_id] = ParamDict()
                self.EditableAttachEffectTable[t_id][eff_id] = record
                seen_keys.add(key)
            else:
                # 幽靈項：不放入 GUI 字典，使其無法被工具檢索與更動
                pass

            # 盲渡關鍵：無論唯一或重複，通通依原始順序塞進物理清單，導出時以此為準
            self._editable_table_order.append(record)

        for k in self._editable_chance_map.keys():
            self.update_chance_rate_map(k)

        print("🔄 編輯層與物理序列已完成再初始化（含 unknown_0 與幽靈項隔離機制）。")

    def update_chance_rate_map(self, id):
        total_weight = sum(
            rcrd.final_chance_weight for rcrd in self.EditableAttachEffectTable[id].values())
        for eid, rcrd in self.EditableAttachEffectTable[id].items():
            self._editable_chance_map[id][eid] = float(
                rcrd.final_chance_weight/total_weight) if total_weight != 0 else 0

    def validate_editable(self) -> bool:
        """核心規則檢驗"""
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

    def export_editable_to_csv(self, output_path: str = "data/param/AttachEffectTableParam.csv"):
        """透過物理清單平鋪輸出，保證輸出檔案的行數、欄位順序與重複項完整性"""
        self.validate_editable()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, mode='w', encoding='utf-8-sig', newline='') as f:
            # ⚠️ 這裡的 fieldnames 順序極度關鍵，必須與遊戲舊有的 CSV 列順序完全一致
            fieldnames = ["ID", "Name", "unknown_0",
                          "attachEffectId", "chanceWeight", "chanceWeight_dlc"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # 依據盲渡物理清單輸出
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


# 全域單例

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
                if record is None or record.origin_chance_weight == 0:
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
        """Apply changed source weights to matching filters in every other table."""
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
                    target = max(candidates, key=lambda item: int(
                        item.attachEffectId))
                else:
                    lower_or_equal = [item for item in candidates if int(
                        item.attachEffectId) <= source_effect_id]
                    if not lower_or_equal:
                        continue
                    target = max(lower_or_equal, key=lambda item: int(
                        item.attachEffectId))
                target.update_weight(source.final_chance_weight)
                touched_tables.add(target_table_id)
                print(
                    f"touched table:{target_table_id}, Effect ID:{target.ID}")
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


GameParam = GameParamManager(r"src\game_data\game_param.db")
