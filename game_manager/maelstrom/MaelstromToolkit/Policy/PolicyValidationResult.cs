namespace MaelstromToolkit.Policy;

internal sealed record PolicyValidationResult(
    PolicySnapshot? Snapshot,
    IReadOnlyList<PolicyDiagnostic> Diagnostics,
    string OperatingMode,
    string LiveStatus,
    IReadOnlyList<string> Reasons)
{
    public bool HasErrors => Diagnostics.Any(d => d.Severity == DiagnosticSeverity.Error);
}
