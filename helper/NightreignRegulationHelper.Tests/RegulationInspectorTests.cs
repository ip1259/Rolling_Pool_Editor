using NightreignRegulationHelper;
using Xunit;

namespace NightreignRegulationHelper.Tests;

public sealed class RegulationInspectorTests
{
    [Fact]
    public void EditableTableIdsMatchConfirmedWhitelist()
    {
        int[] expected =
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

        Assert.Equal(expected, RegulationInspector.EditableTableIds.Order());
    }

    [Fact]
    public void InspectRejectsMissingBase()
    {
        RegulationInspector inspector = new();

        Assert.Throws<InvalidBaseException>(() =>
            inspector.Inspect(
                Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.bin"),
                GetParamdefPath()));
    }

    [Fact]
    public void InspectReadsConfirmedBaseMetadata()
    {
        RegulationInspector inspector = new();

        InspectResult result = inspector.Inspect(
            GetFixturePath("regulation.bin"),
            GetParamdefPath());

        Assert.Equal(RegulationInspector.ExpectedBaseSha256, result.BaseSha256);
        Assert.Equal(RegulationInspector.ExpectedBaseSize, result.BaseSize);
        Assert.Equal("10350000", result.BinderVersion);
        Assert.Equal(252, result.BinderFileCount);
        Assert.Equal("AttachEffectTableParam.param", result.ParamName);
        Assert.Equal("ATTACHEFFECT_TABLE_PARAM_ST", result.ParamType);
        Assert.Equal(22_088, result.ParamRowCount);
        Assert.Equal(3_393, result.EditableRowCount);
    }

    [Fact]
    public void GoldenFixtureContainsExpectedSingleWeightChange()
    {
        RegulationInspector inspector = new();

        WeightRecord baseRecord = Assert.Single(inspector.ReadWeights(
            GetFixturePath("regulation.bin"),
            GetParamdefPath(),
            tableId: 100,
            attachEffectId: 7_000_000));
        WeightRecord diffRecord = Assert.Single(inspector.ReadWeights(
            GetFixturePath("diff regulation.bin"),
            GetParamdefPath(),
            tableId: 100,
            attachEffectId: 7_000_000));

        Assert.Equal((ushort)52, baseRecord.ChanceWeight);
        Assert.Equal((short)-1, baseRecord.ChanceWeightDlc);
        Assert.Equal((ushort)100, diffRecord.ChanceWeight);
        Assert.Equal((short)-1, diffRecord.ChanceWeightDlc);
    }

    [Fact]
    public void PatchReproducesGoldenWeightChange()
    {
        string testDirectory = Path.Combine(
            Path.GetTempPath(),
            $"NightreignRegulationHelperTests-{Guid.NewGuid():N}");
        Directory.CreateDirectory(testDirectory);
        string manifestPath = Path.Combine(testDirectory, "changes.json");
        string outputPath = Path.Combine(testDirectory, "regulation.bin");

        try
        {
            File.Copy(
                Path.Combine(
                    AppContext.BaseDirectory,
                    "Fixtures",
                    "golden-change.json"),
                manifestPath);

            RegulationPatcher patcher = new();
            PatchResult result = patcher.Patch(
                GetFixturePath("regulation.bin"),
                manifestPath,
                outputPath,
                GetParamdefPath());

            Assert.Equal(1, result.ModifiedCount);
            Assert.True(File.Exists(outputPath));

            RegulationInspector inspector = new();
            WeightRecord outputRecord = Assert.Single(inspector.ReadWeights(
                outputPath,
                GetParamdefPath(),
                tableId: 100,
                attachEffectId: 7_000_000));
            Assert.Equal((ushort)100, outputRecord.ChanceWeight);
            Assert.Equal((short)-1, outputRecord.ChanceWeightDlc);
        }
        finally
        {
            if (Directory.Exists(testDirectory))
            {
                Directory.Delete(testDirectory, recursive: true);
            }
        }
    }

    [Fact]
    public void PatchRejectsNonEditableTableWithoutCreatingOutput()
    {
        string testDirectory = Path.Combine(
            Path.GetTempPath(),
            $"NightreignRegulationHelperTests-{Guid.NewGuid():N}");
        Directory.CreateDirectory(testDirectory);
        string manifestPath = Path.Combine(testDirectory, "changes.json");
        string outputPath = Path.Combine(testDirectory, "regulation.bin");

        try
        {
            string manifest = File.ReadAllText(Path.Combine(
                AppContext.BaseDirectory,
                "Fixtures",
                "golden-change.json"));
            File.WriteAllText(
                manifestPath,
                manifest.Replace(
                    "\"id\": 100",
                    "\"id\": 999",
                    StringComparison.Ordinal));

            RegulationPatcher patcher = new();
            Assert.Throws<InvalidWhitelistException>(() => patcher.Patch(
                GetFixturePath("regulation.bin"),
                manifestPath,
                outputPath,
                GetParamdefPath()));
            Assert.False(File.Exists(outputPath));
        }
        finally
        {
            if (Directory.Exists(testDirectory))
            {
                Directory.Delete(testDirectory, recursive: true);
            }
        }
    }

    private static string GetParamdefPath()
    {
        return Path.Combine(
            AppContext.BaseDirectory,
            "Assets",
            "AttachEffectTableParam.xml");
    }

    private static string GetFixturePath(string fileName)
    {
        DirectoryInfo? directory = new(AppContext.BaseDirectory);
        while (directory is not null)
        {
            string candidate = Path.Combine(
                directory.FullName,
                "Grand Only",
                fileName);
            if (File.Exists(candidate))
            {
                return candidate;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException(
            $"Could not locate Grand Only/{fileName} from {AppContext.BaseDirectory}.");
    }
}
