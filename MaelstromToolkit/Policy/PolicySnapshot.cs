namespace MaelstromToolkit.Policy;

internal sealed record PolicySnapshot(
    GlobalSettings Global,
    EthicsSettings Ethics,
    IReadOnlyDictionary<string, ProfileSettings> Profiles,
    AiSettings Ai)
{
    public static PolicySnapshot FromDocument(PolicyDocument doc)
    {
        var profiles = doc.Profiles.ToDictionary(k => k.Key, v => v.Value, StringComparer.OrdinalIgnoreCase);
        return new PolicySnapshot(doc.Global, doc.Ethics, profiles, doc.Ai);
    }
}

internal sealed record ParsedPolicy(PolicySnapshot? Snapshot, IReadOnlyList<PolicyDiagnostic> Diagnostics);
