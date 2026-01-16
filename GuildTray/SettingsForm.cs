using System;
using System.Windows.Forms;

namespace HandoffTray;

public sealed class SettingsForm : Form
{
    private readonly TextBox _baseUrl = new() { Dock = DockStyle.Top, PlaceholderText = "http://localhost:5000" };
    private readonly TextBox _token = new() { Dock = DockStyle.Top, PlaceholderText = "Bearer token", UseSystemPasswordChar = true };
    private readonly Button _save = new() { Text = "Save", Dock = DockStyle.Top };
    private readonly Button _cancel = new() { Text = "Cancel", Dock = DockStyle.Top };

    public string BaseUrl => _baseUrl.Text.Trim();
    public string Token => _token.Text.Trim();

    public SettingsForm(TraySettings settings, string? token)
    {
        Text = "Maelstrom Tray Settings";
        Width = 420;
        Height = 220;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;

        _baseUrl.Text = settings.BaseUrl;
        _token.Text = token ?? string.Empty;

        var panel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.TopDown,
            Padding = new Padding(10)
        };

        panel.Controls.Add(new Label { Text = "Base URL (server):", AutoSize = true });
        panel.Controls.Add(_baseUrl);
        panel.Controls.Add(new Label { Text = "Admin token (Bearer):", AutoSize = true });
        panel.Controls.Add(_token);
        panel.Controls.Add(_save);
        panel.Controls.Add(_cancel);

        _save.Click += (_, _) => DialogResult = DialogResult.OK;
        _cancel.Click += (_, _) => DialogResult = DialogResult.Cancel;

        Controls.Add(panel);

        AcceptButton = _save;
        CancelButton = _cancel;
    }
}
