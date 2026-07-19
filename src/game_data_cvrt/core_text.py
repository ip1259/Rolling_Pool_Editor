import os
import glob
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor

# 引入 SQLAlchemy 核心、DDL 與條件式元件
from sqlalchemy import create_engine, MetaData, Table, Column, String, inspect, DDL, case
from sqlalchemy.dialects.sqlite import insert

# === 設定區 ===
PROJECT_ROOT = "data/msg"
DB_NAME = "game_texts.db"
REPORT_NAME = "integration_report.txt"  # 整合成功報告輸出路徑
CHUNK_SIZE = 5000  # 資料庫批次寫入的每批筆數

# 定義目標分類（會以此關鍵字進行檔名匹配，並建立對應資料表）
CATEGORIES = ["Menu", "Goods", "Antique", "AttachEffect"]


def parse_single_file(args: Tuple[str, str, str]) -> Tuple[str, str, str, str, Dict[str, str]]:
    """
    【頂層函式：讓多進程序列化使用】
    單一 XML 檔案的解析任務
    輸入 args: (lang, file_path, category)
    """
    lang, file_path, category = args
    texts = {}
    filename_field = os.path.basename(file_path)
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        xml_filename = root.find('filename')
        if xml_filename is not None and xml_filename.text:
            filename_field = xml_filename.text.strip()

        entries = root.find('entries')
        if entries is not None:
            for elem in entries.findall('text'):
                text_id = elem.get('id')
                if text_id:
                    content = elem.text.strip() if elem.text else "%null%"
                    texts[text_id] = content
    except Exception as e:
        print(f"[錯誤] 解析檔案失敗 {file_path}: {e}")

    return lang, file_path, category, filename_field, texts


def get_languages(root_dir: str) -> List[str]:
    """從目錄結構中找出所有的語言代碼"""
    if not os.path.exists(root_dir):
        return []
    return [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and not d.startswith('.')]


def setup_and_migrate_table(engine, table_name: str, lang_codes: List[str]) -> Table:
    """動態建立或補齊指定資料表的語系欄位"""
    metadata = MetaData()
    inspector = inspect(engine)

    columns = [
        Column('id', String, primary_key=True)
    ]

    for lang in lang_codes:
        columns.append(
            Column(lang, String, default='%null%', server_default='%null%'))

    target_table = Table(table_name, metadata, *columns)

    if not inspector.has_table(table_name):
        metadata.create_all(engine)
        print(f"[資料庫] 建立全新分類資料表 '{table_name}'。")
    else:
        existing_columns = {col['name']
                            for col in inspector.get_columns(table_name)}
        missing_langs = [
            lang for lang in lang_codes if lang not in existing_columns]

        if missing_langs:
            print(f"[資料庫] 資料表 '{table_name}' 補齊缺失語系欄位: {missing_langs}")
            with engine.begin() as conn:
                for lang in missing_langs:
                    dml_stmt = DDL(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{lang}" TEXT DEFAULT "%null%"')
                    conn.execute(dml_stmt)

    return target_table


def integrate_texts():
    lang_codes = get_languages(PROJECT_ROOT)
    if not lang_codes:
        print("[警告] 找不到任何語言資料夾。")
        return

    print(f"[資訊] 偵測到當前目錄語系: {lang_codes}")
    engine = create_engine(f"sqlite:///{DB_NAME}")

    # 動態配置 4 個分類對應的資料表物件
    tables_map = {}
    for cat in CATEGORIES:
        table_name = f"{cat.lower()}_texts"
        tables_map[cat] = setup_and_migrate_table(
            engine, table_name, lang_codes)

    # 1. 收集並過濾符合分類名稱的 XML 檔案任務
    tasks = []
    for lang in lang_codes:
        lang_dir = os.path.join(PROJECT_ROOT, lang)
        xml_files = glob.glob(os.path.join(
            lang_dir, "**", "*.xml"), recursive=True)
        for file_path in xml_files:
            filename = os.path.basename(file_path)

            # 檢查檔名是否包含指定的分類關鍵字（不區分大小寫）
            matched_cat = None
            for cat in CATEGORIES:
                if cat.lower() in filename.lower():
                    matched_cat = cat
                    break

            # 只加入有匹配到分類的任務
            if matched_cat:
                tasks.append((lang, file_path, matched_cat))

    print(f"[資訊] 開始多核心平行解析，篩選後總計 {len(tasks)} 個目標 XML 檔案...")

    # 2. 記憶體聚合容器：結構為 db_data[category][text_id][lang] = (content, source_file)
    db_data: Dict[str, Dict[str, Dict[str, Tuple[str, str]]]] = {
        cat: {} for cat in CATEGORIES}

    # 3. 啟動多進程平行解析
    with ProcessPoolExecutor() as executor:
        results = executor.map(parse_single_file, tasks)

        # 在主進程中收集並執行「權重衝突處理邏輯」
        for lang, file_path, category, filename_field, file_texts in results:
            filename_lower = os.path.basename(file_path).lower()
            is_new_dlc = "dlc01" in filename_lower

            for text_id, content in file_texts.items():
                if text_id not in db_data[category]:
                    db_data[category][text_id] = {}

                # 如果該語系的該 ID 還沒有資料，直接採納
                if lang not in db_data[category][text_id]:
                    db_data[category][text_id][lang] = (content, file_path)
                    continue

                # 既有資料比對
                old_content, old_file = db_data[category][text_id][lang]
                old_filename_lower = os.path.basename(old_file).lower()
                is_old_dlc = "dlc01" in old_filename_lower

                # 優先級規則 1：%null% 最低優先級
                if content == "%null%":
                    # 新內容是空值，直接忽略，保留舊內容
                    continue
                if old_content == "%null%":
                    # 舊內容是空值，新內容是有效字，無條件覆蓋
                    db_data[category][text_id][lang] = (content, file_path)
                    continue

                # 優先級規則 2：雙方皆為有效字，比對 dlc01 權重
                if is_new_dlc and not is_old_dlc:
                    # 新檔案帶有 dlc01，舊檔案沒有 -> 新檔案勝出
                    db_data[category][text_id][lang] = (content, file_path)
                elif not is_new_dlc and is_old_dlc:
                    # 舊檔案帶有 dlc01，新檔案沒有 -> 保留舊檔案
                    continue
                else:
                    # 優先級規則 3：同燈同分（同為 dlc01 或同為普通檔案），直接拋出錯誤中斷
                    raise ValueError(
                        f"\n[嚴重衝突中斷] 在語系 [{lang}] 的 [{category}] 分類中發現同權重的 ID 重複定義！\n"
                        f"  ├─ 文字 ID: {text_id}\n"
                        f"  ├─ 衝突檔案 A: {old_file} (內容: {old_content})\n"
                        f"  └─ 衝突檔案 B: {file_path} (內容: {content})\n"
                        f"請修正原始 XML 檔案後再重新執行整合。"
                    )

    # 4. 依照分類獨立批次安全寫入資料庫
    print("\n[資訊] 衝突檢查完畢（全數通過），開始分表寫入資料庫...")

    with engine.begin() as connection:
        for category in CATEGORIES:
            target_table = tables_map[category]
            category_data = db_data[category]

            if not category_data:
                print(f"  └─ 分類 [{category}] 無任何資料，跳過。")
                continue

            # 整理成 SQLAlchemy 批次格式
            bulk_values = []
            for text_id, langs_map in category_data.items():
                row = {'id': text_id}
                for lang in lang_codes:
                    # 只取 tuple 中的 content
                    row[lang] = langs_map.get(lang, ('%null%', ''))[0]
                bulk_values.append(row)

            # 建立 Upsert 語句
            stmt = insert(target_table)
            set_dict = {}
            for lang in lang_codes:
                lang_col = target_table.c[lang]
                set_dict[lang] = case(
                    ((lang_col == '%null%') |
                     (stmt.excluded[lang] != '%null%'), stmt.excluded[lang]),
                    else_=lang_col
                )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=set_dict
            )

            print(
                f"  └─ 開始寫入資料表 [{target_table.name}]，總計 {len(bulk_values)} 筆...")
            for i in range(0, len(bulk_values), CHUNK_SIZE):
                chunk = bulk_values[i:i+CHUNK_SIZE]
                connection.execute(upsert_stmt, chunk)

    # 5. 產生成功整合報告
    with open(REPORT_NAME, "w", encoding="utf-8") as rep:
        rep.write("=== 遊戲文本精簡整合成功報告 ===\n")
        rep.write("執行狀態: 成功完成（未觸發任何同權重衝突拋錯）\n\n")
        for category in CATEGORIES:
            rep.write(
                f"分類 [{category}] 總計整合不重複 ID 數量: {len(db_data[category])} 筆\n")

    print(f"\n[成功] 整合完成！無任何重複衝突。報告已儲存至：{REPORT_NAME}")


if __name__ == "__main__":
    integrate_texts()
