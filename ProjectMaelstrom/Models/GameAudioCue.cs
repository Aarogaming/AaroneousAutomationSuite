namespace ProjectMaelstrom.Models;

/// <summary>
/// Lightweight representation of an audio-derived signal that SmartPlay can use in place of (or to reinforce) visual cues.
/// </summary>
internal sealed class GameAudioCue
{
    /// <summary>
    /// Short name for the cue (e.g., "petdance_left", "petdance_right", "quest_complete").
    /// </summary>
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// Confidence from 0-1 for the detected cue.
    /// </summary>
    public double Confidence { get; init; }

    /// <summary>
    /// When the cue was detected (UTC).
    /// </summary>
    public DateTime CapturedUtc { get; init; }

    /// <summary>
    /// Optional free-form metadata (e.g., frequency, amplitude bands).
    /// </summary>
    public string? Metadata { get; init; }
}
