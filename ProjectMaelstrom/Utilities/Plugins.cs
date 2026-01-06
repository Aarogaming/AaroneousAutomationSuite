using System.Text.Json;
using System.Text.Json.Serialization;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

internal enum PluginCapability
{
    OverlayWidgets,
    MinigameCatalog,
    MinigameDefinitions,
    ReplayAnalyzers,
    LiveIntegration,
    Other
}

internal enum PluginProfileRequirement
{
    Public,
    Experimental
}

internal sealed class PluginManifest
{
    [JsonPropertyName("pluginId")]
    public string? PluginId { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("version")]
    public string? Version { get; set; }

    [JsonPropertyName("targetAppVersion")]
    public string? TargetAppVersion { get; set; }

    [JsonPropertyName("requiredProfile")]
    public string? RequiredProfile { get; set; }

    [JsonPropertyName("declaredCapabilities")]
    public List<string>? DeclaredCapabilities { get; set; }
}

public interface IMaelstromPlugin
{
    string Id { get; }
    string Name { get; }
    Version Version { get; }
    void Initialize(object context);
}

internal enum PluginStatus
{
    Allowed,
    Blocked,
    Incompatible,
    Failed
}

internal sealed class PluginInfo
{
    public string PluginId { get; init; } = "unknown";
    public string Name { get; init; } = "Unnamed Plugin";
    public string Version { get; init; } = "0.0.0";
    public string TargetAppVersion { get; init; } = "unknown";
    public PluginProfileRequirement RequiredProfile { get; init; } = PluginProfileRequirement.Public;
    public IReadOnlyList<PluginCapability> Capabilities { get; init; } = Array.Empty<PluginCapability>();
    public string AssemblyPath { get; init; } = string.Empty;
    public string ManifestPath { get; init; } = string.Empty;
    public PluginStatus Status { get; init; }
    public string Reason { get; init; } = string.Empty;
}

internal static class PluginGate
{
    public static (PluginStatus status, string reason) Evaluate(PluginInfo info, ExecutionPolicySnapshot policy)
    {
        if (info == null) return (PluginStatus.Failed, "Plugin info missing");
        if (policy == null) return (PluginStatus.Blocked, "Policy unavailable");

        if (info.Capabilities.Contains(PluginCapability.LiveIntegration) && !policy.AllowLiveAutomation)
        {
            return (PluginStatus.Blocked, "Live disabled by policy");
        }

        if (info.RequiredProfile == PluginProfileRequirement.Experimental &&
            policy.Profile == ExecutionProfile.AcademicSimulation)
        {
            return (PluginStatus.Blocked, "Requires Experimental profile");
        }

        if (info.Status == PluginStatus.Failed || info.Status == PluginStatus.Incompatible)
        {
            return (info.Status, info.Reason);
        }

        return (PluginStatus.Allowed, "Allowed");
    }
}

internal static class PluginLoader
{
    private static readonly object _lock = new();
    private static IReadOnlyList<PluginInfo> _plugins = Array.Empty<PluginInfo>();
    private static bool _loaded;
    public static string PluginRoot
    {
        get
        {
            var policyDir = Path.GetDirectoryName(ExecutionPolicyManager.PolicyPath);
            var root = string.IsNullOrWhiteSpace(policyDir)
                ? StorageUtils.GetCacheDirectory()
                : policyDir!;
            return Path.Combine(root, "plugins");
        }
    }

    public static IReadOnlyList<PluginInfo> Current
    {
        get
        {
            EnsureLoaded();
            return _plugins;
        }
    }

    public static void Reload()
    {
        lock (_lock)
        {
            _loaded = false;
        }
    }

    private static void EnsureLoaded()
    {
        if (_loaded) return;
        lock (_lock)
        {
            if (_loaded) return;
            _plugins = LoadPluginsSafe();
            _loaded = true;
        }
    }

    private static IReadOnlyList<PluginInfo> LoadPluginsSafe()
    {
        var list = new List<PluginInfo>();
        try
        {
            var pluginDir = PluginRoot;
            if (!Directory.Exists(pluginDir))
            {
                return list;
            }

            var manifests = Directory.GetFiles(pluginDir, "*.manifest.json", SearchOption.AllDirectories);
            foreach (var manifestPath in manifests)
            {
                var info = LoadSingle(manifestPath);
                list.Add(info);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("[Plugins] Failed to enumerate plugins", ex);
        }

        return list;
    }

    private static PluginInfo LoadSingle(string manifestPath)
    {
        var currentPolicy = ExecutionPolicyManager.Current;
        string pluginId = Path.GetFileNameWithoutExtension(manifestPath);
        string pluginName = "Unnamed Plugin";
        string version = "0.0.0";
        string target = "unknown";
        PluginProfileRequirement profileReq = PluginProfileRequirement.Public;
        var capabilities = new List<PluginCapability>();
        string assemblyPath = string.Empty;
        PluginStatus status = PluginStatus.Allowed;
        string reason = "Allowed";

        try
        {
            var json = File.ReadAllText(manifestPath);
            var manifest = JsonSerializer.Deserialize<PluginManifest>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (!string.IsNullOrWhiteSpace(manifest?.PluginId))
            {
                pluginId = manifest.PluginId!;
            }
            if (!string.IsNullOrWhiteSpace(manifest?.Name))
            {
                pluginName = manifest.Name!;
            }
            if (!string.IsNullOrWhiteSpace(manifest?.Version))
            {
                version = manifest!.Version!;
            }
            if (!string.IsNullOrWhiteSpace(manifest?.TargetAppVersion))
            {
                target = manifest!.TargetAppVersion!;
            }
            if (!string.IsNullOrWhiteSpace(manifest?.RequiredProfile))
            {
                if (Enum.TryParse<PluginProfileRequirement>(manifest.RequiredProfile, true, out var req))
                {
                    profileReq = req;
                }
            }

            if (manifest?.DeclaredCapabilities != null)
            {
                foreach (var cap in manifest.DeclaredCapabilities)
                {
                    if (Enum.TryParse<PluginCapability>(cap, true, out var parsed))
                    {
                        capabilities.Add(parsed);
                    }
                    else
                    {
                        capabilities.Add(PluginCapability.Other);
                    }
                }
            }

            var manifestDir = Path.GetDirectoryName(manifestPath)!;
            var dll = Directory.GetFiles(manifestDir, "*.dll", SearchOption.TopDirectoryOnly).FirstOrDefault();
            assemblyPath = dll ?? string.Empty;

            if (status == PluginStatus.Allowed && !string.IsNullOrWhiteSpace(target) && !target.Equals("any", StringComparison.OrdinalIgnoreCase))
            {
                var appVersion = Application.ProductVersion;
                if (!appVersion.StartsWith(target, StringComparison.OrdinalIgnoreCase))
                {
                    status = PluginStatus.Incompatible;
                    reason = $"Target {target} incompatible";
                }
            }

            var provisional = new PluginInfo
            {
                PluginId = pluginId,
                Name = pluginName,
                Version = version,
                TargetAppVersion = target,
                RequiredProfile = profileReq,
                Capabilities = capabilities,
                AssemblyPath = assemblyPath,
                Status = status,
                Reason = reason
            };

            // Gate against policy
            var gate = PluginGate.Evaluate(provisional, currentPolicy);
            status = gate.status;
            reason = gate.reason;

            // If still allowed but no dll, keep allowed but note manifest-only
            if (status == PluginStatus.Allowed && string.IsNullOrWhiteSpace(assemblyPath))
            {
                reason = "Manifest only (no assembly)";
            }
        }
        catch (Exception ex)
        {
            status = PluginStatus.Failed;
            reason = $"Manifest error ({ex.Message})";
        }

        return new PluginInfo
        {
            PluginId = pluginId,
            Name = pluginName,
            Version = version,
            TargetAppVersion = target,
            RequiredProfile = profileReq,
            Capabilities = capabilities,
            AssemblyPath = assemblyPath,
            ManifestPath = manifestPath,
            Status = status,
            Reason = reason
        };
    }
}

internal static class PluginSamples
{
    public const string SampleOverlayId = "SampleOverlay";
    public const string SampleLiveIntegrationId = "SampleLiveIntegration";
    public const string SampleReplayAnalyzerId = "SampleReplayAnalyzer";
    public const string SampleOverlayWidgetsId = "SampleOverlayWidgets";
    public const string SampleMinigameCatalogId = "SampleMinigameCatalog";
    public static string SamplesRoot => Path.Combine(PluginLoader.PluginRoot, "_samples");
}
