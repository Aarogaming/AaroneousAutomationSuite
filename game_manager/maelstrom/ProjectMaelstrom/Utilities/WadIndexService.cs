using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight WAD indexer: lists local .wad files and writes a manifest for downstream matching.
/// Does not parse assets yet; safe for quick lookups.
/// </summary>
internal static class WadIndexService
{
    private static readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = true };
    private static readonly string[] PythonCandidates = new[] { "python", "py" };

    /// <summary>
    /// Build an index of .wad files under the known Wizard101 install root.
    /// </summary>
    public static string BuildIndex()
    {
        var root = GetDefaultWizardInstall();
        var wadDir = root == null ? null : Path.Combine(root, "Wads");
        var list = new List<WadEntry>();

        if (wadDir != null && Directory.Exists(wadDir))
        {
            foreach (var path in Directory.GetFiles(wadDir, "*.wad", SearchOption.TopDirectoryOnly))
            {
                try
                {
                    var info = new FileInfo(path);
                    list.Add(new WadEntry
                    {
                        Name = info.Name,
                        FullPath = info.FullName,
                        SizeBytes = info.Length,
                        ModifiedUtc = info.LastWriteTimeUtc
                    });
                }
                catch (Exception ex)
                {
                    DevTelemetry.Log("WAD", $"Failed to index {path}: {ex.Message}");
                }
            }
        }
        else
        {
            DevTelemetry.Log("WAD", "Wads folder not found; set Wizard101 directory in settings.");
        }

        var manifest = new WadManifest
        {
            BasePath = wadDir ?? "unknown",
            Entries = list.OrderBy(e => e.Name, StringComparer.OrdinalIgnoreCase).ToList()
        };

        var outDir = Path.Combine(AppContext.BaseDirectory, "logs", "wads");
        Directory.CreateDirectory(outDir);
        var outPath = Path.Combine(outDir, "wad_index.json");
        File.WriteAllText(outPath, JsonSerializer.Serialize(manifest, _jsonOptions));
        DevTelemetry.Log("WAD", $"Indexed {manifest.Entries.Count} wads to {outPath}");
        return outPath;
    }

    /// <summary>
    /// Best-effort asset listing using bundled wizwad/wizard101-wad-reader Python scripts if available.
    /// Writes per-wad asset manifests to logs/wads/assets_{wad}.json.
    /// </summary>
    public static void BuildAssetManifests()
    {
        var wadIndexPath = Path.Combine(AppContext.BaseDirectory, "logs", "wads", "wad_index.json");
        if (!File.Exists(wadIndexPath))
        {
            BuildIndex();
        }

        var manifest = LoadIndex(wadIndexPath);
        if (manifest == null || manifest.Entries.Count == 0) return;

        string? python = FindPython();
        if (python == null)
        {
            DevTelemetry.Log("WAD", "Python not found; skipping asset manifests.");
            return;
        }

        var wadScript = FindWadScript();
        if (wadScript == null)
        {
            DevTelemetry.Log("WAD", "wizwad/wad.py not found; skipping asset manifests.");
            return;
        }

        var outDir = Path.Combine(AppContext.BaseDirectory, "logs", "wads");
        Directory.CreateDirectory(outDir);

        foreach (var entry in manifest.Entries)
        {
            try
            {
                var outPath = Path.Combine(outDir, $"assets_{Path.GetFileNameWithoutExtension(entry.Name)}.json");
                if (File.Exists(outPath)) continue; // avoid rework

                var args = $"\"{wadScript}\" \"{entry.FullPath}\"";
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = python,
                    Arguments = args,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using var proc = System.Diagnostics.Process.Start(psi);
                if (proc == null) continue;
                string stdout = proc.StandardOutput.ReadToEnd();
                string stderr = proc.StandardError.ReadToEnd();
                if (!proc.WaitForExit(15000))
                {
                    try { proc.Kill(); } catch { }
                    DevTelemetry.Log("WAD", $"Asset listing timed out for {entry.Name}");
                    continue;
                }

                if (proc.ExitCode != 0)
                {
                    DevTelemetry.Log("WAD", $"Asset listing failed for {entry.Name}: {stderr.Trim()}");
                    continue;
                }

                // Heuristic: keep first 1000 lines and only include useful asset extensions.
                var lines = stdout.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries)
                    .Take(1000)
                    .Select(l => l.Trim())
                    .Where(l => l.Length > 1)
                    .Where(HasUsefulExtension)
                    .ToList();

                var assets = lines.Select(l =>
                {
                    var name = l;
                    var comma = l.IndexOf(',');
                    if (comma > 0) name = l[..comma].Trim();
                    return new WadAssetEntry
                    {
                        Name = Path.GetFileName(name),
                        Path = name,
                        Size = 0
                    };
                }).ToList();

                var assetIndex = new WadAssetIndex
                {
                    WadName = entry.Name,
                    Entries = assets
                };

                File.WriteAllText(outPath, JsonSerializer.Serialize(assetIndex, _jsonOptions));
                DevTelemetry.Log("WAD", $"Asset manifest saved for {entry.Name} ({assets.Count} entries)");
            }
            catch (Exception ex)
            {
                DevTelemetry.Log("WAD", $"Asset manifest error for {entry.Name}: {ex.Message}");
            }
        }
    }

    private static WadManifest? LoadIndex(string path)
    {
        try
        {
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<WadManifest>(json, _jsonOptions);
        }
        catch
        {
            return null;
        }
    }

    private static string? FindPython()
    {
        foreach (var candidate in PythonCandidates)
        {
            try
            {
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = candidate,
                    Arguments = "--version",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using var proc = System.Diagnostics.Process.Start(psi);
                if (proc == null) continue;
                if (!proc.WaitForExit(5000)) continue;
                if (proc.ExitCode == 0) return candidate;
            }
            catch { /* ignore */ }
        }
        return null;
    }

    private static string? FindWadScript()
    {
        var roots = new[]
        {
            Path.Combine(StorageUtils.GetScriptLibraryPath(), "wizwad-main", "wizwad-main", "wizwad", "wad.py"),
            Path.Combine(StorageUtils.GetScriptLibraryPath(), "wizard101-wad-reader", "wad.py"),
            Path.Combine(StorageUtils.GetScriptLibraryPath(), "wiz-packet-map-main", "wiz-packet-map-main", "wiz_wad.py")
        };
        return roots.FirstOrDefault(File.Exists);
    }

    private static string? GetDefaultWizardInstall()
    {
        var candidates = new[]
        {
            @"C:\ProgramData\KingsIsle Entertainment\Wizard101",
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "KingsIsle Entertainment", "Wizard101"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "KingsIsle Entertainment", "Wizard101")
        };
        return candidates.FirstOrDefault(Directory.Exists);
    }

    private static bool HasUsefulExtension(string path)
    {
        var lower = path.ToLowerInvariant();
        return lower.EndsWith(".png") ||
               lower.EndsWith(".jpg") ||
               lower.EndsWith(".jpeg") ||
               lower.EndsWith(".dds") ||
               lower.EndsWith(".json") ||
               lower.EndsWith(".txt") ||
               lower.EndsWith(".xml") ||
               lower.EndsWith(".csv") ||
               lower.EndsWith(".bmp") ||
               lower.EndsWith(".tga") ||
               lower.EndsWith(".ttf") ||
               lower.EndsWith(".otf");
    }

    private sealed class WadEntry
    {
        public string Name { get; set; } = "";
        public string FullPath { get; set; } = "";
        public long SizeBytes { get; set; }
        public DateTime ModifiedUtc { get; set; }
    }

    private sealed class WadManifest
    {
        public string BasePath { get; set; } = "";
        public List<WadEntry> Entries { get; set; } = new();
    }
}
