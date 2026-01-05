using System.Drawing;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Central placeholder for shared UI color tokens to be used in a future polish pass.
/// NOTE: Do not change behavior yet; these constants are currently unused on purpose.
/// </summary>
internal static class UiColorTokens
{
    public static readonly Color AccentGreen = Color.FromArgb(34, 74, 54);
    public static readonly Color AccentGreenText = Color.LightGreen;

    public static readonly Color AccentRed = Color.FromArgb(104, 52, 52);
    public static readonly Color AccentRedText = Color.MistyRose;

    public static readonly Color AccentAmber = Color.Goldenrod;
    public static readonly Color AccentGold = Color.Gold;

    public static readonly Color SurfaceDark = Color.FromArgb(26, 34, 58);
    public static readonly Color SurfaceMuted = Color.FromArgb(54, 54, 54);
    public static readonly Color TextMuted = Color.Silver;
}
