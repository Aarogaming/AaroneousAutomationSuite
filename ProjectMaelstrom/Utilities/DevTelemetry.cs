using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Central dev-only telemetry sink that aggregates interesting events without capturing sensitive data.
/// </summary>
internal static class DevTelemetry
{
    private static readonly object _lock = new();
    private static readonly string _logDir = Path.Combine(AppContext.BaseDirectory, "logs", "dev");
    private static readonly string _logPath = Path.Combine(_logDir, "dev_telemetry.log");
    private static readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = false };

    private static bool Enabled => DevMode.IsEnabled && Properties.Settings.Default.ENABLE_DEV_TELEMETRY;

    public static void Log(string area, string message)
    {
        if (!Enabled) return;
        try
        {
            Directory.CreateDirectory(_logDir);
            var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} [{area}] {message}";
            lock (_lock)
            {
                File.AppendAllText(_logPath, line + Environment.NewLine);
            }
            Logger.Log($"[Dev][{area}] {message}");
        }
        catch
        {
            // swallow telemetry failures
        }
    }

    public static void WriteSnapshot(string name, object payload)
    {
        if (!Enabled) return;
        try
        {
            Directory.CreateDirectory(_logDir);
            var json = JsonSerializer.Serialize(payload, _jsonOptions);
            var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} [{name}] {json}";
            lock (_lock)
            {
                File.AppendAllText(_logPath, line + Environment.NewLine);
            }
        }
        catch
        {
            // swallow telemetry failures
        }
    }
}
