namespace NightreignRegulationHelper;

internal sealed class InvalidBaseException(string message) : Exception(message);

internal sealed class TargetParamNotFoundException(string message) : Exception(message);

internal sealed class InvalidChangeException(string message) : Exception(message);

internal sealed class InvalidWhitelistException(string message) : Exception(message);

internal sealed class RegulationWriteException(string message, Exception innerException)
    : Exception(message, innerException);

internal sealed class RegulationVerificationException(string message) : Exception(message);
