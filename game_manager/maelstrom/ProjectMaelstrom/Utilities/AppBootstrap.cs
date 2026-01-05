using ProjectMaelstrom.Utilities.Overlay;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Minimal, safe bootstrap to align DevTools and runtime initialization paths.
/// </summary>
public static class AppBootstrap
{
    /// <summary>
    /// Initialize services for normal runtime.
    /// </summary>
    public static void Initialize()
    {
        InitializePolicyAndPlugins();
    }

    /// <summary>
    /// Initialize services for DevTools/self-capture without changing runtime behavior.
    /// </summary>
    public static void InitializeForDevTools()
    {
        InitializePolicyAndPlugins();
    }

    private static void InitializePolicyAndPlugins()
    {
        try
        {
            ExecutionPolicyManager.Reload();
            PluginHost.LoadAllowedPlugins();
            OverlaySnapshotHub.SetExecutorStatus("Unknown");
        }
        catch
        {
            // Best-effort; never crash tools or runtime on bootstrap failure.
        }
    }
}
