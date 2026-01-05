using System.Drawing;
using System.Text.Json;
using System.Text.RegularExpressions;
using ProjectMaelstrom.Models;
using ProjectMaelstrom.Modules.ImageRecognition;

namespace ProjectMaelstrom.Utilities;

internal static class GameStateService
{
    private const string RoiFileName = "rois.json";
    private static readonly JsonSerializerOptions JsonOpts = new() { PropertyNameCaseInsensitive = true };

    public static async Task<GameStateSnapshot> CaptureSnapshotAsync(string? expectedResolution = null)
    {
        var warnings = new List<string>();
        expectedResolution = string.IsNullOrWhiteSpace(expectedResolution)
            ? StateManager.Instance.SelectedResolution ?? "1280x720"
            : expectedResolution;

        var syncState = GameSyncService.Evaluate(expectedResolution);
        if (!syncState.HasWindow)
        {
            return new GameStateSnapshot
            {
                CapturedUtc = DateTime.UtcNow,
                WindowPresent = false,
                HasFocus = false,
                Resolution = expectedResolution,
                Warnings = new[] { syncState.Message }
            };
        }

        IntPtr handle = ImageFinder.GetWindowHandle();
        var rect = ImageFinder.GetWindowRect(handle);

        string screenshotPath = ImageFinder.CaptureScreen(rect);
        try
        {
            using var bmp = new Bitmap(screenshotPath);

            var regions = LoadRegions(expectedResolution, bmp.Width, bmp.Height, warnings);

            var health = await ExtractPairAsync(bmp, regions, "health", warnings);
            var mana = await ExtractPairAsync(bmp, regions, "mana", warnings);
            var energy = await ExtractPairAsync(bmp, regions, "energy", warnings);
            var gold = await ExtractSingleAsync(bmp, regions, "gold", warnings);
            var potions = await ExtractSingleAsync(bmp, regions, "potions", warnings);

            return new GameStateSnapshot
            {
                CapturedUtc = DateTime.UtcNow,
                WindowPresent = true,
                HasFocus = syncState.Health != GameSyncHealth.FocusLost && syncState.Health != GameSyncHealth.WindowMissing,
                Resolution = $"{bmp.Width}x{bmp.Height}",
                Health = health,
                Mana = mana,
                Energy = energy,
                Gold = gold,
                Potions = potions,
                Warnings = warnings
            };
        }
        finally
        {
            try { File.Delete(screenshotPath); } catch { /* ignore cleanup */ }
        }
    }

    private static Dictionary<string, Rectangle> LoadRegions(string resolution, int width, int height, List<string> warnings)
    {
        var regions = new Dictionary<string, Rectangle>(StringComparer.OrdinalIgnoreCase);

        var roiConfigPath = Path.Combine(StorageUtils.GetAppPath(), RoiFileName);
        if (!File.Exists(roiConfigPath))
        {
            warnings.Add($"ROI config not found for {resolution}. Using full-image OCR as fallback.");
            regions["health"] = new Rectangle(0, 0, width, height);
            regions["mana"] = new Rectangle(0, 0, width, height);
            regions["energy"] = new Rectangle(0, 0, width, height);
            regions["gold"] = new Rectangle(0, 0, width, height);
            regions["potions"] = new Rectangle(0, 0, width, height);
            return regions;
        }

        try
        {
            var json = File.ReadAllText(roiConfigPath);
            var parsed = JsonSerializer.Deserialize<List<OcrRegionConfig>>(json, JsonOpts);
            if (parsed == null || parsed.Count == 0)
            {
                warnings.Add("ROI config empty; using full-image OCR.");
                regions["health"] = new Rectangle(0, 0, width, height);
                regions["mana"] = new Rectangle(0, 0, width, height);
                regions["energy"] = new Rectangle(0, 0, width, height);
                regions["gold"] = new Rectangle(0, 0, width, height);
                regions["potions"] = new Rectangle(0, 0, width, height);
                return regions;
            }

            foreach (var item in parsed)
            {
                if (string.IsNullOrWhiteSpace(item.Name)) continue;
                var rect = NormalizeToPixels(item, width, height);
                regions[item.Name.Trim().ToLowerInvariant()] = rect;
            }
        }
        catch (Exception ex)
        {
            warnings.Add($"Failed to load ROI config: {ex.Message}");
            regions["health"] = new Rectangle(0, 0, width, height);
            regions["mana"] = new Rectangle(0, 0, width, height);
            regions["energy"] = new Rectangle(0, 0, width, height);
            regions["gold"] = new Rectangle(0, 0, width, height);
            regions["potions"] = new Rectangle(0, 0, width, height);
        }

        return regions;
    }

    private static Rectangle NormalizeToPixels(OcrRegionConfig cfg, int width, int height)
    {
        int x = ClampToRange((int)(cfg.X * width), 0, width - 1);
        int y = ClampToRange((int)(cfg.Y * height), 0, height - 1);
        int w = ClampToRange((int)(cfg.Width * width), 1, width - x);
        int h = ClampToRange((int)(cfg.Height * height), 1, height - y);
        return new Rectangle(x, y, w, h);
    }

    private static async Task<GameStateSnapshot.MetricPair?> ExtractPairAsync(
        Bitmap bitmap,
        Dictionary<string, Rectangle> regions,
        string key,
        List<string> warnings)
    {
        if (!regions.TryGetValue(key, out var rect))
        {
            warnings.Add($"Region missing for {key}");
            return null;
        }

        string text = await OcrRegionAsync(bitmap, rect);
        if (string.IsNullOrWhiteSpace(text))
        {
            warnings.Add($"{key} OCR returned empty text");
            return null;
        }

        var pair = ParsePair(text);
        if (pair == null)
        {
            warnings.Add($"{key} OCR could not parse values: '{text.Trim()}'");
            return null;
        }

        return new GameStateSnapshot.MetricPair
        {
            Current = pair.Value.current,
            Max = pair.Value.max,
            Confidence = 0.6,
            Source = key
        };
    }

    private static async Task<GameStateSnapshot.MetricSingle?> ExtractSingleAsync(
        Bitmap bitmap,
        Dictionary<string, Rectangle> regions,
        string key,
        List<string> warnings)
    {
        if (!regions.TryGetValue(key, out var rect))
        {
            warnings.Add($"Region missing for {key}");
            return null;
        }

        string text = await OcrRegionAsync(bitmap, rect);
        if (string.IsNullOrWhiteSpace(text))
        {
            warnings.Add($"{key} OCR returned empty text");
            return null;
        }

        var single = ParseSingle(text);
        if (single == null)
        {
            warnings.Add($"{key} OCR could not parse value: '{text.Trim()}'");
            return null;
        }

        return new GameStateSnapshot.MetricSingle
        {
            Value = single.Value,
            Confidence = 0.6,
            Source = key
        };
    }

    private static async Task<string> OcrRegionAsync(Bitmap source, Rectangle rect)
    {
        using var cropped = source.Clone(rect, source.PixelFormat);
        string tempPath = Path.Combine(Path.GetTempPath(), $"maelstrom_roi_{Guid.NewGuid():N}.png");
        try
        {
            cropped.Save(tempPath);
            return await ImageHelpers.ExtractTextFromImage(tempPath);
        }
        finally
        {
            try { File.Delete(tempPath); } catch { /* ignore */ }
        }
    }

    private static (int current, int max)? ParsePair(string text)
    {
        // Accept formats like "123/456" or "123 / 456"
        var match = Regex.Match(text, @"(\d+)\s*[/]\s*(\d+)");
        if (match.Success &&
            int.TryParse(match.Groups[1].Value, out int current) &&
            int.TryParse(match.Groups[2].Value, out int max))
        {
            return (current, max);
        }

        return null;
    }

    private static int? ParseSingle(string text)
    {
        // First integer token
        var match = Regex.Match(text, @"(\d+)");
        if (match.Success && int.TryParse(match.Groups[1].Value, out int value))
        {
            return value;
        }

        return null;
    }

    private static int ClampToRange(int value, int min, int max)
    {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }
}
