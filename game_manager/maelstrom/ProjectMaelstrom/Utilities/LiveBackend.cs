using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

internal interface ILiveIntegrationBackend
{
    string Id { get; }
    string Name { get; }
    ExecutionResult Dispatch(IEnumerable<InputCommand> commands, ExecutionContext context);
}

internal sealed class NullLiveBackend : ILiveIntegrationBackend
{
    public string Id => "null-backend";
    public string Name => "No authorized backend installed";

    public ExecutionResult Dispatch(IEnumerable<InputCommand> commands, ExecutionContext context)
    {
        var list = commands?.Where(c => c != null).ToList() ?? new List<InputCommand>();
        return new ExecutionResult
        {
            Status = ExecutionStatus.LiveEnabledNoBackend,
            CommandsCount = list.Count,
            Message = "Live allowed but no backend installed"
        };
    }
}

internal static class LiveBackendProvider
{
    private static readonly object _lock = new();
    private static ILiveIntegrationBackend _backend = new NullLiveBackend();
    private static bool _loaded;

    public static ILiveIntegrationBackend Current
    {
        get
        {
            EnsureLoaded();
            return _backend;
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
            _backend = LoadBackendSafe();
            _loaded = true;
        }
    }

    private static ILiveIntegrationBackend LoadBackendSafe()
    {
        try
        {
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            var pluginDir = Path.Combine(baseDir, "plugins", "live-backends");
            if (!Directory.Exists(pluginDir))
            {
                return new NullLiveBackend();
            }

            var dlls = Directory.GetFiles(pluginDir, "*.dll");
            foreach (var dll in dlls)
            {
                try
                {
                    var asm = Assembly.LoadFrom(dll);
                    var backendType = asm.GetTypes()
                        .FirstOrDefault(t => typeof(ILiveIntegrationBackend).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract);
                    if (backendType != null)
                    {
                        if (Activator.CreateInstance(backendType) is ILiveIntegrationBackend backend)
                        {
                            Logger.Log($"[LiveBackend] Loaded backend {backend.Name} from {dll}");
                            return backend;
                        }
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogError($"[LiveBackend] Failed to load backend from {dll}", ex);
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("[LiveBackend] Loader failed, using null backend", ex);
        }
        return new NullLiveBackend();
    }
}
