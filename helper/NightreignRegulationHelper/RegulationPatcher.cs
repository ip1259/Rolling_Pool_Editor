using System.Security.Cryptography;
using System.Text.Json;
using SoulsFormats;

namespace NightreignRegulationHelper;

internal sealed class RegulationPatcher
{
    public PatchResult Patch(
        string basePath,
        string manifestPath,
        string outputPath,
        string paramdefPath)
    {
        string fullBasePath = Path.GetFullPath(basePath);
        string fullOutputPath = Path.GetFullPath(outputPath);
        if (string.Equals(
                fullBasePath,
                fullOutputPath,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidChangeException(
                "Output path must not overwrite the fixed base regulation.");
        }

        RegulationInspector inspector = new();
        inspector.Inspect(fullBasePath, paramdefPath);

        PatchManifest manifest = ReadManifest(manifestPath);
        ValidateManifest(manifest);

        using BND4 binder = RegulationInspector.ReadBinder(fullBasePath);
        (BinderFile paramFile, PARAM param) =
            RegulationInspector.ReadTargetParam(binder, paramdefPath);

        List<(WeightChange Change, PARAM.Row Row)> targets =
            ResolveTargets(param, manifest.Changes);

        foreach ((WeightChange change, PARAM.Row row) in targets)
        {
            SetCellValue(row, "chanceWeight", change.ChanceWeight);
            SetCellValue(row, "chanceWeight_dlc", change.ChanceWeightDlc);
        }

        paramFile.Bytes = param.Write();

        string? outputDirectory = Path.GetDirectoryName(fullOutputPath);
        if (string.IsNullOrEmpty(outputDirectory))
        {
            throw new InvalidChangeException(
                $"Output path has no parent directory: {fullOutputPath}");
        }

        Directory.CreateDirectory(outputDirectory);
        string temporaryPath = Path.Combine(
            outputDirectory,
            $".{Path.GetFileName(fullOutputPath)}.{Guid.NewGuid():N}.tmp");

        try
        {
            byte[] baseBytes = File.ReadAllBytes(fullBasePath);
            byte[] originalIv = baseBytes[..16];
            byte[] encrypted = SFUtil.EncryptNightreignRegulation(
                binder,
                originalIv,
                binder.Compression);
            File.WriteAllBytes(temporaryPath, encrypted);

            RegulationVerifier verifier = new();
            verifier.Verify(
                fullBasePath,
                temporaryPath,
                paramdefPath,
                manifest.Changes);
            File.Move(temporaryPath, fullOutputPath, overwrite: true);

            return new PatchResult(
                fullOutputPath,
                targets.Count,
                new FileInfo(fullOutputPath).Length);
        }
        catch (RegulationVerificationException)
        {
            throw;
        }
        catch (Exception exception)
        {
            throw new RegulationWriteException(
                $"Failed to write regulation output: {fullOutputPath}",
                exception);
        }
        finally
        {
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }

    private static PatchManifest ReadManifest(string manifestPath)
    {
        try
        {
            string json = File.ReadAllText(manifestPath);
            PatchManifest? manifest = JsonSerializer.Deserialize<PatchManifest>(
                json,
                new JsonSerializerOptions(JsonSerializerDefaults.Web));
            return manifest ?? throw new InvalidChangeException(
                "Patch manifest is empty.");
        }
        catch (JsonException exception)
        {
            throw new InvalidChangeException(
                $"Patch manifest is invalid JSON: {exception.Message}");
        }
    }

    private static void ValidateManifest(PatchManifest manifest)
    {
        if (manifest.FormatVersion != 1)
        {
            throw new InvalidChangeException(
                $"Unsupported manifest formatVersion: {manifest.FormatVersion}");
        }

        if (!string.Equals(
                manifest.BaseSha256,
                RegulationInspector.ExpectedBaseSha256,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidChangeException(
                "Manifest baseSha256 does not match the fixed base regulation.");
        }

        if (!string.Equals(
                manifest.Param,
                RegulationInspector.TargetParamName,
                StringComparison.Ordinal))
        {
            throw new InvalidChangeException(
                $"Manifest param must be {RegulationInspector.TargetParamName}.");
        }

        if (!manifest.EditableTableIds.ToHashSet().SetEquals(
                RegulationInspector.EditableTableIds))
        {
            throw new InvalidWhitelistException(
                "Manifest editableTableIds does not match the built-in whitelist.");
        }

        if (manifest.Changes.Count == 0)
        {
            throw new InvalidChangeException(
                "Patch manifest contains no changes.");
        }

        foreach (WeightChange change in manifest.Changes)
        {
            if (!RegulationInspector.EditableTableIds.Contains(change.TableId))
            {
                throw new InvalidWhitelistException(
                    $"Table ID {change.TableId} is not editable.");
            }

            if (change.Occurrence < 0)
            {
                throw new InvalidChangeException(
                    "Change occurrence must not be negative.");
            }
        }
    }

    private static List<(WeightChange Change, PARAM.Row Row)> ResolveTargets(
        PARAM param,
        IReadOnlyList<WeightChange> changes)
    {
        List<(WeightChange Change, PARAM.Row Row)> targets = [];
        HashSet<(int TableId, int AttachEffectId, int Occurrence)> identities = [];

        foreach (WeightChange change in changes)
        {
            var identity = (
                change.TableId,
                change.AttachEffectId,
                change.Occurrence);
            if (!identities.Add(identity))
            {
                throw new InvalidChangeException(
                    $"Duplicate change: Table {change.TableId}, " +
                    $"AttachEffect {change.AttachEffectId}, " +
                    $"occurrence {change.Occurrence}.");
            }

            PARAM.Row[] matchingRows = param.Rows
                .Where(row => row.ID == change.TableId)
                .Where(row =>
                    RegulationInspector.GetCellValue<int>(
                        row,
                        "attachEffectId") == change.AttachEffectId)
                .ToArray();

            if (change.Occurrence >= matchingRows.Length)
            {
                throw new InvalidChangeException(
                    $"Target row was not found: Table {change.TableId}, " +
                    $"AttachEffect {change.AttachEffectId}, " +
                    $"occurrence {change.Occurrence}.");
            }

            PARAM.Row row = matchingRows[change.Occurrence];
            ushort currentWeight =
                RegulationInspector.GetCellValue<ushort>(row, "chanceWeight");
            short currentDlcWeight =
                RegulationInspector.GetCellValue<short>(row, "chanceWeight_dlc");

            if (currentWeight != change.ExpectedChanceWeight ||
                currentDlcWeight != change.ExpectedChanceWeightDlc)
            {
                throw new InvalidChangeException(
                    $"Expected value mismatch for Table {change.TableId}, " +
                    $"AttachEffect {change.AttachEffectId}, " +
                    $"occurrence {change.Occurrence}. " +
                    $"Expected {change.ExpectedChanceWeight}/" +
                    $"{change.ExpectedChanceWeightDlc}, got " +
                    $"{currentWeight}/{currentDlcWeight}.");
            }

            targets.Add((change, row));
        }

        return targets;
    }

    private static void SetCellValue(
        PARAM.Row row,
        string fieldName,
        object value)
    {
        PARAM.Cell cell = row.Cells.Single(cell =>
            string.Equals(
                cell.Def.InternalName,
                fieldName,
                StringComparison.Ordinal));
        cell.Value = value;
    }
}
