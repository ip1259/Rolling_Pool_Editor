namespace NightreignRegulationHelper;

internal sealed record PatchResult(
    string OutputPath,
    int ModifiedCount,
    long OutputSize);
