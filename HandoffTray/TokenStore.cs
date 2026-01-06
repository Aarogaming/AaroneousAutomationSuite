using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace HandoffTray;

public static class TokenStore
{
    private static string Dir => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MaelstromBot.Tray");
    private static string TokenPath => Path.Combine(Dir, "admin.token");

    public static string? TryLoad()
    {
        if (!File.Exists(TokenPath)) return null;
        try
        {
            var data = File.ReadAllBytes(TokenPath);
            var clear = ProtectedData.Unprotect(data, null, DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(clear);
        }
        catch
        {
            return null;
        }
    }

    public static void Save(string token)
    {
        Directory.CreateDirectory(Dir);
        var data = Encoding.UTF8.GetBytes(token);
        var protectedBytes = ProtectedData.Protect(data, null, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(TokenPath, protectedBytes);
    }

    public static void Clear()
    {
        if (File.Exists(TokenPath)) File.Delete(TokenPath);
    }
}

public sealed class TraySettings
{
    public string BaseUrl { get; set; } = "http://localhost:5000";
}

public static class SettingsStore
{
    private static string Dir => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MaelstromBot.Tray");
    private static string PathJson => Path.Combine(Dir, "settings.json");

    public static TraySettings Load()
    {
        try
        {
            if (File.Exists(PathJson))
            {
                var json = File.ReadAllText(PathJson);
                var s = JsonSerializer.Deserialize<TraySettings>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                if (s != null) return s;
            }
        }
        catch { }
        return new TraySettings();
    }

    public static void Save(TraySettings settings)
    {
        Directory.CreateDirectory(Dir);
        var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(PathJson, json);
    }
}
