using ProjectMaelstrom.Models;
using ProjectMaelstrom.Utilities;
using Microsoft.VisualBasic;
using System.Threading.Tasks;

namespace ProjectMaelstrom;

public partial class ManageScriptsForm : Form
{
    private readonly ScriptLibraryService _service = ScriptLibraryService.Instance;
    private readonly BridgeCoordinator? _bridge;

    public ManageScriptsForm() : this(null)
    {
    }

    internal ManageScriptsForm(BridgeCoordinator? bridge = null)
    {
        _bridge = bridge;
        InitializeComponent();
        NormalizeSplitter();
    }

    private void NormalizeSplitter()
    {
        try
        {
            var min = Math.Max(1, splitContainer.Panel1MinSize);
            var max = Math.Max(min, Math.Max(1, splitContainer.Width - splitContainer.Panel2MinSize));
            var desired = splitContainer.SplitterDistance;
            var safe = Math.Clamp(desired, min, max);
            splitContainer.SplitterDistance = safe;
        }
        catch
        {
            // non-fatal for dev tools capture
        }
    }

    private void ManageScriptsForm_Load(object sender, EventArgs e)
    {
        ThemeManager.ApplyTheme(this);
        ApplyPalette();
        scriptListBox.SelectedIndexChanged += scriptListBox_SelectedIndexChanged;
        LoadScriptLibrary();
        UpdateScriptStatus();
        ApplyPolicyUiState();
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        UIStyles.ApplyCardStyle(this, palette.Surface, palette.Border);
        var buttons = new[]
        {
            runScriptButton, stopScriptButton, refreshScriptsButton, importFromGithubButton,
            updateScriptButton, removeScriptButton, loadLogButton, openScriptFolderButton,
            openLibraryRootButton, openFullLogButton, viewSourceButton
        };
        foreach (var btn in buttons)
        {
            UIStyles.ApplyButtonStyle(btn, palette.ControlBack, palette.ControlFore, palette.Border);
        }
        scriptListBox.BackColor = palette.ControlBack;
        scriptListBox.ForeColor = palette.ControlFore;
        logPreviewTextBox.BackColor = palette.ControlBack;
        logPreviewTextBox.ForeColor = palette.ControlFore;
    }

    private void LoadScriptLibrary()
    {
        _service.ReloadLibrary();
        var scripts = _service.Scripts
            .Where(s => !ShouldHideInPlayerMode(s))
            .ToList();
        scriptListBox.DisplayMember = nameof(ScriptDefinition.DisplayName);
        scriptListBox.ValueMember = nameof(ScriptDefinition.Manifest);
        scriptListBox.DataSource = scripts;
        var playerPreview = SettingsSafe.GetBool("PLAYER_PREVIEW_MODE", false);
        filterNoteLabel.Visible = playerPreview;
        filterNoteLabel.Text = playerPreview
            ? $"Player mode: showing {scripts.Count} items (reference/deprecated hidden)"
            : string.Empty;
    }

    private void ApplyPolicyUiState()
    {
        var policy = ExecutionPolicyManager.Current;
        if (!policy.AllowLiveAutomation)
        {
            runScriptButton.Enabled = false;
            stopScriptButton.Enabled = false;
            scriptStatusLabel.Text = "Status: Simulation only (live disabled)";
            simulationNoteLabel.Text = "Simulation only (live disabled)";
        }
        else
        {
            runScriptButton.Enabled = true;
            stopScriptButton.Enabled = true;
            simulationNoteLabel.Text = string.Empty;
        }
    }

    private void runScriptButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script to run.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        if (selected.ValidationErrors.Any())
        {
            MessageBox.Show(string.Join(Environment.NewLine, selected.ValidationErrors), "Script validation issues",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        if (!PassesPreflight(selected))
        {
            return;
        }

        try
        {
            if (_bridge != null)
            {
                if (!_bridge.TryStartScript(selected))
                {
                    return;
                }
            }
            else
            {
                _service.StartScript(selected);
            }
            UpdateScriptStatus();
        }
        catch (InvalidOperationException ex)
        {
            MessageBox.Show(ex.Message, "Blocked", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to start script: {ex.Message}", "Script Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private bool PassesPreflight(ScriptDefinition script)
    {
        var check = _service.PreflightCheck;
        if (check == null)
        {
            return true;
        }

        var result = check(script);
        if (result.Allowed)
        {
            return true;
        }

        var reason = string.IsNullOrWhiteSpace(result.Reason) ? "Start blocked by preflight." : result.Reason;
        var allowQueue = result.AutoQueued || reason.Contains("potion", StringComparison.OrdinalIgnoreCase);
        using var dlg = new PreflightDialog(reason, allowQueue);
        dlg.ShowDialog(this);
        if (allowQueue && dlg.QueueSelected)
        {
            _bridge?.EnqueuePotionRefill();
        }
        _bridge?.NotifyWarning(reason);
        return false;
    }

    private void stopScriptButton_Click(object sender, EventArgs e)
    {
        try
        {
            if (_bridge != null)
            {
                _bridge.StopCurrentScript();
            }
            else
            {
                _service.StopCurrentScript();
            }
            UpdateScriptStatus();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to stop script: {ex.Message}", "Script Stop Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void refreshScriptsButton_Click(object sender, EventArgs e)
    {
        LoadScriptLibrary();
        UpdateScriptStatus();
    }

    private async void updateScriptButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        Cursor = Cursors.WaitCursor;
        try
        {
            var updated = await _service.UpdateScriptAsync(selected);
            LoadScriptLibrary();
            if (updated != null)
            {
                scriptListBox.SelectedItem = _service.Scripts.FirstOrDefault(s => s.Manifest.Name == updated.Manifest.Name);
                MessageBox.Show($"Updated {updated.Manifest.Name}", "Update", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                MessageBox.Show("Update completed, but updated manifest not found.", "Update", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Update failed: {ex.Message}", "Update Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            Cursor = Cursors.Default;
        }
    }

    private void removeScriptButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var confirm = MessageBox.Show($"Remove {selected.Manifest.Name} from the library?", "Remove Script",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (confirm != DialogResult.Yes) return;

        try
        {
            _service.UninstallScript(selected);
            LoadScriptLibrary();
            UpdateScriptStatus();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to remove: {ex.Message}", "Remove Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private async void importFromGithubButton_Click(object sender, EventArgs e)
    {
        string input = Interaction.InputBox(
            "Enter a GitHub repo URL (e.g., https://github.com/user/repo) or a direct .zip URL. Branch/tag optional (default: main).",
            "Add from GitHub",
            "https://github.com/user/repo");

        if (string.IsNullOrWhiteSpace(input))
        {
            return;
        }

        string? branch = Interaction.InputBox(
            "Optional: specify branch or tag (leave blank for main).",
            "Branch/Tag",
            string.Empty);

        Cursor = Cursors.WaitCursor;
        try
        {
            var imported = await _service.ImportFromGitHubAsync(input, string.IsNullOrWhiteSpace(branch) ? null : branch);
            LoadScriptLibrary();
            UpdateScriptStatus();

            if (imported != null)
            {
                scriptListBox.SelectedItem = _service.Scripts.FirstOrDefault(s => s.Manifest.Name == imported.Manifest.Name);
                MessageBox.Show($"Imported {imported.Manifest.Name}", "GitHub Import", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                MessageBox.Show("Import completed, but manifest was not found. Verify the downloaded folder contains manifest.json.", "GitHub Import", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"GitHub import failed: {ex.Message}", "GitHub Import Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            Cursor = Cursors.Default;
        }
    }

    private void dryRunCheckBox_CheckedChanged(object sender, EventArgs e)
    {
        _service.DryRun = dryRunCheckBox.Checked;
        Logger.Log($"[ScriptLibrary] DryRun set to {dryRunCheckBox.Checked}");
    }

    private static bool ShouldHideInPlayerMode(ScriptDefinition script)
    {
        var playerPreview = SettingsSafe.GetBool("PLAYER_PREVIEW_MODE", false);
        if (!playerPreview)
        {
            return false;
        }

        var kind = GetScriptKind(script);
        return IsHiddenInPlayerPreview(kind);
    }

    private static string GetScriptKind(ScriptDefinition script)
    {
        if (!string.IsNullOrWhiteSpace(script.Manifest.Status))
        {
            return script.Manifest.Status;
        }

        if (IsReferenceName(script.Manifest.Name))
        {
            return "reference";
        }

        if (!string.IsNullOrWhiteSpace(script.Manifest.SourceUrl))
        {
            return "external";
        }

        return "native";
    }

    private static bool IsReferenceName(string name)
    {
        if (string.IsNullOrWhiteSpace(name)) return false;
        var n = name.ToLowerInvariant();
        return n.Contains("wizwalker") ||
               n.Contains("wizsdk") ||
               n.Contains("wizproxy") ||
               n.Contains("wizwiki") ||
               n.Contains("wizwad") ||
               n.Contains("wiz-packet") ||
               n.Contains("wad-reader") ||
               n.Contains("proto") ||
               n.Contains("sample") ||
               n.Contains("utilities") ||
               n.Contains("trivia") ||
               n.Contains("gallery");
    }

    private static bool IsHiddenInPlayerPreview(string kind)
    {
        if (string.IsNullOrWhiteSpace(kind)) return false;
        var k = kind.ToLowerInvariant();
        return k.Contains("deprecated") || k.Contains("reference");
    }

    private void loadLogButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        string logPath = GetScriptLogPath(selected.Manifest.Name);
        if (!File.Exists(logPath))
        {
            logPreviewTextBox.Text = "No log found for this script.";
            return;
        }

        try
        {
            var lines = File.ReadAllLines(logPath);
            var lastLines = lines.Reverse().Take(50).Reverse();
            logPreviewTextBox.Text = string.Join(Environment.NewLine, lastLines);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to load log: {ex.Message}", "Log Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void openScriptFolderButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            System.Diagnostics.Process.Start("explorer.exe", selected.RootPath);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to open folder: {ex.Message}", "Open Folder Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void openLibraryRootButton_Click(object sender, EventArgs e)
    {
        try
        {
            var path = StorageUtils.GetScriptLibraryPath();
            System.Diagnostics.Process.Start("explorer.exe", path);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to open library: {ex.Message}", "Open Library Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void openFullLogButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        string logPath = GetScriptLogPath(selected.Manifest.Name);
        if (!File.Exists(logPath))
        {
            MessageBox.Show("Log file not found for this script.", "Missing Log", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = logPath,
                UseShellExecute = true
            });
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to open log: {ex.Message}", "Open Log Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void viewSourceButton_Click(object sender, EventArgs e)
    {
        if (scriptListBox.SelectedItem is not ScriptDefinition selected)
        {
            MessageBox.Show("Select a script first.", "No Script Selected", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var url = selected.PackageInfo?.SourceUrl;
        if (string.IsNullOrWhiteSpace(url))
        {
            MessageBox.Show("No source URL recorded for this script.", "Source", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = url,
                UseShellExecute = true
            });
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to open source: {ex.Message}", "Source Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void scriptListBox_SelectedIndexChanged(object? sender, EventArgs e)
    {
        UpdateScriptStatus();
    }

    private void UpdateScriptStatus()
    {
        var running = _service.CurrentSession;
        scriptStatusLabel.Text = running == null
            ? "Status: Idle"
            : $"Running: {running.Script.Manifest.Name}";

        if (scriptListBox.SelectedItem is ScriptDefinition selected)
        {
            var src = selected.PackageInfo?.SourceUrl;
            sourceLabel.Text = string.IsNullOrWhiteSpace(src) ? "Source: -" : $"Source: {src}";
            var author = selected.Manifest.Author;
            authorLabel.Text = string.IsNullOrWhiteSpace(author) ? "Author: -" : $"Author: {author}";
        }
        else
        {
            sourceLabel.Text = "Source: -";
            authorLabel.Text = "Author: -";
        }
    }

    private static string GetScriptLogPath(string scriptName)
    {
        string sanitized = SanitizeFileName(scriptName);
        return Path.Combine(AppContext.BaseDirectory, "logs", $"{sanitized}.log");
    }

    private static string SanitizeFileName(string name)
    {
        foreach (char c in Path.GetInvalidFileNameChars())
        {
            name = name.Replace(c, '_');
        }
        return string.IsNullOrWhiteSpace(name) ? "script" : name;
    }
}
