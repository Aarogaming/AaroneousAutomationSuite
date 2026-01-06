using System.Collections.Generic;

namespace ProjectMaelstrom.Models;

/// <summary>
/// Aggregated sensor input for SmartPlay (visual snapshot + optional audio cues).
/// </summary>
internal sealed class GameSensors
{
    public GameStateSnapshot? Snapshot { get; init; }
    public IReadOnlyList<GameAudioCue> AudioCues { get; init; } = Array.Empty<GameAudioCue>();
}
