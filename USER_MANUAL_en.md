# Rolling Pool Editor User Manual

## 1. Introduction

Rolling Pool Editor is an open-source Python GUI tool for adjusting relic rolling-pool weights. It calculates each effect's chance from its weight in real time and exports a Smithbox-compatible `AttachEffectTableParam.csv`.

The exported CSV must be imported into `AttachEffectTableParam` through Smithbox. The resulting `regulation.bin` can then be used as a mod. See the [Smithbox Guide](SMITHBOX_GUIDE_en.md) for the complete import procedure.

## 2. Starting the application

### Packaged Windows x64 version

A packaged Windows x64 build is provided. Extract the package and run `RollingPoolEditor.exe`; a separate Python installation is not required.

### Running from source

The project uses Python 3.13. [uv](https://docs.astral.sh/uv/) can create and synchronize its virtual environment. Run the following commands from the repository root:

```powershell
uv sync
uv run python src/main.py
```

The application entry point is `src/main.py`. Start it from the repository root so it can locate the databases under `src/game_data`.

## 3. Interface overview

### System settings

- **UI & Game Language** changes both the interface language and the localized in-game effect names. English is the default on first launch.
- **Appearance Theme** switches between Dark and Light modes.
- **Table ID** selects the rolling pool to edit.

The application automatically saves the selected language, theme, and checked effect tags. These settings are restored on the next launch and do not require a manual save. On Windows, the configuration file is stored at:

```text
%APPDATA%\RollingPoolEditor\config.json
```

> [!NOTE]
> The configuration file does not save weight edits, the selected Table ID, sorting, or expanded and collapsed category states. Weight changes must be exported to CSV to be retained.

### Effect Tag Filter

The filter panel organizes entries into categories, subcategories, and effect tags:

- Use the arrow beside a category to expand or collapse it.
- Selecting a subcategory selects or clears all effect tags below it.
- Selecting individual tags limits the table to matching effects.
- When no tag is selected, all effects in the current Table are shown.
- **Clear All Filters** clears every selected filter.

### Parameter Editor Workspace

The table displays:

- **Effect ID**: the effect's identifier in the game parameters.
- **Effect Name**: localized in-game text for the current language.
- **Final Weight**: the weight actually used in chance calculations.
- **Chance Rate**: the effect's weight as a proportion of the current Table's total weight.
- **New Weight Value**: controls for entering, saving, or quickly setting a new weight to 1.

Click a column header to sort the table. Click the same header again to toggle between ascending and descending order.

## 4. Table ID reference

| Table ID | Purpose |
| --- | --- |
| `100`, `200`, `300` | Standard Relic rolling pools described by the shop as Ver. 1.02 |
| `110`, `210`, `310` | Standard Relic rolling pools for Ver. 1.03, including DLC |
| `2000000` | Shared Deep Relic pool |
| `2100000` | Deep Relic Ver. 1.02 pool |
| `2200000` | Deep Relic Ver. 1.03 pool, including DLC |
| `3000000` | Debuff pool |

## 5. Editing an individual effect weight

1. Select the Table ID to edit.
2. Use effect tags to narrow the displayed records if needed.
3. Click the weight input area at the right end of the target row.
4. Enter an integer weight.
5. Press `Enter` or click the check mark to save.

After saving, the application immediately recalculates the chance rates for every effect in the current Table.

> [!IMPORTANT]
> Effects whose original final weight is `0` when the application starts cannot be rolled from that pool. They are permanently locked and cannot be edited with this tool. An entry whose original weight is non-zero can still be manually set to `0` during the current editing session.

> [!CAUTION]
> Setting any editable effect to `0` is not recommended. Removing too many effects may leave too few valid entries in a pool and may produce a configuration that does not meet game requirements. Use non-negative integers; although a negative value may be accepted as input, it does not represent a valid rolling-pool configuration.

### Quick set-to-1 button

Click the **1** button at the far right of a row to set that effect's weight directly to 1. This greatly reduces its chance while keeping it in the pool. The button is unavailable for entries locked because their original weight is zero.

## 6. Batch editing

### Add 100 to Filtered

Select one or more effect tags, then click **Add 100 to Filtered**. After confirmation, the application adds 100 to every editable record currently displayed.

If no filter is active, the entire Table is displayed, so this action applies to every editable record in the current Table. Check the visible scope and the record count in the confirmation dialog before proceeding.

### Set Unmodified to 1

Click **Set Unmodified to 1** and confirm. The application changes records in the current Table to 1 when both conditions are met:

- Their original weight is greater than zero, so they are not locked.
- Their current weight still equals the original weight, meaning they have not been modified.

This feature deliberately uses `1` instead of `0`. It greatly reduces the chance of unselected effects while keeping enough entries available in the pool.

### Auto Configure

Select the effect tags whose weights should be favored, then click **Auto Configure**. After confirmation, the application uses the active filters and effect stacking behavior to adjust every editable Table listed in this manual.

Every automatic adjustment follows these base rules:

- Entries whose original final weight is `0` are locked and remain unchanged.
- An entry whose current weight differs from its original weight is considered modified and remains unchanged.
- Entries outside the active filters are reduced to `1`, never `0`.
- Every increase is based on the entry's current weight immediately before Auto Configure runs.

Filtered entries are adjusted according to their `spCategory`:

- **`spCategory = 10` (self-stackable):** within the same `attachFilterParamId` group, the still-editable entry with the highest Effect ID receives `+300`; the other editable entries in that group are reduced to `1`.
- **`spCategory = 20` (not self-stackable; different levels stack):** entries in the same `attachFilterParamId` group are ordered by descending Effect ID and receive `+300`, `+250`, `+200`, `+150`, and so on. Each successive increase is 50 lower, with a minimum increase of `0`.
- **Other `spCategory` values:** only entries with the same Effect ID are adjusted by `+300`; other Effect IDs under the same tag are not changed by that entry.

> [!IMPORTANT]
> **Auto Configure** affects every editable Table, not only the Table currently displayed. The button remains disabled until at least one effect tag is selected. Review each Table after running it. Use **Reset All Current Changes** if you need to restore every Table.

## 7. Apply to Other Tables

**Apply to Other Tables** maps changed effects from the current Table to other editable Tables by effect-category tag. It does not simply copy values to identical Effect IDs.

For example, “Vigor +1,” “Vigor +2,” and “Vigor +3” share an effect tag, and a higher Effect ID usually represents a stronger version of the same type. “Improved Vigor” uses a different tag and is therefore not treated as the same type.

Only source records whose original weight is greater than zero and whose current weight has actually changed are processed. Entries originally locked at zero in target Tables are never used as mapping targets.

The mapping rules are:

- **When increasing a weight:** the application selects the editable entry with the highest Effect ID under the same effect tag in each target Table. For example, after editing “Vigor +2,” the corresponding entry increased in another Table may be “Vigor +3.”
- **When decreasing a weight:** every editable entry under the same tag whose Effect ID is less than or equal to the source Effect ID is set to the source's new weight. This may modify multiple effects in the same target Table at once.
- If a target Table has no entry matching the rule, that change is not applied to that Table.
- The operation covers the other editable Tables listed in this manual and excludes the current source Table.

> [!IMPORTANT]
> Review each Table after applying the changes. Because mapping depends on the effect tag, Effect ID, and original lock state, the entry changed in another Table may not have the same name or Effect ID as the source entry.

## 8. Importing from CSV

Click **Import CSV** and select a CSV file. The file must contain these columns:

```text
ID
attachEffectId
chanceWeight
chanceWeight_dlc
```

The application matches records by Table ID and Effect ID, imports weights into editable records, and skips missing records or entries whose original weight is zero. A message reports the number of updated records after the import.

## 9. Resetting all current changes

Click **Reset All Current Changes** to reload the entire editable data set to its initial state from application startup. This clears manual edits, batch changes, and CSV imports across every Table, not only the currently displayed Table.

## 10. Validating and exporting CSV

1. Finish adjusting weights in all required Tables.
2. Click **Validate & Export CSV**.
3. Choose the output location and filename. The default filename is `AttachEffectTableParam.csv`.
4. After validation passes, the application exports a Smithbox-compatible CSV.

The output preserves the original row order and required fields and contains both `chanceWeight` and `chanceWeight_dlc`.

### Debuff pool validation

Table `3000000` is the Debuff pool. Some configurations may require three Debuffs at once, especially powerful Deep Relics, so this pool must retain at least three entries with non-zero final weights.

If fewer than three entries remain non-zero:

- A warning appears in the interface.
- The CSV fails validation and cannot be exported.

## 11. Smithbox and mod loading

After exporting, import both `chanceWeight` and `chanceWeight_dlc` from the same CSV into Smithbox. Smithbox can select only one field per import, so the import must be performed twice. See the [Smithbox Guide](SMITHBOX_GUIDE_en.md) for detailed steps and mod-safety warnings.
