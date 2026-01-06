using System.Linq;
using System.Diagnostics;
using System.IO;
using ProjectMaelstrom.Utilities;
using System.Threading.Tasks;
using Microsoft.VisualBasic;
using System.Net.Http;
using System.Text.Json;
using System.IO.Compression;
using ProjectMaelstrom.Utilities.Overlay;

namespace ProjectMaelstrom;

public partial class SettingsForm : Form
{
    private List<MinigameCatalogEntry> _minigameEntries = new();

    public SettingsForm()
    {
        InitializeComponent();
    }

    private void SettingsForm_Load(object sender, EventArgs e)
    {
        ocrSpaceApiKey.Text = SettingsSafe.GetString("OCR_SPACE_APIKEY", string.Empty);
        string storedTheme = SettingsSafe.GetString("THEME_MODE", "System");
        themeModeCombo.SelectedItem = themeModeCombo.Items.Cast<string>().FirstOrDefault(i =>
            i.Equals(storedTheme, StringComparison.OrdinalIgnoreCase)) ?? "System";
        captureToggle.Checked = SettingsSafe.GetBool("ENABLE_SCREEN_CAPTURE", false);
        audioToggle.Checked = SettingsSafe.GetBool("ENABLE_AUDIO_RECOGNIZER", false);
        tuningToggle.Checked = SettingsSafe.GetBool("ENABLE_SELF_TUNING", false);
        devTelemetryToggle.Checked = SettingsSafe.GetBool("ENABLE_DEV_TELEMETRY", false);
        devTelemetryToggle.Visible = DevMode.IsEnabled;
        devTelemetryToggle.Enabled = DevMode.IsEnabled;
        double delta = SettingsSafe.GetDouble("AUDIO_TRANSIENT_DELTA", 0.12);
        if (delta < 0.05 || delta > 0.5) delta = 0.12;
        audioDeltaNumeric.Value = (decimal)delta;
        feedUrlText.Text = SettingsSafe.GetString("UPDATE_FEED_URL", string.Empty);
        autoCheckUpdatesToggle.Checked = SettingsSafe.GetBool("AUTO_CHECK_UPDATES", false);
        updaterStatusLabel.Text = "Status: Idle";
        runDiagnosticsButton.Visible = DevMode.IsEnabled;
        viewDevSuggestionsButton.Visible = DevMode.IsEnabled;
        refreshWikiButton.Visible = true;
        refreshWikiButton.Enabled = true;
        devUiSnapshotsToggle.Checked = SettingsSafe.GetBool("ENABLE_DEV_UI_SNAPSHOTS", false);
        devUiSnapshotsToggle.Visible = DevMode.IsEnabled;
        devUiSnapshotsToggle.Enabled = DevMode.IsEnabled;
        captureUiSnapshotButton.Visible = DevMode.IsEnabled;
        playerPreviewToggle.Checked = SettingsSafe.GetBool("PLAYER_PREVIEW_MODE", false);
        playerPreviewToggle.Visible = DevMode.IsEnabled;
        playerPreviewToggle.Enabled = DevMode.IsEnabled;
        autoPauseToggle.Checked = Properties.Settings.Default.AUTO_PAUSE_ON_FOCUS_LOSS;
        goldMinNumeric.Value = SettingsSafe.GetInt("BAZAAR_GOLD_MIN", (int)goldMinNumeric.Minimum);
        goldCapNumeric.Value = SettingsSafe.GetInt("BAZAAR_GOLD_CAP", (int)goldCapNumeric.Minimum);
        // Policy view (read-only)
        var policy = ExecutionPolicyManager.Current;
        policyAllowLabel.Text = $"Allow Live: {policy.AllowLiveAutomation}";
        policyModeLabel.Text = $"Mode: {policy.Mode}";
        policyPathLabel.Text = $"Path: {ExecutionPolicyManager.PolicyPath}";
        policyLoadedLabel.Text = $"Loaded: {ExecutionPolicyManager.LoadedUtc:yyyy-MM-dd HH:mm:ss}Z";
        var backend = LiveBackendProvider.Current;
        var backendName = backend is NullLiveBackend ? "None installed" : backend.Name;
        policyBackendLabel.Text = $"Live backend: {backendName}";
        policyBackendIdLabel.Text = $"Backend ID: {backend.Id}";
        PopulatePlugins();
        PopulateReplays();
        PopulateOverlayWidgets();
        PopulateMinigames();

        // Apply system theme
        ThemeManager.ApplyTheme(this);
        ApplyPalette();

        _ = TryAutoCheckQuietAsync();
    }

    private void saveSettingsBtn_Click(object sender, EventArgs e)
    {
        Properties.Settings.Default["OCR_SPACE_APIKEY"] = ocrSpaceApiKey.Text;
        Properties.Settings.Default["GAME_RESOLUTION"] = selectedGameResolution.Text;
        Properties.Settings.Default["THEME_MODE"] = themeModeCombo.SelectedItem?.ToString() ?? "System";
        Properties.Settings.Default.ENABLE_SCREEN_CAPTURE = captureToggle.Checked;
        Properties.Settings.Default.ENABLE_AUDIO_RECOGNIZER = audioToggle.Checked;
        Properties.Settings.Default.ENABLE_SELF_TUNING = tuningToggle.Checked;
        Properties.Settings.Default.ENABLE_DEV_TELEMETRY = devTelemetryToggle.Checked;
        Properties.Settings.Default.ENABLE_DEV_UI_SNAPSHOTS = devUiSnapshotsToggle.Checked;
        Properties.Settings.Default.PLAYER_PREVIEW_MODE = playerPreviewToggle.Checked;
        Properties.Settings.Default.AUTO_PAUSE_ON_FOCUS_LOSS = autoPauseToggle.Checked;
        Properties.Settings.Default.BAZAAR_GOLD_MIN = (int)goldMinNumeric.Value;
        Properties.Settings.Default.BAZAAR_GOLD_CAP = (int)goldCapNumeric.Value;
        Properties.Settings.Default.AUDIO_TRANSIENT_DELTA = (double)audioDeltaNumeric.Value;
        Properties.Settings.Default.UPDATE_FEED_URL = feedUrlText.Text;
        Properties.Settings.Default.AUTO_CHECK_UPDATES = autoCheckUpdatesToggle.Checked;

        Properties.Settings.Default.Save();

        if (!StateManager.Instance.SetResolution(selectedGameResolution.Text))
        {
            MessageBox.Show($"Invalid resolution: {selectedGameResolution.Text}. Valid resolutions are: 1024x768, 1280x720, 2256x1504",
                "Invalid Resolution", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        ThemeManager.SetModeFromString(Properties.Settings.Default["THEME_MODE"]?.ToString());
        ThemeManager.ApplyTheme(Owner ?? this);

        this.Close();
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        var buttons = new[]
        {
            saveSettingsBtn, checkUpdatesButton, downloadUpdateButton, applyUpdateButton,
            launchManagerButton, openMapViewerButton, refreshWikiButton, runDiagnosticsButton, captureUiSnapshotButton, viewDevSuggestionsButton,
            openPluginsFolderButton, reloadPluginsButton, installSamplesButton, removeSamplesButton, installFromGithubButton,
            openReplaysFolderButton, refreshReplaysButton
        };
        foreach (var btn in buttons)
        {
            UIStyles.ApplyButtonStyle(btn, palette.ControlBack, palette.ControlFore, palette.Border);
        }
        UIStyles.ApplyButtonStyle(openPolicyFolderButton, palette.ControlBack, palette.ControlFore, palette.Border);

        var textBoxes = new[] { ocrSpaceApiKey, feedUrlText };
        foreach (var tb in textBoxes)
        {
            tb.BackColor = palette.ControlBack;
            tb.ForeColor = palette.ControlFore;
        }

        updaterStatusLabel.BackColor = palette.Surface;
        updaterStatusLabel.ForeColor = palette.Fore;
        selectedGameResolution.BackColor = palette.ControlBack;
        selectedGameResolution.ForeColor = palette.ControlFore;
        themeModeCombo.BackColor = palette.ControlBack;
        themeModeCombo.ForeColor = palette.ControlFore;
        goldMinNumeric.BackColor = palette.ControlBack;
        goldMinNumeric.ForeColor = palette.ControlFore;
        goldCapNumeric.BackColor = palette.ControlBack;
        goldCapNumeric.ForeColor = palette.ControlFore;
        pluginInstallStatusLabel.ForeColor = palette.Fore;
        replayDetailsBox.BackColor = palette.Surface;
        replayDetailsBox.ForeColor = palette.Fore;
        overlayStatusLabel.ForeColor = palette.Fore;
        overlayHostPanel.BackColor = palette.Surface;
        overlayListBox.BackColor = palette.ControlBack;
        overlayListBox.ForeColor = palette.ControlFore;
        minigameDetailsBox.BackColor = palette.Surface;
        minigameDetailsBox.ForeColor = palette.Fore;
        minigameCategoryFilter.BackColor = palette.ControlBack;
        minigameCategoryFilter.ForeColor = palette.ControlFore;
        minigameStatusFilter.BackColor = palette.ControlBack;
        minigameStatusFilter.ForeColor = palette.ControlFore;
    }

    private void openPolicyFolderButton_Click(object sender, EventArgs e)
    {
        try
        {
            var path = ExecutionPolicyManager.PolicyPath;
            var folder = Path.GetDirectoryName(path);
            if (folder != null && Directory.Exists(folder))
            {
                Process.Start("explorer.exe", folder);
            }
            else
            {
                MessageBox.Show("Policy folder not found.", "Policy", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Unable to open policy folder: {ex.Message}", "Policy", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private async void installFromGithubButton_Click(object sender, EventArgs e)
    {
        using var dialog = new Form
        {
            Text = "Install from GitHub Release",
            StartPosition = FormStartPosition.CenterParent,
            Size = new Size(640, 220),
            MinimumSize = new Size(640, 220),
            FormBorderStyle = FormBorderStyle.FixedDialog,
            MaximizeBox = false,
            MinimizeBox = false,
            Padding = new Padding(12)
        };

        var label = new Label
        {
            Text = "GitHub Release Asset ZIP URL:",
            AutoSize = true,
            Location = new Point(12, 12),
            MaximumSize = new Size(600, 0),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        };

        var text = new TextBox
        {
            Location = new Point(12, 40),
            Width = dialog.ClientSize.Width - 24,
            Text = "https://github.com/owner/repo/releases/download/v1.0/asset.zip",
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
            MinimumSize = new Size(480, 27)
        };

        var buttonY = dialog.ClientSize.Height - 60;
        var installBtn = new Button
        {
            Text = "Install",
            DialogResult = DialogResult.OK,
            Location = new Point(dialog.ClientSize.Width - 200, buttonY),
            Width = 90,
            Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        };
        var cancelBtn = new Button
        {
            Text = "Cancel",
            DialogResult = DialogResult.Cancel,
            Location = new Point(dialog.ClientSize.Width - 100, buttonY),
            Width = 90,
            Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        };
        dialog.Controls.Add(label);
        dialog.Controls.Add(text);
        dialog.Controls.Add(installBtn);
        dialog.Controls.Add(cancelBtn);
        dialog.AcceptButton = installBtn;
        dialog.CancelButton = cancelBtn;

        if (dialog.ShowDialog(this) != DialogResult.OK) return;

        var url = text.Text?.Trim() ?? string.Empty;
        if (!IsValidGithubReleaseUrl(url))
        {
            pluginInstallStatusLabel.Text = "Invalid GitHub release URL.";
            return;
        }

        installFromGithubButton.Enabled = false;
        pluginInstallStatusLabel.Text = "Downloading...";
        try
        {
            var tempZip = Path.Combine(Path.GetTempPath(), $"maelstrom_plugin_{Guid.NewGuid():N}.zip");
            using (var client = new HttpClient())
            using (var resp = await client.GetAsync(url))
            {
                if (!resp.IsSuccessStatusCode)
                {
                    pluginInstallStatusLabel.Text = $"Download failed: {resp.StatusCode}";
                    installFromGithubButton.Enabled = true;
                    return;
                }

                await using (var fs = File.Create(tempZip))
                {
                    await resp.Content.CopyToAsync(fs);
                }
            }

            var staging = Path.Combine(Path.GetTempPath(), $"maelstrom_plugin_stage_{Guid.NewGuid():N}");
            Directory.CreateDirectory(staging);
            ZipFile.ExtractToDirectory(tempZip, staging);

            var manifestPath = Directory.GetFiles(staging, "plugin.manifest.json", SearchOption.AllDirectories).FirstOrDefault();
            if (manifestPath == null)
            {
                pluginInstallStatusLabel.Text = "Manifest not found in ZIP.";
                SafeCleanup(tempZip, staging);
                installFromGithubButton.Enabled = true;
                return;
            }

            var manifest = JsonDocument.Parse(File.ReadAllText(manifestPath));
            if (!manifest.RootElement.TryGetProperty("pluginId", out var idProp) || string.IsNullOrWhiteSpace(idProp.GetString()))
            {
                pluginInstallStatusLabel.Text = "Manifest missing pluginId.";
                SafeCleanup(tempZip, staging);
                installFromGithubButton.Enabled = true;
                return;
            }

            var pluginId = idProp.GetString()!;
            var destRoot = PluginLoader.PluginRoot;
            var dest = Path.Combine(destRoot, pluginId);

            if (Directory.Exists(dest))
            {
                var prompt = MessageBox.Show($"Plugin '{pluginId}' already exists. Replace?", "Replace Plugin", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (prompt != DialogResult.Yes)
                {
                    SafeCleanup(tempZip, staging);
                    installFromGithubButton.Enabled = true;
                    pluginInstallStatusLabel.Text = "Install canceled.";
                    return;
                }
                Directory.Delete(dest, true);
            }

            Directory.CreateDirectory(destRoot);
            // Normalize manifest to root
            File.Copy(manifestPath, Path.Combine(staging, "plugin.manifest.json"), true);
            // Move staging to destination
            CopyDirectory(staging, dest);

            PluginLoader.Reload();
            PopulatePlugins();
            pluginInstallStatusLabel.Text = $"Installed {pluginId}.";
            SafeCleanup(tempZip, staging);
        }
        catch (Exception ex)
        {
            pluginInstallStatusLabel.Text = $"Install failed: {ex.Message}";
        }
        finally
        {
            installFromGithubButton.Enabled = true;
        }
    }

    private bool IsValidGithubReleaseUrl(string url)
    {
        if (string.IsNullOrWhiteSpace(url)) return false;
        if (!url.StartsWith("https://github.com/", StringComparison.OrdinalIgnoreCase)) return false;
        if (!url.Contains("/releases/download/")) return false;
        if (!url.EndsWith(".zip", StringComparison.OrdinalIgnoreCase)) return false;
        return true;
    }

    private void SafeCleanup(string tempZip, string staging)
    {
        try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { }
        try { if (Directory.Exists(staging)) Directory.Delete(staging, true); } catch { }
    }

    private void CopyDirectory(string sourceDir, string destDir)
    {
        foreach (var dirPath in Directory.GetDirectories(sourceDir, "*", SearchOption.AllDirectories))
        {
            var target = dirPath.Replace(sourceDir, destDir);
            Directory.CreateDirectory(target);
        }

        foreach (var filePath in Directory.GetFiles(sourceDir, "*", SearchOption.AllDirectories))
        {
            var target = filePath.Replace(sourceDir, destDir);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(filePath, target, true);
        }
    }
    private async Task TryAutoCheckQuietAsync()
    {
        if (!Properties.Settings.Default.AUTO_CHECK_UPDATES)
        {
            return;
        }

        var feed = Properties.Settings.Default.UPDATE_FEED_URL;
        if (string.IsNullOrWhiteSpace(feed))
        {
            updaterStatusLabel.Text = "Status: Set update feed to enable auto-check.";
            return;
        }

        try
        {
            updaterStatusLabel.Text = "Status: Checking...";
            var manifest = await UpdaterService.Instance.CheckForUpdateAsync(feed);
            if (manifest == null || string.IsNullOrWhiteSpace(manifest.Version))
            {
                updaterStatusLabel.Text = "Status: Feed unreachable; enter URL manually.";
                feedUrlText.Focus();
                return;
            }

            if (!Version.TryParse(Application.ProductVersion, out var current) ||
                !Version.TryParse(manifest.Version, out var latest))
            {
                updaterStatusLabel.Text = $"Status: Latest {manifest.Version}";
                return;
            }

            if (latest > current)
            {
                updaterStatusLabel.Text = $"Status: Update available ({current} → {latest})";
            }
            else
            {
                updaterStatusLabel.Text = $"Status: Up to date ({current})";
            }
        }
        catch
        {
            updaterStatusLabel.Text = "Status: Auto-check failed; enter feed manually.";
            feedUrlText.Focus();
        }
    }

    private void PopulatePlugins()
    {
        try
        {
            pluginListView.Items.Clear();
            foreach (var p in PluginLoader.Current)
            {
                var caps = p.Capabilities != null && p.Capabilities.Any()
                    ? string.Join(", ", p.Capabilities)
                    : "None";
                var status = p.Status.ToString();
                var reason = string.IsNullOrWhiteSpace(p.Reason) ? status : p.Reason;
                var item = new ListViewItem(new[]
                {
                    string.IsNullOrWhiteSpace(p.Name) ? p.PluginId : p.Name,
                    p.Version,
                    caps,
                    status,
                    reason
                });
                item.UseItemStyleForSubItems = true;
                if (p.Status == PluginStatus.Allowed)
                {
                    item.ForeColor = Color.LightGreen;
                }
                else if (p.Status == PluginStatus.Blocked)
                {
                    item.ForeColor = Color.Goldenrod;
                }
                else
                {
                    item.ForeColor = Color.IndianRed;
                }
                if (item.SubItems.Count > 4)
                {
                    item.SubItems[4].ForeColor = Color.Silver;
                }
                pluginListView.Items.Add(item);
            }
            if (pluginListView.Items.Count == 0)
            {
                pluginListView.Items.Add(new ListViewItem(new[] { "No plugins installed", "-", "-", "-", "-" }));
            }
        }
        catch (Exception ex)
        {
            pluginListView.Items.Clear();
            pluginListView.Items.Add(new ListViewItem(new[] { "Error", "-", "-", "-", ex.Message }));
        }
    }

    private void openPluginsFolderButton_Click(object sender, EventArgs e)
    {
        try
        {
            var folder = PluginLoader.PluginRoot;
            Directory.CreateDirectory(folder);
            Process.Start("explorer.exe", folder);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Unable to open plugins folder: {ex.Message}", "Plugins", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void reloadPluginsButton_Click(object sender, EventArgs e)
    {
        PluginLoader.Reload();
        PopulatePlugins();
        PopulateOverlayWidgets();
        PopulateMinigames();
    }

    private void PopulateReplays()
    {
        try
        {
            replayListView.Items.Clear();
            foreach (var path in ReplayLogger.ListReplays())
            {
                var name = Path.GetFileName(path);
                var date = File.GetLastWriteTime(path).ToString("yyyy-MM-dd HH:mm");
                var item = new ListViewItem(new[] { name, date }) { Tag = path };
                replayListView.Items.Add(item);
            }
            if (replayListView.Items.Count == 0)
            {
                replayListView.Items.Add(new ListViewItem(new[] { "No replays found", "-" }));
            }
        }
        catch (Exception ex)
        {
            replayListView.Items.Clear();
            replayListView.Items.Add(new ListViewItem(new[] { "Error", ex.Message }));
        }
    }

    private void replayListView_SelectedIndexChanged(object sender, EventArgs e)
    {
        try
        {
            if (replayListView.SelectedItems.Count == 0 || replayListView.SelectedItems[0].Tag is not string path)
            {
                replayDetailsBox.Text = string.Empty;
                return;
            }

            var lines = ReplayLogger.ReadTail(path, 40);
            replayDetailsBox.Text = string.Join(Environment.NewLine, lines);
        }
        catch (Exception ex)
        {
            replayDetailsBox.Text = $"Error reading replay: {ex.Message}";
        }
    }

    private void openReplaysFolderButton_Click(object sender, EventArgs e)
    {
        try
        {
            var folder = ReplayLogger.ReplayRoot;
            Directory.CreateDirectory(folder);
            Process.Start("explorer.exe", folder);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Unable to open replays folder: {ex.Message}", "Replays", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void refreshReplaysButton_Click(object sender, EventArgs e)
    {
        PopulateReplays();
    }

    private void installSamplesButton_Click(object sender, EventArgs e)
        {
            try
            {
                var samplesRoot = PluginSamples.SamplesRoot;
                Directory.CreateDirectory(samplesRoot);

            WriteSampleManifest(
                Path.Combine(samplesRoot, PluginSamples.SampleOverlayId, "plugin.manifest.json"),
                PluginSamples.SampleOverlayId,
                "Sample Overlay",
                new[] { PluginCapability.OverlayWidgets.ToString() },
                "Public");

            WriteSampleManifest(
                Path.Combine(samplesRoot, PluginSamples.SampleLiveIntegrationId, "plugin.manifest.json"),
                PluginSamples.SampleLiveIntegrationId,
                "Sample Live Integration",
                new[] { PluginCapability.LiveIntegration.ToString() },
                "Experimental");

            WriteSampleManifest(
                Path.Combine(samplesRoot, PluginSamples.SampleOverlayWidgetsId, "plugin.manifest.json"),
                PluginSamples.SampleOverlayWidgetsId,
                "Sample Overlay Widgets",
                new[] { PluginCapability.OverlayWidgets.ToString() },
                "Public");

            WriteSampleManifest(
                Path.Combine(samplesRoot, PluginSamples.SampleMinigameCatalogId, "plugin.manifest.json"),
                PluginSamples.SampleMinigameCatalogId,
                "Sample Minigame Catalog",
                new[] { PluginCapability.MinigameCatalog.ToString() },
                "Public");

            WriteSampleMinigameCatalog(Path.Combine(samplesRoot, PluginSamples.SampleMinigameCatalogId, "minigames.catalog.json"));

            PluginLoader.Reload();
            MinigameCatalogRegistry.Reload();
            PopulatePlugins();
            PopulateOverlayWidgets();
            PopulateMinigames();
            MessageBox.Show("Sample plugins installed (manifest-only). Reloaded plugin list.", "Plugins", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to install sample plugins: {ex.Message}", "Plugins", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void removeSamplesButton_Click(object sender, EventArgs e)
    {
        try
        {
            var samplesRoot = PluginSamples.SamplesRoot;
            var sampleDirs = new[]
            {
                Path.Combine(samplesRoot, PluginSamples.SampleOverlayId),
                Path.Combine(samplesRoot, PluginSamples.SampleLiveIntegrationId),
                Path.Combine(samplesRoot, PluginSamples.SampleOverlayWidgetsId),
                Path.Combine(samplesRoot, PluginSamples.SampleMinigameCatalogId)
            };
            foreach (var dir in sampleDirs)
            {
                if (Directory.Exists(dir))
                {
                    Directory.Delete(dir, true);
                }
            }
            PluginLoader.Reload();
            MinigameCatalogRegistry.Reload();
            PopulatePlugins();
            PopulateOverlayWidgets();
            PopulateMinigames();
            MessageBox.Show("Sample plugins removed.", "Plugins", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to remove sample plugins: {ex.Message}", "Plugins", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void WriteSampleManifest(string manifestPath, string id, string name, IEnumerable<string> capabilities, string requiredProfile)
    {
        var targetDir = Path.GetDirectoryName(manifestPath)!;
        Directory.CreateDirectory(targetDir);
        if (File.Exists(manifestPath))
        {
            return; // do not overwrite existing
        }

        var manifest = new
        {
            pluginId = id,
            name = name,
            version = "1.0.0",
            targetAppVersion = "any",
            requiredProfile = requiredProfile,
            declaredCapabilities = capabilities.ToArray()
        };

        var json = System.Text.Json.JsonSerializer.Serialize(manifest, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(manifestPath, json);
    }

    private void WriteSampleMinigameCatalog(string catalogPath)
    {
        var targetDir = Path.GetDirectoryName(catalogPath)!;
        Directory.CreateDirectory(targetDir);
        if (File.Exists(catalogPath))
        {
            return;
        }

        var entries = new[]
        {
            new MinigameCatalogEntry
            {
                Id = "pet-dance",
                Name = "Pet Dance",
                Category = MinigameCategory.Pet,
                Status = MinigameStatus.Planned,
                Description = "Future pet mini dance game concept (catalog only).",
                Tags = new[] { "pet", "rhythm" },
                Notes = "Catalog entry only. No gameplay implemented."
            },
            new MinigameCatalogEntry
            {
                Id = "potion-refill",
                Name = "Potion Refill",
                Category = MinigameCategory.Potion,
                Status = MinigameStatus.Planned,
                Description = "Potion refill minigame goal; track requirements for future build.",
                Tags = new[] { "potion", "timing" },
                Requirements = "Needs potion station assets.",
                Notes = "Declarative listing only."
            },
            new MinigameCatalogEntry
            {
                Id = "gardening-cycle",
                Name = "Gardening",
                Category = MinigameCategory.Gardening,
                Status = MinigameStatus.Planned,
                Description = "Gardening helper minigame concept for future iteration.",
                Tags = new[] { "gardening", "loop" }
            },
            new MinigameCatalogEntry
            {
                Id = "crafting-puzzle",
                Name = "Crafting Puzzle",
                Category = MinigameCategory.Other,
                Status = MinigameStatus.Planned,
                Description = "Placeholder crafting puzzle idea; serves as catalog example.",
                Tags = new[] { "crafting", "puzzle" },
                Notes = "Demo entry in sample catalog."
            }
        };

        var json = System.Text.Json.JsonSerializer.Serialize(entries, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(catalogPath, json);
    }

    private async void checkUpdatesButton_Click(object sender, EventArgs e)
    {
        updaterStatusLabel.Text = "Status: Checking...";
        var manifest = await UpdaterService.Instance.CheckForUpdateAsync(feedUrlText.Text);
        if (manifest == null)
        {
            updaterStatusLabel.Text = "Status: No update or invalid feed.";
            return;
        }

        var change = string.IsNullOrWhiteSpace(manifest.Changelog) ? "No changelog." : manifest.Changelog;
        updaterStatusLabel.Text = $"Status: Found {manifest.Version}";
        MessageBox.Show($"Latest version: {manifest.Version}\n{change}", "Update Check",
            MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private async void downloadUpdateButton_Click(object sender, EventArgs e)
    {
        updaterStatusLabel.Text = "Status: Downloading...";
        var path = await UpdaterService.Instance.DownloadPackageAsync();
        if (path == null)
        {
            updaterStatusLabel.Text = "Status: Download failed.";
            return;
        }
        updaterStatusLabel.Text = $"Status: Downloaded to temp";
    }

    private void applyUpdateButton_Click(object sender, EventArgs e)
    {
        var staged = UpdaterService.Instance.StagePackage();
        if (staged == null)
        {
            updaterStatusLabel.Text = "Status: Stage failed.";
            return;
        }
        if (UpdaterService.Instance.MarkApplyPending())
        {
            updaterStatusLabel.Text = "Status: Pending apply on restart.";
            PromptForRestartLoop();
        }
        else
        {
            updaterStatusLabel.Text = "Status: Apply mark failed.";
        }
    }

    private async void PromptForRestartLoop()
    {
        while (true)
        {
            var result = MessageBox.Show(
                "An update is ready. Apply and restart now?",
                "Update Ready",
                MessageBoxButtons.YesNoCancel,
                MessageBoxIcon.Question,
                MessageBoxDefaultButton.Button1);

            if (result == DialogResult.Yes)
            {
                Application.Restart();
                return;
            }

            if (result == DialogResult.Cancel)
            {
                updaterStatusLabel.Text = "Status: Update deferred until next restart.";
                return;
            }

            // Delay option selected
            string input = Interaction.InputBox("Enter delay in minutes before re-prompting:", "Delay Restart", "5");
            if (!int.TryParse(input, out int minutes) || minutes <= 0) minutes = 5;
            updaterStatusLabel.Text = $"Status: Will re-prompt in {minutes} minutes.";
            await Task.Delay(TimeSpan.FromMinutes(minutes));
            // loop to re-prompt
        }
    }

    private void launchManagerButton_Click(object sender, EventArgs e)
    {
        try
        {
            var appRoot = StorageUtils.GetAppRoot();
            var candidates = new[]
            {
                Path.Combine(appRoot, "Installer.exe"),
                Path.Combine(appRoot, "Installer", "Installer.exe"),
                Path.Combine(appRoot, "Installer", "publish", "Installer.exe"),
                Path.GetFullPath(Path.Combine(appRoot, "..", "Installer", "publish", "Installer.exe"))
            };

            var exe = candidates.FirstOrDefault(File.Exists);
            if (exe == null)
        {
            updaterStatusLabel.Text = "Status: Project Manager not found. Reinstall or download installer.";
            MessageBox.Show("Project Manager (Installer) not found near the app. Please reinstall or download the installer package.", "Not Found",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

            Process.Start(new ProcessStartInfo
            {
                FileName = exe,
                UseShellExecute = true,
                WorkingDirectory = Path.GetDirectoryName(exe)!
            });
            updaterStatusLabel.Text = "Status: Project Manager launched.";
        }
        catch (Exception ex)
        {
            updaterStatusLabel.Text = "Status: Failed to launch Project Manager.";
            MessageBox.Show($"Failed to launch Project Manager: {ex.Message}", "Launch Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void openMapViewerButton_Click(object sender, EventArgs e)
    {
        try
        {
            using var viewer = new MapViewerForm
            {
                StartPosition = FormStartPosition.CenterParent,
                TopMost = true
            };
            viewer.ShowDialog(this);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to open map viewer: {ex.Message}", "Map Viewer", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private async void runDiagnosticsButton_Click(object sender, EventArgs e)
    {
        if (!DevMode.IsEnabled)
        {
            MessageBox.Show("Diagnostics are available only in dev mode.", "Dev Mode Required", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        runDiagnosticsButton.Enabled = false;
        updaterStatusLabel.Text = "Status: Running diagnostics...";
        try
        {
            var report = await DiagnosticsService.RunBasicAsync();
            updaterStatusLabel.Text = "Status: Diagnostics complete.";
            MessageBox.Show(report, "Diagnostics", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            updaterStatusLabel.Text = "Status: Diagnostics failed.";
            MessageBox.Show($"Diagnostics failed: {ex.Message}", "Diagnostics Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            runDiagnosticsButton.Enabled = true;
        }
    }

    private void captureUiSnapshotButton_Click(object sender, EventArgs e)
    {
        if (!DevMode.IsEnabled)
        {
            MessageBox.Show("UI capture is available only in dev mode.", "Dev Mode Required", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var target = Owner ?? this;
        UiSnapshotService.TryCapture(target, "manual");
        MessageBox.Show("UI snapshot captured to logs/dev.", "Snapshot", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private void viewDevSuggestionsButton_Click(object sender, EventArgs e)
    {
        if (!DevMode.IsEnabled)
        {
            MessageBox.Show("Dev suggestions are available only in dev mode.", "Dev Mode Required", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            var dir = Path.Combine(AppContext.BaseDirectory, "logs", "dev");
            if (!Directory.Exists(dir))
            {
                MessageBox.Show("No dev logs found yet.", "Dev Suggestions", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var latest = Directory.GetFiles(dir, "ui_*.json")
                .OrderByDescending(File.GetLastWriteTimeUtc)
                .FirstOrDefault();

            if (latest == null)
            {
                MessageBox.Show("No UI suggestion logs found. Capture a UI snapshot first.", "Dev Suggestions", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var json = File.ReadAllText(latest);
            var doc = System.Text.Json.JsonDocument.Parse(json);
            var issues = doc.RootElement.TryGetProperty("Issues", out var issuesEl) && issuesEl.ValueKind == System.Text.Json.JsonValueKind.Array
                ? string.Join(Environment.NewLine, issuesEl.EnumerateArray().Select(i => i.GetString()).Where(s => !string.IsNullOrWhiteSpace(s)))
                : "No issues recorded.";

            MessageBox.Show($"Latest: {Path.GetFileName(latest)}\n\n{issues}", "Dev Suggestions", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to load suggestions: {ex.Message}", "Dev Suggestions", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void refreshWikiButton_Click(object sender, EventArgs e)
    {
        try
        {
            WizWikiDataService.Instance.Refresh();
            updaterStatusLabel.Text = $"Status: Wiki cache refreshed ({WizWikiDataService.Instance.ZoneCount} zones, {WizWikiDataService.Instance.ResourceCount} resources)";
        }
        catch (Exception ex)
        {
            updaterStatusLabel.Text = "Status: Wiki refresh failed.";
            MessageBox.Show($"Failed to refresh wiki cache: {ex.Message}", "Wiki Refresh", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    public void RefreshPluginListSafe()
    {
        try
        {
            PluginLoader.Reload();
            PopulatePlugins();
            PopulateOverlayWidgets();
        }
        catch
        {
            // best effort; ignore
        }
    }

    private void PopulateOverlayWidgets()
    {
        try
        {
            overlayHostPanel.Controls.Clear();
            overlayListBox.Items.Clear();
            var widgets = OverlayWidgetRegistry.Current;
            if (widgets.Count == 0)
            {
                overlayHostPanel.Visible = false;
                overlayListBox.Visible = false;
                overlayEmptyLabel.Visible = true;
                overlayStatusLabel.Text = "No overlay widgets installed.";
                return;
            }

            overlayEmptyLabel.Visible = false;
            overlayHostPanel.Visible = true;
            overlayListBox.Visible = true;

            foreach (var widget in widgets)
            {
                overlayListBox.Items.Add(widget.Title);
            }

            if (overlayListBox.Items.Count > 0)
            {
                overlayListBox.SelectedIndex = 0;
            }

            OverlaySnapshotHub.SnapshotUpdated -= OverlaySnapshotHub_SnapshotUpdated;
            OverlaySnapshotHub.SnapshotUpdated += OverlaySnapshotHub_SnapshotUpdated;
            OverlaySnapshotHub.SetExecutorStatus(OverlaySnapshotHub.Current.LastExecutorStatus);
        }
        catch (Exception ex)
        {
            overlayHostPanel.Controls.Clear();
            overlayHostPanel.Visible = false;
            overlayListBox.Visible = false;
            overlayEmptyLabel.Visible = true;
            overlayEmptyLabel.Text = $"Unable to load overlay widgets: {ex.Message}";
        }
    }

    private void OverlaySnapshotHub_SnapshotUpdated(OverlayStateSnapshot snapshot)
    {
        try
        {
            if (overlayListBox.SelectedIndex < 0) return;
            var widgets = OverlayWidgetRegistry.Current;
            if (overlayListBox.SelectedIndex >= widgets.Count) return;
            var widget = widgets[overlayListBox.SelectedIndex];
            var ctrl = overlayHostPanel.Controls.OfType<Control>().FirstOrDefault();
            widget.Update(snapshot);
            overlayStatusLabel.Text = $"Profile: {snapshot.Profile} | Mode: {snapshot.Mode} | Live: {snapshot.AllowLiveAutomation}";
        }
        catch
        {
            // ignore
        }
    }

    private void overlayListBox_SelectedIndexChanged(object sender, EventArgs e)
    {
        try
        {
            overlayHostPanel.Controls.Clear();
            var widgets = OverlayWidgetRegistry.Current;
            if (overlayListBox.SelectedIndex < 0 || overlayListBox.SelectedIndex >= widgets.Count) return;
            var widget = widgets[overlayListBox.SelectedIndex];
            var ctrl = widget.CreateControl();
            overlayHostPanel.Controls.Add(ctrl);
            widget.Update(OverlaySnapshotHub.Current);
            overlayStatusLabel.Text = $"Profile: {OverlaySnapshotHub.Current.Profile} | Mode: {OverlaySnapshotHub.Current.Mode} | Live: {OverlaySnapshotHub.Current.AllowLiveAutomation}";
        }
        catch
        {
            // ignore
        }
    }

    private void PopulateMinigames()
    {
        try
        {
            MinigameCatalogRegistry.Reload();
            _minigameEntries = MinigameCatalogRegistry.Current.ToList();

            // filters: populate combos once
            if (minigameCategoryFilter.Items.Count == 0)
            {
                minigameCategoryFilter.Items.Add("All");
                foreach (var cat in Enum.GetNames(typeof(MinigameCategory)))
                {
                    minigameCategoryFilter.Items.Add(cat);
                }
                minigameCategoryFilter.SelectedIndex = 0;
            }
            if (minigameStatusFilter.Items.Count == 0)
            {
                minigameStatusFilter.Items.Add("All");
                foreach (var st in Enum.GetNames(typeof(MinigameStatus)))
                {
                    minigameStatusFilter.Items.Add(st);
                }
                minigameStatusFilter.SelectedIndex = 0;
            }

            ApplyMinigameFilters();
        }
        catch (Exception ex)
        {
            minigameListView.Items.Clear();
            minigameListView.Items.Add(new ListViewItem(new[] { "Error loading catalog", ex.Message, "-", "-", "-" }));
            minigameDetailsBox.Text = $"Error: {ex.Message}";
        }
    }

    private void ApplyMinigameFilters()
    {
        minigameListView.Items.Clear();
        IEnumerable<MinigameCatalogEntry> filtered = _minigameEntries;

        if (minigameCategoryFilter.SelectedIndex > 0)
        {
            var selected = minigameCategoryFilter.SelectedItem?.ToString();
            if (Enum.TryParse<MinigameCategory>(selected, out var cat))
            {
                filtered = filtered.Where(e => e.Category == cat);
            }
        }

        if (minigameStatusFilter.SelectedIndex > 0)
        {
            var selected = minigameStatusFilter.SelectedItem?.ToString();
            if (Enum.TryParse<MinigameStatus>(selected, out var status))
            {
                filtered = filtered.Where(e => e.Status == status);
            }
        }

        foreach (var entry in filtered)
        {
            var tags = entry.Tags != null && entry.Tags.Length > 0
                ? string.Join(", ", entry.Tags)
                : "-";
            var item = new ListViewItem(new[]
            {
                entry.Name,
                entry.Category.ToString(),
                entry.Status.ToString(),
                tags,
                string.IsNullOrWhiteSpace(entry.SourcePluginId) ? "-" : entry.SourcePluginId
            })
            { Tag = entry };
            minigameListView.Items.Add(item);
        }

        if (minigameListView.Items.Count == 0)
        {
            minigameListView.Items.Add(new ListViewItem(new[] { "No minigame catalogs found", "-", "-", "-", "-" }));
            minigameDetailsBox.Text = string.Empty;
            return;
        }

        if (minigameListView.Items[0].Tag is MinigameCatalogEntry)
        {
            minigameListView.Items[0].Selected = true;
        }
    }

    private void minigameListView_SelectedIndexChanged(object sender, EventArgs e)
    {
        if (minigameListView.SelectedItems.Count == 0 || minigameListView.SelectedItems[0].Tag is not MinigameCatalogEntry entry)
        {
            minigameDetailsBox.Text = string.Empty;
            return;
        }

        var details = new List<string>
        {
            $"Plugin: {entry.SourcePluginId}",
            $"Description: {entry.Description}"
        };

        if (!string.IsNullOrWhiteSpace(entry.Requirements))
        {
            details.Add($"Requirements: {entry.Requirements}");
        }
        if (!string.IsNullOrWhiteSpace(entry.Notes))
        {
            details.Add($"Notes: {entry.Notes}");
        }
        if (!string.IsNullOrWhiteSpace(entry.Provenance))
        {
            details.Add($"Provenance: {entry.Provenance}");
        }

        minigameDetailsBox.Text = string.Join(Environment.NewLine + Environment.NewLine, details);
    }

    private void minigameCategoryFilter_SelectedIndexChanged(object sender, EventArgs e)
    {
        ApplyMinigameFilters();
    }

    private void minigameStatusFilter_SelectedIndexChanged(object sender, EventArgs e)
    {
        ApplyMinigameFilters();
    }
}
