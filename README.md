# Rolling Pool Editor

[繁體中文](#繁體中文) | [English](#english)

## 繁體中文

### 專案簡介

Rolling Pool Editor 是一套用於《艾爾登法環 黑夜君臨》（ELDEN RING NIGHTREIGN）的開源 Mod 輔助製作工具，專門協助修改遺物抽獎池的效果權重與出現機率。

本程式可將編輯結果直接套用至內建的 Regulation Ver. 1.03.5 基底，輸出可供 **Mod Engine 3（ME3）** 使用的 `regulation.bin`，不需要另外使用 Smithbox。既有的 Smithbox 相容 CSV 匯入／匯出功能仍予保留。

### 主要功能

- 依遊戲效果標籤篩選遺物效果。
- 編輯效果權重並即時計算出現機率。
- 支援一般 Relic、Deep Relic 與 Debuff 等多種抽獎池 Table。
- 將篩選結果批次增加權重，或將未修改項目設為 `1`。
- 依效果的堆疊類型自動設定所有 Table，並保留鎖定項與已修改項。
- 依效果標籤與 Effect ID 規則，將修改套用至其他 Table。
- 從既有 CSV 匯入權重設定。
- 驗證 Debuff 池的最低項目數量並匯出 Smithbox 相容 CSV。
- 直接輸出經完整驗證的 `regulation.bin`；只會寫入已修改且可編輯的 Table。
- 提供多語言介面及 Dark／Light 主題，並自動保存語言、主題與篩選設定。

### 使用方式

#### Windows x64 打包版

下載並解壓縮 Windows x64 打包檔後，執行 `RollingPoolEditor.exe`。

此打包版已在未安裝 Python、.NET SDK／Runtime 及 Smithbox 的 Windows 電腦完成啟動與輸出測試；產生的 `regulation.bin` 亦已確認可在遊戲中正常使用。

#### 從原始碼執行

本專案使用 Python 3.13，並以 `uv` 管理虛擬環境與相依套件：

```powershell
uv sync
uv run python src/main.py
```

請從專案根目錄啟動程式。主程式進入點為 `src/main.py`。

若要建立包含固定 Regulation 基底與自包含 .NET Helper 的 Windows x64 發布包，請依照 [Windows x64 建置說明（繁體中文）](BUILD_zh-TW.md) 操作。僅執行上述 Python 指令不會建立完整發布包。

### 基本工作流程

1. 選擇要編輯的 Table ID。
2. 使用效果標籤篩選項目，手動調整權重或執行「自動設定」。
3. 檢查各項效果的即時出現機率。
4. 按下「輸出 MOD」並選擇 MOD 資料夾。
5. 若資料夾中已有 `regulation.bin`，確認是否覆寫。
6. 透過 ME3 載入輸出的 `regulation.bin`。

> [!IMPORTANT]
> 若選擇傳統 CSV 流程，Smithbox 一次只能匯入一個 Specific Field，因此 `chanceWeight` 與 `chanceWeight_dlc` 必須分別操作一次。請勿使用 **All Field** 匯入。

> [!CAUTION]
> 建議使用 ME3 管理及載入 Mod，不要直接覆蓋遊戲原始的 `regulation.bin`。若忘記在連線遊玩前還原修改檔案，帳號可能面臨封鎖風險。

### 詳細文件

- [程式操作手冊（繁體中文）](USER_MANUAL_zh-TW.md)
- [Smithbox 匯入與 Mod 載入指南（繁體中文）](SMITHBOX_GUIDE_zh-TW.md)
- [Grand Only Base](Grand%20Only/regulation.bin)：以 Regulation Ver. 1.03.5 為基礎的 `regulation.bin`

### 引用與感謝

本專案的 Nightreign `regulation.bin` 加解密、DCX／BND4 及 PARAM 讀寫功能，採用 [Smithbox](https://github.com/vawser/Smithbox) 專案中的 `Andre.SoulsFormats` 程式庫，固定於 commit `1538fed4cfa5f3618a7a0191ff753ce4a1d54c00`，並依 MIT License 使用與散佈。來源及版本紀錄請參閱 [Andre.SoulsFormats provenance](helper/vendor/Andre.SoulsFormats.provenance.md)，授權全文請參閱 [Smithbox MIT License](helper/vendor/LICENSE-Smithbox.txt)。

特別感謝 **Vawser、Smithbox 與 SoulsFormats 的開發及貢獻者**，使 Nightreign Regulation 的格式處理與本工具的直接 MOD 輸出功能得以實現。

---

## English

### About

Rolling Pool Editor is an open-source modding utility for **ELDEN RING NIGHTREIGN**. It is specifically designed to help create mods that adjust effect weights and probabilities in Relic rolling pools.

The application can apply edits directly to its bundled Regulation Ver. 1.03.5 base and export a verified `regulation.bin` for **Mod Engine 3 (ME3)**. Smithbox is not required for this workflow. The existing Smithbox-compatible CSV import and export features remain available.

### Features

- Filter Relic effects by their in-game effect tags.
- Edit effect weights and recalculate chance rates in real time.
- Work with standard Relic, Deep Relic, and Debuff pool Tables.
- Increase filtered weights in batches or set unmodified entries to `1`.
- Automatically configure every Table according to effect stacking behavior while preserving locked and previously modified entries.
- Apply changes to other Tables using effect-tag and Effect ID mapping rules.
- Import weight settings from an existing CSV.
- Validate the minimum Debuff-pool size and export a Smithbox-compatible CSV.
- Export a fully verified `regulation.bin` directly; only modified rows in editable Tables are written.
- Use a multilingual interface with Dark and Light themes; language, theme, and filter selections are saved automatically.

### Running the application

#### Packaged Windows x64 version

Download and extract the Windows x64 package, then run `RollingPoolEditor.exe`.

The packaged build has been tested on a Windows computer without Python, the .NET SDK/runtime, or Smithbox installed. It starts and exports successfully, and the generated `regulation.bin` has been confirmed to work in game.

#### Running from source

The project uses Python 3.13 and `uv` for its virtual environment and dependencies:

```powershell
uv sync
uv run python src/main.py
```

Run the application from the repository root. Its entry point is `src/main.py`.

To create the complete Windows x64 distribution with the fixed Regulation base and self-contained .NET helper, follow the [Windows x64 Build Guide (English)](BUILD_en.md). Running the Python commands above does not create the complete distribution.

### Basic workflow

1. Select the Table ID to edit.
2. Filter effects by tag, then adjust weights manually or use **Auto Configure**.
3. Review the recalculated chance rates.
4. Click **Export MOD** and select a MOD folder.
5. Confirm before overwriting an existing `regulation.bin`.
6. Load the exported `regulation.bin` through ME3.

> [!IMPORTANT]
> If you use the optional CSV workflow, Smithbox can import only one Specific Field at a time, so `chanceWeight` and `chanceWeight_dlc` must be imported in two separate operations. Do not use **All Field**.

> [!CAUTION]
> Use ME3 to manage and load mods instead of overwriting the game's original `regulation.bin`. Forgetting to restore a modified game file before going online may put your account at risk of a ban.

### Documentation

- [User Manual (English)](USER_MANUAL_en.md)
- [Smithbox Import and Mod Loading Guide (English)](SMITHBOX_GUIDE_en.md)
- [Grand Only Base](Grand%20Only/regulation.bin): a `regulation.bin` based on Regulation Ver. 1.03.5

### Credits and acknowledgements

Nightreign `regulation.bin` encryption/decryption and DCX/BND4/PARAM handling use the `Andre.SoulsFormats` library from [Smithbox](https://github.com/vawser/Smithbox), pinned to commit `1538fed4cfa5f3618a7a0191ff753ce4a1d54c00` and used and distributed under the MIT License. See [Andre.SoulsFormats provenance](helper/vendor/Andre.SoulsFormats.provenance.md) for the recorded source and version, and [Smithbox MIT License](helper/vendor/LICENSE-Smithbox.txt) for the full license text.

Special thanks to **Vawser and all Smithbox and SoulsFormats developers and contributors**. Their work made Nightreign regulation handling and this application's direct MOD export possible.
