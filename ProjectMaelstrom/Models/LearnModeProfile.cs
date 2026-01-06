namespace ProjectMaelstrom.Models;

/// <summary>
/// Profiles for Learn Mode behavior.
/// Mixed = balanced roam; Seek = prefer encounters/targets; Avoid = minimize encounters.
/// </summary>
internal enum LearnModeProfile
{
    Mixed = 0,
    Seek = 1,
    Avoid = 2
}
