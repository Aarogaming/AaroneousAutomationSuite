using System.Security.Cryptography;
using System.Text;

namespace MaelstromToolkit.Policy;

internal sealed record PolicyEffectiveResult(
    string Source,
    string Hash,
    PolicySnapshot? Snapshot,
    string ActiveProfile,
    string ProfileMode,
    string OperatingMode,
    string LiveStatus,
    IReadOnlyList<string> Reasons,
    IReadOnlyList<PolicyDiagnostic> Diagnostics,
    IReadOnlyList<PolicyDiagnostic> FileDiagnostics,
    IReadOnlyList<PolicyDiagnostic> LkgDiagnostics,
    string RawText)
{
    public bool IsValid => Snapshot != null && Diagnostics.All(d => d.Severity != DiagnosticSeverity.Error);
}

internal sealed class PolicyEffectiveResolver
{
    private readonly PolicyTxtParserFacade _parser = new();
    private readonly PolicyValidator _validator = new();
    private readonly string _defaultPolicyText;

    public PolicyEffectiveResolver(string defaultPolicyText)
    {
        _defaultPolicyText = Normalize(defaultPolicyText);
    }

    public PolicyEffectiveResult Resolve(string fileText, string? lkgText)
    {
        var fileResult = Evaluate("FILE", Normalize(fileText ?? string.Empty));
        if (fileResult.IsValid)
        {
            return fileResult with { FileDiagnostics = fileResult.Diagnostics };
        }

        PolicyEffectiveResult? lkgResult = null;
        if (!string.IsNullOrEmpty(lkgText))
        {
            lkgResult = Evaluate("LKG", Normalize(lkgText!));
            if (lkgResult.IsValid)
            {
                return lkgResult with { FileDiagnostics = fileResult.Diagnostics, LkgDiagnostics = lkgResult.Diagnostics };
            }
        }

        var defaultResult = Evaluate("DEFAULT", _defaultPolicyText);
        return defaultResult with
        {
            FileDiagnostics = fileResult.Diagnostics,
            LkgDiagnostics = lkgResult?.Diagnostics ?? Array.Empty<PolicyDiagnostic>()
        };
    }

    private PolicyEffectiveResult Evaluate(string source, string text)
    {
        var parsed = _parser.Parse(text);
        var diagnostics = new List<PolicyDiagnostic>(parsed.Diagnostics);
        PolicySnapshot? snapshot = null;
        string operatingMode = "UNKNOWN";
        string liveStatus = "BLOCKED";
        var reasons = new List<string>();

        if (parsed.Snapshot != null)
        {
            var validation = _validator.Validate(parsed.Snapshot);
            snapshot = validation.Snapshot;
            diagnostics.AddRange(validation.Diagnostics);
            operatingMode = validation.OperatingMode;
            liveStatus = validation.LiveStatus;
            reasons.AddRange(validation.Reasons);
        }
        else
        {
            reasons.Add("AASLIVE001");
        }

        var ordered = diagnostics
            .OrderBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.Section, StringComparer.Ordinal)
            .ThenBy(d => d.Key, StringComparer.Ordinal)
            .ThenBy(d => d.LineNumber ?? int.MaxValue)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();

        var activeProfile = snapshot?.Global.ActiveProfile ?? "unknown";
        var profileMode = snapshot != null && snapshot.Profiles.TryGetValue(activeProfile, out var p)
            ? p.Mode.ToUpperInvariant()
            : "UNKNOWN";

        var hash = ComputeSha256(text);
        var orderedReasons = reasons.OrderBy(r => r, StringComparer.Ordinal).ToList();

        return new PolicyEffectiveResult(
            Source: source,
            Hash: hash,
            Snapshot: snapshot,
            ActiveProfile: activeProfile,
            ProfileMode: profileMode,
            OperatingMode: operatingMode,
            LiveStatus: liveStatus,
            Reasons: orderedReasons,
            Diagnostics: ordered,
            FileDiagnostics: Array.Empty<PolicyDiagnostic>(),
            LkgDiagnostics: Array.Empty<PolicyDiagnostic>(),
            RawText: text);
    }

    private static string Normalize(string input) =>
        input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\r", "\n", StringComparison.Ordinal);

    private static string ComputeSha256(string text)
    {
        using var sha = SHA256.Create();
        var bytes = Encoding.UTF8.GetBytes(Normalize(text));
        var hash = sha.ComputeHash(bytes);
        return BitConverter.ToString(hash).Replace("-", string.Empty).ToLowerInvariant();
    }
}
