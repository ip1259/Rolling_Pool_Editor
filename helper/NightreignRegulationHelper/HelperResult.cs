using System.Text.Json.Serialization;

namespace NightreignRegulationHelper;

internal sealed record HelperResult(
    [property: JsonPropertyName("success")] bool Success,
    [property: JsonPropertyName("code")] int Code,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("details")] object? Details = null);
