using System.Globalization;
using System.IO;

namespace ProjectMaelstrom.Utilities;

internal enum ExecutionMode
{
    SimulationOnly,
    LiveAllowed
}

internal enum ExecutionProfile
{
    AcademicSimulation,
    ExperimentalSimulation
}

internal sealed class ExecutionPolicySnapshot
{
    public bool AllowLiveAutomation { get; init; }
    public ExecutionMode Mode { get; init; }
    public ExecutionProfile Profile { get; init; }
}

/// <summary>
/// Loads execution policy from a simple key=value file. Defaults are safe (live disabled).
/// </summary>
internal static class ExecutionPolicyManager
{
    private const string PolicyFileName = "execution_policy.conf";
    private const string AllowLiveKey = "ALLOW_LIVE_AUTOMATION";
    private const string ProfileKey = "EXECUTION_PROFILE";
    private static string _policyPath = string.Empty;
    private static DateTime _loadedUtc = DateTime.UtcNow;
    private static ExecutionPolicySnapshot _currentSnap = LoadPolicy();

    public static ExecutionPolicySnapshot Current => _currentSnap;
    public static string PolicyPath => _policyPath;
    public static DateTime LoadedUtc => _loadedUtc;

    public static void Reload()
    {
        _currentSnap = LoadPolicy();
        LiveBackendProvider.Reload();
        PluginLoader.Reload();
        PluginHost.LoadAllowedPlugins();
    }

    public static void SetProfile(ExecutionProfile profile)
    {
        var path = Path.Combine(StorageUtils.GetCacheDirectory(), PolicyFileName);
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllLines(path, new[]
            {
                $"{AllowLiveKey}=false",
                $"{ProfileKey}={profile}"
            });
        }
        catch (Exception ex)
        {
            Logger.LogError("[ExecutionPolicy] Failed to write policy file", ex);
        }
        _currentSnap = LoadPolicy();
        LiveBackendProvider.Reload();
        PluginLoader.Reload();
        PluginHost.LoadAllowedPlugins();
    }

    private static ExecutionPolicySnapshot LoadPolicy()
    {
        var path = Path.Combine(StorageUtils.GetCacheDirectory(), PolicyFileName);
        _policyPath = path;
        _loadedUtc = DateTime.UtcNow;
        bool allowLive = false; // default safe
        ExecutionProfile profile = ExecutionProfile.AcademicSimulation;

        if (File.Exists(path))
        {
            try
            {
                foreach (var line in File.ReadAllLines(path))
                {
                    if (string.IsNullOrWhiteSpace(line) || line.TrimStart().StartsWith("#"))
                        continue;

                    var parts = line.Split('=', StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length != 2) continue;

                    var key = parts[0].Trim();
                    var value = parts[1].Trim();

                    if (key.Equals(AllowLiveKey, StringComparison.OrdinalIgnoreCase) &&
                        bool.TryParse(value, out var parsed))
                    {
                        allowLive = parsed;
                    }
                    if (key.Equals(ProfileKey, StringComparison.OrdinalIgnoreCase))
                    {
                        if (Enum.TryParse<ExecutionProfile>(value, true, out var parsedProfile))
                        {
                            profile = parsedProfile;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("[ExecutionPolicy] Failed to read policy file, using safe defaults", ex);
            }
        }
        else
        {
            // Write default file for visibility
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllText(path,
                    $"{AllowLiveKey}=false{Environment.NewLine}" +
                    $"{ProfileKey}={profile}{Environment.NewLine}" +
                    "# Set ALLOW_LIVE_AUTOMATION to true to enable live dispatch (not recommended)");
            }
            catch
            {
                // ignore write errors; still return defaults
            }
        }

        return new ExecutionPolicySnapshot
        {
            AllowLiveAutomation = allowLive,
            Mode = allowLive ? ExecutionMode.LiveAllowed : ExecutionMode.SimulationOnly,
            Profile = profile
        };
    }
}
