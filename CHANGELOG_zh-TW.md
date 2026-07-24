# 更新日誌

## 尚未發布

### 新增

- 新增「**輸出 MOD**」，可將目前的權重修改直接寫入使用者所選 MOD 資料夾中的固定檔名 `regulation.bin`。
- 新增獨立且自包含的 .NET Helper，負責 Nightreign regulation 的解密、PARAM 修改、重新封裝、加密及輸出驗證。
- Windows x64 打包版內含 Regulation Ver. 1.03.5 的 `Grand Only/regulation.bin` 基底與 Helper；使用者不需選擇自訂輸入 regulation，也不需使用 Smithbox。
- 為全部 15 個支援語系加入「輸出 MOD」相關介面文字。

### 安全性與驗證

- 沒有任何權重修改時拒絕輸出；目標檔案已存在時必須先確認覆寫。
- 只允許寫入可編輯 Table ID 白名單中實際修改的資料列。鎖定項、不可編輯 Table 及 regulation 內其他資料均維持不變。
- 固定基底會檢查檔案大小及 SHA-256，且永遠不會被覆寫。
- 產生的 regulation 會重新開啟並與基底比較，全部驗證通過後才成為正式輸出；失敗時不留下正式檔案。
- 新增 Python 整合測試、.NET Helper 測試及 golden regulation fixture 測試。
- 已在遊戲中確認 Helper 產生的 `regulation.bin` 可正常使用。
- 已確認打包版可在未安裝 Python、.NET SDK／Runtime 及 Smithbox 的 Windows 電腦正常啟動與輸出，且其輸出的 `regulation.bin` 可在遊戲中正常使用。
- README 新增 Smithbox 及其 `Andre.SoulsFormats` 程式庫的來源引用與感謝，說明 Nightreign regulation 加解密及格式處理所使用的程式庫。

## Release Ver 1.1 — 2026-07-21

### 新增

- 新增「**自動設定**」功能，可依目前勾選的效果標籤，自動調整所有可編輯抽獎池 Table 的權重。
- 新增 `SpEffectParam` 資料及 `passiveSpEffectId_1` 關聯，讓編輯器能判斷每個效果的 `spCategory`。
- 新增依效果堆疊特性決定的自動權重規則：
  - `spCategory = 10`：效果自身可疊加。同一篩選群組中 Effect ID 最大且可修改的項目增加 `300`，其餘可修改項目降為 `1`。
  - `spCategory = 20`：相同等級的效果自身不可疊加，但不同等級可以疊加。同一篩選群組依 Effect ID 由大至小，權重增加量依序為 `300`、`250`、`200`……，最低增加量為 `0`。
  - 其他 `spCategory`：相同 Effect ID 的項目增加 `300`，不會將調整延伸到相同效果標籤下的其他等級。
- 為全部 15 個支援語系加入「自動設定」相關介面文字。
- 新增 `NexusDesc.txt`，提供 Nexus Mods 頁面使用的中英文 BBCode 說明。

### 變更

- 「自動設定」不會修改原始最終權重為 `0` 的鎖定項目。
- 「自動設定」不會覆蓋使用者已修改的項目。
- 非篩選且可修改的項目會降為 `1`，不會降為 `0`。
- 未勾選任何效果標籤時，「自動設定」按鈕會保持停用。
- 更新英文與繁體中文操作手冊，加入自動設定流程、堆疊分類含義及注意事項。
- 清理重複的實作註解與過時的重構說明，不影響程式行為。

### 驗證

- 已確認擴充後的遊戲參數資料庫可正常載入。
- 已驗證鎖定項、已修改項、非篩選項，以及 `spCategory` 為 `10`、`20` 與其他值時的規則。
- 已驗證所有 GUI 語系 JSON 及「自動設定」必要鍵值。
