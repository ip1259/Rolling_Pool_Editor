# Rolling Pool Editor User Guide

## Overview

Rolling Pool Editor is designed to be used with **Smithbox**. It exports CSV files in a Smithbox-compatible format. These files can be imported into specific parameter fields to create a modified `regulation.bin` for use in the game.

## CSV Import Instructions

### 1. Create a Smithbox project

When creating the Smithbox project, you may use the modified **Grand Only Base** as the project's `regulation.bin`. It is based on **Regulation Ver. 1.03.5** and includes the following changes:

- The rolling pool only awards **Grand Scenes**.
- Grand Scene purchase prices have been reduced.
- The price difference from selling approximately seven relics is enough to purchase one additional relic.
- The changes improve the rolling experience while maintaining a balanced **Murk** economy.

### 2. Select the parameter table

In Smithbox's **Param Editor**, select:

```text
AttachEffectTableParam
```

### 3. Import the CSV

Open the following menu:

```text
Tool → Data Transfer → Import CSV → From File...
```

Under **From File...**, select **Specific Field**. A submenu containing the available fields will appear. Both of the following fields must be overwritten using the CSV:

```text
chanceWeight
chanceWeight_dlc
```

Smithbox can select and import only one field at a time, so the import must be performed twice:

1. Select `chanceWeight`. When the file selection dialog opens, select the CSV exported by Rolling Pool Editor.
2. Open the same menu again, select `chanceWeight_dlc`, and select the same CSV in the file selection dialog.

Both fields have been fully overwritten only after these two imports are complete.

> [!WARNING]
> Do not select **All Field**. Importing all fields may overwrite unrelated values and cause parameter data errors.

### 4. Load the mod

After importing the CSV and saving the Smithbox project, the modified `regulation.bin` can be used as a mod and loaded through **Mod Engine 3 (ME3)**.

> [!CAUTION]
> You should use **Mod Engine 3 (ME3)** to manage and load your mods instead of modifying the original game files directly.
>
> Although you can overwrite the game's original `regulation.bin` and later restore it by using your game platform's file-integrity verification feature, forgetting to restore the modified file may result in an account ban. You assume the risk if you choose to overwrite the original game files directly.
