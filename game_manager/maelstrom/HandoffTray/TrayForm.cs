using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace HandoffTray;

public class TrayForm : Form
{
    private readonly NotifyIcon _notifyIcon;
    private readonly ContextMenuStrip _menu;
    private readonly ToolStripMenuItem _modeOff;
    private readonly ToolStripMenuItem _modeTo;
    private readonly ToolStripMenuItem _modeFrom;
    private readonly ToolStripMenuItem _modeBoth;
    private readonly ToolStripMenuItem _toggleApi;
    private readonly ToolStripMenuItem _statusItem;
    private readonly ToolStripMenuItem _openDashboardItem;
    private readonly ToolStripMenuItem _automationsMenu;
    private readonly ToolStripMenuItem _cancelJobItem;
    private readonly ToolStripMenuItem _settingsItem;

    private readonly HandoffWatcher _watcher;
    private readonly ApiSender _apiSender = new();
    private readonly LogHelper _log;
    private readonly string _root;
    private bool _apiSendEnabled;

    private readonly BotApiClient _botApi;
    private readonly TraySettings _settings;
    private string? _token;
    private readonly System.Windows.Forms.Timer _pollTimer;
    private string? _lastNotifiedJobId;
    private bool _initialLoadDone;
    private DateTime _nextRetryUtc;

    public TrayForm()
    {
        _root = Directory.GetCurrentDirectory();
        _log = new LogHelper(_root);
        var toDir = Path.Combine(_root, "artifacts", "handoff", "to_codex");
        var fromDir = Path.Combine(_root, "artifacts", "handoff", "from_codex");
        Directory.CreateDirectory(toDir);
        Directory.CreateDirectory(fromDir);

        _watcher = new HandoffWatcher(toDir, fromDir);
        _watcher.PromptDetected += OnPromptDetected;
        _watcher.ResultDetected += OnResultDetected;

        _settings = SettingsStore.Load();
        _token = TokenStore.TryLoad();
        _botApi = new BotApiClient(_settings.BaseUrl, _token);

        _menu = new ContextMenuStrip();
        _modeOff = new ToolStripMenuItem("Mode: Off", null, (_, _) => SetMode(Mode.Off)) { Checked = true };
        _modeTo = new ToolStripMenuItem("Mode: Watch To-Codex", null, (_, _) => SetMode(Mode.To));
        _modeFrom = new ToolStripMenuItem("Mode: Watch From-Codex", null, (_, _) => SetMode(Mode.From));
        _modeBoth = new ToolStripMenuItem("Mode: Both", null, (_, _) => SetMode(Mode.Both));
        _toggleApi = new ToolStripMenuItem("Enable API send (default OFF)", null, OnToggleApi)
        {
            Checked = false,
            CheckOnClick = true
        };
        _statusItem = new ToolStripMenuItem("Status: (not checked)") { Enabled = false };
        _openDashboardItem = new ToolStripMenuItem("Open Dashboard (/bot/ui)", null, (_, _) => OpenDashboard());
        _automationsMenu = new ToolStripMenuItem("Automations (toggle)");
        _cancelJobItem = new ToolStripMenuItem("Cancel latest awaiting job", null, async (_, _) => await CancelLatestAsync());
        _settingsItem = new ToolStripMenuItem("Settings...", null, (_, _) => OpenSettings());

        _menu.Items.AddRange(new ToolStripItem[]
        {
            _modeOff, _modeTo, _modeFrom, _modeBoth,
            new ToolStripSeparator(),
            new ToolStripMenuItem("Copy latest prompt", null, (_, _) => CopyLatestPrompt()),
            new ToolStripMenuItem("Run handoff import", null, async (_, _) => await RunImportAsync()),
            new ToolStripMenuItem("Send latest prompt via API", null, async (_, _) => await SendLatestPromptAsync()),
            new ToolStripMenuItem("Open reports folder", null, (_, _) => OpenReports()),
            new ToolStripSeparator(),
            _openDashboardItem,
            _automationsMenu,
            _cancelJobItem,
            _settingsItem,
            new ToolStripSeparator(),
            _toggleApi,
            new ToolStripMenuItem("Check server status", null, async (_, _) => await PollOnceAsync(forceNotify:true)),
            _statusItem,
            new ToolStripSeparator(),
            new ToolStripMenuItem("Exit", null, (_, _) => ExitApplication())
        });

        _notifyIcon = new NotifyIcon
        {
            Icon = System.Drawing.SystemIcons.Application,
            Visible = true,
            ContextMenuStrip = _menu,
            Text = "HandoffTray (default OFF)"
        };

        _pollTimer = new System.Windows.Forms.Timer { Interval = 5000 };
        _pollTimer.Tick += async (_, _) => await PollOnceAsync();
        _pollTimer.Start();

        ShowInTaskbar = false;
        WindowState = FormWindowState.Minimized;
        Visible = false;
    }

    private void ExitApplication()
    {
        _notifyIcon.Visible = false;
        _pollTimer.Stop();
        _pollTimer.Dispose();
        _watcher.Dispose();
        Application.Exit();
    }

    private void SetMode(Mode mode)
    {
        _modeOff.Checked = mode == Mode.Off;
        _modeTo.Checked = mode == Mode.To;
        _modeFrom.Checked = mode == Mode.From;
        _modeBoth.Checked = mode == Mode.Both;

        var watchTo = mode is Mode.To or Mode.Both;
        var watchFrom = mode is Mode.From or Mode.Both;
        _watcher.SetEnabled(watchTo, watchFrom);
        _notifyIcon.Text = $"HandoffTray ({mode})";
        _log.Info($"Mode set to {mode}");
    }

    private void OnPromptDetected(object? sender, string path)
    {
        _notifyIcon.BalloonTipTitle = "HandoffTray";
        _notifyIcon.BalloonTipText = "New HANDOFF_TO_CODEX detected. Use tray menu to copy or send.";
        _notifyIcon.ShowBalloonTip(3000);
        _log.Info($"Prompt detected: {path}");
    }

    private void OnResultDetected(object? sender, string path)
    {
        _notifyIcon.BalloonTipTitle = "HandoffTray";
        _notifyIcon.BalloonTipText = "New RESULT.md detected. Run handoff import from tray menu.";
        _notifyIcon.ShowBalloonTip(3000);
        _log.Info($"Result detected: {path}");
    }

    private string ReportsDir => Path.Combine(_root, "artifacts", "handoff", "reports");

    private string? GetLatestFile(string dir)
    {
        if (!Directory.Exists(dir)) return null;
        var info = new DirectoryInfo(dir);
        return info.GetFiles("*", SearchOption.TopDirectoryOnly)
            .OrderByDescending(f => f.LastWriteTimeUtc)
            .FirstOrDefault()?.FullName;
    }

    private void CopyLatestPrompt()
    {
        var latest = GetLatestFile(Path.Combine(_root, "artifacts", "handoff", "to_codex"));
        if (latest == null)
        {
            MessageBox.Show("No prompt found in to_codex.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var text = File.ReadAllText(latest, Encoding.UTF8);
        Clipboard.SetText(text);
        MessageBox.Show("Copied latest HANDOFF_TO_CODEX to clipboard.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
        _log.Info($"Copied prompt: {latest}");
    }

    private async Task RunImportAsync()
    {
        try
        {
            Directory.CreateDirectory(ReportsDir);
            var psi = new ProcessStartInfo
            {
                FileName = "dotnet",
                Arguments = "run --project MaelstromToolkit/MaelstromToolkit.csproj -- handoff import --out artifacts/handoff/reports",
                WorkingDirectory = _root,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using var proc = Process.Start(psi);
            if (proc == null)
            {
                MessageBox.Show("Failed to start toolkit import.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Error);
                _log.Error("Toolkit import failed to start.");
                return;
            }
            await proc.WaitForExitAsync();
            var output = await proc.StandardOutput.ReadToEndAsync();
            var err = await proc.StandardError.ReadToEndAsync();
            if (proc.ExitCode != 0)
            {
                MessageBox.Show($"Import failed (exit {proc.ExitCode}).\n{output}\n{err}", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Error);
                _log.Error($"Import failed (exit {proc.ExitCode}). Output: {output} Err: {err}");
                return;
            }
            MessageBox.Show("Import completed. Check CODEX_REPORT.md in reports.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            _log.Info("Import completed successfully.");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Error);
            _log.Error($"Import exception: {ex}");
        }
    }

    private async Task SendLatestPromptAsync()
    {
        if (!_apiSendEnabled)
        {
            MessageBox.Show("API send is disabled. Toggle it on first.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var latest = GetLatestFile(Path.Combine(_root, "artifacts", "handoff", "to_codex"));
        if (latest == null)
        {
            MessageBox.Show("No prompt found in to_codex.", "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var text = File.ReadAllText(latest, Encoding.UTF8);
        var confirm = MessageBox.Show("Send the latest fenced block to OpenAI API?", "HandoffTray", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (confirm != DialogResult.Yes) return;

        try
        {
            var result = await _apiSender.SendAsync(text, "gpt-4o-mini", ReportsDir);
            if (result.Success)
            {
                MessageBox.Show(result.Message, "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Information);
                _log.Info($"API send success: {result.OutputPath}");
            }
            else
            {
                MessageBox.Show(result.Message, "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Error);
                _log.Error($"API send failed: {result.Message}");
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "HandoffTray", MessageBoxButtons.OK, MessageBoxIcon.Error);
            _log.Error($"API send exception: {ex}");
        }
    }

    private void OpenReports()
    {
        Directory.CreateDirectory(ReportsDir);
        Process.Start(new ProcessStartInfo
        {
            FileName = ReportsDir,
            UseShellExecute = true
        });
    }

    private void OnToggleApi(object? sender, EventArgs e)
    {
        _apiSendEnabled = _toggleApi.Checked;
        _notifyIcon.BalloonTipTitle = "HandoffTray";
        _notifyIcon.BalloonTipText = _apiSendEnabled ? "API send ENABLED (default was off)." : "API send DISABLED.";
        _notifyIcon.ShowBalloonTip(2000);
        _log.Info($"API send enabled: {_apiSendEnabled}");
    }

    private async Task PollOnceAsync(bool forceNotify = false)
    {
        if (DateTime.UtcNow < _nextRetryUtc) return;
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(4));
        try
        {
            var status = await _botApi.GetStatusAsync(cts.Token);
            var jobs = await _botApi.GetJobsAsync(limit: 5, cts.Token) ?? new List<JobDto>();

            var tip = status is null
                ? "Status unavailable"
                : $"Q={status.Queued} A={status.Awaiting} C={status.Completed} F={status.Failed}";
            _statusItem.Text = $"Status: {tip}";
            _notifyIcon.Text = $"HandoffTray ({tip})";

            await RefreshAutomationsAsync(cts.Token);
            MaybeNotify(jobs, forceNotify);

            _initialLoadDone = true;
            _nextRetryUtc = DateTime.UtcNow.AddSeconds(5);
        }
        catch (UnauthorizedAccessException)
        {
            _statusItem.Text = "Status: Unauthorized (set token)";
            _notifyIcon.Text = "HandoffTray (unauthorized)";
            _nextRetryUtc = DateTime.UtcNow.AddSeconds(30);
        }
        catch (Exception ex)
        {
            _statusItem.Text = "Status: offline";
            _notifyIcon.Text = "HandoffTray (server offline)";
            _log.Error($"Poll failed: {ex.Message}");
            _nextRetryUtc = DateTime.UtcNow.AddSeconds(15);
        }
    }

    private void MaybeNotify(List<JobDto> jobs, bool forceNotify)
    {
        if (jobs.Count == 0) return;
        var latest = jobs.OrderByDescending(j => j.UpdatedAtUtc).First();

        if (!_initialLoadDone && !forceNotify)
        {
            _lastNotifiedJobId = latest.JobId;
            return;
        }

        if (latest.Status.Equals("completed", StringComparison.OrdinalIgnoreCase) ||
            latest.Status.Equals("failed", StringComparison.OrdinalIgnoreCase))
        {
            if (_lastNotifiedJobId != latest.JobId)
            {
                var snippet = latest.ResultSnippet ?? latest.Error ?? "(no details)";
                if (snippet.Length > 120) snippet = snippet[..120] + "...";
                _notifyIcon.BalloonTipTitle = "MaelstromBot";
                _notifyIcon.BalloonTipText = $"{latest.Status}: {snippet}";
                _notifyIcon.ShowBalloonTip(2500);
                _lastNotifiedJobId = latest.JobId;
            }
        }
    }

    private async Task RefreshAutomationsAsync(CancellationToken ct)
    {
        try
        {
            var autos = await _botApi.GetAutomationsAsync(ct);
            if (autos is null) return;
            _automationsMenu.DropDownItems.Clear();
            foreach (var a in autos)
            {
                var item = new ToolStripMenuItem(a.Id)
                {
                    Checked = a.Enabled,
                    CheckOnClick = true
                };
                item.Click += async (_, _) =>
                {
                    try
                    {
                        await _botApi.SetAutomationAsync(a.Id, item.Checked, ct);
                    }
                    catch
                    {
                        item.Checked = !item.Checked;
                        _notifyIcon.BalloonTipTitle = "MaelstromBot";
                        _notifyIcon.BalloonTipText = "Failed to update automation (check token/role).";
                        _notifyIcon.ShowBalloonTip(2000);
                    }
                };
                _automationsMenu.DropDownItems.Add(item);
            }
        }
        catch
        {
            // ignore errors; will retry on next poll
        }
    }

    private async Task CancelLatestAsync()
    {
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        try
        {
            var jobs = await _botApi.GetJobsAsync(5, cts.Token);
            var job = jobs?.FirstOrDefault(j => j.Status.Equals("awaiting_openai", StringComparison.OrdinalIgnoreCase) || j.Status.Equals("running", StringComparison.OrdinalIgnoreCase));
            if (job == null)
            {
                _notifyIcon.BalloonTipTitle = "MaelstromBot";
                _notifyIcon.BalloonTipText = "No running/awaiting job to cancel.";
                _notifyIcon.ShowBalloonTip(2000);
                return;
            }

            var ok = await _botApi.CancelJobAsync(job.JobId, cts.Token);
            _notifyIcon.BalloonTipTitle = "MaelstromBot";
            _notifyIcon.BalloonTipText = ok ? "Cancel requested." : "Cancel failed.";
            _notifyIcon.ShowBalloonTip(2000);
        }
        catch (UnauthorizedAccessException)
        {
            _notifyIcon.BalloonTipTitle = "MaelstromBot";
            _notifyIcon.BalloonTipText = "Unauthorized (use admin token).";
            _notifyIcon.ShowBalloonTip(2000);
        }
        catch (Exception ex)
        {
            _notifyIcon.BalloonTipTitle = "MaelstromBot";
            _notifyIcon.BalloonTipText = "Cancel failed.";
            _notifyIcon.ShowBalloonTip(2000);
            _log.Error($"Cancel failed: {ex.Message}");
        }
    }

    private void OpenDashboard()
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = _settings.BaseUrl.TrimEnd('/') + "/bot/ui",
                UseShellExecute = true
            });
        }
        catch (Exception ex)
        {
            _log.Error($"Failed to open dashboard: {ex.Message}");
        }
    }

    private void OpenSettings()
    {
        using var f = new SettingsForm(_settings, _token);
        if (f.ShowDialog() != DialogResult.OK) return;

        _settings.BaseUrl = string.IsNullOrWhiteSpace(f.BaseUrl) ? _settings.BaseUrl : f.BaseUrl;
        SettingsStore.Save(_settings);
        _botApi.SetBaseUrl(_settings.BaseUrl);

        if (!string.IsNullOrWhiteSpace(f.Token))
        {
            _token = f.Token;
            TokenStore.Save(_token);
            _botApi.SetToken(_token);
        }

        _nextRetryUtc = DateTime.UtcNow;
    }

    private async Task PollOnceAsync()
    {
        await PollOnceAsync(forceNotify: false);
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _notifyIcon.Dispose();
            _pollTimer.Dispose();
            _watcher.Dispose();
        }
        base.Dispose(disposing);
    }
}

internal enum Mode
{
    Off,
    To,
    From,
    Both
}
