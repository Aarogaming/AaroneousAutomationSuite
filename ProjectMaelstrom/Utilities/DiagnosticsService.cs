using System.Text;
using System.Threading.Tasks;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight diagnostics runner for dev mode.
/// </summary>
internal static class DiagnosticsService
{
    public static Task<string> RunBasicAsync()
    {
        return Task.Run(() =>
        {
            var sb = new StringBuilder();
            sb.AppendLine("Diagnostics Report");
            sb.AppendLine("------------------");

            try
            {
                var libPath = StorageUtils.GetScriptLibraryPath();
                var scripts = ScriptLibraryService.Instance.Scripts.ToList();
                sb.AppendLine($"Scripts: {scripts.Count} found at {libPath}");
            }
            catch (Exception ex)
            {
                sb.AppendLine($"Scripts check failed: {ex.Message}");
                Logger.LogError("[Diagnostics] Scripts check failed", ex);
            }

            try
            {
                var feed = Properties.Settings.Default.UPDATE_FEED_URL;
                sb.AppendLine($"Update feed configured: {(string.IsNullOrWhiteSpace(feed) ? "none" : feed)}");
            }
            catch (Exception ex)
            {
                sb.AppendLine($"Update feed check failed: {ex.Message}");
            }

            try
            {
                var appRoot = StorageUtils.GetAppRoot();
                sb.AppendLine($"App root: {appRoot}");
            }
            catch (Exception ex)
            {
                sb.AppendLine($"App root check failed: {ex.Message}");
            }

            return sb.ToString();
        });
    }
}
