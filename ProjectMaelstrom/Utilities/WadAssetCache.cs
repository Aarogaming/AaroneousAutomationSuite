using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Simple in-memory cache of extracted WAD asset names for OCR cross-check.
/// </summary>
internal static class WadAssetCache
{
    private static readonly object _lock = new();
    private static bool _loaded;
    private static HashSet<string> _names = new(StringComparer.OrdinalIgnoreCase);

    public static void EnsureLoaded()
    {
        if (_loaded) return;
        lock (_lock)
        {
            if (_loaded) return;
            LoadFromLogs();
            _loaded = true;
        }
    }

    private static void LoadFromLogs()
    {
        try
        {
            var dir = Path.Combine(AppContext.BaseDirectory, "logs", "wads");
            if (!Directory.Exists(dir)) return;

            foreach (var file in Directory.GetFiles(dir, "assets_*.json"))
            {
                try
                {
                    var json = File.ReadAllText(file);
                    var index = JsonSerializer.Deserialize<WadAssetIndex>(json);
                    if (index?.Entries == null) continue;
                    foreach (var e in index.Entries)
                    {
                        if (!string.IsNullOrWhiteSpace(e.Name))
                        {
                            _names.Add(e.Name);
                        }
                    }
                }
                catch
                {
                    // skip bad files
                }
            }
            DevTelemetry.Log("WAD", $"Loaded {_names.Count} asset names for OCR cross-check.");
        }
        catch (Exception ex)
        {
            DevTelemetry.Log("WAD", $"Asset cache load failed: {ex.Message}");
        }
    }

    public static IEnumerable<string> MatchLine(string line)
    {
        EnsureLoaded();
        if (string.IsNullOrWhiteSpace(line) || _names.Count == 0)
            return Array.Empty<string>();

        var tokens = line.Split(new[] { ' ', ',', ':', ';', '.', '\t' }, StringSplitOptions.RemoveEmptyEntries)
            .Where(t => t.Length > 3)
            .Select(t => t.Trim().TrimEnd('.', ',', ';', ':'))
            .Where(t => t.Length > 3)
            .ToArray();

        var hits = new List<string>();
        foreach (var token in tokens)
        {
            if (_names.Contains(token))
            {
                hits.Add(token);
            }
        }
        return hits.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
    }
}
