namespace MaelstromToolkit;

internal sealed record EvalSummary(string RiskLevel, IReadOnlyList<string> ChangedFields, IReadOnlyList<string> Notes);
