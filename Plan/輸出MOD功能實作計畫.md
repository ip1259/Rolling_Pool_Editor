# 輸出 MOD 功能實作計畫

## 1. 目標

在 Rolling Pool Editor 新增「輸出 MOD」功能，將 GUI 中已編輯的權重直接套用至專案內固定基底：

`Grand Only/regulation.bin`

輸出結果為可供 Mod Engine 3 使用的 `regulation.bin`。使用者不選擇、也不能替換輸入用的 regulation；GUI 只讓使用者選擇輸出位置。

本功能只修改 `AttachEffectTableParam` 內目標資料列的：

- `chanceWeight`
- `chanceWeight_dlc`（僅依現有資料語意處理；原值為 `-1` 時不得擅自改成一般權重）

其他 PARAM、資料列、欄位與 Binder 內容必須保持不變。

## 2. 固定條件

### 2.1 基底檔案

- 相對路徑：`Grand Only/regulation.bin`
- Regulation 版本：`1.03.5`
- 檔案大小：`2,134,944 bytes`
- SHA-256：`585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6`

輸出前必須檢查檔案存在、大小與 SHA-256。任何一項不符時停止輸出並顯示明確錯誤，不嘗試猜測格式或繼續修改。

### 2.2 不在本次範圍內

- 不讓使用者匯入其他版本或自訂的 `regulation.bin`。
- 不製作通用 regulation 編輯器。
- 不修改 `AttachEffectTableParam` 以外的 PARAM。
- 不直接覆寫 `Grand Only/regulation.bin`。
- 不移除既有 CSV 匯入／匯出功能。
- 不自動啟動遊戲或 Mod Engine 3。

### 2.3 可修改 Table ID 白名單

套用權重時，只允許修改目前程式定義為可編輯 Table 的下列 ID：

- `100`
- `110`
- `200`
- `210`
- `300`
- `310`
- `2000000`
- `2100000`
- `2200000`
- `3000000`

這是輸出功能的強制限制，而不是只供 GUI 顯示或篩選使用。Python 產生 manifest 前及 Helper 寫入 PARAM 前都必須各自檢查 Table ID。即使 manifest 被手動竄改，只要包含白名單外的 ID，Helper 就必須拒絕整次輸出，不得略過該項後繼續，也不得修改任何正式輸出檔。

白名單應由單一明確定義產生或在測試中確認 Python 與 Helper 的內容完全一致，避免兩邊規則不同步。

此白名單已由專案擁有者確認，實作時不得自行增加或移除 ID；任何變更都必須先更新本計畫及兩端測試。

### 2.4 已確認的差異基準

專案內已有一份使用相同固定基底製作、並確認可用的差異 regulation，可作為 Helper 的 golden fixture：

- 差異檔案：`Grand Only/diff regulation.bin`
- 差異說明：`Grand Only/diff.txt`
- 差異檔案大小：`2,549,936 bytes`
- 差異檔案 SHA-256：`78FCC709A89EAE135B58C4BDA6FF95D1CEFDC3F10B7B32217CEAD56BAA42C11E`
- Table ID：`100`
- Attach Effect ID：`7000000`
- 修改前 `chanceWeight`：`52`
- 修改前 `chanceWeight_dlc`：`-1`
- 修改後 `chanceWeight`：`100`
- 修改後 `chanceWeight_dlc`：`-1`
- 已確認差異 regulation 可正常使用。
- 2026-07-23 已確認 `NightreignRegulationHelper` 從固定基底產生的 `Grand Only/helper diff regulation.bin` 可正常使用，代表 Helper 的 Nightreign 解密、PARAM 修改、重新封裝及加密流程已通過遊戲端驗收。

此差異檔用於確認 Helper 對同一資料列的解析與輸出語意正確。由於不同工具重新封裝後的壓縮結果或檔案大小可能不同，不要求 Helper 產物與差異檔逐 byte 相同；應比較解密、解壓後的 BND4/PARAM 結構與目標欄位，並確認遊戲可載入。

## 3. 確定架構

保留目前 Python GUI、資料庫及權重計算邏輯，新增一個精簡的 Nightreign regulation Helper：

```text
Python GUI
  ├─ 驗證目前資料
  ├─ 產生變更清單 JSON
  └─ 呼叫 Helper
       ├─ 驗證固定基底
       ├─ 解密 regulation.bin
       ├─ 解壓 DCX 並讀取 BND4
       ├─ 修改 AttachEffectTableParam
       ├─ 重新封裝、壓縮及加密
       └─ 重新讀取輸出並驗證
```

Helper 必須使用 .NET 建立為獨立命令列程式 `NightreignRegulationHelper.exe`，採用與目前 Nightreign 相容的 SoulsFormatsNEXT regulation/PARAM 實作。不要沿用 Soulstruct 內只支援 DS3／Elden Ring 的舊 ParamCrypt。

Python 必須以 `subprocess` 呼叫 Helper，雙方只透過命令列參數、JSON manifest、標準輸出及 process exit code 溝通。不得在 Python 程序內嵌 .NET Runtime，也不採用 `pythonnet` 或其他 CLR bridge。Helper 必須能脫離 GUI 單獨執行與測試。

### 3.1 專案邊界

- Python 負責 GUI、編輯狀態、輸出前驗證、manifest 產生及本地化訊息。
- .NET Helper 負責固定基底驗證、Nightreign 加解密、DCX/BND4/PARAM 讀寫、Table ID 白名單檢查及輸出後驗證。
- Python 不直接解析或修改 `regulation.bin`。
- Helper 不依賴 Python 模組、GUI 狀態或 SQLite 資料庫。
- Helper 專案及測試應置於獨立目錄，並可由 `dotnet build`、`dotnet test` 單獨建置與驗證。

## 4. 資料交換格式

Python 不傳送完整 CSV，而是傳送只包含修改項目的 JSON manifest。建議格式：

```json
{
  "formatVersion": 1,
  "baseSha256": "585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6",
  "param": "AttachEffectTableParam",
  "editableTableIds": [
    100,
    110,
    200,
    210,
    300,
    310,
    2000000,
    2100000,
    2200000,
    3000000
  ],
  "changes": [
    {
      "id": 123456,
      "attachEffectId": 7000000,
      "occurrence": 0,
      "expectedChanceWeight": 1,
      "expectedChanceWeightDlc": -1,
      "chanceWeight": 301,
      "chanceWeightDlc": -1
    }
  ]
}
```

欄位原則：

- `id`、`attachEffectId` 與 `occurrence` 共同識別可能重複的資料列。
- 每個 `id` 都必須存在於 Helper 內建的可編輯 Table ID 白名單；manifest 的 `editableTableIds` 只用於版本一致性檢查，不能自行授權新的 ID。
- `expectedChanceWeight` 與 `expectedChanceWeightDlc` 用於確認 GUI 資料和固定基底一致。
- Helper 找不到唯一資料列、找到的原值不符或出現額外重複項時，必須停止輸出。
- JSON 寫入系統暫存目錄，Helper 結束後清除。

如果實際 PARAM 結構具有可唯一識別資料列的穩定 Row ID，實作時應優先使用該 Row ID；確認前不得假設 `id + attachEffectId` 一定唯一。

## 5. Helper 命令列介面

第一版只需要下列命令：

```text
NightreignRegulationHelper inspect --base <path>
NightreignRegulationHelper patch --base <path> --changes <json> --output <path>
NightreignRegulationHelper verify --base <path> --changes <json> --output <path>
```

可在 `patch` 完成後內建執行驗證；保留獨立 `verify` 供測試與除錯。

### 5.1 Exit code

- `0`：成功。
- `10`：基底不存在或指紋不符。
- `20`：解密、DCX 或 BND4 解析失敗。
- `30`：找不到 `AttachEffectTableParam`。
- `40`：變更項無法唯一對應或原值不符。
- `41`：manifest 包含不可編輯的 Table ID，或白名單版本不一致。
- `50`：重新封裝或加密失敗。
- `60`：輸出後驗證失敗。
- 其他：未預期錯誤。

Helper 的標準輸出必須回傳一行 JSON，至少包含成功狀態、修改筆數及錯誤代碼，避免 Python 依賴自然語言訊息判斷結果。診斷訊息寫入標準錯誤，不得混入標準輸出的結果 JSON。

## 6. regulation 修改規則

1. 將固定基底複製至獨立暫存工作目錄。
2. 解密 Nightreign regulation。
3. 保留並使用原檔的 DCX 壓縮設定。
4. 讀取 BND4，依檔名尋找 `AttachEffectTableParam.param`，不硬編碼 Binder entry index。
5. 解析 PARAM，先確認 manifest 內所有 `id` 均在可編輯 Table ID 白名單；只要一項不符就中止整次操作。
6. 逐項套用 manifest，且只修改指定資料列的權重欄位，不重建整張 PARAM。
7. 保留未修改欄位、未知資料、Row Name、Binder entry ID、路徑、旗標及順序。
8. 將修改後的 PARAM 放回原 Binder。
9. 重新封裝、壓縮並使用 Nightreign 正確的加密方式輸出。
10. 先寫入輸出目錄內的暫存檔；所有驗證通過後，再以原子替換方式產生正式 `regulation.bin`。

任何失敗都不得留下看似成功的半成品。

## 7. 輸出後驗證

Helper 必須重新解密並讀取剛產生的檔案，至少驗證：

- 輸出可成功解密、解壓並解析為 BND4。
- Binder entry 數量、ID、名稱、順序及旗標與基底一致。
- 除 `AttachEffectTableParam` 外，所有 entry 的內容雜湊與基底一致。
- `AttachEffectTableParam` 的資料列數量與基底一致。
- manifest 指定的每個權重都等於輸出值。
- 所有發生權重變更的資料列，其 Table ID 都在可編輯白名單內。
- 白名單外的所有 Table 及其資料列內容與基底完全一致。
- 未列於 manifest 的資料列及其他欄位沒有變更。
- 實際修改筆數等於 manifest 變更筆數。

只有全部通過才回報成功。

## 8. GUI 變更

### 8.1 新增按鈕

在既有匯入、套用、自動設定及 CSV 匯出功能旁新增「輸出 MOD」按鈕。

已確定的操作：

1. 執行既有匯出前資料驗證。
2. 若目前沒有任何權重修改，拒絕輸出並顯示本地化提示。
3. 顯示資料夾選擇對話框，讓使用者選擇 MOD 資料夾，不讓使用者自訂輸出檔名。
4. 將輸出路徑固定組合為所選資料夾下的 `regulation.bin`。
5. 禁止所選資料夾使輸出路徑指向固定基底本身。
6. 若目標 `regulation.bin` 已存在，使用系統確認視窗詢問是否覆寫；使用者選擇「否」時不呼叫 Helper。
7. 產生 manifest 並呼叫 Helper。
8. 成功時顯示輸出路徑與修改筆數。
9. 失敗時依 Helper error code 顯示可理解的錯誤，不顯示成功訊息。

### 8.2 執行期間

- Helper 執行期間停用「輸出 MOD」按鈕，避免重複輸出。
- GUI 保持可重繪；若同步呼叫會造成明顯凍結，改用背景執行並在主執行緒更新 Tk 元件。
- 結束後無論成功或失敗都恢復按鈕狀態。

### 8.3 多語言

新增的按鈕、確認、進度、成功及各類錯誤文字，必須同步加入目前所有語言 JSON。不得在事件處理函式內硬編碼中英文訊息。

## 9. 路徑與封裝

### 9.1 開發環境

固定基底從專案根目錄解析：

`Grand Only/regulation.bin`

不得依賴使用者啟動程式時的 current working directory。

### 9.2 發布包

預期結構：

```text
RollingPoolEditor/
├─ RollingPoolEditor.exe
├─ Grand Only/
│  └─ regulation.bin
└─ _internal/
   └─ NightreignRegulationHelper.exe
```

需要更新 `src/rolling_pool_editor.spec`：

- 將固定基底加入發布資料。
- 將 Helper 及其必要原生相依檔加入發布包。
- 確認 One-folder 模式下 Python 能找到兩者。

Helper 建議發布為 `win-x64` 自包含版本，使使用者不必另外安裝 .NET Runtime。最終採用的 SoulsFormatsNEXT 套件、原生 DLL 與授權檔必須一併確認及正確散佈。

## 10. 實作階段

### 開發環境基準

- 已安裝 .NET SDK `10.0.302`（.NET 10 LTS）。
- 開發平台為 Windows `win-x64`。
- 新增 `global.json` 將 Helper 使用的 SDK 固定為 `10.0.302`，避免開發機安裝其他 SDK 後無意間改變建置版本。
- SoulsFormatsNEXT 的目標框架與 .NET 10 相容性仍須在建立專案時驗證；若相依套件要求較低的 Target Framework，可使用 .NET 10 SDK 建置該受支援框架，不為追求 `net10.0` 而修改第三方套件。

### 階段 A：格式可行性原型

- 建立可獨立建置及執行的 .NET 命令列 Helper 專案與測試專案。
- 正確解密固定基底並找到 `AttachEffectTableParam`。
- 讀取 golden fixture 指定的 Table `100`、Attach Effect `7000000`，確認基底值為 `52`／`-1`。
- 將該筆權重修改為 `100`／`-1`，重新加密並可再次讀取。
- 將 Helper 產物的解密後結構與 `diff regulation.bin` 比較。
- 使用 Smithbox 或遊戲端確認 Helper 產物可用；既有差異檔已完成可用性確認，但不能取代 Helper 產物本身的驗收。

完成條件：golden fixture 的單一測試變更可穩定往返、語意與已確認差異檔一致、輸出後驗證全部通過，且 Helper 產物已完成遊戲端可用性確認。

狀態：已於 2026-07-23 完成。

### 階段 B：安全的批次 Patch

- 定義 manifest schema。
- 實作重複資料列識別及 expected value 檢查。
- 在 Python 與 Helper 兩層實作可編輯 Table ID 白名單檢查。
- 實作所有變更的批次套用。
- 實作 entry、資料列與欄位差異驗證。
- 補齊 exit code 與 JSON 結果。

完成條件：合法變更全部正確套用；基底錯誤、重複對應、原值不符及破損輸出都會被拒絕。

狀態：已於 2026-07-23 完成，並通過 Helper 單元與整合測試。

### 階段 C：Python 整合

- 從目前可編輯資料產生 manifest。
- 新增 Helper 呼叫層。
- 新增「輸出 MOD」GUI 流程。
- 防止覆寫固定基底。
- 保留既有 CSV 匯出。

完成條件：使用者不需 Smithbox，即可由 GUI 產生驗證通過的 `regulation.bin`。

狀態：已於 2026-07-23 完成，並通過 Python 至 Helper 的實際輸出整合測試。

### 階段 D：發布與文件

- 更新 PyInstaller spec 與發布腳本。
- 補齊所有語言。
- 更新 README、使用手冊、Nexus 說明及 changelog。
- 在乾淨 Windows 環境測試發布包。
- 確認相依套件授權與需附帶的 NOTICE/LICENSE。

完成條件：解壓發布包即可執行並輸出 MOD，不要求開發環境、Python、.NET SDK 或 Smithbox。

狀態：已於 2026-07-24 完成。PyInstaller 打包、資源定位、多語系、授權檔及文件均已完成；打包版已在未安裝 Python、.NET SDK／Runtime 及 Smithbox 的 Windows 電腦正常啟動與輸出，產物亦已通過遊戲端實測。

## 11. 測試計畫

### 11.1 Helper 單元／整合測試

- 正確的固定基底通過檢查。
- `diff regulation.bin` 的檔案大小及 SHA-256 符合已記錄的 golden fixture。
- Helper 可從固定基底重現 Table `100`、Attach Effect `7000000` 的 `52`／`-1` 至 `100`／`-1` 變更。
- 缺少、截斷或 SHA-256 不符的基底被拒絕。
- 空變更清單必須拒絕輸出並回報沒有修改。
- 單筆、多筆及重複鍵資料能正確對應。
- 白名單內的每個 Table ID 都可正常套用合法變更。
- manifest 只要包含一個白名單外的 Table ID，整次輸出即失敗且不產生正式檔案。
- 竄改 manifest 的 `editableTableIds` 不得授權白名單外的 ID。
- expected value 不符時不產生正式輸出。
- `chanceWeight_dlc == -1` 時維持 `-1`。
- 輸出路徑不可寫時回傳正確錯誤。
- 修改前後未觸及 entry 的 SHA-256 完全一致。
- 對輸出再執行 inspect／verify 可成功。

### 11.2 Python 測試

- manifest 只包含實際已修改項。
- manifest 不包含任何不可編輯 Table ID。
- 鎖定項與未修改項不會被列入變更。
- 沒有任何修改時不開啟資料夾選擇對話框，也不呼叫 Helper。
- 取消資料夾選擇對話框時不呼叫 Helper。
- 所選資料夾下的輸出檔名固定為 `regulation.bin`。
- 目標已存在且使用者拒絕覆寫時不呼叫 Helper。
- 不允許輸出覆寫固定基底。
- 各 exit code 對應正確的本地化訊息。
- Helper 失敗時按鈕狀態能恢復。

### 11.3 發布驗收

- 從 PyInstaller 發布目錄啟動，而非專案目錄。
- 變更 current working directory 後仍能找到固定基底與 Helper。
- 無 Python、無 .NET SDK、無 Smithbox 的乾淨 Windows 環境可用。
- 產生的 `regulation.bin` 可被 Smithbox重新開啟。
- 透過 Mod Engine 3 載入後，遊戲內指定權重確實生效。

## 12. 主要風險與處理

### Nightreign 格式或加密版本不符

先完成階段 A，確認 SoulsFormatsNEXT 的實際版本可以處理此 1.03.5 基底，再開始 GUI 整合。不可只因 API 名稱相符便假設可用。

### 資料列識別不唯一

先檢查實際 PARAM 的 Row ID 與重複情形，再確定 manifest key。無法唯一識別時停止，不使用「第一筆符合項」。

### GUI 資料庫與基底不同步

利用固定 SHA-256、expected value 與修改後差異驗證建立三層防護。若仍有差異，應更新專案內資料庫或基底，不放寬驗證。

### 發布體積增加

自包含 .NET Helper 會增加發布大小，但能換取免安裝 Runtime。先量測實際大小，再決定是否採 framework-dependent 發布；不可為縮小容量犧牲可部署性。

### 授權

採用或散佈 SoulsFormatsNEXT、Smithbox 相關程式碼及原生相依檔前，確認實際版本的授權條款，附上必要 LICENSE／NOTICE。不要直接綁入 WitchyBND 作為實作捷徑，除非已接受其 GPLv3 對散佈方式的影響。

## 13. 最終完成定義

全部條件同時成立才算完成：

- 使用者不需選擇輸入 regulation。
- 程式永遠以通過指紋驗證的 `Grand Only/regulation.bin` 為基底。
- GUI 只讓使用者選擇 MOD 資料夾，輸出檔名固定為 `regulation.bin`。
- 目標已存在時必須先確認覆寫，沒有任何修改時必須拒絕輸出。
- GUI 可輸出新的 `regulation.bin`，且不修改固定基底。
- 只有指定 `AttachEffectTableParam` 權重發生變更。
- 所有修改都只發生在明列的可編輯 Table ID；白名單外的 Table 保持不變。
- 輸出後自動驗證成功，失敗時不留下正式產物。
- 發布包不依賴 Smithbox、Python 開發環境或 .NET SDK。
- 所有 GUI 新文字完成多語言更新。
- README、使用手冊、Nexus 說明與 changelog 已反映新流程。
- 產物通過 Smithbox 讀取及遊戲內 Mod Engine 3 實測。
