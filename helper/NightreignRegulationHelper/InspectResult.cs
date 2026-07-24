namespace NightreignRegulationHelper;

internal sealed record InspectResult(
    string BaseSha256,
    long BaseSize,
    string BinderVersion,
    int BinderFileCount,
    string ParamName,
    string ParamType,
    int ParamRowCount,
    int EditableRowCount);
