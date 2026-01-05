namespace ProjectMaelstrom.Models;

internal enum GameSyncHealth
{
    InSync,
    WindowMissing,
    ResolutionMismatch,
    FocusLost,
    Unknown
}

internal readonly struct GameSyncState
{
    public GameSyncState(GameSyncHealth health, string message, string? resolution = null, bool hasWindow = false)
    {
        Health = health;
        Message = message;
        ExpectedResolution = resolution;
        HasWindow = hasWindow;
    }

    public GameSyncHealth Health { get; }
    public string Message { get; }
    public string? ExpectedResolution { get; }
    public bool HasWindow { get; }
    public bool IsInSync => Health == GameSyncHealth.InSync;
}
