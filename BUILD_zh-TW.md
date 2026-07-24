# Rolling Pool Editor Windows x64 建置說明

本文件說明如何從原始碼建立已驗證的 Windows x64 發布包。所有命令均使用 PowerShell，並假設目前位於專案根目錄。

## 1. 建置需求

- Windows x64
- Git
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- .NET SDK 10.0.302

專案根目錄的 `global.json` 會要求 .NET SDK 10.0.302。先確認工具版本：

```powershell
uv --version
dotnet --version
```

`dotnet --version` 應顯示 `10.0.302`。

## 2. 必要檔案

建置前確認固定基底存在：

```text
Grand Only/regulation.bin
```

此檔案必須符合下列指紋：

- 檔案大小：2,134,944 bytes
- SHA-256：585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6

可使用 PowerShell 驗證：

```powershell
Get-Item ".\Grand Only\regulation.bin" | Select-Object Length
Get-FileHash ".\Grand Only\regulation.bin" -Algorithm SHA256
```

Helper 會在執行時再次驗證此指紋；不符時會拒絕輸出。

## 3. 安裝 Python 相依套件

由專案根目錄執行：

```powershell
uv sync --frozen
```

`--frozen` 會依現有的 `uv.lock` 建立環境，不更新鎖定版本。

## 4. 測試並發布 .NET Helper

先執行 Helper 測試：

```powershell
dotnet test ".\helper\NightreignRegulationHelper.Tests\NightreignRegulationHelper.Tests.csproj" `
  --configuration Release
```

接著發布 Windows x64 自包含、單一檔案 Helper：

```powershell
dotnet publish ".\helper\NightreignRegulationHelper\NightreignRegulationHelper.csproj" `
  --configuration Release `
  --runtime win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true
```

PyInstaller 規格會從下列固定位置收集 Helper：

```text
helper/NightreignRegulationHelper/bin/Release/net10.0/win-x64/publish/
```

該目錄至少必須包含：

```text
NightreignRegulationHelper.exe
libzstd.dll
Assets/AttachEffectTableParam.xml
```

可在打包前直接檢查 Helper 能否讀取固定基底：

```powershell
.\helper\NightreignRegulationHelper\bin\Release\net10.0\win-x64\publish\NightreignRegulationHelper.exe `
  inspect `
  --base ".\Grand Only\regulation.bin"
```

成功時會輸出一行 JSON，並以 exit code `0` 結束。

## 5. 執行 Python 測試

Helper 發布完成後，由專案根目錄執行：

```powershell
uv run python -m unittest discover -s src/tests -v
```

測試包含 Python 至實際 .NET Helper 的輸出整合流程，因此必須先完成上一節的 Helper 發布。

## 6. 建立 Windows x64 發布包

`rolling_pool_editor.spec` 使用相對於 `src` 的路徑。必須切換至 `src` 目錄再執行 PyInstaller：

```powershell
Push-Location .\src
uv run pyinstaller --clean --noconfirm .\rolling_pool_editor.spec
Pop-Location
```

完成後，發布目錄位於：

```text
src/dist/RollingPoolEditor/
```

## 7. 驗證發布內容

確認主程式存在：

```text
src/dist/RollingPoolEditor/RollingPoolEditor.exe
```

並確認 `_internal` 下至少包含：

```text
Grand Only/regulation.bin
NightreignRegulationHelper/NightreignRegulationHelper.exe
NightreignRegulationHelper/libzstd.dll
NightreignRegulationHelper/Assets/AttachEffectTableParam.xml
editor/locales/
src/game_data/game_param.db
src/game_data/game_texts.db
```

啟動：

```powershell
.\src\dist\RollingPoolEditor\RollingPoolEditor.exe
```

至少完成以下發布驗收：

1. 程式可正常啟動並切換語言。
2. 修改一筆可編輯權重後，「輸出 MOD」可產生 `regulation.bin`。
3. 沒有修改時會拒絕輸出。
4. 目標已存在時會先詢問是否覆寫。
5. 輸出檔可由 Mod Engine 3 載入並在遊戲中正常使用。

## 8. 散佈方式

必須散佈完整的：

```text
src/dist/RollingPoolEditor/
```

不可只複製 `RollingPoolEditor.exe`。程式執行時需要同目錄中的 `_internal`、固定 Regulation 基底、.NET Helper、原生程式庫、資料庫及語系檔案。

第三方程式庫的來源及授權紀錄位於：

- `helper/vendor/Andre.SoulsFormats.provenance.md`
- `helper/vendor/LICENSE-Smithbox.txt`

