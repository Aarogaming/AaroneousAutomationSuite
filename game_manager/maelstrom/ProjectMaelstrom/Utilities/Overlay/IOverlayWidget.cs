using System.Windows.Forms;

namespace ProjectMaelstrom.Utilities.Overlay;

public interface IOverlayWidget
{
    string Id { get; }
    string Title { get; }
    Control CreateControl();
    void Update(OverlayStateSnapshot snapshot);
}

public sealed class OverlayStateSnapshot
{
    public DateTime TimestampUtc { get; init; } = DateTime.UtcNow;
    public string Profile { get; init; } = "Public";
    public string Mode { get; init; } = "SimulationOnly";
    public bool AllowLiveAutomation { get; init; }
    public string LastExecutorStatus { get; init; } = "Unknown";
    public IReadOnlyList<string> RecentActions { get; init; } = Array.Empty<string>();
    public int LoadedPluginsCount { get; init; }
    public int BlockedPluginsCount { get; init; }
}
