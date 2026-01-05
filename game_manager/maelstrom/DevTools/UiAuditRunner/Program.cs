using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO.Compression;
using System.Text.Json;
using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using ProjectMaelstrom.Utilities.Capture;

namespace UiAuditRunner;

internal sealed class AuditConfig
{
    public string? ProjectExePath { get; set; }
    public int[]? DpiScales { get; set; }
    public ScreenDef[]? Screens { get; set; }
    public string OutputFolder { get; set; } = "ui_audit_pack";
    public string ZipOutput { get; set; } = "ui_audit_pack.zip";
    public int WaitForMainMs { get; set; } = 10000;
    public bool OpenScreens { get; set; } = true;
    public string? MainWindowTitleHint { get; set; }
    public int TimeoutSeconds { get; set; } = 20;
    public string? DpiLabel { get; set; }
    public bool CloseOnFinish { get; set; } = true;
    public NavigationHints? Navigation { get; set; }
}

internal sealed class ScreenDef
{
    public string Name { get; set; } = string.Empty;
    public string WindowTitleContains { get; set; } = string.Empty;
}

internal sealed class NavigationHints
{
    public string[]? OpenSettingsButtonNameHints { get; set; }
    public string[]? OpenManageScriptsButtonNameHints { get; set; }
    public string[]? OpenGitHubInstallButtonNameHints { get; set; }
    public string[]? DeveloperOptionsTabNameHints { get; set; }
    public string[]? PluginsSectionNameHints { get; set; }
    public string[]? OverlaySectionNameHints { get; set; }
}

internal static class Program
{
    private static string _readmePath = string.Empty;

    public static int Main(string[] args)
    {
        if (args.Length == 0 || !File.Exists(args[0]))
        {
            Console.WriteLine("Usage: UiAuditRunner <config.json>");
            return 1;
        }

        var config = LoadConfig(args[0]);
        if (config == null)
        {
            Console.WriteLine("Invalid config.");
            return 1;
        }

        Directory.CreateDirectory(config.OutputFolder);
        _readmePath = Path.Combine(config.OutputFolder, "README.txt");
        File.WriteAllText(_readmePath, "UI Audit Pack (auto-generated)\n");

        // Note: DPI scaling must be set by the user per run. This tool records the intended scale in filenames.
        foreach (var dpi in config.DpiScales ?? Array.Empty<int>())
        {
            Console.WriteLine($"=== Capture pass for DPI {dpi}% ===");
            CapturePass(config, dpi);
        }

        var dpiLabelForZip = config.DpiLabel ?? (config.DpiScales?.FirstOrDefault().ToString() ?? "audit");
        var zipName = Path.GetFileNameWithoutExtension(config.ZipOutput);
        var zipPath = Path.GetFullPath($"{zipName}_{dpiLabelForZip}.zip");
        if (File.Exists(zipPath)) File.Delete(zipPath);
        ZipFile.CreateFromDirectory(config.OutputFolder, zipPath);
        Console.WriteLine($"Audit pack written to: {zipPath}");
        return 0;
    }

    private static AuditConfig? LoadConfig(string path)
    {
        try
        {
            var json = File.ReadAllText(path);
            var cfg = JsonSerializer.Deserialize<AuditConfig>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            return cfg;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Config load failed: {ex.Message}");
            return null;
        }
    }

    private static void CapturePass(AuditConfig config, int dpi)
    {
        var exePath = config.ProjectExePath;
        if (string.IsNullOrWhiteSpace(exePath) || !File.Exists(exePath))
        {
            Console.WriteLine("ProjectMaelstrom.exe not found. Skipping capture.");
            return;
        }

        Process? proc = null;
        using var automation = new UIA3Automation();
        try
        {
            proc = Process.Start(new ProcessStartInfo
            {
                FileName = exePath,
                UseShellExecute = false
            });
            if (proc == null)
            {
                Console.WriteLine("Failed to start process.");
                return;
            }

            if (!proc.WaitForInputIdle(config.WaitForMainMs))
            {
                Console.WriteLine("Process did not become idle in time.");
            }

            var app = FlaUI.Core.Application.Attach(proc);
            if (config.OpenScreens)
            {
                TryOpenScreens(automation, app, config, dpi);
            }

            foreach (var screen in config.Screens ?? Array.Empty<ScreenDef>())
            {
                CaptureWindow(automation, app, config, screen, dpi);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Capture pass failed: {ex.Message}");
        }
        finally
        {
            try
            {
                if (config.CloseOnFinish && proc != null && !proc.HasExited)
                {
                    proc.Kill(entireProcessTree: true);
                }
            }
            catch { }
        }
    }

    private static void CaptureWindow(UIA3Automation automation, FlaUI.Core.Application app, AuditConfig config, ScreenDef screen, int dpi)
    {
        try
        {
            var windows = app.GetAllTopLevelWindows(automation);
            var target = windows.FirstOrDefault(w =>
                w.Title.Contains(screen.WindowTitleContains, StringComparison.OrdinalIgnoreCase));

            if (target == null)
            {
                Console.WriteLine($"Window not found for {screen.Name} ({screen.WindowTitleContains}).");
                AppendReadme($"{ScreenFileName(screen.Name, dpi)} -> {screen.WindowTitleContains} (window not found)");
                return;
            }

            var rect = target.BoundingRectangle;
            var region = new Rectangle((int)rect.Left, (int)rect.Top, (int)rect.Width, (int)rect.Height);

            using (var img = CaptureProvider.Default.CaptureRegion(region))
            {
                var fileName = ScreenFileName(screen.Name, dpi);
                var path = Path.Combine(config.OutputFolder, fileName);
                img.Save(path, ImageFormat.Png);
                AppendReadme($"{fileName} -> {screen.WindowTitleContains}");
                Console.WriteLine($"Captured {fileName}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to capture {screen.Name}: {ex.Message}");
            AppendReadme($"{ScreenFileName(screen.Name, dpi)} -> error: {ex.Message}");
        }
    }

    private static string ScreenFileName(string name, int dpi)
    {
        return $"{name}_{dpi}.png".Replace(" ", "_").ToLowerInvariant();
    }

    private static void AppendReadme(string line)
    {
        try
        {
            File.AppendAllText(_readmePath, line + Environment.NewLine);
        }
        catch { }
    }

    private static void TryOpenScreens(UIA3Automation automation, FlaUI.Core.Application app, AuditConfig config, int dpi)
    {
        try
        {
            var mainHint = config.MainWindowTitleHint ?? "W101Trainer";
            var main = WaitForWindow(automation, app, mainHint, config.WaitForMainMs);
            if (main == null)
            {
                AppendReadme($"Main window not found (hint: {mainHint}); cannot auto-open screens.");
                return;
            }

            // Capture main immediately
            CaptureWindow(automation, app, config, new ScreenDef { Name = "main", WindowTitleContains = main.Name ?? mainHint }, dpi);

            var nav = config.Navigation ?? new NavigationHints();
            var timeoutMs = config.TimeoutSeconds * 1000;

            var settingsWin = TryOpenSettings(automation, app, main, nav, timeoutMs);
            AutomationElement? pluginsContainer = null;
            if (settingsWin != null)
            {
                pluginsContainer = TrySelectDeveloperOptions(settingsWin, nav, timeoutMs);
                TrySelectOverlaySection(settingsWin, nav);
            }

            // Capture plugins
            if (pluginsContainer != null && settingsWin != null)
            {
                CaptureWindow(automation, app, config, new ScreenDef { Name = "plugins", WindowTitleContains = settingsWin.Name }, dpi);
            }
            else
            {
                AppendReadme($"plugins_{dpi}.png -> missing (could not navigate to Plugins)");
            }

            // Capture policy (may be same view)
            if (settingsWin != null)
            {
                CaptureWindow(automation, app, config, new ScreenDef { Name = "policy", WindowTitleContains = settingsWin.Name }, dpi);
            }
            else
            {
                AppendReadme($"policy_{dpi}.png -> missing (Settings window not found)");
            }

            // Overlay preview (same settings window)
            if (settingsWin != null)
            {
                CaptureWindow(automation, app, config, new ScreenDef { Name = "overlay_preview", WindowTitleContains = settingsWin.Name }, dpi);
            }
            else
            {
                AppendReadme($"overlay_preview_{dpi}.png -> missing (Settings window not found)");
            }

            // Manage Scripts
            if (TryInvokeByHints(main, nav.OpenManageScriptsButtonNameHints))
            {
                var manageWin = WaitForWindow(automation, app, "Manage Scripts", timeoutMs);
                if (manageWin != null)
                {
                    CaptureWindow(automation, app, config, new ScreenDef { Name = "manage_scripts", WindowTitleContains = manageWin.Name }, dpi);
                }
                else
                {
                    AppendReadme($"manage_scripts_{dpi}.png -> missing (Manage Scripts not found)");
                }
            }
            else
            {
                AppendReadme($"manage_scripts_{dpi}.png -> missing (manage scripts control not found)");
            }

            // GitHub install dialog
            AutomationElement? gitDialog = null;
            if (settingsWin != null && TryInvokeByHints(settingsWin, nav.OpenGitHubInstallButtonNameHints))
            {
                gitDialog = WaitForWindow(automation, app, "Install", timeoutMs);
            }
            if (gitDialog != null)
            {
                CaptureWindow(automation, app, config, new ScreenDef { Name = "github_install", WindowTitleContains = gitDialog.Name }, dpi);
            }
            else
            {
                AppendReadme($"github_install_{dpi}.png -> missing (GitHub install dialog not found)");
            }
        }
        catch (Exception ex)
        {
            AppendReadme($"Auto-open failed: {ex.Message}");
        }
    }

    private static AutomationElement? TryOpenSettings(UIA3Automation automation, FlaUI.Core.Application app, AutomationElement main, NavigationHints nav, int timeoutMs)
    {
        if (!TryInvokeByHints(main, nav.OpenSettingsButtonNameHints ?? Array.Empty<string>()))
        {
            AppendReadme("Settings open failed: control not found via hints.");
            return null;
        }

        var settings = WaitForWindow(automation, app, "Settings", timeoutMs) ??
                       WaitForWindow(automation, app, "Developer Options", timeoutMs);
        if (settings == null)
        {
            AppendReadme("Settings window not found after invoke.");
        }
        return settings;
    }

    private static AutomationElement? TrySelectDeveloperOptions(AutomationElement settingsWin, NavigationHints nav, int timeoutMs)
    {
        // Try tab/list selection
        if (SelectByNameHints(settingsWin, nav.DeveloperOptionsTabNameHints))
        {
            // Try plugins section/tab
            SelectByNameHints(settingsWin, nav.PluginsSectionNameHints);
            return settingsWin;
        }

        AppendReadme("Developer Options navigation failed.");
        return settingsWin;
    }

    private static void TrySelectOverlaySection(AutomationElement settingsWin, NavigationHints nav)
    {
        SelectByNameHints(settingsWin, nav.OverlaySectionNameHints);
    }

    private static bool TryInvokeByHints(AutomationElement root, IEnumerable<string>? hints)
    {
        if (hints == null) return false;
        foreach (var hint in hints)
        {
            var target = FindByNameContains(root, hint);
            if (target == null) continue;

            var invokable = target.Patterns.Invoke.PatternOrDefault;
            if (invokable != null)
            {
                invokable.Invoke();
                return true;
            }

            var selectable = target.Patterns.SelectionItem.PatternOrDefault;
            if (selectable != null)
            {
                selectable.Select();
                return true;
            }
        }
        return false;
    }

    private static bool SelectByNameHints(AutomationElement root, IEnumerable<string>? hints)
    {
        if (hints == null) return false;
        foreach (var hint in hints)
        {
            var target = FindByNameContains(root, hint);
            if (target == null) continue;
            var selectable = target.Patterns.SelectionItem.PatternOrDefault;
            if (selectable != null)
            {
                selectable.Select();
                return true;
            }
            var invokable = target.Patterns.Invoke.PatternOrDefault;
            if (invokable != null)
            {
                invokable.Invoke();
                return true;
            }
        }
        return false;
    }

    private static AutomationElement? FindByNameContains(AutomationElement root, string hint)
    {
        return root.FindAllDescendants()
            .FirstOrDefault(x => x.Name.Contains(hint, StringComparison.OrdinalIgnoreCase));
    }

    private static AutomationElement? WaitForWindow(UIA3Automation automation, FlaUI.Core.Application app, string titleContains, int timeoutMs)
    {
        var sw = Stopwatch.StartNew();
        while (sw.ElapsedMilliseconds < timeoutMs)
        {
            var win = app.GetAllTopLevelWindows(automation)
                .FirstOrDefault(w => w.Title.Contains(titleContains, StringComparison.OrdinalIgnoreCase));
            if (win != null) return win;
            Thread.Sleep(200);
        }
        return null;
    }
}
