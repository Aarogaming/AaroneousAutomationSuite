using System.Drawing.Imaging;

namespace ProjectMaelstrom.Utilities.Capture;

/// <summary>
/// Shared capture abstraction for grabbing window/region snapshots. Implementation stays local to the process.
/// </summary>
internal interface ICaptureProvider
{
    Bitmap CaptureRegion(Rectangle region);
    Bitmap CaptureForm(Form form);
}

internal sealed class DefaultCaptureProvider : ICaptureProvider
{
    public Bitmap CaptureRegion(Rectangle region)
    {
        var bmp = new Bitmap(region.Width, region.Height);
        using (var g = Graphics.FromImage(bmp))
        {
            g.CopyFromScreen(region.Location, Point.Empty, region.Size, CopyPixelOperation.SourceCopy);
        }
        return bmp;
    }

    public Bitmap CaptureForm(Form form)
    {
        var bounds = form.Bounds;
        var bmp = new Bitmap(bounds.Width, bounds.Height);
        form.DrawToBitmap(bmp, new Rectangle(0, 0, bounds.Width, bounds.Height));
        return bmp;
    }
}

internal static class CaptureProvider
{
    private static readonly ICaptureProvider _current = new DefaultCaptureProvider();
    public static ICaptureProvider Default => _current;
}
