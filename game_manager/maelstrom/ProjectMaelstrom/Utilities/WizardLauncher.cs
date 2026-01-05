using System.Diagnostics;
using System.IO;
using Microsoft.Win32;

namespace ProjectMaelstrom.Utilities;

internal static class WizardLauncher
{
    public enum LauncherState
    {
        NotRunning,
        LauncherRunning,
        GameRunning
    }

    private static readonly string[] CandidatePaths =
    {
        // Prefer the main game executable; fall back to launcher only if needed.
        @"C:\ProgramData\KingsIsle Entertainment\Wizard101\Wizard101.exe",
        @"C:\ProgramData\KingsIsle Entertainment\Wizard101\PlayWizard101.exe",
        @"C:\Program Files (x86)\KingsIsle Entertainment\Wizard101\Wizard101.exe",
        @"C:\Program Files (x86)\KingsIsle Entertainment\Wizard101\PlayWizard101.exe",
        @"C:\Program Files\KingsIsle Entertainment\Wizard101\PlayWizard101.exe",
        @"C:\Program Files\KingsIsle Entertainment\Wizard101\Wizard101.exe",
        @"C:\KingsIsle Entertainment\Wizard101\PlayWizard101.exe",
        @"C:\KingsIsle Entertainment\Wizard101\Wizard101.exe"
    };

    private static string CachePath => Path.Combine(StorageUtils.GetCacheDirectory(), "wizard_path.txt");

    public static string? FindClient()
    {
        try
        {
            // Prefer cached path if still valid
            var cached = ReadCachedPath();
            if (!string.IsNullOrWhiteSpace(cached) && File.Exists(cached))
            {
                return cached;
            }

            var regPath = FindFromRegistry();
            if (!string.IsNullOrEmpty(regPath))
            {
                WriteCachedPath(regPath);
                return regPath;
            }

            foreach (var path in CandidatePaths)
            {
                if (File.Exists(path))
                {
                    WriteCachedPath(path);
                    return path;
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("[WizardLauncher] Failed to search for client", ex);
        }

        return null;
    }

    private static string? FindFromRegistry()
    {
        string? found = TryRegistryKey(@"SOFTWARE\KingsIsle Entertainment\Wizard101");
        if (!string.IsNullOrEmpty(found))
        {
            return found;
        }

        found = TryRegistryKey(@"SOFTWARE\WOW6432Node\KingsIsle Entertainment\Wizard101");
        return found;
    }

    private static string? TryRegistryKey(string keyPath)
    {
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(keyPath);
            if (key == null)
            {
                return null;
            }

            var installDir = key.GetValue("InstallLocation") as string ?? key.GetValue("InstallDir") as string;
            if (string.IsNullOrEmpty(installDir))
            {
                return null;
            }

            string[] candidates =
            {
                Path.Combine(installDir, "Wizard101.exe"),
                Path.Combine(installDir, "PlayWizard101.exe")
            };

            foreach (var candidate in candidates)
            {
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("[WizardLauncher] Registry search failed", ex);
        }

        return null;
    }

    public static bool Launch(out string message)
    {
        message = string.Empty;
        string? client = FindClient();
        if (string.IsNullOrEmpty(client))
        {
            var dialog = new OpenFileDialog
            {
                Title = "Locate Wizard101.exe",
                Filter = "Wizard101|Wizard101.exe|Exe Files|*.exe",
                Multiselect = false
            };
            if (dialog.ShowDialog() == DialogResult.OK && File.Exists(dialog.FileName))
            {
                client = dialog.FileName;
                WriteCachedPath(client);
            }
            else
            {
                message = "Wizard101 client not found. Please install or set a custom path.";
                return false;
            }
        }

        try
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = client,
                UseShellExecute = true
            });
            message = $"Launched Wizard101 from {client}";
            return true;
        }
        catch (Exception ex)
        {
            message = $"Failed to launch Wizard101: {ex.Message}";
            Logger.LogError("[WizardLauncher] Launch failed", ex);
            return false;
        }
    }

    private static string? ReadCachedPath()
    {
        try
        {
            if (File.Exists(CachePath))
            {
                var path = File.ReadAllText(CachePath).Trim();
                return string.IsNullOrWhiteSpace(path) ? null : path;
            }
        }
        catch
        {
            // ignore cache read errors
        }
        return null;
    }

    private static void WriteCachedPath(string path)
    {
        try
        {
            File.WriteAllText(CachePath, path);
        }
        catch
        {
            // ignore cache write errors
        }
    }

    public static LauncherState DetectState(out string description)
    {
        try
        {
            var game = Process.GetProcessesByName("Wizard101").FirstOrDefault();
            if (game != null)
            {
                var title = SafeTitle(game);
                description = string.IsNullOrWhiteSpace(title) ? "Game running" : $"Game running ({title})";
                return LauncherState.GameRunning;
            }

            var launcher = Process.GetProcessesByName("PlayWizard101").FirstOrDefault();
            if (launcher != null)
            {
                var title = SafeTitle(launcher);
                description = DescribeLauncherTitle(title);
                return LauncherState.LauncherRunning;
            }
        }
        catch
        {
            // ignore detection failures
        }

        description = "Not running";
        return LauncherState.NotRunning;
    }

    private static string SafeTitle(Process p)
    {
        try
        {
            return p.MainWindowTitle ?? string.Empty;
        }
        catch
        {
            return string.Empty;
        }
    }

    private static string DescribeLauncherTitle(string title)
    {
        if (string.IsNullOrWhiteSpace(title)) return "Launcher/patcher running";
        var lower = title.ToLowerInvariant();
        if (lower.Contains("login") || lower.Contains("log in"))
        {
            return "Launcher ready (Login)";
        }
        if (lower.Contains("play"))
        {
            return $"Launcher ready (Play)";
        }
        if (lower.Contains("patch") || lower.Contains("update"))
        {
            return $"Patching/updating";
        }
        if (lower.Contains("wizard101"))
        {
            return "Launcher running";
        }
        return $"Launcher/patcher ({title})";
    }
}
