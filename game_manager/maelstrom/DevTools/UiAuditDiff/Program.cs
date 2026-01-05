using System.Collections.Immutable;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.Text;

namespace UiAuditDiff;

internal sealed record DiffOptions(
    string BaselineDir,
    string CurrentDir,
    double ThresholdPct,
    string? ReportPath);

internal sealed record DiffEntry(string FileName, double DiffPct, double MeanDelta, string Note);

internal static class Program
{
    private const double DefaultThresholdPct = 0.5;

    private static int Main(string[] args)
    {
        try
        {
            var options = ParseArgs(args);
            return Run(options);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[ERROR] {ex.Message}");
            return 1;
        }
    }

    private static int Run(DiffOptions options)
    {
        var baselineDir = Path.GetFullPath(options.BaselineDir);
        var currentDir = Path.GetFullPath(options.CurrentDir);

        if (!Directory.Exists(baselineDir))
        {
            Console.Error.WriteLine($"[FAIL] Baseline folder not found: {baselineDir}");
            Console.Error.WriteLine("       Run ui_set_baseline.ps1 to create it before checking regressions.");
            return 1;
        }

        if (!Directory.Exists(currentDir))
        {
            Console.Error.WriteLine($"[FAIL] Current folder not found: {currentDir}");
            return 1;
        }

        var baselineFiles = GetPngSet(baselineDir);
        var currentFiles = GetPngSet(currentDir);

        var missing = baselineFiles.Except(currentFiles, StringComparer.OrdinalIgnoreCase).OrderBy(f => f, StringComparer.OrdinalIgnoreCase).ToList();
        var added = currentFiles.Except(baselineFiles, StringComparer.OrdinalIgnoreCase).OrderBy(f => f, StringComparer.OrdinalIgnoreCase).ToList();
        var common = baselineFiles.Intersect(currentFiles, StringComparer.OrdinalIgnoreCase).OrderBy(f => f, StringComparer.OrdinalIgnoreCase).ToList();

        var changed = new List<DiffEntry>();
        double worstDiff = 0;

        foreach (var file in common)
        {
            var basePath = Path.Combine(baselineDir, file);
            var curPath = Path.Combine(currentDir, file);
            var (diffPct, meanDelta, note) = CompareImages(basePath, curPath);
            if (diffPct > 0 || !string.IsNullOrEmpty(note))
            {
                changed.Add(new DiffEntry(file, diffPct, meanDelta, note));
            }
            if (diffPct > worstDiff) worstDiff = diffPct;
        }

        changed.Sort((a, b) => b.DiffPct.CompareTo(a.DiffPct));

        var summary = $"Summary: Total={common.Count}, Changed={changed.Count}, Missing={missing.Count}, New={added.Count}, WorstDiffPct={worstDiff:0.###}";

        var reportBuilder = new StringBuilder();
        reportBuilder.AppendLine(summary);

        if (changed.Count > 0)
        {
            reportBuilder.AppendLine("Changed (by diffPct desc):");
            foreach (var ch in changed)
            {
                var noteSuffix = string.IsNullOrEmpty(ch.Note) ? string.Empty : $" | {ch.Note}";
                reportBuilder.AppendLine($"  {ch.FileName} | {ch.DiffPct:0.###}% | meanΔ {ch.MeanDelta:0.###}{noteSuffix}");
            }
        }

        if (missing.Count > 0)
        {
            reportBuilder.AppendLine("Missing in current (present in baseline):");
            foreach (var m in missing) reportBuilder.AppendLine($"  {m}");
        }

        if (added.Count > 0)
        {
            reportBuilder.AppendLine("New in current (not in baseline):");
            foreach (var n in added) reportBuilder.AppendLine($"  {n}");
        }

        var reportText = reportBuilder.ToString().TrimEnd();
        Console.WriteLine(reportText);

        if (!string.IsNullOrWhiteSpace(options.ReportPath))
        {
            var reportPath = Path.GetFullPath(options.ReportPath);
            Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
            File.WriteAllText(reportPath, reportText);
        }

        var failMissing = missing.Count > 0;
        var failDiff = changed.Any(c => c.DiffPct > options.ThresholdPct);

        if (failMissing || failDiff)
        {
            Console.Error.WriteLine($"[FAIL] Threshold={options.ThresholdPct:0.###} | Missing={missing.Count} | ChangedAboveThreshold={(failDiff ? "yes" : "no")}");
            return 1;
        }

        Console.WriteLine($"[PASS] All differences <= {options.ThresholdPct:0.###} and no missing baseline files.");
        return 0;
    }

    private static DiffOptions ParseArgs(string[] args)
    {
        string? baseline = null;
        string? current = null;
        double threshold = DefaultThresholdPct;
        string? report = null;

        for (int i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            switch (arg)
            {
                case "--baseline":
                    baseline = RequireNext(args, ref i, "--baseline");
                    break;
                case "--current":
                    current = RequireNext(args, ref i, "--current");
                    break;
                case "--threshold":
                    var raw = RequireNext(args, ref i, "--threshold");
                    if (!double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out threshold))
                    {
                        throw new ArgumentException($"Invalid threshold value: {raw}");
                    }
                    break;
                case "--report":
                    report = RequireNext(args, ref i, "--report");
                    break;
                default:
                    throw new ArgumentException($"Unknown argument: {arg}");
            }
        }

        if (string.IsNullOrWhiteSpace(baseline) || string.IsNullOrWhiteSpace(current))
        {
            throw new ArgumentException("Usage: --baseline <path> --current <path> [--threshold <float>] [--report <path>]");
        }

        if (threshold < 0) threshold = 0;

        return new DiffOptions(baseline!, current!, threshold, report);
    }

    private static string RequireNext(string[] args, ref int index, string name)
    {
        if (index + 1 >= args.Length) throw new ArgumentException($"Missing value for {name}");
        index++;
        return args[index];
    }

    private static ImmutableHashSet<string> GetPngSet(string directory)
    {
        return Directory.Exists(directory)
            ? Directory.GetFiles(directory, "*.png", SearchOption.TopDirectoryOnly)
                .Select(Path.GetFileName)
                .Where(f => f != null)
                .Select(f => f!)
                .ToImmutableHashSet(StringComparer.OrdinalIgnoreCase)
            : ImmutableHashSet<string>.Empty;
    }

    private static (double diffPct, double meanDelta, string note) CompareImages(string baselinePath, string currentPath)
    {
        using var baseBmpRaw = new Bitmap(baselinePath);
        using var curBmpRaw = new Bitmap(currentPath);

        if (baseBmpRaw.Width != curBmpRaw.Width || baseBmpRaw.Height != curBmpRaw.Height)
        {
            return (100.0, 255.0, "dimension mismatch");
        }

        using var baseBmp = EnsureArgb32(baseBmpRaw);
        using var curBmp = EnsureArgb32(curBmpRaw);

        var rect = new Rectangle(0, 0, baseBmp.Width, baseBmp.Height);
        var totalPixels = rect.Width * rect.Height;

        var diffPixels = 0;
        long sumDelta = 0;

        var dataA = baseBmp.LockBits(rect, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        var dataB = curBmp.LockBits(rect, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);

        try
        {
            unsafe
            {
                byte* ptrA = (byte*)dataA.Scan0;
                byte* ptrB = (byte*)dataB.Scan0;
                int strideA = dataA.Stride;
                int strideB = dataB.Stride;
                for (int y = 0; y < rect.Height; y++)
                {
                    var rowA = ptrA + y * strideA;
                    var rowB = ptrB + y * strideB;
                    for (int x = 0; x < rect.Width; x++)
                    {
                        var idx = x * 4;
                        byte bA = rowA[idx];
                        byte gA = rowA[idx + 1];
                        byte rA = rowA[idx + 2];
                        byte aA = rowA[idx + 3];

                        byte bB = rowB[idx];
                        byte gB = rowB[idx + 1];
                        byte rB = rowB[idx + 2];
                        byte aB = rowB[idx + 3];

                        bool differs = bA != bB || gA != gB || rA != rB || aA != aB;
                        if (differs) diffPixels++;

                        sumDelta += Math.Abs(bA - bB);
                        sumDelta += Math.Abs(gA - gB);
                        sumDelta += Math.Abs(rA - rB);
                        sumDelta += Math.Abs(aA - aB);
                    }
                }
            }
        }
        finally
        {
            baseBmp.UnlockBits(dataA);
            curBmp.UnlockBits(dataB);
        }

        double diffPct = totalPixels == 0 ? 0 : (double)diffPixels / totalPixels * 100.0;
        double meanDelta = totalPixels == 0 ? 0 : (double)sumDelta / (totalPixels * 4);
        return (diffPct, meanDelta, string.Empty);
    }

    private static Bitmap EnsureArgb32(Bitmap source)
    {
        if (source.PixelFormat == PixelFormat.Format32bppArgb)
        {
            return (Bitmap)source.Clone();
        }

        var clone = new Bitmap(source.Width, source.Height, PixelFormat.Format32bppArgb);
        using var g = Graphics.FromImage(clone);
        g.DrawImage(source, new Rectangle(0, 0, source.Width, source.Height));
        return clone;
    }
}
