using System.Text.Json;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight loader for offline WizWiki data (mobs/zones) if present in Scripts/Library/WizWikiAPI-main.
/// Falls back to an empty dataset when no cache is found; intended for optional seek/avoid routing hints.
/// </summary>
internal sealed class WizWikiDataService
{
    private static readonly Lazy<WizWikiDataService> _lazy = new(() => new WizWikiDataService());
    public static WizWikiDataService Instance => _lazy.Value;

    private readonly List<WikiMob> _mobs = new();
    private readonly List<ResourceSpawn> _resourceSpawns = new();
    private readonly List<WikiNpc> _npcs = new();
    private readonly List<WikiQuest> _quests = new();
    private readonly List<WikiRecipe> _recipes = new();
    private readonly List<WikiZone> _zones = new();
    private readonly List<ResourceSpawn> _observedSpawns = new();
    private readonly object _spawnLock = new();
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };
    public bool HasData { get; private set; }
    public int MobCount => _mobs.Count;
    public int NpcCount => _npcs.Count;
    public int QuestCount => _quests.Count;
    public int RecipeCount => _recipes.Count;
    public int ZoneCount => _zones.Count;
    public int ResourceCount => _resourceSpawns.Count + _observedSpawns.Count;
    private string ObservedSpawnPath => Path.Combine(StorageUtils.GetCacheDirectory(), "spawn_observations.json");

    private WizWikiDataService()
    {
        TryLoad();
    }

    public void Refresh()
    {
        lock (_mobs)
        {
            _mobs.Clear();
            _npcs.Clear();
            _quests.Clear();
            _recipes.Clear();
            _zones.Clear();
            HasData = false;
            TryLoad();
        }
        LoadObservedSpawns();
    }

    private void TryLoad()
    {
        try
        {
            var scriptsRoot = StorageUtils.GetScriptsRoot();
            var candidates = new[]
            {
                Path.Combine(scriptsRoot, "Library", "WizWikiAPI-main", "wizwiki_cache.json"),
                Path.Combine(scriptsRoot, "Library", "WizWikiAPI-main", "wizwiki_data.json")
            };

            var path = candidates.FirstOrDefault(File.Exists);
            if (path == null)
            {
                HasData = false;
                LoadObservedSpawns();
                return;
            }

            var json = File.ReadAllText(path);
            var data = JsonSerializer.Deserialize<List<WikiMob>>(json, _jsonOptions);
            if (data != null && data.Count > 0)
            {
                _mobs.AddRange(data);
                HasData = true;
                DevTelemetry.Log("WizWikiData", $"Loaded {_mobs.Count} mobs from {Path.GetFileName(path)}");
            }

            // Optional crafting recipes
            var recipePath = Path.Combine(Path.GetDirectoryName(path) ?? scriptsRoot, "wizwiki_crafting.json");
            if (File.Exists(recipePath))
            {
                var rJson = File.ReadAllText(recipePath);
                var rData = JsonSerializer.Deserialize<List<WikiRecipe>>(rJson, _jsonOptions);
                if (rData != null && rData.Count > 0)
                {
                    _recipes.AddRange(rData);
                    DevTelemetry.Log("WizWikiData", $"Loaded {_recipes.Count} recipes from {Path.GetFileName(recipePath)}");
                }
            }

            // Optional zones/waypoints for maps/neighbor graph
            var zonePath = Path.Combine(Path.GetDirectoryName(path) ?? scriptsRoot, "wizwiki_zones.json");
            if (File.Exists(zonePath))
            {
                var zJson = File.ReadAllText(zonePath);
                var zData = JsonSerializer.Deserialize<List<WikiZone>>(zJson, _jsonOptions);
                if (zData != null && zData.Count > 0)
                {
                    _zones.AddRange(zData);
                    DevTelemetry.Log("WizWikiData", $"Loaded {_zones.Count} zones from {Path.GetFileName(zonePath)}");
                }
            }

            // Optional resource data alongside mobs
            var resPath = Path.Combine(Path.GetDirectoryName(path) ?? scriptsRoot, "wizwiki_resources.json");
            if (File.Exists(resPath))
            {
                var resJson = File.ReadAllText(resPath);
                var resData = JsonSerializer.Deserialize<List<ResourceSpawn>>(resJson, _jsonOptions);
                if (resData != null && resData.Count > 0)
                {
                    _resourceSpawns.AddRange(resData);
                    DevTelemetry.Log("WizWikiData", $"Loaded {_resourceSpawns.Count} resource spawns from {Path.GetFileName(resPath)}");
                }
            }

            // Optional NPCs
            var npcPath = Path.Combine(Path.GetDirectoryName(path) ?? scriptsRoot, "wizwiki_npcs.json");
            if (File.Exists(npcPath))
            {
                var npcJson = File.ReadAllText(npcPath);
                var npcData = JsonSerializer.Deserialize<List<WikiNpc>>(npcJson, _jsonOptions);
                if (npcData != null && npcData.Count > 0)
                {
                    _npcs.AddRange(npcData);
                    DevTelemetry.Log("WizWikiData", $"Loaded {_npcs.Count} NPCs from {Path.GetFileName(npcPath)}");
                }
            }

            // Optional quests
            var questPath = Path.Combine(Path.GetDirectoryName(path) ?? scriptsRoot, "wizwiki_quests.json");
            if (File.Exists(questPath))
            {
                var qJson = File.ReadAllText(questPath);
                var qData = JsonSerializer.Deserialize<List<WikiQuest>>(qJson, _jsonOptions);
                if (qData != null && qData.Count > 0)
                {
                    _quests.AddRange(qData);
                    DevTelemetry.Log("WizWikiData", $"Loaded {_quests.Count} quests from {Path.GetFileName(questPath)}");
                }
            }

            LoadObservedSpawns();
        }
        catch (Exception ex)
        {
            HasData = false;
            DevTelemetry.Log("WizWikiData", $"Failed to load: {ex.Message}");
            LoadObservedSpawns();
        }
    }

    private void LoadObservedSpawns()
    {
        lock (_spawnLock)
        {
            _observedSpawns.Clear();
            try
            {
                if (!File.Exists(ObservedSpawnPath)) return;
                var json = File.ReadAllText(ObservedSpawnPath);
                var data = JsonSerializer.Deserialize<List<ResourceSpawn>>(json, _jsonOptions);
                if (data != null && data.Count > 0)
                {
                    _observedSpawns.AddRange(data);
                }
            }
            catch (Exception ex)
            {
                DevTelemetry.Log("WizWikiData", $"Failed to load observed spawns: {ex.Message}");
            }
        }
    }

    private void SaveObservedSpawns()
    {
        lock (_spawnLock)
        {
            try
            {
                var json = JsonSerializer.Serialize(_observedSpawns, new JsonSerializerOptions { WriteIndented = true });
                Directory.CreateDirectory(Path.GetDirectoryName(ObservedSpawnPath)!);
                File.WriteAllText(ObservedSpawnPath, json);
            }
            catch (Exception ex)
            {
                DevTelemetry.Log("WizWikiData", $"Failed to save observed spawns: {ex.Message}");
            }
        }
    }

    public IEnumerable<WikiMob> FindMobs(string query, int max = 25)
    {
        if (!HasData || string.IsNullOrWhiteSpace(query)) return Enumerable.Empty<WikiMob>();
        query = query.Trim();
        return _mobs
            .Where(m => m.Name.Contains(query, StringComparison.OrdinalIgnoreCase))
            .Take(max)
            .ToList();
    }

    public IEnumerable<string> GetZones(bool distinctOnly = true)
    {
        if (!HasData) return Enumerable.Empty<string>();
        var zones = _mobs.Select(m => m.Zone ?? string.Empty).Where(z => !string.IsNullOrWhiteSpace(z));
        return distinctOnly ? zones.Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(z => z) : zones;
    }

    public IEnumerable<WikiMob> GetMobsInZone(string zone, int max = 50)
    {
        if (!HasData || string.IsNullOrWhiteSpace(zone)) return Enumerable.Empty<WikiMob>();
        return _mobs
            .Where(m => string.Equals(m.Zone, zone, StringComparison.OrdinalIgnoreCase))
            .Take(max)
            .ToList();
    }

    public IEnumerable<string> GetTopMobs(int max = 5)
    {
        if (!HasData) return Enumerable.Empty<string>();
        return _mobs
            .Select(m => m.Name)
            .Where(n => !string.IsNullOrWhiteSpace(n))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(n => n)
            .Take(max)
            .ToList();
    }

    public void RecordObservedSpawn(string type, string zone, string? area = null, double? x = null, double? y = null, string source = "learned")
    {
        if (string.IsNullOrWhiteSpace(type) || string.IsNullOrWhiteSpace(zone)) return;
        var spawn = new ResourceSpawn
        {
            Type = type.Trim(),
            Zone = zone.Trim(),
            Area = string.IsNullOrWhiteSpace(area) ? null : area.Trim(),
            X = x,
            Y = y,
            CapturedUtc = DateTime.UtcNow,
            Source = source
        };

        lock (_spawnLock)
        {
            _observedSpawns.Add(spawn);
        }

        SaveObservedSpawns();
    }

    public IEnumerable<ResourceSpawn> GetResourceSpawns(string zone, string? type = null)
    {
        if (string.IsNullOrWhiteSpace(zone)) return Enumerable.Empty<ResourceSpawn>();
        var z = zone.Trim();
        IEnumerable<ResourceSpawn> Query(IEnumerable<ResourceSpawn> seq) =>
            seq.Where(s => string.Equals(s.Zone, z, StringComparison.OrdinalIgnoreCase) &&
                           (string.IsNullOrWhiteSpace(type) || string.Equals(s.Type, type, StringComparison.OrdinalIgnoreCase)));

        lock (_spawnLock)
        {
            return Query(_resourceSpawns).Concat(Query(_observedSpawns)).ToList();
        }
    }

    public IEnumerable<WikiNpc> GetNpcs(string? zone = null, string? nameContains = null, int max = 25)
    {
        IEnumerable<WikiNpc> seq = _npcs;
        if (!string.IsNullOrWhiteSpace(zone))
        {
            seq = seq.Where(n => string.Equals(n.Zone, zone, StringComparison.OrdinalIgnoreCase));
        }
        if (!string.IsNullOrWhiteSpace(nameContains))
        {
            seq = seq.Where(n => n.Name.Contains(nameContains, StringComparison.OrdinalIgnoreCase));
        }
        return seq.Take(max).ToList();
    }

    public IEnumerable<WikiQuest> GetQuests(string? zone = null, string? questName = null, int max = 25)
    {
        IEnumerable<WikiQuest> seq = _quests;
        if (!string.IsNullOrWhiteSpace(zone))
        {
            seq = seq.Where(q => string.Equals(q.Zone, zone, StringComparison.OrdinalIgnoreCase));
        }
        if (!string.IsNullOrWhiteSpace(questName))
        {
            seq = seq.Where(q => q.Name.Contains(questName, StringComparison.OrdinalIgnoreCase));
        }
        return seq.Take(max).ToList();
    }

    public IEnumerable<WikiRecipe> GetRecipes(string? item = null, int max = 25)
    {
        IEnumerable<WikiRecipe> seq = _recipes;
        if (!string.IsNullOrWhiteSpace(item))
        {
            seq = seq.Where(r => r.Result.Contains(item, StringComparison.OrdinalIgnoreCase));
        }
        return seq.Take(max).ToList();
    }

    public IEnumerable<WikiZone> GetZonesData(string? world = null)
    {
        if (_zones.Count == 0) return Enumerable.Empty<WikiZone>();
        IEnumerable<WikiZone> seq = _zones;
        if (!string.IsNullOrWhiteSpace(world))
        {
            seq = seq.Where(z => string.Equals(z.World, world, StringComparison.OrdinalIgnoreCase));
        }
        return seq.ToList();
    }

    public WikiZone? FindZone(string zoneName)
    {
        if (string.IsNullOrWhiteSpace(zoneName)) return null;
        return _zones.FirstOrDefault(z => string.Equals(z.Zone, zoneName, StringComparison.OrdinalIgnoreCase));
    }
}

internal sealed class WikiMob
{
    public string Name { get; set; } = string.Empty;
    public string? Zone { get; set; }
    public string? Area { get; set; }
    public string? School { get; set; }
    public string? Type { get; set; }
}

internal sealed class ResourceSpawn
{
    public string Zone { get; set; } = string.Empty;
    public string? Area { get; set; }
    public string Type { get; set; } = string.Empty;
    public double? X { get; set; }
    public double? Y { get; set; }
    public DateTime CapturedUtc { get; set; }
    public string Source { get; set; } = "wizwiki";
}

internal sealed class WikiNpc
{
    public string Name { get; set; } = string.Empty;
    public string Zone { get; set; } = string.Empty;
    public string? Area { get; set; }
    public string? Role { get; set; }
}

internal sealed class WikiQuest
{
    public string Name { get; set; } = string.Empty;
    public string Zone { get; set; } = string.Empty;
    public string? Giver { get; set; }
    public string? Objective { get; set; }
}

internal sealed class WikiRecipe
{
    public string Result { get; set; } = string.Empty;
    public string? Station { get; set; }
    public List<RecipeIngredient> Ingredients { get; set; } = new();
}

internal sealed class RecipeIngredient
{
    public string Name { get; set; } = string.Empty;
    public int Quantity { get; set; }
}

internal sealed class WikiZone
{
    public string World { get; set; } = string.Empty;
    public string Zone { get; set; } = string.Empty;
    public string? Image { get; set; }
    public List<string> Neighbors { get; set; } = new();
    public string? Notes { get; set; }
}
