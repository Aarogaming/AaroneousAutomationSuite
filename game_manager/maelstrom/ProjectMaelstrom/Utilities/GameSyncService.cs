using System.Runtime.InteropServices;
using ProjectMaelstrom.Models;
using ProjectMaelstrom.Modules.ImageRecognition;

namespace ProjectMaelstrom.Utilities;

internal static class GameSyncService
{
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    public static GameSyncState Evaluate(string? expectedResolution)
    {
        try
        {
            IntPtr handle = ImageFinder.GetWindowHandle();
            if (handle == IntPtr.Zero)
            {
                return new GameSyncState(GameSyncHealth.WindowMissing, "Wizard101 window not detected");
            }

            var rect = ImageFinder.GetWindowRect(handle);
            bool hasFocus = GetForegroundWindow() == handle;
            bool resolutionOk = ResolutionMatches(rect, expectedResolution);

            if (!resolutionOk)
            {
                return new GameSyncState(GameSyncHealth.ResolutionMismatch,
                    $"Window size does not match {expectedResolution}", expectedResolution, true);
            }

            if (!hasFocus)
            {
                return new GameSyncState(GameSyncHealth.FocusLost, "Wizard101 is not focused", expectedResolution, true);
            }

            return new GameSyncState(GameSyncHealth.InSync, "Wizard101 window in sync", expectedResolution, true);
        }
        catch (Exception ex)
        {
            Logger.LogError("[GameSync] Unable to evaluate sync state", ex);
            return new GameSyncState(GameSyncHealth.Unknown, "Sync check failed");
        }
    }

    private static bool ResolutionMatches(ImageFinder.RECT rect, string? expectedResolution)
    {
        if (string.IsNullOrWhiteSpace(expectedResolution))
        {
            return true;
        }

        var parts = expectedResolution.ToLowerInvariant().Split('x');
        if (parts.Length != 2 ||
            !int.TryParse(parts[0], out int expectedWidth) ||
            !int.TryParse(parts[1], out int expectedHeight))
        {
            return true;
        }

        int windowWidth = rect.Right - rect.Left;
        int windowHeight = rect.Bottom - rect.Top;

        const int tolerance = 40;
        bool widthMatch = Math.Abs(windowWidth - expectedWidth) <= tolerance;
        bool heightMatch = Math.Abs(windowHeight - expectedHeight) <= tolerance;

        return widthMatch && heightMatch;
    }
}
