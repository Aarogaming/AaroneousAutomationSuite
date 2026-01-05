using System.Drawing.Imaging;
using System.Text.Json;
using ProjectMaelstrom.Utilities.Capture;

namespace ProjectMaelstrom.Utilities;

internal static class UiSnapshotService
{
    private static readonly JsonSerializerOptions _jsonOpts = new() { WriteIndented = true };

    public static void TryCapture(Form form, string reason = "manual")
    {
        if (!DevMode.IsEnabled || !Properties.Settings.Default.ENABLE_DEV_UI_SNAPSHOTS)
            return;

        try
        {
            var dir = Path.Combine(AppContext.BaseDirectory, "logs", "dev");
            Directory.CreateDirectory(dir);
            var stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var baseName = Path.Combine(dir, $"ui_{reason}_{stamp}");

            // Capture bitmap
            using (var bmp = CaptureProvider.Default.CaptureForm(form))
            {
                bmp.Save(baseName + ".png", ImageFormat.Png);
            }

            // Collect control metadata
            var controls = new List<ControlInfo>();
            CollectControls(form, controls, form);

            // Analyze issues
            var issues = Analyze(controls);

            var snapshot = new UiSnapshot
            {
                Reason = reason,
                TimestampUtc = DateTime.UtcNow,
                Form = form.Name,
                Controls = controls,
                Issues = issues
            };

            File.WriteAllText(baseName + ".json", JsonSerializer.Serialize(snapshot, _jsonOpts));

            DevTelemetry.Log("UI", $"Snapshot captured ({reason}) with {issues.Count} issue(s)");
        }
        catch (Exception ex)
        {
            DevTelemetry.Log("UI", $"Snapshot failed: {ex.Message}");
        }
    }

    private static void CollectControls(Control root, List<ControlInfo> list, Control form)
    {
        foreach (Control c in root.Controls)
        {
            if (!c.Visible) continue;
            var bounds = form.RectangleToClient(c.RectangleToScreen(c.ClientRectangle));
            var info = new ControlInfo
            {
                Name = c.Name,
                Type = c.GetType().Name,
                Text = c.Text,
                Bounds = new Rect(bounds.X, bounds.Y, bounds.Width, bounds.Height),
                AutoSize = c is ButtonBase bb && bb.AutoSize,
                AutoEllipsis = (c as Label)?.AutoEllipsis ?? (c as ButtonBase)?.AutoEllipsis ?? false,
                FontName = c.Font?.Name,
                FontSize = c.Font?.Size ?? 0
            };
            list.Add(info);
            if (c.HasChildren)
            {
                CollectControls(c, list, form);
            }
        }
    }

    private static List<string> Analyze(List<ControlInfo> controls)
    {
        var issues = new List<string>();
        foreach (var c in controls)
        {
            if (!string.IsNullOrEmpty(c.Text) && c.Bounds.Width > 0 && c.Bounds.Height > 0)
            {
                // rough text fit heuristic: 8px padding
                int pad = 8;
                int available = Math.Max(0, c.Bounds.Width - pad);
                if (c.Text.Length * 7 > available) // coarse width estimate
                {
                    issues.Add($"Text may be clipped: {c.Type} '{c.Text}' ({c.Name}) width={c.Bounds.Width}");
                }
                int verticalSpace = c.Bounds.Height;
                if (verticalSpace > 0)
                {
                    // assume 60% of font size as height estimate
                    var estHeight = (int)Math.Max(10, c.FontSize * 1.2);
                    var delta = Math.Abs((verticalSpace - estHeight) / 2);
                    if (delta > 3)
                    {
                        issues.Add($"Text may be off-center vertically: {c.Type} '{c.Text}' ({c.Name})");
                    }
                }
            }
        }

        // overlap detection
        for (int i = 0; i < controls.Count; i++)
        {
            for (int j = i + 1; j < controls.Count; j++)
            {
                var a = controls[i].Bounds;
                var b = controls[j].Bounds;
                if (a.Intersects(b))
                {
                    issues.Add($"Overlap: {controls[i].Name} and {controls[j].Name}");
                }
            }
        }

        return issues;
    }

    private sealed record UiSnapshot
    {
        public string Reason { get; init; } = "";
        public DateTime TimestampUtc { get; init; }
        public string Form { get; init; } = "";
        public List<ControlInfo> Controls { get; init; } = new();
        public List<string> Issues { get; init; } = new();
    }

    private sealed record ControlInfo
    {
        public string Name { get; init; } = "";
        public string Type { get; init; } = "";
        public string Text { get; init; } = "";
        public Rect Bounds { get; init; }
        public bool AutoSize { get; init; }
        public bool AutoEllipsis { get; init; }
        public string? FontName { get; init; }
        public float FontSize { get; init; }
    }

    private readonly record struct Rect(int X, int Y, int Width, int Height)
    {
        public bool Intersects(Rect other)
        {
            return !(other.X > X + Width ||
                     other.X + other.Width < X ||
                     other.Y > Y + Height ||
                     other.Y + other.Height < Y);
        }
    }
}
