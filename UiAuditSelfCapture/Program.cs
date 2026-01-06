using System.Drawing.Imaging;
using System.IO.Compression;
using System.Reflection;
using System.Text.Json;
using ProjectMaelstrom;

namespace UiAuditSelfCapture;

internal sealed class CaptureConfig
{
    public string OutputDir { get; set; } = "ui_audit_pack_selfcapture";
    public List<double> Scales { get; set; } = new() { 1.0, 1.25, 1.5, 1.75 };
}

internal sealed class CaptureResult
{
    public string Target { get; set; } = string.Empty;
    public string ScaleLabel { get; set; } = string.Empty;
    public string? FileName { get; set; }
    public string Status { get; set; } = "Missing";
    public string Notes { get; set; } = string.Empty;
}

internal enum CaptureTarget
{
    Main,
    Plugins,
    Policy,
    Overlay,
    ManageScripts,
    GitHubInstall
}

internal static class Program
{
    private static readonly Dictionary<CaptureTarget, string> FileMap = new()
    {
        { CaptureTarget.Main, "01_main_{0}.png" },
        { CaptureTarget.Plugins, "02_plugins_{0}.png" },
        { CaptureTarget.Policy, "03_policy_{0}.png" },
        { CaptureTarget.Overlay, "04_overlay_{0}.png" },
        { CaptureTarget.ManageScripts, "05_manage_scripts_{0}.png" },
        { CaptureTarget.GitHubInstall, "06_github_install_{0}.png" }
    };

    [STAThread]
    private static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        var (configPath, outputOverride) = ParseArgs(args);
        var config = LoadConfig(configPath);
        if (!string.IsNullOrWhiteSpace(outputOverride))
        {
            config.OutputDir = outputOverride!;
        }
        ApplicationConfiguration.Initialize();
        ProjectMaelstrom.Utilities.AppBootstrap.InitializeForDevTools();
        TryReloadPolicyAndPlugins();

        // Some app components try to write to a local "screenshots" directory; ensure it exists to avoid warnings.
        var screenshotDir = Path.Combine(Environment.CurrentDirectory, "screenshots");
        Directory.CreateDirectory(screenshotDir);

        var outputDir = Path.GetFullPath(config.OutputDir);
        if (Directory.Exists(outputDir))
        {
            Directory.Delete(outputDir, recursive: true);
        }
        Directory.CreateDirectory(outputDir);

        var results = new List<CaptureResult>();

        foreach (var scale in config.Scales)
        {
            var label = $"{(int)(scale * 100)}";
            Console.WriteLine($"[Capture] Scale {label}%");
            results.AddRange(CaptureAllTargets(outputDir, scale, label));
        }

        WriteReadme(outputDir, results);
        var zipPath = Path.Combine(Path.GetDirectoryName(outputDir) ?? ".", "ui_audit_pack.zip");
        if (File.Exists(zipPath)) File.Delete(zipPath);
        ZipFile.CreateFromDirectory(outputDir, zipPath);
        Console.WriteLine($"UI audit pack created at: {zipPath}");
    }

    private static (string path, string? outputOverride) ParseArgs(string[] args)
    {
        string path = "ui_self_capture_config.json";
        string? outDir = null;
        for (int i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            if (arg.Equals("--out", StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
            {
                outDir = args[i + 1];
                i++;
            }
            else
            {
                path = arg;
            }
        }
        return (path, outDir);
    }

    private static CaptureConfig LoadConfig(string path)
    {
        if (!File.Exists(path))
        {
            var cfg = new CaptureConfig();
            File.WriteAllText(path, JsonSerializer.Serialize(cfg, new JsonSerializerOptions { WriteIndented = true }));
            return cfg;
        }

        return JsonSerializer.Deserialize<CaptureConfig>(File.ReadAllText(path), new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        }) ?? new CaptureConfig();
    }

    private static IEnumerable<CaptureResult> CaptureAllTargets(string outputDir, double scale, string label)
    {
        var list = new List<CaptureResult>();

        list.Add(CaptureForm(() => new Main(), CaptureTarget.Main, outputDir, scale, label));

        // Settings form reused for multiple captures
        list.Add(CaptureForm(() => new SettingsForm(), CaptureTarget.Plugins, outputDir, scale, label));
        list.Add(CaptureForm(() => new SettingsForm(), CaptureTarget.Policy, outputDir, scale, label));
        list.Add(CaptureForm(() => new SettingsForm(), CaptureTarget.Overlay, outputDir, scale, label));

        list.Add(CaptureForm(CreateManageScriptsForm, CaptureTarget.ManageScripts, outputDir, scale, label));

        // GitHub install area is also on SettingsForm
        list.Add(CaptureForm(BuildGithubInstallStub, CaptureTarget.GitHubInstall, outputDir, scale, label));

        return list;
    }

    private static CaptureResult CaptureForm(Func<Form> factory, CaptureTarget target, string outputDir, double scale, string label)
    {
        var result = new CaptureResult
        {
            Target = target.ToString(),
            ScaleLabel = label
        };

        try
        {
            using var form = factory();
            PrepareForm(form, scale);

            if (form is SettingsForm settings)
            {
                settings.Show();
                settings.CreateControl();
                Application.DoEvents();
                if (target == CaptureTarget.Overlay)
                {
                    var listBox = settings.Controls.Find("overlayListBox", true).FirstOrDefault() as ListBox;
                    if (listBox != null && listBox.Items.Count > 0)
                    {
                        listBox.SelectedIndex = 0;
                    }
                }
            }
            else
            {
                form.Show();
                form.CreateControl();
            }

            Application.DoEvents();

            var fileName = string.Format(FileMap[target], label);
            var path = Path.Combine(outputDir, fileName);
            using var bmp = new Bitmap(form.Width, form.Height);
            form.DrawToBitmap(bmp, new Rectangle(Point.Empty, form.Size));
            bmp.Save(path, ImageFormat.Png);

            result.FileName = fileName;
            result.Status = "Captured";
        }
        catch (Exception ex)
        {
            var stack = ex.StackTrace ?? "<no stack>";
            var inner = ex.InnerException != null ? $" | Inner: {ex.InnerException.GetType().FullName}: {ex.InnerException.Message}" : string.Empty;
            var full = $"{ex.GetType().FullName}: {ex.Message}{inner} | {stack}";
            result.Status = "Missing";
            result.Notes = full;
            Console.WriteLine($"[WARN] {target} at {label}% failed: {full}");
        }

        return result;
    }

    private static void PrepareForm(Form form, double scale)
    {
        form.StartPosition = FormStartPosition.Manual;
        form.Location = new Point(50, 50);
        form.WindowState = FormWindowState.Normal;
        form.AutoScaleMode = AutoScaleMode.Font;
        var baseFont = form.Font;
        form.Font = new Font(baseFont.FontFamily, (float)(baseFont.Size * scale), baseFont.Style, baseFont.Unit, baseFont.GdiCharSet, baseFont.GdiVerticalFont);
        form.PerformLayout();
        form.Refresh();
        Application.DoEvents();
    }

    private static void WriteReadme(string outputDir, IEnumerable<CaptureResult> results)
    {
        var lines = new List<string> { "UI Audit Pack (self-capture)" };
        foreach (var r in results)
        {
            var file = r.FileName ?? "<missing>";
            lines.Add($"{file} -> {r.Target} @{r.ScaleLabel}% | {r.Status} | {r.Notes}");
        }
        File.WriteAllLines(Path.Combine(outputDir, "README.txt"), lines);
    }

    private static Form CreateManageScriptsForm()
    {
        var type = typeof(ManageScriptsForm);
        var ctor = type.GetConstructors(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)
            .FirstOrDefault(c => c.GetParameters().Length == 1);
        if (ctor != null)
        {
            return (Form)ctor.Invoke(new object?[] { null });
        }

        var anyCtor = type.GetConstructors(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)
            .FirstOrDefault(c => c.GetParameters().Length == 0);
        if (anyCtor != null)
        {
            return (Form)anyCtor.Invoke(Array.Empty<object?>());
        }

        throw new InvalidOperationException("ManageScriptsForm constructor not found");
    }

    private static void TryReloadPolicyAndPlugins()
    {
        try
        {
            var asm = typeof(Main).Assembly;
            var epType = asm.GetType("ProjectMaelstrom.Utilities.ExecutionPolicyManager");
            var reload = epType?.GetMethod("Reload", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            reload?.Invoke(null, null);
        }
        catch
        {
            // Safe to ignore; defaults will be used
        }
    }

    private static Form BuildGithubInstallStub()
    {
        var dialog = new Form
        {
            Text = "Install from GitHub Release (stub)",
            StartPosition = FormStartPosition.Manual,
            Size = new Size(520, 200),
            FormBorderStyle = FormBorderStyle.FixedDialog,
            MaximizeBox = false,
            MinimizeBox = false
        };

        var label = new Label { Text = "GitHub Release Asset ZIP URL:", AutoSize = true, Location = new Point(12, 12) };
        var text = new TextBox
        {
            Location = new Point(12, 40),
            Width = 480,
            Text = "https://github.com/owner/repo/releases/download/v1.0/asset.zip",
            ReadOnly = true
        };
        var installBtn = new Button { Text = "Install", Location = new Point(320, 100), Width = 80 };
        var cancelBtn = new Button { Text = "Cancel", Location = new Point(410, 100), Width = 80 };
        dialog.Controls.Add(label);
        dialog.Controls.Add(text);
        dialog.Controls.Add(installBtn);
        dialog.Controls.Add(cancelBtn);
        return dialog;
    }
}
