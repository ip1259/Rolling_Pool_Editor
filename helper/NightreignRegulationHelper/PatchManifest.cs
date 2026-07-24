using System.Text.Json.Serialization;

namespace NightreignRegulationHelper;

internal sealed record PatchManifest(
    [property: JsonPropertyName("formatVersion")] int FormatVersion,
    [property: JsonPropertyName("baseSha256")] string BaseSha256,
    [property: JsonPropertyName("param")] string Param,
    [property: JsonPropertyName("editableTableIds")] IReadOnlyList<int> EditableTableIds,
    [property: JsonPropertyName("changes")] IReadOnlyList<WeightChange> Changes);

internal sealed record WeightChange(
    [property: JsonPropertyName("id")] int TableId,
    [property: JsonPropertyName("attachEffectId")] int AttachEffectId,
    [property: JsonPropertyName("occurrence")] int Occurrence,
    [property: JsonPropertyName("expectedChanceWeight")] ushort ExpectedChanceWeight,
    [property: JsonPropertyName("expectedChanceWeightDlc")] short ExpectedChanceWeightDlc,
    [property: JsonPropertyName("chanceWeight")] ushort ChanceWeight,
    [property: JsonPropertyName("chanceWeightDlc")] short ChanceWeightDlc);
