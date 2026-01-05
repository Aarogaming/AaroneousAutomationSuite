using System.Text.Json;

namespace MaelstromToolkit.Packs;

internal sealed class PackManifest
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Version { get; set; } = string.Empty;
    public string? Description { get; set; }
    public List<PackScenario> Scenarios { get; set; } = new();
}

internal sealed class PackScenario
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string Entry { get; set; } = string.Empty;
    public List<string>? RequiredCapabilities { get; set; }
}

internal sealed class PackDiagnostic
{
    public PackDiagnostic(string code, string severity, string packId, string scenarioId, string message)
    {
        Code = code;
        Severity = severity;
        PackId = packId;
        ScenarioId = scenarioId;
        Message = message;
    }

    public string Code { get; }
    public string Severity { get; }
    public string PackId { get; }
    public string ScenarioId { get; }
    public string Message { get; }
}

internal sealed class PackListResult
{
    public List<PackManifest> Packs { get; } = new();
    public List<PackDiagnostic> Diagnostics { get; set; } = new();
}

internal sealed class PackValidationResult
{
    public List<PackDiagnostic> Diagnostics { get; set; } = new();
    public bool HasErrors => Diagnostics.Any(d => d.Severity.Equals("Error", StringComparison.OrdinalIgnoreCase));
}
