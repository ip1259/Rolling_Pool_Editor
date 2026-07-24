using System.Text.Json;
using NightreignRegulationHelper;

return Run(args);

static int Run(string[] args)
{
    JsonSerializerOptions jsonOptions = new(JsonSerializerDefaults.Web);

    try
    {
        if (TryParseInspectArguments(args, out string? inspectBasePath))
        {
            string paramdefPath = GetParamdefPath();
            RegulationInspector inspector = new();
            InspectResult details = inspector.Inspect(inspectBasePath!, paramdefPath);
            return WriteResult(
                new HelperResult(true, ExitCodes.Success, "Inspection succeeded.", details),
                jsonOptions);
        }

        if (TryParsePatchArguments(
                args,
                out string? patchBasePath,
                out string? manifestPath,
                out string? outputPath))
        {
            RegulationPatcher patcher = new();
            PatchResult details = patcher.Patch(
                patchBasePath!,
                manifestPath!,
                outputPath!,
                GetParamdefPath());
            return WriteResult(
                new HelperResult(true, ExitCodes.Success, "Patch succeeded.", details),
                jsonOptions);
        }

        string error =
            "Usage: NightreignRegulationHelper inspect --base <path> | " +
            "patch --base <path> --changes <json> --output <path>";
        return WriteResult(
            new HelperResult(false, ExitCodes.UnexpectedFailure, error),
            jsonOptions);
    }
    catch (InvalidBaseException exception)
    {
        Console.Error.WriteLine(exception.Message);
        return WriteResult(
            new HelperResult(false, ExitCodes.InvalidBase, exception.Message),
            jsonOptions);
    }
    catch (TargetParamNotFoundException exception)
    {
        Console.Error.WriteLine(exception.Message);
        return WriteResult(
            new HelperResult(false, ExitCodes.ParamNotFound, exception.Message),
            jsonOptions);
    }
    catch (InvalidWhitelistException exception)
    {
        Console.Error.WriteLine(exception.Message);
        return WriteResult(
            new HelperResult(false, ExitCodes.InvalidWhitelist, exception.Message),
            jsonOptions);
    }
    catch (InvalidChangeException exception)
    {
        Console.Error.WriteLine(exception.Message);
        return WriteResult(
            new HelperResult(false, ExitCodes.InvalidChange, exception.Message),
            jsonOptions);
    }
    catch (RegulationWriteException exception)
    {
        Console.Error.WriteLine(exception);
        return WriteResult(
            new HelperResult(false, ExitCodes.WriteFailure, exception.Message),
            jsonOptions);
    }
    catch (RegulationVerificationException exception)
    {
        Console.Error.WriteLine(exception);
        return WriteResult(
            new HelperResult(false, ExitCodes.VerificationFailure, exception.Message),
            jsonOptions);
    }
    catch (InvalidDataException exception)
    {
        Console.Error.WriteLine(exception);
        return WriteResult(
            new HelperResult(false, ExitCodes.ParseFailure, exception.Message),
            jsonOptions);
    }
    catch (Exception exception)
    {
        Console.Error.WriteLine(exception);
        return WriteResult(
            new HelperResult(false, ExitCodes.UnexpectedFailure, exception.Message),
            jsonOptions);
    }
}

static bool TryParseInspectArguments(
    string[] args,
    out string? basePath)
{
    basePath = null;

    if (args.Length != 3 ||
        !string.Equals(args[0], "inspect", StringComparison.OrdinalIgnoreCase) ||
        !string.Equals(args[1], "--base", StringComparison.OrdinalIgnoreCase))
    {
        return false;
    }

    basePath = Path.GetFullPath(args[2]);
    return true;
}

static bool TryParsePatchArguments(
    string[] args,
    out string? basePath,
    out string? manifestPath,
    out string? outputPath)
{
    basePath = null;
    manifestPath = null;
    outputPath = null;

    if (args.Length != 7 ||
        !string.Equals(args[0], "patch", StringComparison.OrdinalIgnoreCase))
    {
        return false;
    }

    for (int index = 1; index < args.Length; index += 2)
    {
        string value = Path.GetFullPath(args[index + 1]);
        switch (args[index].ToLowerInvariant())
        {
            case "--base":
                basePath = value;
                break;
            case "--changes":
                manifestPath = value;
                break;
            case "--output":
                outputPath = value;
                break;
            default:
                return false;
        }
    }

    return basePath is not null &&
        manifestPath is not null &&
        outputPath is not null;
}

static string GetParamdefPath()
{
    return Path.Combine(
        AppContext.BaseDirectory,
        "Assets",
        "AttachEffectTableParam.xml");
}

static int WriteResult(HelperResult result, JsonSerializerOptions options)
{
    Console.Out.WriteLine(JsonSerializer.Serialize(result, options));
    return result.Code;
}
