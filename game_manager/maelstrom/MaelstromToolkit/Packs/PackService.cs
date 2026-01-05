using System.Text.Json;

namespace MaelstromToolkit.Packs;

internal sealed class PackService
{
    public PackListResult ListPacks(string root)
    {
        var result = new PackListResult();
        if (!Directory.Exists(root)) return result;

        foreach (var dir in Directory.EnumerateDirectories(root).OrderBy(d => d, StringComparer.OrdinalIgnoreCase))
        {
            var manifestPath = Path.Combine(dir, "pack.json");
            if (!File.Exists(manifestPath))
            {
                result.Diagnostics.Add(new PackDiagnostic("PACK010", "Error", Path.GetFileName(dir), string.Empty, "Missing pack.json"));
                continue;
            }

            try
            {
                var manifest = JsonSerializer.Deserialize<PackManifest>(File.ReadAllText(manifestPath), new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true,
                });
                if (manifest == null)
                {
                    result.Diagnostics.Add(new PackDiagnostic("PACK001", "Error", Path.GetFileName(dir), string.Empty, "Invalid pack.json"));
                    continue;
                }
                result.Packs.Add(manifest);
            }
            catch (JsonException ex)
            {
                result.Diagnostics.Add(new PackDiagnostic("PACK001", "Error", Path.GetFileName(dir), string.Empty, $"Invalid JSON: {ex.Message}"));
            }
        }

        result.Packs.Sort((a, b) => string.Compare(a.Id, b.Id, StringComparison.OrdinalIgnoreCase));
        result.Diagnostics = result.Diagnostics
            .OrderBy(d => d.PackId, StringComparer.Ordinal)
            .ThenBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.ScenarioId, StringComparer.Ordinal)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();
        return result;
    }

    public PackValidationResult ValidatePacks(string root)
    {
        var list = ListPacks(root);
        var result = new PackValidationResult();
        result.Diagnostics.AddRange(list.Diagnostics);

        foreach (var pack in list.Packs)
        {
            ValidatePack(root, pack, result.Diagnostics);
        }

        result.Diagnostics = result.Diagnostics
            .OrderBy(d => d.PackId, StringComparer.Ordinal)
            .ThenBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.ScenarioId, StringComparer.Ordinal)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();
        return result;
    }

    private static void ValidatePack(string root, PackManifest pack, List<PackDiagnostic> diagnostics)
    {
        var id = string.IsNullOrWhiteSpace(pack.Id) ? "(missing-id)" : pack.Id;
        if (string.IsNullOrWhiteSpace(pack.Id))
        {
            diagnostics.Add(new PackDiagnostic("PACK020", "Error", id, string.Empty, "Pack id is required."));
        }
        if (string.IsNullOrWhiteSpace(pack.Name))
        {
            diagnostics.Add(new PackDiagnostic("PACK021", "Error", id, string.Empty, "Pack name is required."));
        }
        if (string.IsNullOrWhiteSpace(pack.Version))
        {
            diagnostics.Add(new PackDiagnostic("PACK022", "Error", id, string.Empty, "Pack version is required."));
        }
        if (pack.Scenarios == null || pack.Scenarios.Count == 0)
        {
            diagnostics.Add(new PackDiagnostic("PACK030", "Error", id, string.Empty, "At least one scenario is required."));
            return;
        }

        foreach (var scenario in pack.Scenarios.OrderBy(s => s.Id, StringComparer.OrdinalIgnoreCase))
        {
            if (string.IsNullOrWhiteSpace(scenario.Id))
            {
                diagnostics.Add(new PackDiagnostic("PACK031", "Error", id, string.Empty, "Scenario id is required."));
                continue;
            }
            if (string.IsNullOrWhiteSpace(scenario.Entry))
            {
                diagnostics.Add(new PackDiagnostic("PACK032", "Error", id, scenario.Id, "Scenario entry is required."));
                continue;
            }

            var scenarioPath = Path.Combine(root, pack.Id, scenario.Entry.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(scenarioPath))
            {
                diagnostics.Add(new PackDiagnostic("PACK033", "Error", id, scenario.Id, $"Scenario entry missing: {scenario.Entry}"));
                continue;
            }

            try
            {
                var json = JsonDocument.Parse(File.ReadAllText(scenarioPath));
                if (json.RootElement.TryGetProperty("id", out var idProp))
                {
                    var scenarioId = idProp.GetString() ?? string.Empty;
                    if (!scenarioId.Equals(scenario.Id, StringComparison.OrdinalIgnoreCase))
                    {
                        diagnostics.Add(new PackDiagnostic("PACK034", "Error", id, scenario.Id, $"Scenario id mismatch: manifest={scenario.Id} file={scenarioId}"));
                    }
                }
            }
            catch (JsonException ex)
            {
                diagnostics.Add(new PackDiagnostic("PACK035", "Error", id, scenario.Id, $"Invalid scenario JSON: {ex.Message}"));
            }
        }
    }
}
