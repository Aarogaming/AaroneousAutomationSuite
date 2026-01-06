using Microsoft.Win32;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

public static class ThemeManager
{
    private const string RegistryKeyPath = @"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize";
    private const string RegistryValueName = "AppsUseLightTheme";

    public enum ThemeMode
    {
        System,
        Wizard101
    }

    public enum Theme
    {
        Light,
        Dark,
        Unknown
    }

    public sealed class ThemePalette
    {
        public Color Back { get; init; }
        public Color Fore { get; init; }
        public Color Surface { get; init; }
        public Color Accent { get; init; }
        public Color AccentAlt { get; init; }
        public Color Border { get; init; }
        public Color TextMuted { get; init; }
        public Color ControlBack { get; init; }
        public Color ControlFore { get; init; }
    }

    private static ThemePalette WizardPalette = new ThemePalette
    {
        Back = Color.FromArgb(18, 24, 46),          // deep midnight blue
        Surface = Color.FromArgb(22, 30, 56),       // panel surface
        ControlBack = Color.FromArgb(30, 42, 72),   // controls
        Border = Color.FromArgb(96, 68, 22),        // warm border
        Accent = Color.FromArgb(227, 177, 39),      // gold accent
        AccentAlt = Color.FromArgb(191, 79, 0),     // ember orange
        Fore = Color.FromArgb(243, 236, 219),       // parchment text
        ControlFore = Color.FromArgb(243, 236, 219),
        TextMuted = Color.FromArgb(198, 190, 169)
    };

    public static ThemeMode CurrentMode { get; set; } = ThemeMode.System;

    public static void SetModeFromString(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            CurrentMode = ThemeMode.System;
            return;
        }

        if (value.Trim().Equals("Wizard101", StringComparison.OrdinalIgnoreCase))
        {
            CurrentMode = ThemeMode.Wizard101;
            TryLoadWizardPalette();
        }
        else
        {
            CurrentMode = ThemeMode.System;
        }
    }

    public static string GetModeAsString()
    {
        return CurrentMode == ThemeMode.Wizard101 ? "Wizard101" : "System";
    }

    public static Theme GetSystemTheme()
    {
        try
        {
            using (RegistryKey? key = Registry.CurrentUser.OpenSubKey(RegistryKeyPath))
            {
                if (key != null)
                {
                    object? value = key.GetValue(RegistryValueName);
                    if (value is int intValue)
                    {
                        return intValue == 1 ? Theme.Light : Theme.Dark;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to detect system theme", ex);
        }

        return Theme.Unknown;
    }

    public static bool IsDarkMode => GetSystemTheme() == Theme.Dark;

    public static Color GetBackgroundColor()
    {
        return IsDarkMode ? Color.FromArgb(32, 32, 32) : SystemColors.Control;
    }

    public static Color GetForegroundColor()
    {
        return IsDarkMode ? Color.White : SystemColors.ControlText;
    }

    public static ThemePalette GetActivePalette()
    {
        if (CurrentMode == ThemeMode.Wizard101)
        {
            return WizardPalette;
        }

        if (IsDarkMode)
        {
            return new ThemePalette
            {
                Back = Color.FromArgb(32, 32, 32),
                Surface = Color.FromArgb(40, 40, 40),
                ControlBack = Color.FromArgb(48, 48, 48),
                Border = Color.Gray,
                Accent = Color.SteelBlue,
                AccentAlt = Color.SteelBlue,
                Fore = Color.White,
                ControlFore = Color.White,
                TextMuted = Color.Gainsboro
            };
        }

        return new ThemePalette
        {
            Back = SystemColors.Control,
            Surface = SystemColors.ControlLight,
            ControlBack = SystemColors.Control,
            Border = SystemColors.ControlDark,
            Accent = SystemColors.Highlight,
            AccentAlt = SystemColors.Highlight,
            Fore = SystemColors.ControlText,
            ControlFore = SystemColors.ControlText,
            TextMuted = SystemColors.GrayText
        };
    }

    public static Color GetButtonBackColor()
    {
        var palette = GetActivePalette();
        return palette.ControlBack;
    }

    public static Color GetButtonForeColor()
    {
        var palette = GetActivePalette();
        return palette.ControlFore;
    }

    public static Color GetTextBoxBackColor()
    {
        var palette = GetActivePalette();
        return palette.ControlBack;
    }

    public static Color GetTextBoxForeColor()
    {
        var palette = GetActivePalette();
        return palette.ControlFore;
    }

    public static Color GetLabelForeColor()
    {
        var palette = GetActivePalette();
        return palette.Fore;
    }

    private static void TryLoadWizardPalette()
    {
        try
        {
            string baseDir = StorageUtils.GetAppRoot();
            // Try shared design tokens first, then fallback to local palette
            string palettePath = Path.Combine(baseDir, "..", "..", "AaroneousAutomationSuite", "design_tokens.json");
            if (!File.Exists(palettePath))
            {
                palettePath = Path.Combine(baseDir, "wizard_palette.json");
            }
            
            if (!File.Exists(palettePath))
            {
                return;
            }

            string json = File.ReadAllText(palettePath);
            if (palettePath.EndsWith("design_tokens.json"))
            {
                // Handle shared token format
                var tokens = JsonSerializer.Deserialize<JsonElement>(json);
                var colors = tokens.GetProperty("colors");
                WizardPalette = new ThemePalette
                {
                    Back = ParseColor(colors.GetProperty("back").GetString(), WizardPalette.Back),
                    Fore = ParseColor(colors.GetProperty("fore").GetString(), WizardPalette.Fore),
                    Surface = ParseColor(colors.GetProperty("surface").GetString(), WizardPalette.Surface),
                    Accent = ParseColor(colors.GetProperty("accent").GetString(), WizardPalette.Accent),
                    AccentAlt = ParseColor(colors.GetProperty("accent_alt").GetString(), WizardPalette.AccentAlt),
                    Border = ParseColor(colors.GetProperty("border").GetString(), WizardPalette.Border),
                    TextMuted = ParseColor(colors.GetProperty("text_muted").GetString(), WizardPalette.TextMuted),
                    ControlBack = ParseColor(colors.GetProperty("control_back").GetString(), WizardPalette.ControlBack),
                    ControlFore = ParseColor(colors.GetProperty("control_fore").GetString(), WizardPalette.ControlFore)
                };
                return;
            }

            var dto = JsonSerializer.Deserialize<WizardPaletteDto>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (dto == null)
            {
                return;
            }

            WizardPalette = new ThemePalette
            {
                Back = ParseColor(dto.Back, WizardPalette.Back),
                Fore = ParseColor(dto.Fore, WizardPalette.Fore),
                Surface = ParseColor(dto.Surface, WizardPalette.Surface),
                Accent = ParseColor(dto.Accent, WizardPalette.Accent),
                AccentAlt = ParseColor(dto.AccentAlt, WizardPalette.AccentAlt),
                Border = ParseColor(dto.Border, WizardPalette.Border),
                TextMuted = ParseColor(dto.TextMuted, WizardPalette.TextMuted),
                ControlBack = ParseColor(dto.ControlBack, WizardPalette.ControlBack),
                ControlFore = ParseColor(dto.ControlFore, WizardPalette.ControlFore)
            };
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to load wizard_palette.json", ex);
        }
    }

    private static Color ParseColor(string? hex, Color fallback)
    {
        if (string.IsNullOrWhiteSpace(hex))
        {
            return fallback;
        }

        try
        {
            return ColorTranslator.FromHtml(hex);
        }
        catch
        {
            return fallback;
        }
    }

    private sealed class WizardPaletteDto
    {
        public string? Back { get; set; }
        public string? Fore { get; set; }
        public string? Surface { get; set; }
        public string? Accent { get; set; }
        public string? AccentAlt { get; set; }
        public string? Border { get; set; }
        public string? TextMuted { get; set; }
        public string? ControlBack { get; set; }
        public string? ControlFore { get; set; }
    }

    public static void ApplyTheme(Form form)
    {
        var palette = GetActivePalette();
        form.BackColor = palette.Back;
        form.ForeColor = palette.Fore;

        ApplyThemeToControls(form.Controls);
    }

    private static void ApplyThemeToControls(Control.ControlCollection controls)
    {
        var palette = GetActivePalette();

        foreach (Control control in controls)
        {
            switch (control)
            {
                case Button button:
                    button.BackColor = GetButtonBackColor();
                    button.ForeColor = GetButtonForeColor();
                    button.FlatStyle = FlatStyle.Flat;
                    button.FlatAppearance.BorderColor = palette.Border;
                    button.FlatAppearance.MouseOverBackColor = palette.AccentAlt;
                    button.FlatAppearance.MouseDownBackColor = palette.Accent;
                    button.FlatAppearance.BorderSize = 1;
                    button.Padding = new Padding(4, 4, 4, 4);
                    break;

                case TextBox textBox:
                    textBox.BackColor = GetTextBoxBackColor();
                    textBox.ForeColor = GetTextBoxForeColor();
                    break;

                case Label label:
                    label.ForeColor = GetLabelForeColor();
                    break;

                case GroupBox groupBox:
                    groupBox.ForeColor = GetLabelForeColor();
                    groupBox.BackColor = palette.Surface;
                    groupBox.FlatStyle = FlatStyle.Flat;
                    groupBox.Padding = new Padding(10);
                    break;

                case ListBox listBox:
                    listBox.BackColor = GetTextBoxBackColor();
                    listBox.ForeColor = GetTextBoxForeColor();
                    break;

                case ListView listView:
                    listView.BackColor = palette.Surface;
                    listView.ForeColor = palette.ControlFore;
                    listView.BorderStyle = BorderStyle.FixedSingle;
                    listView.GridLines = false;
                    listView.OwnerDraw = false;
                    listView.Font = new Font(listView.Font, FontStyle.Regular);
                    listView.HeaderStyle = ColumnHeaderStyle.Nonclickable;
                    break;

                case ComboBox comboBox:
                    comboBox.BackColor = GetTextBoxBackColor();
                    comboBox.ForeColor = GetTextBoxForeColor();
                    break;

                case CheckBox checkBox:
                    checkBox.ForeColor = palette.Fore;
                    break;

                case RadioButton radioButton:
                    radioButton.ForeColor = GetLabelForeColor();
                    break;

                case Panel panel:
                    panel.BackColor = palette.Surface;
                    panel.ForeColor = palette.Fore;
                    break;
            }

            // Recursively apply to child controls
            if (control.HasChildren)
            {
                ApplyThemeToControls(control.Controls);
            }
        }
    }
}
