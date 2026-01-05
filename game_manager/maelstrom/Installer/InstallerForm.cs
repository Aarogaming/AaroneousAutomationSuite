using System.Diagnostics;
using System.IO.Compression;
using System.Reflection;
using System.Text.Json;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using Installer.Models;

namespace Installer;

public partial class InstallerForm : Form
{
    private const string DefaultFeedUrl = "https://raw.githubusercontent.com/Aarogaming/aaroneous-automation-suite/main/update_manifest.json";
    private readonly string? _feedUrlFromArgs;
    private string _defaultInstallPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ProjectMaelstrom");
    private string _logPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ProjectMaelstrom", "logs", "installer.log");
    private string _desktop => Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
    private string _startMenu => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Project Maelstrom");
    private string _latestVersion = "Unknown";
    private string? _latestChangelog = null;
    private string _installedVersion = "Unknown";
    private bool _devMode;
    private static readonly HttpClient _httpClient = new();
    private string? _manualPayloadPath;
    private bool _feedControlsVisible;

    private string ResolveInstallPath()
    {
        return string.IsNullOrWhiteSpace(installPathText.Text)
            ? _defaultInstallPath
            : installPathText.Text.Trim();
    }

    public InstallerForm(string? feedUrl)
    {
        _feedUrlFromArgs = feedUrl;
        InitializeComponent();
        ApplyPalette();
    }

    private void InstallerForm_Load(object sender, EventArgs e)
    {
        if (!string.IsNullOrWhiteSpace(_feedUrlFromArgs))
            {
                feedText.Text = _feedUrlFromArgs;
                SetFeedControlsVisible(true);
            }
            else
            {
                // Use default feed silently unless the user opts to change it.
                feedText.Text = DefaultFeedUrl;
                autoCheckUpdatesCheck.Checked = true;
                SetFeedControlsVisible(autoCheckUpdatesCheck.Checked);
            }
        // Leave feed empty unless explicitly provided
        installPathText.Text = _defaultInstallPath;
        logPathLabel.Text = $"Log: {_logPath}";
        DetectInstalled();
        _ = DetectDevModeAsync();
        _ = PopulateScriptsFromEmbeddedAsync();
        if (autoCheckUpdatesCheck.Checked)
        {
            checkButton_Click(this, EventArgs.Empty);
        }
    }

    private sealed record Palette(
        Color Back,
        Color Surface,
        Color ControlBack,
        Color ControlFore,
        Color Border,
        Color Accent,
        Color Fore,
        Color TextMuted);

    private void ApplyPalette()
    {
        // Mirror the main app's Wizard101-inspired palette.
        var palette = new Palette(
            Back: Color.FromArgb(18, 24, 46),
            Surface: Color.FromArgb(22, 30, 56),
            ControlBack: Color.FromArgb(30, 42, 72),
            ControlFore: Color.FromArgb(243, 236, 219),
            Border: Color.FromArgb(96, 68, 22),
            Accent: Color.FromArgb(227, 177, 39),
            Fore: Color.FromArgb(243, 236, 219),
            TextMuted: Color.FromArgb(198, 190, 169));

        BackColor = palette.Surface;
        ForeColor = palette.Fore;

        void StyleButton(Button btn)
        {
            btn.BackColor = palette.ControlBack;
            btn.ForeColor = palette.ControlFore;
            btn.FlatStyle = FlatStyle.Flat;
            btn.FlatAppearance.BorderColor = palette.Border;
            btn.FlatAppearance.BorderSize = 1;
        }

        var buttons = new[]
        {
            checkButton, installButton, uninstallButton, createPortableButton, updateButton, browseInstallButton,
            devButton, openLogButton, openInstallFolderButton, openLibraryButton, launchAppButton, manualSourceButton
        };
        foreach (var b in buttons)
        {
            StyleButton(b);
        }

        var textInputs = new[] { feedText, installPathText };
        foreach (var tb in textInputs)
        {
            tb.BackColor = palette.ControlBack;
            tb.ForeColor = palette.ControlFore;
        }

        scriptsList.BackColor = palette.ControlBack;
        scriptsList.ForeColor = palette.ControlFore;
        activityList.BackColor = palette.ControlBack;
        activityList.ForeColor = palette.ControlFore;

        var labels = new[]
        {
            titleLabel, feedLabel, installPathLabel, statusLabel, installedVersionLabel, latestVersionLabel,
            stepLabel, scriptsLabel, logPathLabel
        };
        foreach (var lbl in labels)
        {
            lbl.ForeColor = palette.Fore;
        }

        var checks = new[]
        {
            desktopShortcutCheck, startMenuShortcutCheck, uninstallShortcutCheck, autoCheckUpdatesCheck,
            cleanInstallCheck, launchAfterInstallCheck, openReleaseNotesCheck, smartPlayInitCheck
        };
        foreach (var chk in checks)
        {
            chk.ForeColor = palette.Fore;
            chk.BackColor = palette.Surface;
        }
    }

    private void SetFeedControlsVisible(bool visible)
    {
        if (_feedControlsVisible == visible) return;
        _feedControlsVisible = visible;
        feedLabel.Visible = visible;
        feedText.Visible = visible;
        checkButton.Visible = visible;
    }

    private void autoCheckUpdatesCheck_CheckedChanged(object sender, EventArgs e)
    {
        if (!autoCheckUpdatesCheck.Checked)
        {
            // If user disables auto-check, hide feed controls to reduce clutter.
            SetFeedControlsVisible(false);
        }
        else
        {
            // If they re-enable, show so they can override the feed.
            SetFeedControlsVisible(true);
        }
    }

    private void DetectInstalled()
    {
        var exe = Path.Combine(ResolveInstallPath(), "ProjectMaelstrom.exe");
        if (File.Exists(exe))
        {
            var info = FileVersionInfo.GetVersionInfo(exe);
            _installedVersion = info.FileVersion ?? "Unknown";
            installedVersionLabel.Text = $"Installed: {_installedVersion}";
        }
        else
        {
            installedVersionLabel.Text = "Installed: Not found";
            _installedVersion = "Not found";
        }
    }

    private async Task DetectDevModeAsync()
    {
        try
        {
            var cfg = Path.Combine(ResolveInstallPath(), "dev.config");
            if (!File.Exists(cfg))
            {
                cfg = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ProjectMaelstrom", "dev.config");
            }

            string? token = null;
            if (File.Exists(cfg))
            {
                var lines = File.ReadAllLines(cfg);
                foreach (var line in lines)
                {
                    if (line.IndexOf("DEV_MODE=true", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        _devMode = true;
                        devButton.Visible = true;
                        LogStep("Dev mode enabled via config.");
                        return;
                    }
                    if (line.TrimStart().StartsWith("GITHUB_TOKEN=", StringComparison.OrdinalIgnoreCase))
                    {
                        token = line.Split('=', 2)[1].Trim();
                    }
                }
            }

            if (!string.IsNullOrWhiteSpace(token))
            {
                try
                {
                    var req = new HttpRequestMessage(HttpMethod.Get, "https://api.github.com/user");
                    req.Headers.UserAgent.ParseAdd("ProjectMaelstromInstaller");
                    req.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
                    var resp = await _httpClient.SendAsync(req);
                    if (resp.IsSuccessStatusCode)
                    {
                        var json = await resp.Content.ReadAsStringAsync();
                        using var doc = JsonDocument.Parse(json);
                        if (doc.RootElement.TryGetProperty("login", out var loginEl))
                        {
                            var login = loginEl.GetString();
                            if (!string.IsNullOrWhiteSpace(login) &&
                                login.Equals("aarog", StringComparison.OrdinalIgnoreCase))
                            {
                                _devMode = true;
                                devButton.Visible = true;
                                LogStep("Dev mode enabled via GitHub token.");
                                return;
                            }
                        }
                    }
                }
                catch
                {
                    // ignore token failures
                }
            }
        }
        catch
        {
            // ignore
        }
        _devMode = false;
        devButton.Visible = false;
    }

    private async void checkButton_Click(object sender, EventArgs e)
    {
        var url = feedText.Text;
        if (string.IsNullOrWhiteSpace(url))
        {
            statusLabel.Text = "Status: No feed provided.";
            LogError("No feed provided for update check.");
            manualSourceButton.Visible = true;
            return;
        }

        LogStep("Checking feed...");
        try
        {
            progressBar.Style = ProgressBarStyle.Marquee;
            statusLabel.Text = "Status: Checking feed...";
            using var client = new HttpClient();
            var json = await client.GetStringAsync(url);
            var manifest = JsonSerializer.Deserialize<UpdateManifest>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            _latestVersion = manifest?.Version ?? "Unknown";
            latestVersionLabel.Text = $"Latest: {_latestVersion}";
            DetectInstalled(); // refresh installed version info for comparison

            if (Version.TryParse(_installedVersion, out var installed) &&
                Version.TryParse(_latestVersion, out var latest) &&
                latest > installed)
            {
                statusLabel.Text = $"Status: Update available (Installed: {_installedVersion}, Latest: {_latestVersion})";
            }
            else
            {
                statusLabel.Text = $"Status: Up to date (Installed: {_installedVersion}, Latest: {_latestVersion})";
            }

            LogStep($"Latest version: {_latestVersion} | Installed: {_installedVersion}");
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Status: Check failed ({ex.Message})";
            LogStep($"Check failed: {ex.Message}");
            LogError($"Check failed: {ex}");
            manualSourceButton.Visible = true;
        }
        finally
        {
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 0;
        }
    }

    private async void installButton_Click(object sender, EventArgs e)
    {
        await InstallOrUpdateAsync(force: true);
    }

    private async void updateButton_Click(object sender, EventArgs e)
    {
        await InstallOrUpdateAsync(force: false);
    }

    private async Task InstallOrUpdateAsync(bool force)
    {
        ToggleButtons(false);
        progressBar.Style = ProgressBarStyle.Marquee;
        statusLabel.Text = force ? "Status: Fresh install..." : "Status: Checking for update...";
        LogStep(force ? "Starting fresh install..." : "Starting update...");
        try
        {
            // Modular packaging: allow selecting components
            var payload = _manualPayloadPath ?? (await TryDownloadLatest(feedText.Text) ?? ExtractEmbeddedPayload());
            if (payload == null)
            {
                statusLabel.Text = "Status: No payload available.";
                LogStep("No payload available.");
                LogError("No payload available for install/update.");
                return;
            }

            if (!force && IsUpToDate())
            {
                statusLabel.Text = "Status: Already up to date.";
                LogStep("No update needed; versions match.");
                return;
            }

            var installPath = ResolveInstallPath();

            if (cleanInstallCheck.Checked && Directory.Exists(installPath))
            {
                Directory.Delete(installPath, recursive: true);
            }
            Directory.CreateDirectory(installPath);

            LogStep("Extracting package...");
            // Backup existing installation if it exists
            if (Directory.Exists(installPath))
            {
                var backupPath = installPath + "_backup_" + DateTime.Now.ToString("yyyyMMddHHmmss");
                LogStep($"Backing up existing installation to {backupPath}...");
                try { 
                    // Simple directory move for backup
                    // In a real scenario, we might want to zip it
                    Directory.Move(installPath, backupPath); 
                } catch (Exception ex) {
                    LogStep($"Backup failed: {ex.Message}. Proceeding with caution.");
                }
            }

            await ExtractPayloadAsync(payload, installPath);

            if (smartPlayInitCheck.Checked)
            {
                try
                {
                    var scriptsRoot = Path.Combine(installPath, "Scripts");
                    var libraryPath = Path.Combine(scriptsRoot, "Library");
                    var cachePath = Path.Combine(scriptsRoot, ".cache");
                    Directory.CreateDirectory(scriptsRoot);
                    Directory.CreateDirectory(libraryPath);
                    Directory.CreateDirectory(cachePath);
                    Directory.CreateDirectory(Path.Combine(installPath, "logs"));
                }
                catch
                {
                    // best effort
                }
            }

            if (desktopShortcutCheck.Checked)
            {
                CreateShortcut(Path.Combine(_desktop, "Project Maelstrom.lnk"), installPath);
            }
            if (startMenuShortcutCheck.Checked)
            {
                Directory.CreateDirectory(_startMenu);
                CreateShortcut(Path.Combine(_startMenu, "Project Maelstrom.lnk"), installPath);
            }
            if (uninstallShortcutCheck.Checked)
            {
                CreateUninstallScript(installPath, createShortcut: true);
            }
            else
            {
                CreateUninstallScript(installPath, createShortcut: false);
            }

            statusLabel.Text = "Status: Install complete.";
            LogStep("Install complete.");
            DetectInstalled();

            if (launchAfterInstallCheck.Checked)
            {
                var exePath = Path.Combine(installPath, "ProjectMaelstrom.exe");
                if (File.Exists(exePath))
                {
                    try { Process.Start(new ProcessStartInfo(exePath) { UseShellExecute = true }); } catch { /* ignore */ }
                }
            }

            if (openReleaseNotesCheck.Checked && !string.IsNullOrWhiteSpace(_latestChangelog))
            {
                MessageBox.Show(_latestChangelog, "Release Notes", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Status: Install failed ({ex.Message})";
            LogStep($"Install failed: {ex.Message}");
            LogError($"Install failed: {ex}");
        }
        finally
        {
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 100;
            ToggleButtons(true);
        }
    }

    private async void createPortableButton_Click(object sender, EventArgs e)
    {
        using var sfd = new SaveFileDialog
        {
            Filter = "Zip Files|*.zip",
            FileName = "ProjectMaelstrom-portable.zip",
            OverwritePrompt = true
        };

        if (sfd.ShowDialog() != DialogResult.OK) return;

        ToggleButtons(false);
        progressBar.Style = ProgressBarStyle.Marquee;
        statusLabel.Text = "Status: Creating portable package...";
        LogStep("Creating portable package...");
        try
        {
            var payload = await TryDownloadLatest(feedText.Text) ?? ExtractEmbeddedPayload();
            if (payload == null)
            {
                statusLabel.Text = "Status: No payload available.";
                LogStep("No payload available for portable.");
                LogError("No payload available for portable.");
                return;
            }

            File.Copy(payload, sfd.FileName, overwrite: true);
            using (var archive = ZipFile.Open(sfd.FileName, ZipArchiveMode.Update))
            {
                var entry = archive.GetEntry("portable_mode.txt");
                entry?.Delete();
                var newEntry = archive.CreateEntry("portable_mode.txt");
                using var writer = new StreamWriter(newEntry.Open());
                writer.WriteLine("portable");
            }

            statusLabel.Text = $"Status: Portable package created: {sfd.FileName}";
            LogStep($"Portable package created at {sfd.FileName}");
            var openFolder = MessageBox.Show("Portable package created. Open folder now?", "Portable Created", MessageBoxButtons.YesNo, MessageBoxIcon.Information);
            if (openFolder == DialogResult.Yes)
            {
                try
                {
                    Process.Start("explorer.exe", $"/select,\"{sfd.FileName}\"");
                }
                catch
                {
                    // non-fatal
                }
            }
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Status: Portable creation failed ({ex.Message})";
            LogStep($"Portable failed: {ex.Message}");
            LogError($"Portable creation failed: {ex}");
        }
        finally
        {
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 100;
            ToggleButtons(true);
        }
    }

    private void uninstallButton_Click(object sender, EventArgs e)
    {
        ToggleButtons(false);
        progressBar.Style = ProgressBarStyle.Marquee;
        try
        {
            var desktopShortcut = Path.Combine(_desktop, "Project Maelstrom.lnk");
            var startShortcut = Path.Combine(_startMenu, "Project Maelstrom.lnk");
            var startUninstall = Path.Combine(_startMenu, "Uninstall Project Maelstrom.lnk");
            if (File.Exists(desktopShortcut)) File.Delete(desktopShortcut);
            if (File.Exists(startShortcut)) File.Delete(startShortcut);
            if (File.Exists(startUninstall)) File.Delete(startUninstall);
            var installPath = ResolveInstallPath();
            if (Directory.Exists(installPath)) Directory.Delete(installPath, recursive: true);
            statusLabel.Text = "Status: Uninstalled.";
            installedVersionLabel.Text = "Installed: Not found";
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Status: Uninstall failed ({ex.Message})";
            LogError($"Uninstall failed: {ex}");
        }
        finally
        {
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 0;
            ToggleButtons(true);
        }
    }

    private void ToggleButtons(bool enabled)
    {
        installButton.Enabled = enabled;
        uninstallButton.Enabled = enabled;
        checkButton.Enabled = enabled;
        updateButton.Enabled = enabled;
        createPortableButton.Enabled = enabled;
    }

    private async Task<string?> TryDownloadLatest(string? feedUrl)
    {
        if (string.IsNullOrWhiteSpace(feedUrl)) return null;
        try
        {
            using var client = new HttpClient();
            var json = await client.GetStringAsync(feedUrl);
            var manifest = JsonSerializer.Deserialize<UpdateManifest>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (manifest == null || string.IsNullOrWhiteSpace(manifest.PackageUrl))
            {
                LogStep("Manifest missing packageUrl.");
                return null;
            }
            var tempZip = Path.Combine(Path.GetTempPath(), $"ProjectMaelstrom_latest_{DateTime.UtcNow:yyyyMMddHHmmss}.zip");
            var data = await client.GetByteArrayAsync(manifest.PackageUrl);
            await File.WriteAllBytesAsync(tempZip, data);
            _latestVersion = manifest.Version ?? "Unknown";
            _latestChangelog = manifest.Changelog;
            latestVersionLabel.Text = $"Latest: {_latestVersion}";
            LogStep($"Downloaded latest package {_latestVersion}");
            return tempZip;
        }
        catch (Exception ex)
        {
            LogError($"Download latest failed: {ex}");
            manualSourceButton.Visible = true;
            SetFeedControlsVisible(true);
            return null;
        }
    }

    private async Task<UpdateManifest?> FetchLatestManifestAsync(string feedUrl)
    {
        try
        {
            using var client = new HttpClient();
            var json = await client.GetStringAsync(feedUrl);
            var manifest = JsonSerializer.Deserialize<UpdateManifest>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            return manifest;
        }
        catch (Exception ex)
        {
            LogError($"Fetch manifest failed: {ex}");
            manualSourceButton.Visible = true;
            SetFeedControlsVisible(true);
            return null;
        }
    }

    private string? ExtractEmbeddedPayload()
    {
        var asm = Assembly.GetExecutingAssembly();
        var resourceName = asm.GetManifestResourceNames().FirstOrDefault(n => n.EndsWith("ProjectMaelstrom-win-x64.zip", StringComparison.OrdinalIgnoreCase));
        if (resourceName == null) return null;
        var tempZip = Path.Combine(Path.GetTempPath(), "ProjectMaelstrom-win-x64.zip");
        using var resStream = asm.GetManifestResourceStream(resourceName);
        using var fs = File.Create(tempZip);
        resStream!.CopyTo(fs);
        _latestVersion = "Embedded";
        latestVersionLabel.Text = $"Latest: {_latestVersion}";
        LogStep("Using embedded package.");
        return tempZip;
    }

    private async Task ExtractPayloadAsync(string payloadPath, string installPath)
    {
        if (string.IsNullOrWhiteSpace(payloadPath) || !File.Exists(payloadPath))
        {
            throw new FileNotFoundException("Payload not found", payloadPath);
        }

        var selected = scriptsList.CheckedItems.Cast<object>()
            .Select(o => o?.ToString())
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .Select(s => s!.Trim())
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        var limitScripts = selected.Count > 0;

        using var archive = ZipFile.OpenRead(payloadPath);
        var sep = Path.DirectorySeparatorChar.ToString();
        var scriptPrefix = $"Scripts{sep}Library{sep}";

        foreach (var entry in archive.Entries)
        {
            var normalized = entry.FullName.Replace('/', Path.DirectorySeparatorChar);
            if (string.IsNullOrWhiteSpace(normalized))
            {
                continue;
            }

            var isDirectory = normalized.EndsWith(Path.DirectorySeparatorChar);
            var isScript = normalized.StartsWith(scriptPrefix, StringComparison.OrdinalIgnoreCase);
            string? scriptName = null;
            if (isScript)
            {
                var remainder = normalized.Substring(scriptPrefix.Length);
                var slashIndex = remainder.IndexOf(Path.DirectorySeparatorChar);
                if (slashIndex > 0)
                {
                    scriptName = remainder[..slashIndex];
                }
                else if (!string.IsNullOrWhiteSpace(remainder))
                {
                    scriptName = remainder;
                }
            }

            if (isScript && limitScripts && (scriptName == null || !selected.Contains(scriptName)))
            {
                continue;
            }

            var destinationPath = Path.GetFullPath(Path.Combine(installPath, normalized));
            if (!destinationPath.StartsWith(Path.GetFullPath(installPath), StringComparison.OrdinalIgnoreCase))
            {
                continue; // safety
            }

            if (isDirectory || string.IsNullOrEmpty(entry.Name))
            {
                Directory.CreateDirectory(destinationPath);
                continue;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(destinationPath)!);
            using var entryStream = entry.Open();
            using var fileStream = File.Create(destinationPath);
            await entryStream.CopyToAsync(fileStream);
        }
    }

    private void CreateShortcut(string shortcutPath, string installPath)
    {
        try
        {
            var exePath = Path.Combine(installPath, "ProjectMaelstrom.exe");
            IShellLinkW shellLink = (IShellLinkW)new ShellLink();
            shellLink.SetPath(exePath);
            shellLink.SetWorkingDirectory(installPath);
            shellLink.SetIconLocation(exePath, 0);
            IPersistFile persistFile = (IPersistFile)shellLink;
            persistFile.Save(shortcutPath, false);
        }
        catch { /* best effort */ }
    }

    private void CreateUninstallScript(string installPath, bool createShortcut)
    {
        try
        {
            var scriptPath = Path.Combine(installPath, "uninstall_maelstrom.ps1");
            var desktopShortcut = Path.Combine(_desktop, "Project Maelstrom.lnk");
            var startShortcut = Path.Combine(_startMenu, "Project Maelstrom.lnk");
            var startUninstall = Path.Combine(_startMenu, "Uninstall Project Maelstrom.lnk");
            var script = $@"
$ErrorActionPreference = 'SilentlyContinue'
Remove-Item -Path '{desktopShortcut}' -ErrorAction SilentlyContinue
Remove-Item -Path '{startShortcut}' -ErrorAction SilentlyContinue
Remove-Item -Path '{startUninstall}' -ErrorAction SilentlyContinue
if (Test-Path '{installPath}') {{
    Remove-Item -Recurse -Force '{installPath}'
}}
Write-Host 'Project Maelstrom removed.'
";
            File.WriteAllText(scriptPath, script);
            if (createShortcut)
            {
                Directory.CreateDirectory(_startMenu);
                CreateScriptShortcut(Path.Combine(_startMenu, "Uninstall Project Maelstrom.lnk"), scriptPath, "Uninstall Project Maelstrom");
            }
        }
        catch { /* ignore */ }
    }

    private static void CreateScriptShortcut(string shortcutPath, string scriptPath, string title)
    {
        try
        {
            IShellLinkW shellLink = (IShellLinkW)new ShellLink();
            shellLink.SetPath("powershell.exe");
            shellLink.SetArguments($"-NoLogo -NoProfile -ExecutionPolicy Bypass -File \"{scriptPath}\"");
            shellLink.SetDescription(title);
            shellLink.SetWorkingDirectory(Path.GetDirectoryName(scriptPath)!);
            IPersistFile persistFile = (IPersistFile)shellLink;
            persistFile.Save(shortcutPath, false);
        }
        catch { /* ignore */ }
    }

    #region COM Interop
    [ComImport]
    [Guid("000214F9-0000-0000-C000-000000000046")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cchMaxPath, out WIN32_FIND_DATAW pfd, uint fFlags);
        void GetIDList(out IntPtr ppidl);
        void SetIDList(IntPtr pidl);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cchMaxName);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cchMaxPath);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cchMaxPath);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
        void GetHotkey(out short pwHotkey);
        void SetHotkey(short wHotkey);
        void GetShowCmd(out int piShowCmd);
        void SetShowCmd(int iShowCmd);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cchIconPath, out int piIcon);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, uint dwReserved);
        void Resolve(IntPtr hwnd, uint fFlags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
    }

    private bool IsUpToDate()
    {
        if (string.IsNullOrWhiteSpace(_installedVersion) || string.IsNullOrWhiteSpace(_latestVersion))
            return false;

        if (Version.TryParse(_installedVersion, out var installed) && Version.TryParse(_latestVersion, out var latest))
        {
            return installed >= latest;
        }

        return string.Equals(_installedVersion, _latestVersion, StringComparison.OrdinalIgnoreCase);
    }

    private void devButton_Click(object sender, EventArgs e)
    {
        if (!_devMode)
        {
            MessageBox.Show("Dev mode not enabled.", "Access Denied", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        var msg = $"Dev Console\nInstalled: {_installedVersion}\nLatest: {_latestVersion}\nFeed: {feedText.Text}";
        MessageBox.Show(msg, "Dev Console", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct WIN32_FIND_DATAW
    {
        public uint dwFileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
        public uint nFileSizeHigh;
        public uint nFileSizeLow;
        public uint dwReserved0;
        public uint dwReserved1;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string cFileName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 14)]
        public string cAlternateFileName;
    }

    [ComImport]
    [Guid("00021401-0000-0000-C000-000000000046")]
    private class ShellLink { }

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("0000010b-0000-0000-C000-000000000046")]
    private interface IPersistFile
    {
        void GetClassID(out Guid pClassID);
        void IsDirty();
        void Load([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, uint dwMode);
        void Save([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, bool fRemember);
        void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string pszFileName);
        void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string ppszFileName);
    }
    #endregion

    private void LogStep(string message)
    {
        if (activityList.Items.Count > 200) activityList.Items.Clear();
        activityList.Items.Add($"{DateTime.Now:T} {message}");
        activityList.TopIndex = activityList.Items.Count - 1;
        stepLabel.Text = $"Step: {message}";
    }

    private void LogError(string message)
    {
        try
        {
            var dir = Path.GetDirectoryName(_logPath);
            if (!Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir!);
            }
            File.AppendAllText(_logPath, $"{DateTime.Now:u} {message}{Environment.NewLine}");
        }
        catch
        {
            // best effort logging
        }
    }

    private async Task PopulateScriptsFromEmbeddedAsync()
    {
        try
        {
            var asm = Assembly.GetExecutingAssembly();
            var resourceName = asm.GetManifestResourceNames().FirstOrDefault(n => n.EndsWith("ProjectMaelstrom-win-x64.zip", StringComparison.OrdinalIgnoreCase));
            if (resourceName == null) return;

            using var resStream = asm.GetManifestResourceStream(resourceName);
            if (resStream == null) return;
            using var archive = new ZipArchive(resStream, ZipArchiveMode.Read, leaveOpen: false);
            var sep = '/';
            var prefix = "Scripts/Library/";
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var entry in archive.Entries)
            {
                if (!entry.FullName.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) continue;
                var remainder = entry.FullName.Substring(prefix.Length);
                var slash = remainder.IndexOf(sep);
                if (slash > 0)
                {
                    var name = remainder.Substring(0, slash);
                    if (!string.IsNullOrWhiteSpace(name))
                    {
                        names.Add(name.Trim());
                    }
                }
            }

            var sorted = names.OrderBy(n => n).ToList();
            scriptsList.Items.Clear();
            foreach (var n in sorted)
            {
                scriptsList.Items.Add(n, true);
            }

            LogStep(sorted.Count == 0 ? "No scripts detected in package." : $"Scripts detected: {sorted.Count}");
        }
        catch (Exception ex)
        {
            LogError($"Populate scripts failed: {ex}");
        }
    }

    private void browseInstallButton_Click(object sender, EventArgs e)
    {
        using var dlg = new FolderBrowserDialog();
        dlg.SelectedPath = string.IsNullOrWhiteSpace(installPathText.Text) ? _defaultInstallPath : installPathText.Text;
        if (dlg.ShowDialog() == DialogResult.OK)
        {
            installPathText.Text = dlg.SelectedPath;
        }
    }

    private void openLogButton_Click(object sender, EventArgs e)
    {
        try
        {
            var dir = Path.GetDirectoryName(_logPath);
            if (!string.IsNullOrWhiteSpace(dir))
            {
                Directory.CreateDirectory(dir);
                Process.Start(new ProcessStartInfo("explorer.exe", dir) { UseShellExecute = true });
            }
        }
        catch
        {
            // ignore
        }
    }

    private void openInstallFolderButton_Click(object sender, EventArgs e)
    {
        try
        {
            var path = ResolveInstallPath();
            Directory.CreateDirectory(path);
            Process.Start(new ProcessStartInfo("explorer.exe", path) { UseShellExecute = true });
        }
        catch
        {
            // ignore
        }
    }

    private void openLibraryButton_Click(object sender, EventArgs e)
    {
        try
        {
            var library = Path.Combine(ResolveInstallPath(), "Scripts", "Library");
            Directory.CreateDirectory(library);
            Process.Start(new ProcessStartInfo("explorer.exe", library) { UseShellExecute = true });
        }
        catch
        {
            // ignore
        }
    }

    private void manualSourceButton_Click(object sender, EventArgs e)
    {
        var choice = MessageBox.Show(
            "Pick a local package (zip) or enter a feed URL?\nYes = pick local zip, No = enter feed URL",
            "Manual source",
            MessageBoxButtons.YesNoCancel,
            MessageBoxIcon.Question);

        if (choice == DialogResult.Cancel) return;

        if (choice == DialogResult.Yes)
        {
            using var ofd = new OpenFileDialog
            {
                Filter = "Zip Files|*.zip",
                Title = "Select package zip"
            };
            if (ofd.ShowDialog() == DialogResult.OK && File.Exists(ofd.FileName))
            {
                _manualPayloadPath = ofd.FileName;
                latestVersionLabel.Text = "Latest: manual zip";
                statusLabel.Text = "Status: Manual package selected.";
                LogStep($"Manual package selected: {ofd.FileName}");
            }
        }
        else
        {
            string input = Microsoft.VisualBasic.Interaction.InputBox("Enter update feed URL:", "Manual Feed", feedText.Text);
            if (!string.IsNullOrWhiteSpace(input))
            {
                feedText.Text = input.Trim();
                _manualPayloadPath = null;
                statusLabel.Text = "Status: Manual feed set.";
                LogStep("Manual feed set.");
            }
        }
    }

    private async void launchAppButton_Click(object sender, EventArgs e)
    {
        await GuardedLaunchAsync();
    }

    private async Task GuardedLaunchAsync()
    {
        try
        {
            var installPath = ResolveInstallPath();
            var exe = Path.Combine(installPath, "ProjectMaelstrom.exe");
            if (!File.Exists(exe))
            {
                MessageBox.Show("Project Maelstrom is not installed at the selected path.", "Launch", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            // Optional version check before launch
            if (autoCheckUpdatesCheck.Checked && !string.IsNullOrWhiteSpace(feedText.Text))
            {
                var manifest = await FetchLatestManifestAsync(feedText.Text);
                if (manifest?.Version != null)
                {
                    _latestVersion = manifest.Version;
                    latestVersionLabel.Text = $"Latest: {_latestVersion}";
                }

                DetectInstalled(); // refresh installed version info

                if (!string.IsNullOrWhiteSpace(_latestVersion) &&
                    Version.TryParse(_installedVersion, out var installed) &&
                    Version.TryParse(_latestVersion, out var latest) &&
                    latest > installed)
                {
                    var choice = MessageBox.Show(
                        $"An update is available (Installed: {_installedVersion}, Latest: {_latestVersion}).\n\nUpdate now?",
                        "Update Recommended",
                        MessageBoxButtons.YesNoCancel,
                        MessageBoxIcon.Question);

                    if (choice == DialogResult.Yes)
                    {
                        await InstallOrUpdateAsync(force: false);
                        DetectInstalled();
                        exe = Path.Combine(ResolveInstallPath(), "ProjectMaelstrom.exe");
                        if (!File.Exists(exe))
                        {
                            MessageBox.Show("Launch aborted: executable not found after update.", "Launch", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                            return;
                        }
                    }
                    else if (choice == DialogResult.Cancel)
                    {
                        return; // user cancelled
                    }
                    // No => launch anyway
                }
            }

            Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true });
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to launch: {ex.Message}", "Launch Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
