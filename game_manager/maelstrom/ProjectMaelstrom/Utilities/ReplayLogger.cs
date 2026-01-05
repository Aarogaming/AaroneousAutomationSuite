using System.Text.Json;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

internal static class ReplayLogger
{
    private static readonly object _lock = new();

    public static string ReplayRoot
    {
        get
        {
            var policyPath = ExecutionPolicyManager.PolicyPath;
            string? policyDir = string.IsNullOrWhiteSpace(policyPath)
                ? null
                : Path.GetDirectoryName(policyPath);

            var root = string.IsNullOrWhiteSpace(policyDir)
                ? StorageUtils.GetCacheDirectory()
                : policyDir;
            return Path.Combine(root, "replays");
        }
    }

    public static void Append(ExecutionContext context, ExecutionResult result, IEnumerable<InputCommand> commands)
    {
        try
        {
            var snap = ExecutionPolicyManager.Current;
            if (snap == null) return;
            var profile = snap?.Profile.ToString() ?? "Unknown";
            var allowLive = snap?.AllowLiveAutomation ?? false;
            var mode = snap?.Mode.ToString() ?? "Unknown";
            var dir = ReplayRoot;
            Directory.CreateDirectory(dir);
            var file = Path.Combine(dir, $"replay_{DateTime.UtcNow:yyyyMMdd}.jsonl");

            var cmdList = new List<object>();
            if (commands != null)
            {
                foreach (var cmd in commands)
                {
                    if (cmd is not InputCommand c) continue;
                    cmdList.Add(new
                    {
                        type = c?.Type?.ToString() ?? "Unknown",
                        X = c?.X ?? 0,
                        Y = c?.Y ?? 0,
                        delayMs = c?.DelayMs ?? 0
                    });
                    if (cmdList.Count >= 20) break;
                }
            }

            var record = new
            {
                timestampUtc = DateTime.UtcNow.ToString("o"),
                profile,
                allowLive,
                mode,
                source = context?.Source ?? "Unknown",
                task = context?.TaskName ?? "Unknown",
                status = result?.Status.ToString() ?? "Unknown",
                message = result?.Message ?? "",
                commandsCount = result?.CommandsCount ?? cmdList.Count,
                commands = cmdList
            };

            var json = JsonSerializer.Serialize(record);
            lock (_lock)
            {
                File.AppendAllText(file, json + Environment.NewLine);
            }
        }
        catch
        {
            // best-effort; never crash
        }
    }

    public static IEnumerable<string> ListReplays()
    {
        try
        {
            var dir = ReplayRoot;
            if (!Directory.Exists(dir)) return Enumerable.Empty<string>();
            return Directory.GetFiles(dir, "replay_*.jsonl").OrderByDescending(File.GetLastWriteTimeUtc);
        }
        catch
        {
            return Enumerable.Empty<string>();
        }
    }

    public static IEnumerable<string> ReadTail(string path, int maxLines = 50)
    {
        try
        {
            var lines = File.ReadLines(path);
            return lines.Reverse().Take(maxLines).Reverse().ToList();
        }
        catch
        {
            return Array.Empty<string>();
        }
    }
}
