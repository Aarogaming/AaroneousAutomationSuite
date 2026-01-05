using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom;

public partial class AboutForm : Form
{
    public AboutForm()
    {
        InitializeComponent();
        ThemeManager.ApplyTheme(this);
        ApplyPalette();
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        UIStyles.ApplyCardStyle(this, palette.Back, palette.Border);
        creditsTextBox.BackColor = palette.ControlBack;
        creditsTextBox.ForeColor = palette.ControlFore;
        closeButton.BackColor = palette.ControlBack;
        closeButton.ForeColor = palette.ControlFore;
        closeButton.FlatStyle = FlatStyle.Flat;
        closeButton.FlatAppearance.BorderColor = palette.Border;
    }

    private void AboutForm_Load(object sender, EventArgs e)
    {
        creditsTextBox.Text = @"Project Maelstrom
Wizard101 automation toolkit

Credits & Licenses
- Emgu CV (OpenCV) for image processing and template matching (BSD)
- Tesseract OCR (Apache 2.0) for local text extraction
- WindowsInput/InputSimulator (MIT) for keyboard input
- Newtonsoft.Json (MIT) for JSON handling
- System.Drawing / Win32 interop helpers
- Community scripts/bots in Scripts/Library retain original authorship; source URLs and authors should be listed in each manifest.json and surfaced in-app

Use responsibly. Respect game terms of service and other players.";
    }

    private void closeButton_Click(object sender, EventArgs e)
    {
        this.Close();
    }
}
