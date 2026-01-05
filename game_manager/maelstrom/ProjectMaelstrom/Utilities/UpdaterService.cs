using System.IO.Compression;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using ProjectMaelstrom.Models;
using ProjectMaelstrom.Properties;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight updater: fetches a manifest, downloads a package, stages it, and records pending apply/rollback info.
/// Apply/rollback are non-destructive stubs that stage content for a future swap to avoid clobbering the running exe.
/// </summary>
internal sealed class UpdaterService
{
    private static readonly Lazy<UpdaterService> _instance = new(() => new UpdaterService());
    public static UpdaterService Instance => _instance.Value;

    private readonly HttpClient _httpClient = new();
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly string _statePath;

    public UpdateManifest? LatestManifest { get; private set; }
    public string? DownloadedPackagePath { get; private set; }
    public string? StagingPath { get; private set; }
    public string? LastMessage { get; private set; }

    private UpdaterService()
    {
        _statePath = Path.Combine(StorageUtils.GetCacheDirectory(), "updater_state.json");
    }

    public async Task<UpdateManifest?> CheckForUpdateAsync(string? feedUrl)
    {
        if (string.IsNullOrWhiteSpace(feedUrl))
        {
            LastMessage = "Update feed URL is not set.";
            return null;
        }

        try
        {
            var resp = await _httpClient.GetAsync(feedUrl);
            resp.EnsureSuccessStatusCode();
            var json = await resp.Content.ReadAsStringAsync();
            var manifest = JsonSerializer.Deserialize<UpdateManifest>(json, _jsonOptions);
            LatestManifest = manifest;
            LastMessage = manifest == null ? "No manifest parsed." : $"Manifest loaded: {manifest.Version}";
            PersistState();
            return manifest;
        }
        catch (Exception ex)
        {
            LastMessage = $"Check failed: {ex.Message}";
            Logger.LogError("[Updater] CheckForUpdateAsync failed", ex);
            return null;
        }
    }

    public async Task<string?> DownloadPackageAsync()
    {
        if (LatestManifest == null || string.IsNullOrWhiteSpace(LatestManifest.PackageUrl))
        {
            LastMessage = "No package URL in manifest.";
            return null;
        }

        try
        {
            var destFile = Path.Combine(Path.GetTempPath(), $"maelstrom_update_{DateTime.UtcNow:yyyyMMddHHmmss}.zip");
            using var resp = await _httpClient.GetAsync(LatestManifest.PackageUrl);
            resp.EnsureSuccessStatusCode();
            await using (var fs = File.Create(destFile))
            {
                await resp.Content.CopyToAsync(fs);
            }

            if (LatestManifest.Files?.Length > 0)
            {
                var hash = ComputeSha256(destFile);
                // Optional: compare against first file hash if provided for package
                if (!string.IsNullOrWhiteSpace(LatestManifest.Files[0].Sha256) &&
                    !hash.Equals(LatestManifest.Files[0].Sha256, StringComparison.OrdinalIgnoreCase))
                {
                    LastMessage = "Package hash mismatch.";
                    return null;
                }
            }

            DownloadedPackagePath = destFile;
            LastMessage = $"Downloaded to {destFile}";
            PersistState();
            return destFile;
        }
        catch (Exception ex)
        {
            LastMessage = $"Download failed: {ex.Message}";
            Logger.LogError("[Updater] Download failed", ex);
            return null;
        }
    }

    public string? StagePackage()
    {
        if (DownloadedPackagePath == null || !File.Exists(DownloadedPackagePath))
        {
            LastMessage = "No downloaded package to stage.";
            return null;
        }

        try
        {
            var dest = Path.Combine(StorageUtils.GetCacheDirectory(), "update_staged");
            if (Directory.Exists(dest))
            {
                Directory.Delete(dest, recursive: true);
            }
            ZipFile.ExtractToDirectory(DownloadedPackagePath, dest);
            StagingPath = dest;
            LastMessage = $"Staged at {dest}";
            PersistState();
            return dest;
        }
        catch (Exception ex)
        {
            LastMessage = $"Staging failed: {ex.Message}";
            Logger.LogError("[Updater] Staging failed", ex);
            return null;
        }
    }

    public bool MarkApplyPending()
    {
        if (StagingPath == null || !Directory.Exists(StagingPath))
        {
            LastMessage = "No staged content to apply.";
            return false;
        }

        try
        {
            var marker = Path.Combine(StorageUtils.GetCacheDirectory(), "update_pending.txt");
            File.WriteAllText(marker, StagingPath, Encoding.UTF8);
            LastMessage = $"Update pending. Restart to apply from {StagingPath}";
            PersistState();
            return true;
        }
        catch (Exception ex)
        {
            LastMessage = $"Mark apply failed: {ex.Message}";
            Logger.LogError("[Updater] Mark apply failed", ex);
            return false;
        }
    }

    public void ClearState()
    {
        LatestManifest = null;
        DownloadedPackagePath = null;
        StagingPath = null;
        try
        {
            if (File.Exists(_statePath)) File.Delete(_statePath);
        }
        catch { /* ignore */ }
    }

    private void PersistState()
    {
        try
        {
            var state = new
            {
                manifest = LatestManifest,
                package = DownloadedPackagePath,
                staging = StagingPath,
                message = LastMessage
            };
            var json = JsonSerializer.Serialize(state, _jsonOptions);
            File.WriteAllText(_statePath, json);
        }
        catch (Exception ex)
        {
            Logger.LogError("[Updater] Failed to persist state", ex);
        }
    }

    private static string ComputeSha256(string path)
    {
        using var sha = SHA256.Create();
        using var fs = File.OpenRead(path);
        var hash = sha.ComputeHash(fs);
        return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
    }
}
