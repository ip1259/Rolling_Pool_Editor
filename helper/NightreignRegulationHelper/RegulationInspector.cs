using System.Security.Cryptography;
using SoulsFormats;

namespace NightreignRegulationHelper;

internal sealed class RegulationInspector
{
    internal const string ExpectedBaseSha256 =
        "585D837AE6E4B3B1139293984ED1E4406E920FE6D809F7DCE2D9399C910A9CD6";
    internal const long ExpectedBaseSize = 2_134_944;
    internal const string TargetParamName = "AttachEffectTableParam";

    internal static readonly HashSet<int> EditableTableIds =
    [
        100,
        110,
        200,
        210,
        300,
        310,
        2_000_000,
        2_100_000,
        2_200_000,
        3_000_000,
    ];

    public InspectResult Inspect(string basePath, string paramdefPath)
    {
        FileInfo baseFile = new(basePath);
        if (!baseFile.Exists)
        {
            throw new InvalidBaseException($"Base regulation was not found: {basePath}");
        }

        if (baseFile.Length != ExpectedBaseSize)
        {
            throw new InvalidBaseException(
                $"Base regulation size mismatch. Expected {ExpectedBaseSize}, got {baseFile.Length}.");
        }

        string baseSha256 = ComputeSha256(basePath);
        if (!string.Equals(baseSha256, ExpectedBaseSha256, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidBaseException(
                $"Base regulation SHA-256 mismatch. Expected {ExpectedBaseSha256}, got {baseSha256}.");
        }

        using BND4 binder = ReadBinder(basePath);
        (BinderFile paramFile, PARAM param) = ReadTargetParam(binder, paramdefPath);

        int editableRowCount = param.Rows.Count(row => EditableTableIds.Contains(row.ID));

        return new InspectResult(
            baseSha256,
            baseFile.Length,
            binder.Version,
            binder.Files.Count,
            Path.GetFileName(paramFile.Name),
            param.ParamType,
            param.Rows.Count,
            editableRowCount);
    }

    internal IReadOnlyList<WeightRecord> ReadWeights(
        string regulationPath,
        string paramdefPath,
        int tableId,
        int attachEffectId)
    {
        using BND4 binder = ReadBinder(regulationPath);
        (_, PARAM param) = ReadTargetParam(binder, paramdefPath);

        List<WeightRecord> records = [];
        int occurrence = 0;

        foreach (PARAM.Row row in param.Rows.Where(row => row.ID == tableId))
        {
            int rowAttachEffectId = GetCellValue<int>(row, "attachEffectId");
            if (rowAttachEffectId != attachEffectId)
            {
                continue;
            }

            records.Add(new WeightRecord(
                row.ID,
                rowAttachEffectId,
                occurrence,
                GetCellValue<ushort>(row, "chanceWeight"),
                GetCellValue<short>(row, "chanceWeight_dlc")));
            occurrence++;
        }

        return records;
    }

    private static bool IsTargetParam(BinderFile file)
    {
        string normalizedName = file.Name.Replace('\\', Path.DirectorySeparatorChar);
        return string.Equals(
            Path.GetFileNameWithoutExtension(normalizedName),
            TargetParamName,
            StringComparison.OrdinalIgnoreCase);
    }

    internal static BND4 ReadBinder(string regulationPath)
    {
        try
        {
            return SFUtil.DecryptNightreignRegulation(regulationPath);
        }
        catch (Exception exception) when (
            exception is InvalidDataException or CryptographicException)
        {
            throw new InvalidDataException(
                $"Failed to decrypt or parse Nightreign regulation: {regulationPath}",
                exception);
        }
    }

    internal static (BinderFile File, PARAM Param) ReadTargetParam(
        BND4 binder,
        string paramdefPath)
    {
        BinderFile? paramFile = binder.Files.SingleOrDefault(IsTargetParam);
        if (paramFile is null)
        {
            throw new TargetParamNotFoundException(
                $"{TargetParamName}.param was not found in the regulation binder.");
        }

        PARAM param = PARAM.ReadIgnoreCompression(paramFile.Bytes);
        PARAMDEF paramdef = PARAMDEF.XmlDeserialize(paramdefPath);
        param.ApplyParamdef(paramdef);
        return (paramFile, param);
    }

    internal static T GetCellValue<T>(PARAM.Row row, string fieldName)
    {
        PARAM.Cell cell = row.Cells.Single(cell =>
            string.Equals(
                cell.Def.InternalName,
                fieldName,
                StringComparison.Ordinal));
        return (T)cell.Value;
    }

    private static string ComputeSha256(string path)
    {
        using FileStream stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream));
    }
}
