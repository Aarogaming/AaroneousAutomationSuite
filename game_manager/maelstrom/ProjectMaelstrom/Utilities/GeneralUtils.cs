using ProjectMaelstrom.Modules.ImageRecognition;
using System.Threading;

namespace ProjectMaelstrom.Utilities;

internal class GeneralUtils : Util
{
    private static GeneralUtils? _instance;

    public static GeneralUtils Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = new GeneralUtils();
            }

            return _instance;
        }
    }

    private Random _random = new Random();

    public void SetMarker()
    {
        Point? marker = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/marklocation.png");

        int attempts = 0;
        const int maxAttempts = 20;
        while (marker == null && attempts < maxAttempts)
        {
            Thread.Sleep(150);
            marker = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/marklocation.png");
            attempts++;
        }

        if (marker.HasValue)
        {
            _playerController.Click(marker.Value);
        }
    }

    public bool Teleport()
    {
        Point? teleport = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/teleportto.png");

        int attempts = 0;
        const int maxAttempts = 20;
        while (teleport == null && attempts < maxAttempts)
        {
            Thread.Sleep(150);
            teleport = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/teleportto.png");
            attempts++;
        }

        if (teleport.HasValue)
        {
            _playerController.Click(teleport.Value);
            return true;
        }

        Logger.Log("[Teleport] Teleport image not found after retries.");
        return false;
    }

    public void OpenGameWindow()
    {
        ClickIfFound($"{StorageUtils.GetAppPath()}/General/window_taskbar_icon.png", "[OpenGameWindow]");
    }

    public void OpenStatsWindow()
    {
        ClickIfFound($"{StorageUtils.GetAppPath()}/General/spellbook.png", "[OpenStatsWindow]");
    }

    public bool IsGameVisible()
    {
        try
        {
            string appPath = StorageUtils.GetAppPath();
            if (string.IsNullOrEmpty(appPath))
            {
                return false;
            }

            string targetImagePath = $"{appPath}/General/window_header.png";
            if (string.IsNullOrEmpty(targetImagePath) || !File.Exists(targetImagePath))
            {
                return false;
            }

            Point? windowVisible = ImageFinder.RetrieveTargetImagePositionInScreenshot(targetImagePath);

            return windowVisible.HasValue;
        }
        catch
        {
            // If image search fails (for example window not found), treat game as not visible
            return false;
        }
    }

    public bool IsStatsPageVisible()
    {
        Point? statsPageVisible = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/General/spellbook_homepage.png");

        if (statsPageVisible.HasValue)
        {
            return true;
        }

        return false;
    }

    public string RandomString(int length)
    {
        const string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        return new string(Enumerable.Repeat(chars, length)
            .Select(s => s[_random.Next(s.Length)]).ToArray());
    }

    public void ResetCursorPosition()
    {
        Point? blankSpot = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/General/blank.png");

        int attempts = 0;
        const int maxAttempts = 20;
        while (blankSpot == null && attempts < maxAttempts)
        {
            Thread.Sleep(150);
            blankSpot = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/General/blank.png");
            attempts++;
        }

        if (blankSpot.HasValue)
        {
            _playerController.Click(blankSpot.Value);
            return;
        }

        _playerController.Click(new Point(50, 20));
    }

    private void ClickIfFound(string imagePath, string context, int maxAttempts = 20, int delayMs = 150)
    {
        Point? target = ImageFinder.RetrieveTargetImagePositionInScreenshot(imagePath);
        int attempts = 0;

        while (target == null && attempts < maxAttempts)
        {
            Thread.Sleep(delayMs);
            target = ImageFinder.RetrieveTargetImagePositionInScreenshot(imagePath);
            attempts++;
        }

        if (target.HasValue)
        {
            _playerController.Click(target.Value);
        }
        else
        {
            Logger.Log($"{context} target not found after {attempts} attempts ({imagePath})");
        }
    }
}
