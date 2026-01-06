using System.Drawing.Imaging;
using System.Text.Json;
using ProjectMaelstrom.Models;
using ProjectMaelstrom.Utilities.Capture;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Captures screenshots of the running app windows and writes metadata to a design samples folder.
/// </summary>
internal sealed class DesignManager
{
    private readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = true };

    public string CaptureAppWindows(Form mainForm)
    {
        var destRoot = Path.Combine(StorageUtils.GetDesignSamplesPath(), DateTime.UtcNow.ToString("yyyyMMdd_HHmmss"));
        Directory.CreateDirectory(destRoot);

        var meta = new List<DesignSampleMeta>();
        foreach (Form form in Application.OpenForms)
        {
            try
            {
                var fileName = $"{Sanitize(form.Name)}_{Sanitize(form.Text)}.png";
                var path = Path.Combine(destRoot, fileName);
                CaptureForm(form, path);
                meta.Add(new DesignSampleMeta
                {
                    FormName = form.Name,
                    Title = form.Text,
                    Bounds = new RectMeta { X = form.Bounds.X, Y = form.Bounds.Y, Width = form.Bounds.Width, Height = form.Bounds.Height },
                    Theme = Properties.Settings.Default.THEME_MODE,
                    Screenshot = fileName
                });
            }
            catch (Exception ex)
            {
                Logger.LogError("[DesignManager] Failed to capture form", ex);
            }
        }

        try
        {
            var metaPath = Path.Combine(destRoot, "metadata.json");
            File.WriteAllText(metaPath, JsonSerializer.Serialize(meta, _jsonOptions));
        }
        catch (Exception ex)
        {
            Logger.LogError("[DesignManager] Failed to write metadata", ex);
        }

        return destRoot;
    }

    private static void CaptureForm(Form form, string path)
    {
        var bounds = form.Bounds;
        using var bitmap = Capture.CaptureProvider.Default.CaptureRegion(bounds);
        bitmap.Save(path, ImageFormat.Png);
    }

    private static string Sanitize(string input)
    {
        if (string.IsNullOrWhiteSpace(input)) return "window";
        foreach (var c in Path.GetInvalidFileNameChars())
        {
            input = input.Replace(c, '_');
        }
        return input.Trim('_');
    }

    private sealed class DesignSampleMeta
    {
        public string FormName { get; init; } = string.Empty;
        public string Title { get; init; } = string.Empty;
        public RectMeta Bounds { get; init; } = new();
        public string Theme { get; init; } = string.Empty;
        public string Screenshot { get; init; } = string.Empty;
    }

    private sealed class RectMeta
    {
        public int X { get; init; }
        public int Y { get; init; }
        public int Width { get; init; }
        public int Height { get; init; }
    }
}
