# Rolling Pool Editor Windows x64 Build Guide

This guide explains how to create the verified Windows x64 distribution from source. All commands use PowerShell and assume that the current directory is the repository root.

## 1. Requirements

- Windows x64
- Git
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- .NET SDK 10.0.302

The repository's `global.json` requires .NET SDK 10.0.302. Verify the tools first:

```powershell
uv --version
dotnet --version
```

`dotnet --version` should report `10.0.302`.

## 2. Required file

Confirm that the fixed base exists before building:

```text
Grand Only/regulation.bin
```

The file must have this fingerprint:

- Size: 2,134,944 bytes
- SHA-256: 585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6

Verify it with PowerShell:

```powershell
Get-Item ".\Grand Only\regulation.bin" | Select-Object Length
Get-FileHash ".\Grand Only\regulation.bin" -Algorithm SHA256
```

The helper checks this fingerprint again at runtime and refuses to export if it does not match.

## 3. Install the Python dependencies

Run from the repository root:

```powershell
uv sync --frozen
```

`--frozen` creates the environment from the existing `uv.lock` without updating locked versions.

## 4. Test and publish the .NET helper

Run the helper tests first:

```powershell
dotnet test ".\helper\NightreignRegulationHelper.Tests\NightreignRegulationHelper.Tests.csproj" `
  --configuration Release
```

Publish the self-contained, single-file Windows x64 helper:

```powershell
dotnet publish ".\helper\NightreignRegulationHelper\NightreignRegulationHelper.csproj" `
  --configuration Release `
  --runtime win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true
```

The PyInstaller specification collects the helper from this fixed location:

```text
helper/NightreignRegulationHelper/bin/Release/net10.0/win-x64/publish/
```

That directory must contain at least:

```text
NightreignRegulationHelper.exe
libzstd.dll
Assets/AttachEffectTableParam.xml
```

Before packaging, verify that the helper can inspect the fixed base:

```powershell
.\helper\NightreignRegulationHelper\bin\Release\net10.0\win-x64\publish\NightreignRegulationHelper.exe `
  inspect `
  --base ".\Grand Only\regulation.bin"
```

On success, it writes one JSON line and exits with code `0`.

## 5. Run the Python tests

After publishing the helper, run this command from the repository root:

```powershell
uv run python -m unittest discover -s src/tests -v
```

The test suite includes a Python-to-.NET helper export integration test, so the helper must be published first.

## 6. Build the Windows x64 distribution

`rolling_pool_editor.spec` uses paths relative to `src`. Change to that directory before invoking PyInstaller:

```powershell
Push-Location .\src
uv run pyinstaller --clean --noconfirm .\rolling_pool_editor.spec
Pop-Location
```

The completed distribution is written to:

```text
src/dist/RollingPoolEditor/
```

## 7. Verify the distribution

Confirm that the main executable exists:

```text
src/dist/RollingPoolEditor/RollingPoolEditor.exe
```

Also confirm that `_internal` contains at least:

```text
Grand Only/regulation.bin
NightreignRegulationHelper/NightreignRegulationHelper.exe
NightreignRegulationHelper/libzstd.dll
NightreignRegulationHelper/Assets/AttachEffectTableParam.xml
editor/locales/
src/game_data/game_param.db
src/game_data/game_texts.db
```

Launch the packaged application:

```powershell
.\src\dist\RollingPoolEditor\RollingPoolEditor.exe
```

Complete at least these release checks:

1. The application starts and can switch languages.
2. After changing one editable weight, **Export MOD** produces `regulation.bin`.
3. Export is refused when no weights have changed.
4. The application asks before overwriting an existing output.
5. Mod Engine 3 can load the output and it works in game.

## 8. Distribution

Distribute the complete directory:

```text
src/dist/RollingPoolEditor/
```

Do not copy only `RollingPoolEditor.exe`. The application requires the adjacent `_internal` directory, fixed Regulation base, .NET helper, native library, databases, and locale files.

Third-party source and license records are stored in:

- `helper/vendor/Andre.SoulsFormats.provenance.md`
- `helper/vendor/LICENSE-Smithbox.txt`

