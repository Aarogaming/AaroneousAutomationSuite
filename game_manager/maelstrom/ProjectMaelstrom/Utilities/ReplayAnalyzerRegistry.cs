namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Optional registry for replay analyzers contributed by plugins. Empty by default.
/// </summary>
public static class ReplayAnalyzerRegistry
{
    private static readonly List<string> _analyzers = new();
    private static readonly object _lock = new();

    public static IReadOnlyList<string> Current
    {
        get
        {
            lock (_lock) { return _analyzers.ToList(); }
        }
    }

    public static void Register(string analyzerId)
    {
        if (string.IsNullOrWhiteSpace(analyzerId)) return;
        lock (_lock)
        {
            if (!_analyzers.Contains(analyzerId, StringComparer.OrdinalIgnoreCase))
            {
                _analyzers.Add(analyzerId);
            }
        }
    }

    public static void Clear()
    {
        lock (_lock)
        {
            _analyzers.Clear();
        }
    }
}
