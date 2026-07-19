import csv
import os
from collections import defaultdict


def check_attach_effect_table_duplicates(csv_path="data/param/AttachEffectTableParam.csv"):
    """
    檢查 AttachEffectTableParam.csv 中是否存在重複的 (ID, attachEffectId) 組合
    並印出重複項目所在的 CSV 行號。
    """
    if not os.path.exists(csv_path):
        print(f"❌ 測試失敗：找不到目標 CSV 檔案，路徑為：{csv_path}")
        return

    # 用於追蹤組合的字典
    # Key: (ID, attachEffectId), Value: List[行號]
    key_tracker = defaultdict(list)

    print(f"🚀 開始檢查檔案: {csv_path} ...")

    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        # 使用 DictReader 讀取，會自動將第一行視為欄位名稱
        reader = csv.DictReader(f, delimiter=',')

        for row in reader:
            # 取得目前的實體行號 (物理行號，包含 Header)
            line_num = reader.line_num

            t_id = row.get("ID")
            eff_id = row.get("attachEffectId")

            # 防呆：確保欄位存在
            if t_id is not None and eff_id is not None:
                # 去除前後可能殘留的空白字元
                key = (t_id.strip(), eff_id.strip())
                # 記錄此組合出現在哪一行
                key_tracker[key].append(line_num)

    # 篩選出出現次數大於 1 的重複組合
    duplicates = {k: v for k, v in key_tracker.items() if len(v) > 1}

    # --- 輸出測試報告 ---
    print("\n" + "=" * 30 + " 📊 測試報告 " + "=" * 30)

    if not duplicates:
        print("✅ 【PASS】檢查通過！所有 (ID, attachEffectId) 組合皆具備唯一性。")
        print("   資料庫轉換程式 (db_generator.py) 可以安全執行。")
    else:
        print(f"❌ 【FAIL】檢查失敗：共發現 {len(duplicates)} 組重複的複合主鍵！")
        print("   這會導致資料庫寫入失敗，請先修正以下 CSV 行號的資料：\n")

        # 格式化排版輸出
        print(
            f"{'Table ID':<15} | {'attachEffectId':<15} | {'重複次數':<8} | {'出現的 CSV 行號'}")
        print("-" * 75)

        for (t_id, eff_id), lines in duplicates.items():
            lines_str = ", ".join(f"第 {num} 行" for num in lines)
            print(f"{t_id:<15} | {eff_id:<15} | {len(lines):<8} | {lines_str}")

    print("=" * 72 + "\n")


if __name__ == "__main__":
    # 執行測試
    check_attach_effect_table_duplicates(r"src\game_data_cvrt\data\param\AttachEffectTableParam.csv")
