using Emgu.CV;
using Emgu.CV.CvEnum;
using Emgu.CV.Structure;
using ProjectMaelstrom.Utilities;
using ProjectMaelstrom.Utilities.Capture;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Text;

namespace ProjectMaelstrom.Modules.ImageRecognition;

internal class ImageFinder
{
    private static readonly Dictionary<string, Image<Hsv, byte>> ImageCache = new Dictionary<string, Image<Hsv, byte>>();
    private static readonly object CacheLock = new object();

    private static Image<Hsv, byte> GetCachedImage(string imagePath)
    {
        lock (CacheLock)
        {
            if (ImageCache.TryGetValue(imagePath, out var cachedImage))
            {
                return cachedImage;
            }

            // Load and cache the image
            var image = new Image<Bgr, byte>(imagePath).Convert<Hsv, byte>();
            ImageCache[imagePath] = image;
            return image;
        }
    }

    public static void ClearImageCache()
    {
        lock (CacheLock)
        {
            foreach (var image in ImageCache.Values)
            {
                image.Dispose();
            }
            ImageCache.Clear();
        }
    }
    [DllImport("user32.dll")]
    private static extern IntPtr FindWindow(string? lpClassName, string? lpWindowName);

    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public static Point? SearchForTargetImageWithinScreenshot(string targetImagePath)
    {
        IntPtr windowHandle = GetWindowHandle();
        if (windowHandle == IntPtr.Zero)
        {
            throw new Exception("Window not found.");
        }

        RECT rect = GetWindowRect(windowHandle);

        int windowLeft = rect.Left;
        int windowTop = rect.Top;

        string screenshotPath = CaptureScreen(rect);

        using var capturedScreenshot = new Image<Bgr, byte>(screenshotPath).Convert<Hsv, byte>();
        using var targetImage = GetCachedImage(targetImagePath);

        var comparisonWidth = capturedScreenshot.Width - targetImage.Width + 1;
        var comparisonHeight = capturedScreenshot.Height - targetImage.Height + 1;

        using var matchingResult = new Image<Gray, float>(comparisonWidth, comparisonHeight);
        CvInvoke.MatchTemplate(capturedScreenshot, targetImage, matchingResult, TemplateMatchingType.CcoeffNormed);

        double[] minValues, maxValues;
        Point[] minLocations, maxLocations;
        matchingResult.MinMax(out minValues, out maxValues, out minLocations, out maxLocations);

        try
        {
            File.Delete(screenshotPath);
        }
        catch
        {

        }

        double matchingThreshold = 0.75;
        if (maxValues[0] >= matchingThreshold)
        {
            Point matchingPoint = maxLocations[0];

            matchingPoint.X += windowLeft;
            matchingPoint.Y += windowTop;

            return matchingPoint;
        }

        return null;
    }

    public static bool IsImageInCenter(string targetImagePath)
    {
        IntPtr windowHandle = GetWindowHandle();
        if (windowHandle == IntPtr.Zero)
        {
            throw new Exception("Window not found.");
        }

        RECT rect = GetWindowRect(windowHandle);

        int windowLeft = rect.Left;
        int windowTop = rect.Top;

        string screenshotPath = CaptureScreen(rect);

        using var capturedScreenshot = new Image<Bgr, byte>(screenshotPath).Convert<Hsv, byte>();
        using var targetImage = GetCachedImage(targetImagePath);

        var comparisonWidth = capturedScreenshot.Width - targetImage.Width + 1;
        var comparisonHeight = capturedScreenshot.Height - targetImage.Height + 1;

        using var matchingResult = new Image<Gray, float>(comparisonWidth, comparisonHeight);
        CvInvoke.MatchTemplate(capturedScreenshot, targetImage, matchingResult, TemplateMatchingType.CcoeffNormed);

        double[] minValues, maxValues;
        Point[] minLocations, maxLocations;
        matchingResult.MinMax(out minValues, out maxValues, out minLocations, out maxLocations);

        double matchingThreshold = 0.6;
        if (maxValues[0] >= matchingThreshold)
        {
            Point matchingPoint = maxLocations[0];
            matchingPoint.X += windowLeft;
            matchingPoint.Y += windowTop;

            int centerX = capturedScreenshot.Width / 2;
            int centerY = capturedScreenshot.Height / 2;

            int imageCenterX = matchingPoint.X + targetImage.Width / 2;
            int imageCenterY = matchingPoint.Y + targetImage.Height / 2;

            int tolerance = 2000;

            bool isCenter = Math.Abs(centerX - imageCenterX) <= tolerance && Math.Abs(centerY - imageCenterY) <= tolerance;

            return isCenter;
        }

        return false;
    }

    public static Point? RetrieveTargetImagePositionInScreenshot(string targetImagePath)
    {
        Point? position = SearchForTargetImageWithinScreenshot(targetImagePath);

        return position;
    }

    public static string CaptureScreen(RECT rect)
    {
        string randomScreenshotName = GeneralUtils.Instance.RandomString(20);
        string screenshotFilePath = $"screenshots/{randomScreenshotName}.png";

        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        var region = new Rectangle(rect.Left, rect.Top, width, height);

        using (var bitmapScreenshot = CaptureProvider.Default.CaptureRegion(region))
        {
            bitmapScreenshot.Save(screenshotFilePath, ImageFormat.Png);
        }

        return screenshotFilePath;
    }

    public static IntPtr GetWindowHandle()
    {
        // Try direct exact-match first
        IntPtr handle = FindWindow(null, "Wizard101");
        if (handle != IntPtr.Zero && IsWindowVisible(handle) && !IsIconic(handle))
        {
            return handle;
        }

        // Fallback: enumerate top-level windows and look for a title that contains "Wizard101"
        IntPtr found = IntPtr.Zero;

        EnumWindows((hwnd, lParam) =>
        {
            int len = GetWindowTextLength(hwnd);
            if (len <= 0) return true;

            var sb = new StringBuilder(len + 1);
            GetWindowText(hwnd, sb, sb.Capacity);
            var title = sb.ToString();

            if (!string.IsNullOrEmpty(title) && title.IndexOf("Wizard101", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                if (IsWindowVisible(hwnd) && !IsIconic(hwnd))
                {
                    found = hwnd;
                    return false; // stop enumeration
                }
            }

            return true; // continue enumeration
        }, IntPtr.Zero);

        return found;
    }

    public static RECT GetWindowRect(IntPtr windowHandle)
    {
        if (GetWindowRect(windowHandle, out RECT rect))
        {
            return rect;
        }
        else
        {
            throw new Exception("Failed to retrieve window position.");
        }
    }
}
