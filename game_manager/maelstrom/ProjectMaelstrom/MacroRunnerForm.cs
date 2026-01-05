using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom;

public partial class MacroRunnerForm : Form
{
    private readonly Action<string> _runCallback;
    private readonly List<string> _paths = new();

    public MacroRunnerForm(Action<string> runCallback)
    {
        _runCallback = runCallback;
        InitializeComponent();
    }

    private void MacroRunnerForm_Load(object sender, EventArgs e)
    {
        ThemeManager.ApplyTheme(this);
        ApplyPalette();
        RefreshList();
    }

    private void RefreshList()
    {
        _paths.Clear();
        macroList.Items.Clear();
        var dir = Path.Combine(StorageUtils.GetScriptsRoot(), "Macros");
        if (!Directory.Exists(dir))
        {
            Directory.CreateDirectory(dir);
        }

        var files = Directory.GetFiles(dir, "*.json").OrderBy(f => f, StringComparer.OrdinalIgnoreCase).ToList();
        foreach (var f in files)
        {
            _paths.Add(f);
            macroList.Items.Add(Path.GetFileNameWithoutExtension(f));
        }
        statusLabel.Text = _paths.Count == 0 ? "Status: No macros found." : $"Status: {_paths.Count} macros found.";
    }

    private void runButton_Click(object sender, EventArgs e)
    {
        var idx = macroList.SelectedIndex;
        if (idx < 0 || idx >= _paths.Count)
        {
            MessageBox.Show("Select a macro to run.", "Macro Runner", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        _runCallback(_paths[idx]);
        statusLabel.Text = $"Status: Running {_paths[idx]}";
    }

    private void refreshButton_Click(object sender, EventArgs e)
    {
        RefreshList();
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        UIStyles.ApplyCardStyle(this, palette.Surface, palette.Border);
        UIStyles.ApplyButtonStyle(runButton, palette.ControlBack, palette.ControlFore, palette.Border);
        UIStyles.ApplyButtonStyle(refreshButton, palette.ControlBack, palette.ControlFore, palette.Border);
        macroList.BackColor = palette.ControlBack;
        macroList.ForeColor = palette.ControlFore;
        statusLabel.ForeColor = palette.Fore;
    }
}
