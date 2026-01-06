using ProjectMaelstrom.Utilities;
using System.Text.Json;

namespace ProjectMaelstrom;

public partial class MacroRecorderForm : Form
{
    private readonly InputRecorder _recorder = new();
    private bool _recording;

    public MacroRecorderForm()
    {
        InitializeComponent();
        ThemeManager.ApplyTheme(this);
        ApplyPalette();
    }

    private void startStopButton_Click(object sender, EventArgs e)
    {
        if (_recording)
        {
            _recorder.Stop();
            _recording = false;
            startStopButton.Text = "Start Recording";
            statusLabel.Text = $"Status: Stopped ({_recorder.Commands.Count} commands)";
            PopulateList();
        }
        else
        {
            _recorder.Start();
            _recording = true;
            startStopButton.Text = "Stop Recording";
            statusLabel.Text = "Status: Recording...";
            commandsList.Items.Clear();
        }
    }

    private void saveButton_Click(object sender, EventArgs e)
    {
        if (_recorder.Commands.Count == 0)
        {
            MessageBox.Show("No commands recorded yet.", "Save Macro", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var name = macroNameText.Text;
        if (string.IsNullOrWhiteSpace(name))
        {
            MessageBox.Show("Enter a macro name.", "Save Macro", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            var dir = Path.Combine(StorageUtils.GetScriptsRoot(), "Macros");
            Directory.CreateDirectory(dir);
            var safe = SanitizeFileName(name);
            var path = Path.Combine(dir, $"{safe}.json");
            var json = JsonSerializer.Serialize(_recorder.Commands, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(path, json);
            statusLabel.Text = $"Status: Saved to {path}";
            DevTelemetry.Log("Macros", $"Saved macro {safe} with {_recorder.Commands.Count} commands");
            MessageBox.Show($"Saved macro to {path}", "Saved", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            Logger.LogError("[MacroRecorder] Save failed", ex);
            MessageBox.Show($"Save failed: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void PopulateList()
    {
        commandsList.Items.Clear();
        foreach (var cmd in _recorder.Commands)
        {
            commandsList.Items.Add($"{cmd.Type} {cmd.Key ?? ""} ({cmd.X},{cmd.Y}) delay={cmd.DelayMs}");
        }
    }

    private static string SanitizeFileName(string name)
    {
        foreach (var c in Path.GetInvalidFileNameChars())
        {
            name = name.Replace(c, '_');
        }
        return string.IsNullOrWhiteSpace(name) ? "macro" : name;
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        UIStyles.ApplyCardStyle(this, palette.Surface, palette.Border);
        UIStyles.ApplyButtonStyle(startStopButton, palette.ControlBack, palette.ControlFore, palette.Border);
        UIStyles.ApplyButtonStyle(saveButton, palette.ControlBack, palette.ControlFore, palette.Border);
        macroNameText.BackColor = palette.ControlBack;
        macroNameText.ForeColor = palette.ControlFore;
        commandsList.BackColor = palette.ControlBack;
        commandsList.ForeColor = palette.ControlFore;
        statusLabel.ForeColor = palette.Fore;
    }
}
