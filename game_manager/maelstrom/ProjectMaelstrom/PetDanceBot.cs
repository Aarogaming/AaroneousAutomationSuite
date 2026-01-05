using System.Diagnostics;
using System.IO;
using Microsoft.Win32;
using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom;

public class PetDanceBot : Form
{
    private readonly Button _launchButton;
    private readonly Label _statusLabel;

    public PetDanceBot()
    {
        Text = "Wizard101 DanceBot";
        StartPosition = FormStartPosition.Manual;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = false;
        Dock = DockStyle.Fill;
        ClientSize = new Size(360, 160);
        MinimumSize = new Size(360, 160);

        _launchButton = new Button
        {
            Text = "Launch Wizard101 DanceBot",
            Size = new Size(320, 40),
            Location = new Point(20, 20),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        };
        _launchButton.Click += LaunchButton_Click;

        _statusLabel = new Label
        {
            AutoSize = true,
            Location = new Point(20, 80),
            Text = "Ready"
        };

        Controls.Add(_launchButton);
        Controls.Add(_statusLabel);

        ThemeManager.ApplyTheme(this);
        SystemEvents.UserPreferenceChanged += OnUserPreferenceChanged;
        FormClosing += PetDanceBot_FormClosing;
    }

    private void LaunchButton_Click(object? sender, EventArgs e)
    {
        string scriptPath = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory,
            "Scripts",
            "Wizard101_DanceBot",
            "dist",
            "petdance",
            "petdance.exe");

        if (!File.Exists(scriptPath))
        {
            _statusLabel.Text = "DanceBot not found";
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = scriptPath,
                UseShellExecute = true,
                WorkingDirectory = Path.GetDirectoryName(scriptPath)
            });

            _statusLabel.Text = "Launched";
            Logger.Log("Wizard101 DanceBot launched successfully.");
        }
        catch (Exception ex)
        {
            _statusLabel.Text = "Launch failed";
            Logger.Log($"Error launching Wizard101 DanceBot: {ex.Message}");
        }
    }

    private void OnUserPreferenceChanged(object? sender, UserPreferenceChangedEventArgs e)
    {
        if (InvokeRequired)
        {
            BeginInvoke(new Action(() => ThemeManager.ApplyTheme(this)));
        }
        else
        {
            ThemeManager.ApplyTheme(this);
        }
    }

    private void PetDanceBot_FormClosing(object? sender, FormClosingEventArgs e)
    {
        SystemEvents.UserPreferenceChanged -= OnUserPreferenceChanged;
        FormClosing -= PetDanceBot_FormClosing;
    }
}
