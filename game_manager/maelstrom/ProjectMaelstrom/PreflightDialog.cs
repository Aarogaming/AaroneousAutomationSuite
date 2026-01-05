using System;
using System.Drawing;
using System.Windows.Forms;

namespace ProjectMaelstrom;

/// <summary>
/// Simple dialog to surface preflight blocks and optionally queue a helper task (e.g., potion refill).
/// </summary>
internal sealed class PreflightDialog : Form
{
    private readonly Label _message;
    private readonly Button _queueButton;
    private readonly Button _cancelButton;

    public bool QueueSelected { get; private set; }

    public PreflightDialog(string reason, bool canQueue, string queueLabel = "Queue refill run")
    {
        Text = "Preflight Blocked";
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MinimizeBox = false;
        MaximizeBox = false;
        Size = new Size(460, canQueue ? 220 : 180);

        _message = new Label
        {
            AutoSize = true,
            Dock = DockStyle.Top,
            Text = reason,
            TextAlign = ContentAlignment.MiddleLeft,
            MaximumSize = new Size(430, 0),
            Padding = new Padding(8)
        };

        _queueButton = new Button
        {
            Text = queueLabel,
            DialogResult = DialogResult.Yes,
            Visible = canQueue,
            Width = 150,
            Height = 32
        };
        _queueButton.Click += (_, _) => { QueueSelected = true; Close(); };

        _cancelButton = new Button
        {
            Text = canQueue ? "Cancel" : "Close",
            DialogResult = DialogResult.Cancel,
            Width = 100,
            Height = 32
        };
        _cancelButton.Click += (_, _) => Close();

        var buttonPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Bottom,
            FlowDirection = FlowDirection.RightToLeft,
            Padding = new Padding(8),
            Height = 60
        };
        buttonPanel.Controls.Add(_cancelButton);
        buttonPanel.Controls.Add(_queueButton);

        Controls.Add(buttonPanel);
        Controls.Add(_message);

        AcceptButton = canQueue ? _queueButton : _cancelButton;
        CancelButton = _cancelButton;
    }
}
