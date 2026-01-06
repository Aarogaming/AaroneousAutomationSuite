using System.Reflection;

namespace ProjectMaelstrom.Utilities;

internal sealed class PluginContext
{
    public ExecutionPolicySnapshot Policy { get; }
    public PluginContext(ExecutionPolicySnapshot policy)
    {
        Policy = policy;
    }
}

/// <summary>
/// Loads allowed plugins and invokes IMaelstromPlugin.Initialize. Safe/no-op if none.
/// </summary>
internal static class PluginHost
{
    public static void LoadAllowedPlugins()
    {
        var policy = ExecutionPolicyManager.Current;
        var allowed = PluginLoader.Current.Where(p => p.Status == PluginStatus.Allowed && !string.IsNullOrWhiteSpace(p.AssemblyPath));
        ReplayAnalyzerRegistry.Clear();
        Overlay.OverlayWidgetRegistry.Clear();
        MinigameCatalogRegistry.Clear();

        foreach (var plugin in allowed)
        {
            try
            {
                var asm = Assembly.LoadFrom(plugin.AssemblyPath);
                var type = asm.GetTypes().FirstOrDefault(t =>
                    typeof(IMaelstromPlugin).IsAssignableFrom(t) && !t.IsAbstract && !t.IsInterface);
                if (type == null) continue;

                var instance = (IMaelstromPlugin)Activator.CreateInstance(type)!;
                var ctx = new PluginContext(policy);
                instance.Initialize(ctx);
                Logger.Log($"[PluginHost] Loaded plugin {plugin.PluginId} ({plugin.Name})");
            }
            catch (Exception ex)
            {
                Logger.LogError($"[PluginHost] Failed to load plugin {plugin.PluginId}", ex);
            }
        }

        try
        {
            MinigameCatalogRegistry.Reload();
        }
        catch (Exception ex)
        {
            Logger.LogError("[PluginHost] Failed to refresh MinigameCatalog", ex);
        }
    }
}
