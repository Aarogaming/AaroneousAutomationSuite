using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom;

internal static class Program
{
    private static void TestTheme()
    {
        Console.WriteLine("Testing Theme Detection...");
        var theme = ThemeManager.GetSystemTheme();
        Console.WriteLine($"Detected theme: {theme}");
        Console.WriteLine($"Is Dark Mode: {ThemeManager.IsDarkMode}");
        Console.WriteLine($"Background Color: {ThemeManager.GetBackgroundColor()}");
        Console.WriteLine($"Foreground Color: {ThemeManager.GetForegroundColor()}");
        Console.WriteLine("Theme test completed.");
    }

    /// <summary>
    ///  The main entry point for the application.
    /// </summary>
    [STAThread]
    static void Main(string[] args)
    {
        DevMode.EnsureInitialized();

        // Check for theme test
        if (args.Length > 0 && args[0] == "--test-theme")
        {
            TestTheme();
            return;
        }

        // Check for utility tests
        if (args.Length > 0 && args[0] == "--run-tests")
        {
            ProjectMaelstrom.Tests.UtilityTests.RunAllTests();
            return;
        }

        AppBootstrap.Initialize();

        // To customize application configuration such as set high DPI settings or default font,
        // see https://aka.ms/applicationconfiguration.

        if (!Directory.Exists("screenshots"))
        {
            Directory.CreateDirectory("screenshots");
        }

        // Hook global exception logging in dev mode for quicker diagnostics.
        if (DevMode.IsEnabled)
        {
            AppDomain.CurrentDomain.UnhandledException += (_, evt) =>
            {
                try
                {
                    Logger.LogError("[DevMode] Unhandled exception", evt.ExceptionObject as Exception);
                }
                catch { /* ignore */ }
            };
            Application.ThreadException += (_, evt) =>
            {
                try
                {
                    Logger.LogError("[DevMode] UI thread exception", evt.Exception);
                }
                catch { /* ignore */ }
            };
        }

        // Load theme preference
        ThemeManager.SetModeFromString(Properties.Settings.Default["THEME_MODE"]?.ToString());

        ApplicationConfiguration.Initialize();
        Application.Run(new Main());
    }
}
