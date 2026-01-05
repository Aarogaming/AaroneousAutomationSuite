using Emgu.CV;
using Emgu.CV.CvEnum;
using Emgu.CV.Structure;
using System.Drawing;

namespace ProjectMaelstrom.Modules.ImageRecognition;

public record TemplateMatchResult(bool Found, double Score, Rectangle Location, Point Center);

internal static class TemplateMatcher
{
    /// <summary>
    /// Finds the best match for a template within a source image using normalized cross-correlation.
    /// Returns a TemplateMatchResult with score and bounding box. Threshold is inclusive.
    /// </summary>
    public static TemplateMatchResult FindBestMatch(string sourcePath, string templatePath, double threshold = 0.8, Rectangle? region = null)
    {
        if (!File.Exists(sourcePath) || !File.Exists(templatePath))
        {
            return new TemplateMatchResult(false, 0, Rectangle.Empty, Point.Empty);
        }

        using var src = new Mat(sourcePath, ImreadModes.Color);
        using var tpl = new Mat(templatePath, ImreadModes.Color);

        if (region.HasValue)
        {
            var r = region.Value;
            r.Intersect(new Rectangle(0, 0, src.Width, src.Height));
            if (r.Width > 0 && r.Height > 0)
            {
                using var roi = new Mat(src, r);
                return MatchInternal(roi, tpl, threshold, r.Location);
            }
        }

        return MatchInternal(src, tpl, threshold, Point.Empty);
    }

    private static TemplateMatchResult MatchInternal(Mat source, Mat template, double threshold, Point offset)
    {
        using var result = new Mat();
        CvInvoke.MatchTemplate(source, template, result, TemplateMatchingType.CcoeffNormed);
        double minVal = 0, maxVal = 0;
        Point minLoc = Point.Empty, maxLoc = Point.Empty;
        CvInvoke.MinMaxLoc(result, ref minVal, ref maxVal, ref minLoc, ref maxLoc);

        if (maxVal >= threshold)
        {
            var topLeft = new Point(maxLoc.X + offset.X, maxLoc.Y + offset.Y);
            var rect = new Rectangle(topLeft, template.Size);
            var center = new Point(rect.X + rect.Width / 2, rect.Y + rect.Height / 2);
            return new TemplateMatchResult(true, maxVal, rect, center);
        }

        return new TemplateMatchResult(false, maxVal, Rectangle.Empty, Point.Empty);
    }
}
