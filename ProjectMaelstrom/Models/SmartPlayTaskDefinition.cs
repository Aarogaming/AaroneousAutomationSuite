namespace ProjectMaelstrom.Models;

/// <summary>
/// External smart-play task definition, read from cache (smartplay_tasks.json).
/// </summary>
internal sealed class SmartPlayTaskDefinition
{
    public string? Type { get; set; } // script_run | nav | potion_refill
    public string? Target { get; set; } // bazaar|minigames|pet|custom
    public string? ScriptName { get; set; }
    public int? RepeatCount { get; set; } // null => 1; 0 => infinite
}
