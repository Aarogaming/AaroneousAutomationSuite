namespace MaelstromToolkit.Policy;

internal sealed class GlobalSettings
{
    public int SchemaVersion { get; set; } = 1;
    public string ActiveProfile { get; set; } = "catalog";
    public string OnInvalidConfig { get; set; } = "keepLastKnownGood";
    public bool RequireAllProfilesValid { get; set; } = true;
    public bool DenyUnknownCapabilities { get; set; } = true;
    public bool DenyUnknownKeys { get; set; } = false;
    public bool LiveMeansLive { get; set; } = true;
    public string SafeWrites { get; set; } = "outOnly";
}

internal sealed class EthicsSettings
{
    public string Purpose { get; set; } = "educational_research";
    public bool RequireConsentForEnvironmentControl { get; set; } = true;
    public string Prohibit { get; set; } = string.Empty;
    public bool PrivacyNoSecretsInLogs { get; set; } = true;
    public bool PrivacyStoreScreenshots { get; set; } = false;
    public bool PrivacyStoreAudio { get; set; } = false;
}

internal sealed class ProfileSettings
{
    public string Name { get; set; } = string.Empty;
    public string Mode { get; set; } = "catalog"; // catalog|simulation|live
    public string Autonomy { get; set; } = "advisory"; // advisory|pilot|full (for live)
}

internal sealed class AiSettings
{
    public bool Enabled { get; set; } = true;
    public string Provider { get; set; } = "openai"; // openai|http|none
    public string ApiKeyEnv { get; set; } = "OPENAI_API_KEY";
    public string Model { get; set; } = "gpt-5.2-pro";
    public double Temperature { get; set; } = 0;
    public bool AllowSendScreenshotsToModel { get; set; } = false;
    public bool AllowSendAudioToModel { get; set; } = false;
    public bool Store { get; set; } = false;
    public string ReasoningEffort { get; set; } = "none";
    public string? Endpoint { get; set; }
    public int TimeoutSeconds { get; set; } = 60;
    public int MaxOutputTokens { get; set; } = 1024;
    public string? UserTag { get; set; }
    public string? AllowedTools { get; set; }
    public string? DeniedTools { get; set; }
}

internal sealed class PolicyDocument
{
    public GlobalSettings Global { get; } = new();
    public EthicsSettings Ethics { get; } = new();
    public Dictionary<string, ProfileSettings> Profiles { get; } = new(StringComparer.OrdinalIgnoreCase);
    public AiSettings Ai { get; } = new();
}

internal enum DiagnosticSeverity { Info, Warning, Error }

internal sealed record PolicyDiagnostic(string Code, DiagnosticSeverity Severity, string Section, string Key, int? LineNumber, string Message);

internal sealed class PolicyLoadResult
{
    public PolicyDocument? Document { get; set; }
    public List<PolicyDiagnostic> Diagnostics { get; } = new();
    public bool HasErrors => Diagnostics.Any(d => d.Severity == DiagnosticSeverity.Error);
    public IEnumerable<PolicyDiagnostic> SortedDiagnostics() =>
        Diagnostics
            .OrderBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.Section, StringComparer.Ordinal)
            .ThenBy(d => d.Key, StringComparer.Ordinal)
            .ThenBy(d => d.LineNumber ?? int.MaxValue)
            .ThenBy(d => d.Message, StringComparer.Ordinal);
}
