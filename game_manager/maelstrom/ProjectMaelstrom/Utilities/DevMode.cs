using System.Diagnostics;
using System.Text.Json;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Central dev-mode toggle with simple owner gating and helper logging hooks.
/// Reads from dev.config in app root or %LocalAppData%\ProjectMaelstrom\dev.config.
/// </summary>
internal static class DevMode
{
    private static readonly object _lock = new();
    private static bool _initialized;
    private static bool _enabled;
    private static string? _ownerLogin;
    private const string OwnerLogin = "aarog";

    public static bool IsEnabled
    {
        get
        {
            EnsureInitialized();
            return _enabled;
        }
    }

    public static string CurrentOwner => _ownerLogin ?? string.Empty;

    /// <summary>
    /// Initialize dev mode. Safe to call multiple times.
    /// </summary>
    public static void EnsureInitialized()
    {
        if (_initialized) return;
        lock (_lock)
        {
            if (_initialized) return;
            try
            {
                var cfgPaths = new[]
                {
                    Path.Combine(StorageUtils.GetAppRoot(), "dev.config"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ProjectMaelstrom", "dev.config")
                };

                string? token = null;

                foreach (var path in cfgPaths)
                {
                    if (!File.Exists(path)) continue;
                    foreach (var line in File.ReadAllLines(path))
                    {
                        if (line.IndexOf("DEV_MODE=true", StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            _enabled = true;
                        }
                        if (line.TrimStart().StartsWith("GITHUB_TOKEN=", StringComparison.OrdinalIgnoreCase))
                        {
                            token = line.Split('=', 2)[1].Trim();
                        }
                    }
                }

                if (!_enabled && !string.IsNullOrWhiteSpace(token))
                {
                    // Lightweight owner check via GitHub API
                    try
                    {
                        using var client = new HttpClient();
                        client.DefaultRequestHeaders.UserAgent.ParseAdd("ProjectMaelstrom");
                        client.DefaultRequestHeaders.Authorization =
                            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
                        var json = client.GetStringAsync("https://api.github.com/user").GetAwaiter().GetResult();
                        var doc = JsonDocument.Parse(json);
                        if (doc.RootElement.TryGetProperty("login", out var loginEl))
                        {
                            var login = loginEl.GetString();
                            _ownerLogin = login;
                            if (!string.IsNullOrWhiteSpace(login) &&
                                login.Equals(OwnerLogin, StringComparison.OrdinalIgnoreCase))
                            {
                                _enabled = true;
                            }
                        }
                    }
                    catch
                    {
                        // ignore token failures
                    }
                }

                if (_enabled)
                {
                    Logger.Log("[DevMode] Enabled.");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"DevMode init failed: {ex}");
            }
            finally
            {
                _initialized = true;
            }
        }
    }
}
