namespace NightreignRegulationHelper;

internal sealed record WeightRecord(
    int TableId,
    int AttachEffectId,
    int Occurrence,
    ushort ChanceWeight,
    short ChanceWeightDlc);
