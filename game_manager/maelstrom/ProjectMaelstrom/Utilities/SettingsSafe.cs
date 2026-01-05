using System.Configuration;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Safe helpers for reading settings with fallbacks to avoid crashes when keys are missing or stale.
/// </summary>
internal static class SettingsSafe
{
    public static bool GetBool(string key, bool fallback)
    {
        try
        {
            var settings = Properties.Settings.Default;
            if (settings.Properties[key] == null) return fallback;

            var value = settings[key];
            if (value is bool b) return b;
            if (bool.TryParse(value?.ToString(), out var parsed)) return parsed;
        }
        catch
        {
            // Ignore and return fallback
        }
        return fallback;
    }

    public static int GetInt(string key, int fallback)
    {
        try
        {
            var settings = Properties.Settings.Default;
            if (settings.Properties[key] == null) return fallback;
            var value = settings[key];
            if (value is int i) return i;
            if (int.TryParse(value?.ToString(), out var parsed)) return parsed;
        }
        catch
        {
            // ignore
        }
        return fallback;
    }

    public static double GetDouble(string key, double fallback)
    {
        try
        {
            var settings = Properties.Settings.Default;
            if (settings.Properties[key] == null) return fallback;
            var value = settings[key];
            if (value is double d) return d;
            if (double.TryParse(value?.ToString(), out var parsed)) return parsed;
        }
        catch
        {
            // ignore
        }
        return fallback;
    }

    public static string GetString(string key, string fallback)
    {
        try
        {
            var settings = Properties.Settings.Default;
            if (settings.Properties[key] == null) return fallback;
            var value = settings[key];
            return value?.ToString() ?? fallback;
        }
        catch
        {
            // ignore
        }
        return fallback;
    }
}
