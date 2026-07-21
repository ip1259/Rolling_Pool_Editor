# Rolling Pool Editor

[繁體中文](#繁體中文) | [English](#english)

## 繁體中文

### 專案簡介

Rolling Pool Editor 是一套用於《艾爾登法環 黑夜君臨》（ELDEN RING NIGHTREIGN）的開源 Mod 輔助製作工具，專門協助修改遺物抽獎池的效果權重與出現機率。

本程式負責編輯抽獎池資料並輸出 Smithbox 相容的 `AttachEffectTableParam.csv`，無法單獨產生最終 Mod。輸出的 CSV 必須搭配 **Smithbox** 匯入 `regulation.bin`，再透過 **Mod Engine 3（ME3）** 載入修改後的 Mod。

### 主要功能

- 依遊戲效果標籤篩選遺物效果。
- 編輯效果權重並即時計算出現機率。
- 支援一般 Relic、Deep Relic 與 Debuff 等多種抽獎池 Table。
- 將篩選結果批次增加權重，或將未修改項目設為 `1`。
- 依效果的堆疊類型自動設定所有 Table，並保留鎖定項與已修改項。
- 依效果標籤與 Effect ID 規則，將修改套用至其他 Table。
- 從既有 CSV 匯入權重設定。
- 驗證 Debuff 池的最低項目數量並匯出 Smithbox 相容 CSV。
- 提供多語言介面及 Dark／Light 主題，並自動保存語言、主題與篩選設定。

### 使用方式

#### Windows x64 打包版

下載並解壓縮 Windows x64 打包檔後，執行 `RollingPoolEditor.exe`。

#### 從原始碼執行

本專案使用 Python 3.13，並以 `uv` 管理虛擬環境與相依套件：

```powershell
uv sync
uv run python src/main.py
```

請從專案根目錄啟動程式。主程式進入點為 `src/main.py`。

### 基本工作流程

1. 選擇要編輯的 Table ID。
2. 使用效果標籤篩選項目，手動調整權重或執行「自動設定」。
3. 檢查各項效果的即時出現機率。
4. 驗證並匯出 `AttachEffectTableParam.csv`。
5. 在 Smithbox 中將同一份 CSV 分別匯入 `chanceWeight` 與 `chanceWeight_dlc`。
6. 將修改後的 `regulation.bin` 作為 Mod，透過 ME3 載入。

> [!IMPORTANT]
> Smithbox 一次只能匯入一個 Specific Field，因此 `chanceWeight` 與 `chanceWeight_dlc` 必須分別操作一次。請勿使用 **All Field** 匯入。

> [!CAUTION]
> 建議使用 ME3 管理及載入 Mod，不要直接覆蓋遊戲原始的 `regulation.bin`。若忘記在連線遊玩前還原修改檔案，帳號可能面臨封鎖風險。

### 詳細文件

- [程式操作手冊（繁體中文）](USER_MANUAL_zh-TW.md)
- [Smithbox 匯入與 Mod 載入指南（繁體中文）](SMITHBOX_GUIDE_zh-TW.md)
- [Grand Only Base](Grand%20Only/regulation.bin)：以 Regulation Ver. 1.03.5 為基礎的 `regulation.bin`

---

## English

### About

Rolling Pool Editor is an open-source modding utility for **ELDEN RING NIGHTREIGN**. It is specifically designed to help create mods that adjust effect weights and probabilities in Relic rolling pools.

The application edits rolling-pool data and exports a Smithbox-compatible `AttachEffectTableParam.csv`; it cannot create the final mod by itself. The exported CSV must be imported into `regulation.bin` with **Smithbox**, after which the modified mod can be loaded through **Mod Engine 3 (ME3)**.

### Features

- Filter Relic effects by their in-game effect tags.
- Edit effect weights and recalculate chance rates in real time.
- Work with standard Relic, Deep Relic, and Debuff pool Tables.
- Increase filtered weights in batches or set unmodified entries to `1`.
- Automatically configure every Table according to effect stacking behavior while preserving locked and previously modified entries.
- Apply changes to other Tables using effect-tag and Effect ID mapping rules.
- Import weight settings from an existing CSV.
- Validate the minimum Debuff-pool size and export a Smithbox-compatible CSV.
- Use a multilingual interface with Dark and Light themes; language, theme, and filter selections are saved automatically.

### Running the application

#### Packaged Windows x64 version

Download and extract the Windows x64 package, then run `RollingPoolEditor.exe`.

#### Running from source

The project uses Python 3.13 and `uv` for its virtual environment and dependencies:

```powershell
uv sync
uv run python src/main.py
```

Run the application from the repository root. Its entry point is `src/main.py`.

### Basic workflow

1. Select the Table ID to edit.
2. Filter effects by tag, then adjust weights manually or use **Auto Configure**.
3. Review the recalculated chance rates.
4. Validate and export `AttachEffectTableParam.csv`.
5. Import the same CSV into both `chanceWeight` and `chanceWeight_dlc` separately in Smithbox.
6. Use the modified `regulation.bin` as a mod and load it through ME3.

> [!IMPORTANT]
> Smithbox can import only one Specific Field at a time, so `chanceWeight` and `chanceWeight_dlc` must be imported in two separate operations. Do not use **All Field**.

> [!CAUTION]
> Use ME3 to manage and load mods instead of overwriting the game's original `regulation.bin`. Forgetting to restore a modified game file before going online may put your account at risk of a ban.

### Documentation

- [User Manual (English)](USER_MANUAL_en.md)
- [Smithbox Import and Mod Loading Guide (English)](SMITHBOX_GUIDE_en.md)
- [Grand Only Base](Grand%20Only/regulation.bin): a `regulation.bin` based on Regulation Ver. 1.03.5
