using SoulsFormats;

namespace NightreignRegulationHelper;

internal sealed class RegulationVerifier
{
    public void Verify(
        string basePath,
        string outputPath,
        string paramdefPath,
        IReadOnlyList<WeightChange> changes)
    {
        using BND4 baseBinder = RegulationInspector.ReadBinder(basePath);
        using BND4 outputBinder = RegulationInspector.ReadBinder(outputPath);

        VerifyBinderMetadata(baseBinder, outputBinder);
        if (baseBinder.Files.Count != outputBinder.Files.Count)
        {
            throw new RegulationVerificationException(
                "Output binder file count differs from the base.");
        }

        BinderFile? baseParamFile = null;
        BinderFile? outputParamFile = null;

        for (int index = 0; index < baseBinder.Files.Count; index++)
        {
            BinderFile baseFile = baseBinder.Files[index];
            BinderFile outputFile = outputBinder.Files[index];
            VerifyBinderFileMetadata(baseFile, outputFile, index);

            if (IsTargetParam(baseFile))
            {
                baseParamFile = baseFile;
                outputParamFile = outputFile;
            }
            else if (!baseFile.Bytes.Span.SequenceEqual(outputFile.Bytes.Span))
            {
                throw new RegulationVerificationException(
                    $"Untouched binder entry changed: {baseFile.Name}");
            }
        }

        if (baseParamFile is null || outputParamFile is null)
        {
            throw new RegulationVerificationException(
                "Target param was not found during output verification.");
        }

        PARAMDEF paramdef = PARAMDEF.XmlDeserialize(paramdefPath);
        PARAM baseParam = PARAM.ReadIgnoreCompression(baseParamFile.Bytes);
        PARAM outputParam = PARAM.ReadIgnoreCompression(outputParamFile.Bytes);
        baseParam.ApplyParamdef(paramdef);
        outputParam.ApplyParamdef(paramdef);
        VerifyParam(baseParam, outputParam, changes);
    }

    private static void VerifyBinderMetadata(BND4 expected, BND4 actual)
    {
        if (expected.Version != actual.Version ||
            expected.Format != actual.Format ||
            expected.Unk04 != actual.Unk04 ||
            expected.Unk05 != actual.Unk05 ||
            expected.BigEndian != actual.BigEndian ||
            expected.BitBigEndian != actual.BitBigEndian ||
            expected.Unicode != actual.Unicode ||
            expected.Extended != actual.Extended)
        {
            throw new RegulationVerificationException(
                "Output binder metadata differs from the base.");
        }
    }

    private static void VerifyBinderFileMetadata(
        BinderFile expected,
        BinderFile actual,
        int index)
    {
        if (expected.ID != actual.ID ||
            expected.Name != actual.Name ||
            expected.Flags != actual.Flags ||
            expected.CompressionType != actual.CompressionType)
        {
            throw new RegulationVerificationException(
                $"Binder entry metadata changed at index {index}.");
        }
    }

    private static void VerifyParam(
        PARAM expected,
        PARAM actual,
        IReadOnlyList<WeightChange> changes)
    {
        if (expected.ParamType != actual.ParamType ||
            expected.Rows.Count != actual.Rows.Count)
        {
            throw new RegulationVerificationException(
                "Output target param structure differs from the base.");
        }

        Dictionary<(int TableId, int AttachEffectId, int Occurrence), WeightChange>
            changeMap = changes.ToDictionary(
                change => (
                    change.TableId,
                    change.AttachEffectId,
                    change.Occurrence));
        Dictionary<(int TableId, int AttachEffectId), int> occurrences = [];
        int verifiedChanges = 0;

        for (int rowIndex = 0; rowIndex < expected.Rows.Count; rowIndex++)
        {
            PARAM.Row expectedRow = expected.Rows[rowIndex];
            PARAM.Row actualRow = actual.Rows[rowIndex];
            if (expectedRow.ID != actualRow.ID ||
                expectedRow.Name != actualRow.Name ||
                expectedRow.Cells.Count != actualRow.Cells.Count)
            {
                throw new RegulationVerificationException(
                    $"Target param row structure changed at index {rowIndex}.");
            }

            int attachEffectId = RegulationInspector.GetCellValue<int>(
                expectedRow,
                "attachEffectId");
            var pair = (expectedRow.ID, attachEffectId);
            int occurrence = occurrences.GetValueOrDefault(pair);
            occurrences[pair] = occurrence + 1;
            changeMap.TryGetValue(
                (expectedRow.ID, attachEffectId, occurrence),
                out WeightChange? change);

            for (int cellIndex = 0;
                 cellIndex < expectedRow.Cells.Count;
                 cellIndex++)
            {
                PARAM.Cell expectedCell = expectedRow.Cells[cellIndex];
                PARAM.Cell actualCell = actualRow.Cells[cellIndex];
                if (expectedCell.Def.InternalName != actualCell.Def.InternalName)
                {
                    throw new RegulationVerificationException(
                        $"Target param field layout changed at row {rowIndex}.");
                }

                string fieldName = expectedCell.Def.InternalName;
                if (change is not null && fieldName == "chanceWeight")
                {
                    VerifyChangedValue(
                        expectedCell.Value,
                        actualCell.Value,
                        change.ExpectedChanceWeight,
                        change.ChanceWeight,
                        expectedRow,
                        fieldName);
                }
                else if (change is not null && fieldName == "chanceWeight_dlc")
                {
                    VerifyChangedValue(
                        expectedCell.Value,
                        actualCell.Value,
                        change.ExpectedChanceWeightDlc,
                        change.ChanceWeightDlc,
                        expectedRow,
                        fieldName);
                    verifiedChanges++;
                }
                else if (!CellValuesEqual(
                             expectedCell.Value,
                             actualCell.Value))
                {
                    throw new RegulationVerificationException(
                        $"Unexpected field change at Table {expectedRow.ID}, " +
                        $"AttachEffect {attachEffectId}, field {fieldName}.");
                }
            }
        }

        if (verifiedChanges != changes.Count)
        {
            throw new RegulationVerificationException(
                $"Expected {changes.Count} changed rows, verified {verifiedChanges}.");
        }
    }

    private static void VerifyChangedValue(
        object expectedBaseValue,
        object actualOutputValue,
        object manifestExpectedValue,
        object manifestOutputValue,
        PARAM.Row row,
        string fieldName)
    {
        if (!CellValuesEqual(expectedBaseValue, manifestExpectedValue) ||
            !CellValuesEqual(actualOutputValue, manifestOutputValue))
        {
            throw new RegulationVerificationException(
                $"Changed value verification failed at Table {row.ID}, " +
                $"field {fieldName}.");
        }
    }

    private static bool CellValuesEqual(object left, object right)
    {
        if (left is byte[] leftBytes && right is byte[] rightBytes)
        {
            return leftBytes.AsSpan().SequenceEqual(rightBytes);
        }

        return left.Equals(right);
    }

    private static bool IsTargetParam(BinderFile file)
    {
        string normalizedName = file.Name.Replace(
            '\\',
            Path.DirectorySeparatorChar);
        return string.Equals(
            Path.GetFileNameWithoutExtension(normalizedName),
            RegulationInspector.TargetParamName,
            StringComparison.OrdinalIgnoreCase);
    }
}
