using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom.Modules.ImageRecognition;

internal static class ScreenCaptureService
{
    /// <summary>
    /// Captures the Wizard101 window (if visible) and saves to Screenshots folder. Returns saved path or null.
    /// </summary>
    public static string? CaptureWizardWindow()
    {
        try
        {
            IntPtr handle = ImageFinder.GetWindowHandle();
            if (handle == IntPtr.Zero)
            {
                Logger.Log("[ScreenCapture] Wizard101 window not found.");
                return null;
            }

            var rect = ImageFinder.GetWindowRect(handle);
            string path = ImageFinder.CaptureScreen(rect);

            // Move to Screenshots folder under app root
            string shotsDir = Path.Combine(StorageUtils.GetAppRoot(), "Screenshots");
            Directory.CreateDirectory(shotsDir);
            string dest = Path.Combine(shotsDir, Path.GetFileName(path));
            File.Move(path, dest, true);

            Logger.Log($"[ScreenCapture] Saved: {dest}");
            return dest;
        }
        catch (Exception ex)
        {
            Logger.LogError("[ScreenCapture] Capture failed", ex);
            return null;
        }
    }
}
