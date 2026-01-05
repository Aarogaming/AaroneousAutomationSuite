namespace MaelstromToolkit.Policy;

internal sealed record EffectivePolicy(
    string Source,
    string ActiveProfile,
    string OperatingMode,
    string LiveStatus,
    IReadOnlyList<string> Reasons,
    string AiProvider,
    string AiModel,
    string AiKeyEnv,
    bool LiveMeansLive);

internal sealed class PolicyResolver
{
    private readonly PolicyService _service;
    private readonly PolicyValidator _validator = new();

    public PolicyResolver(PolicyService service)
    {
        _service = service;
    }

    public (EffectivePolicy effective, PolicyLoadResult sourceResult, string source) Resolve(string policyPath, string outRoot)
    {
        var load = _service.Load(policyPath);
        var mergedDiagnostics = new List<PolicyDiagnostic>(load.Diagnostics);

        PolicySnapshot? snapshot = null;
        if (load.Document != null && !load.HasErrors)
        {
            snapshot = PolicySnapshot.FromDocument(load.Document);
            var validation = _validator.Validate(snapshot);
            mergedDiagnostics.AddRange(validation.Diagnostics);
            var combinedResult = new PolicyLoadResult { Document = load.Document };
            combinedResult.Diagnostics.AddRange(mergedDiagnostics
                .OrderBy(d => d.Code, StringComparer.Ordinal)
                .ThenBy(d => d.Section, StringComparer.Ordinal)
                .ThenBy(d => d.Key, StringComparer.Ordinal)
                .ThenBy(d => d.LineNumber ?? int.MaxValue)
                .ThenBy(d => d.Message, StringComparer.Ordinal));

            var effective = new EffectivePolicy(
                Source: "current",
                ActiveProfile: snapshot.Global.ActiveProfile,
                OperatingMode: validation.OperatingMode,
                LiveStatus: validation.LiveStatus,
                Reasons: validation.Reasons,
                AiProvider: snapshot.Ai.Provider,
                AiModel: snapshot.Ai.Model,
                AiKeyEnv: snapshot.Ai.ApiKeyEnv,
                LiveMeansLive: snapshot.Global.LiveMeansLive);

            return (effective, combinedResult, "current");
        }

        var errorResult = new PolicyLoadResult { Document = load.Document };
        errorResult.Diagnostics.AddRange(mergedDiagnostics);

        var effectiveFallback = new EffectivePolicy(
            Source: "current",
            ActiveProfile: load.Document?.Global.ActiveProfile ?? "unknown",
            OperatingMode: "UNKNOWN",
            LiveStatus: "BLOCKED",
            Reasons: new List<string> { "AASLIVE001" },
            AiProvider: load.Document?.Ai.Provider ?? "none",
            AiModel: load.Document?.Ai.Model ?? string.Empty,
            AiKeyEnv: load.Document?.Ai.ApiKeyEnv ?? string.Empty,
            LiveMeansLive: load.Document?.Global.LiveMeansLive ?? true);

        return (effectiveFallback, errorResult, "current");
    }
}
