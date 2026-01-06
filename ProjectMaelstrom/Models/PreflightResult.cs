namespace ProjectMaelstrom.Models;

internal sealed class PreflightResult
{
    public bool Allowed { get; init; }
    public string? Reason { get; init; }
    public bool AutoQueued { get; init; }

    public static PreflightResult Allow() => new() { Allowed = true };
    public static PreflightResult Block(string reason, bool autoQueued = false) => new() { Allowed = false, Reason = reason, AutoQueued = autoQueued };
}
