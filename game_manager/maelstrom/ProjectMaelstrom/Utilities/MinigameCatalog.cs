using System.IO;
using System.Reflection;
using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

public enum MinigameCategory
{
    Pet,
    Potion,
    Gardening,
    Other
}

public enum MinigameStatus
{
    Planned,
    InProgress,
    Implemented,
    Deprecated
}

public sealed class MinigameCatalogEntry
{
    public string Id { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public MinigameCategory Category { get; init; } = MinigameCategory.Other;
    public MinigameStatus Status { get; init; } = MinigameStatus.Planned;
    public string Description { get; init; } = string.Empty;
    public string[] Tags { get; init; } = Array.Empty<string>();
    public string Provenance { get; init; } = string.Empty;
    public string Requirements { get; init; } = string.Empty;
    public string Notes { get; init; } = string.Empty;
    public string SourcePluginId { get; init; } = string.Empty;
}

public interface IMinigameCatalogProvider
{
    IEnumerable<MinigameCatalogEntry> GetEntries();
}

/// <summary>
/// Aggregates declarative minigame catalog entries from plugins.
/// Supports both provider assemblies and manifest-only JSON catalogs.
/// </summary>
internal static class MinigameCatalogRegistry
{
    private const string CatalogFileName = "minigames.catalog.json";
    private static readonly object _lock = new();
    private static IReadOnlyList<MinigameCatalogEntry> _entries = Array.Empty<MinigameCatalogEntry>();

    public static IReadOnlyList<MinigameCatalogEntry> Current
    {
        get
        {
            lock (_lock)
            {
                return _entries;
            }
        }
    }

    public static IEnumerable<MinigameCatalogEntry> GetAll() => Current;

    public static IReadOnlyDictionary<MinigameCategory, List<MinigameCatalogEntry>> GroupByCategory()
    {
        return Current
            .GroupBy(e => e.Category)
            .ToDictionary(g => g.Key, g => g.ToList());
    }

    public static IReadOnlyDictionary<MinigameStatus, List<MinigameCatalogEntry>> GroupByStatus()
    {
        return Current
            .GroupBy(e => e.Status)
            .ToDictionary(g => g.Key, g => g.ToList());
    }

    public static void Clear()
    {
        lock (_lock)
        {
            _entries = Array.Empty<MinigameCatalogEntry>();
        }
    }

    public static void Reload()
    {
        var aggregated = new List<MinigameCatalogEntry>();
        var allowed = PluginLoader.Current.Where(p =>
            p.Status == PluginStatus.Allowed &&
            p.Capabilities.Contains(PluginCapability.MinigameCatalog));

        foreach (var plugin in allowed)
        {
            aggregated.AddRange(LoadEntriesForPlugin(plugin));
        }

        lock (_lock)
        {
            _entries = aggregated;
        }
    }

    private static IEnumerable<MinigameCatalogEntry> LoadEntriesForPlugin(PluginInfo plugin)
    {
        var results = new List<MinigameCatalogEntry>();
        results.AddRange(LoadFromAssembly(plugin));
        results.AddRange(LoadFromJson(plugin));

        return results;
    }

    private static IEnumerable<MinigameCatalogEntry> LoadFromAssembly(PluginInfo plugin)
    {
        var results = new List<MinigameCatalogEntry>();
        try
        {
            if (string.IsNullOrWhiteSpace(plugin.AssemblyPath) || !File.Exists(plugin.AssemblyPath))
            {
                return results;
            }

            var asm = Assembly.LoadFrom(plugin.AssemblyPath);
            var providers = asm.GetTypes()
                .Where(t => typeof(IMinigameCatalogProvider).IsAssignableFrom(t) && !t.IsAbstract && !t.IsInterface)
                .ToList();

            foreach (var type in providers)
            {
                try
                {
                    if (Activator.CreateInstance(type) is IMinigameCatalogProvider provider)
                    {
                        var entries = provider.GetEntries() ?? Enumerable.Empty<MinigameCatalogEntry>();
                        results.AddRange(entries.Select(e => NormalizeEntry(e, plugin.PluginId)));
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogError($"[MinigameCatalog] Provider load failed for {plugin.PluginId}", ex);
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"[MinigameCatalog] Failed to load assembly entries for {plugin.PluginId}", ex);
        }

        return results;
    }

    private static IEnumerable<MinigameCatalogEntry> LoadFromJson(PluginInfo plugin)
    {
        var results = new List<MinigameCatalogEntry>();
        try
        {
            var manifestDir = !string.IsNullOrWhiteSpace(plugin.ManifestPath)
                ? Path.GetDirectoryName(plugin.ManifestPath)
                : null;

            if (string.IsNullOrWhiteSpace(manifestDir))
            {
                return results;
            }

            var jsonPath = Path.Combine(manifestDir!, CatalogFileName);
            if (!File.Exists(jsonPath))
            {
                return results;
            }

            var json = File.ReadAllText(jsonPath);
            var entries = JsonSerializer.Deserialize<List<MinigameCatalogEntry>>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (entries != null)
            {
                results.AddRange(entries.Select(e => NormalizeEntry(e, plugin.PluginId)));
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"[MinigameCatalog] Failed to load JSON catalog for {plugin.PluginId}", ex);
        }

        return results;
    }

    private static MinigameCatalogEntry NormalizeEntry(MinigameCatalogEntry entry, string pluginId)
    {
        if (entry == null) return new MinigameCatalogEntry { SourcePluginId = pluginId };

        return new MinigameCatalogEntry
        {
            Id = entry.Id ?? string.Empty,
            Name = string.IsNullOrWhiteSpace(entry.Name) ? (entry.Id ?? string.Empty) : entry.Name,
            Category = entry.Category,
            Status = entry.Status,
            Description = entry.Description ?? string.Empty,
            Tags = entry.Tags ?? Array.Empty<string>(),
            Provenance = entry.Provenance ?? string.Empty,
            Requirements = entry.Requirements ?? string.Empty,
            Notes = entry.Notes ?? string.Empty,
            SourcePluginId = pluginId
        };
    }
}
