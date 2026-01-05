namespace MaelstromToolkit.Policy;

internal sealed class PolicyValidator
{
    private static readonly string[] RequiredProfiles = { "catalog", "simulation", "live_advisory", "live_pilot" };

    public PolicyValidationResult Validate(PolicySnapshot snapshot)
    {
        var diagnostics = new List<PolicyDiagnostic>();

        ValidateGlobal(snapshot, diagnostics);
        ValidateProfiles(snapshot, diagnostics);
        ValidateActiveProfile(snapshot, diagnostics);
        ValidateAi(snapshot, diagnostics);

        var sorted = diagnostics
            .OrderBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.Section, StringComparer.Ordinal)
            .ThenBy(d => d.Key, StringComparer.Ordinal)
            .ThenBy(d => d.LineNumber ?? int.MaxValue)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();

        var (mode, liveStatus, reasons) = EvaluateLiveStatus(snapshot, sorted);
        return new PolicyValidationResult(snapshot, sorted, mode, liveStatus, reasons);
    }

    private static void ValidateGlobal(PolicySnapshot snapshot, List<PolicyDiagnostic> diagnostics)
    {
        if (snapshot.Global.SchemaVersion != 1)
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "global", "schemaVersion", null, "Unsupported schemaVersion (expected 1)."));
        }
        if (!snapshot.Global.SafeWrites.Equals("outOnly", StringComparison.OrdinalIgnoreCase))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "global", "safeWrites", null, "safeWrites must be outOnly."));
        }
    }

    private static void ValidateProfiles(PolicySnapshot snapshot, List<PolicyDiagnostic> diagnostics)
    {
        foreach (var req in RequiredProfiles)
        {
            if (!snapshot.Profiles.ContainsKey(req))
            {
                var severity = snapshot.Global.RequireAllProfilesValid ? DiagnosticSeverity.Error : DiagnosticSeverity.Warning;
                diagnostics.Add(new PolicyDiagnostic("AASPOL010", severity, "profiles", req, null, $"Missing required profile \"{req}\"."));
            }
        }

        foreach (var profile in snapshot.Profiles.Values)
        {
            var section = $"profile {profile.Name}";
            if (!IsValidMode(profile.Mode))
            {
                diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, section, "mode", null, $"Invalid mode \"{profile.Mode}\" (expected catalog|simulation|live)."));
            }

            if (profile.Mode.Equals("live", StringComparison.OrdinalIgnoreCase))
            {
                if (string.IsNullOrWhiteSpace(profile.Autonomy))
                {
                    diagnostics.Add(new PolicyDiagnostic("AASPOL030", DiagnosticSeverity.Error, section, "autonomy", null, "Autonomy required for live profiles."));
                }
                else if (!IsValidAutonomy(profile.Autonomy))
                {
                    diagnostics.Add(new PolicyDiagnostic("AASPOL030", DiagnosticSeverity.Error, section, "autonomy", null, $"Invalid autonomy \"{profile.Autonomy}\" (expected advisory|pilot)."));
                }
            }
        }
    }

    private static void ValidateActiveProfile(PolicySnapshot snapshot, List<PolicyDiagnostic> diagnostics)
    {
        if (!snapshot.Profiles.ContainsKey(snapshot.Global.ActiveProfile))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Error, "global", "activeProfile", null, $"Active profile \"{snapshot.Global.ActiveProfile}\" is not defined."));
        }
    }

    private static void ValidateAi(PolicySnapshot snapshot, List<PolicyDiagnostic> diagnostics)
    {
        var provider = snapshot.Ai.Provider ?? string.Empty;
        if (!IsValidProvider(provider))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "ai", "provider", null, "Provider must be openai|http|none."));
        }

        if (provider.Equals("openai", StringComparison.OrdinalIgnoreCase) && string.IsNullOrWhiteSpace(snapshot.Ai.ApiKeyEnv))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Error, "ai", "apiKeyEnv", null, "apiKeyEnv is required when provider=openai."));
        }
        if (provider.Equals("http", StringComparison.OrdinalIgnoreCase) && string.IsNullOrWhiteSpace(snapshot.Ai.Endpoint))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Error, "ai", "endpoint", null, "endpoint is required when provider=http."));
        }
        if (!IsValidReasoningEffort(snapshot.Ai.ReasoningEffort))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "ai", "reasoningEffort", null, "reasoningEffort must be none|medium|high|xhigh."));
        }
        if (snapshot.Ai.TimeoutSeconds is < 1 or > 600)
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "ai", "timeoutSeconds", null, "timeoutSeconds must be between 1 and 600."));
        }
        if (snapshot.Ai.MaxOutputTokens is < 1 or > 16384)
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "ai", "maxOutputTokens", null, "maxOutputTokens must be between 1 and 16384."));
        }
        if (!snapshot.Ai.ReasoningEffort.Equals("none", StringComparison.OrdinalIgnoreCase) && snapshot.Ai.Temperature != 0)
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Warning, "ai", "temperature", null, "temperature is only supported when reasoningEffort=none."));
        }
    }

    private static (string mode, string liveStatus, IReadOnlyList<string> reasons) EvaluateLiveStatus(PolicySnapshot snapshot, IReadOnlyList<PolicyDiagnostic> diagnostics)
    {
        var active = snapshot.Profiles.TryGetValue(snapshot.Global.ActiveProfile, out var p) ? p : null;
        var operatingMode = active?.Mode?.ToUpperInvariant() switch
        {
            "LIVE" => "LIVE",
            "SIMULATION" => "SIMULATION",
            "CATALOG" => "CATALOG",
            _ => "UNKNOWN"
        };

        if (operatingMode == "LIVE")
        {
            var hasErrors = diagnostics.Any(d => d.Severity == DiagnosticSeverity.Error);
            var reasons = new List<string>();
            if (hasErrors)
            {
                reasons.Add("AASLIVE001");
            }
            var status = hasErrors ? "BLOCKED" : "READY";
            return (operatingMode, status, reasons);
        }

        return (operatingMode, "N/A", Array.Empty<string>());
    }

    private static bool IsValidMode(string? mode) =>
        mode != null && (mode.Equals("catalog", StringComparison.OrdinalIgnoreCase)
                         || mode.Equals("simulation", StringComparison.OrdinalIgnoreCase)
                         || mode.Equals("live", StringComparison.OrdinalIgnoreCase));

    private static bool IsValidAutonomy(string? autonomy) =>
        autonomy != null && (autonomy.Equals("advisory", StringComparison.OrdinalIgnoreCase)
                             || autonomy.Equals("pilot", StringComparison.OrdinalIgnoreCase));

    private static bool IsValidProvider(string? provider) =>
        provider != null && (provider.Equals("openai", StringComparison.OrdinalIgnoreCase)
                             || provider.Equals("http", StringComparison.OrdinalIgnoreCase)
                             || provider.Equals("none", StringComparison.OrdinalIgnoreCase));

    private static bool IsValidReasoningEffort(string? value) =>
        value != null && (value.Equals("none", StringComparison.OrdinalIgnoreCase)
                          || value.Equals("medium", StringComparison.OrdinalIgnoreCase)
                          || value.Equals("high", StringComparison.OrdinalIgnoreCase)
                          || value.Equals("xhigh", StringComparison.OrdinalIgnoreCase));
}
