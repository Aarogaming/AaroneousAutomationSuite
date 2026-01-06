using System.Text.Json;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Simple macro playback: loads InputCommand JSON and dispatches through executor with basic guards.
/// </summary>
internal static class MacroPlayer
{
    private static readonly JsonSerializerOptions _jsonOpts = new() { PropertyNameCaseInsensitive = true };

    public static bool Play(string macroPath, InputBridge? bridge, Func<GameStateSnapshot?> snapshotProvider, string? expectedResolution = null)
    {
        if (!File.Exists(macroPath))
        {
            MessageBox.Show("Macro file not found.", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }

        // Focus guard
        var sync = GameSyncService.Evaluate(expectedResolution);
        if (sync.Health == GameSyncHealth.FocusLost || sync.Health == GameSyncHealth.WindowMissing)
        {
            MessageBox.Show("Wizard101 is not focused/visible. Focus the game before running the macro.", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }

        // Health/energy guard
        var snap = snapshotProvider();
        if (snap != null)
        {
            var hp = snap.Health?.Current ?? int.MaxValue;
            if (hp < 50)
            {
                MessageBox.Show("Health too low to run macro (below 50).", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
        }

        try
        {
            var json = File.ReadAllText(macroPath);
            var commands = JsonSerializer.Deserialize<List<InputCommand>>(json, _jsonOpts);
            if (commands == null || commands.Count == 0)
            {
                MessageBox.Show("Macro is empty or invalid.", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }

            var policy = ExecutionPolicyManager.Current;
            var executor = ExecutorFactory.FromPolicy(policy);
            if (bridge == null && policy.AllowLiveAutomation)
            {
                MessageBox.Show("Live automation allowed but input bridge not ready.", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }

            var ctx = new ExecutionContext { Source = "Macro", TaskName = Path.GetFileNameWithoutExtension(macroPath), Bridge = bridge };
            executor.Execute(commands, ctx);
            DevTelemetry.Log("Macros", $"Queued macro {Path.GetFileName(macroPath)} with {commands.Count} commands (mode={policy.Mode})");
            return true;
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to play macro: {ex.Message}", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return false;
        }
    }
}
