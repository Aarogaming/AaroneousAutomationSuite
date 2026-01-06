using System.Collections.Concurrent;

namespace ProjectMaelstrom.Utilities.Overlay;

/// <summary>
/// Maintains read-only overlay snapshots and recent action summaries.
/// </summary>
public static class OverlaySnapshotHub
{
    private static readonly object _lock = new();
    private static OverlayStateSnapshot _current = BuildSnapshot("Unknown");
    private const int BufferSize = 50;
    private static readonly ConcurrentQueue<string> _recentActions = new();

    public static event Action<OverlayStateSnapshot>? SnapshotUpdated;

    public static OverlayStateSnapshot Current
    {
        get
        {
            lock (_lock) { return _current; }
        }
    }

    public static void SetExecutorStatus(string status)
    {
        lock (_lock)
        {
            _current = BuildSnapshot(status);
        }
        SnapshotUpdated?.Invoke(_current);
    }

    public static void AppendAction(string summary)
    {
        if (string.IsNullOrWhiteSpace(summary)) return;
        _recentActions.Enqueue(summary);
        while (_recentActions.Count > BufferSize && _recentActions.TryDequeue(out _)) { }
        lock (_lock)
        {
            _current = BuildSnapshot(_current.LastExecutorStatus);
        }
        SnapshotUpdated?.Invoke(_current);
    }

    private static OverlayStateSnapshot BuildSnapshot(string status)
    {
        var policy = ExecutionPolicyManager.Current;
        var plugins = PluginLoader.Current;
        var loaded = plugins.Count(p => p.Status == PluginStatus.Allowed);
        var blocked = plugins.Count(p => p.Status == PluginStatus.Blocked || p.Status == PluginStatus.Incompatible || p.Status == PluginStatus.Failed);

        return new OverlayStateSnapshot
        {
            TimestampUtc = DateTime.UtcNow,
            Profile = policy.Profile.ToString(),
            Mode = policy.Mode.ToString(),
            AllowLiveAutomation = policy.AllowLiveAutomation,
            LastExecutorStatus = status,
            RecentActions = _recentActions.ToArray(),
            LoadedPluginsCount = loaded,
            BlockedPluginsCount = blocked
        };
    }
}
