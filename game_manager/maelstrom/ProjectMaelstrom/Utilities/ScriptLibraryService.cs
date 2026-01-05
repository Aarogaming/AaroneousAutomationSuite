using System.Diagnostics;
using System.Text.Json;
using System.Linq;
using System.IO.Compression;
using System.Net.Http;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

internal class ScriptLibraryService
{
    private static readonly Lazy<ScriptLibraryService> _instance = new(() => new ScriptLibraryService());
    private readonly object _lock = new();
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly Dictionary<string, GameStateSnapshot> _latestSnapshots = new(StringComparer.OrdinalIgnoreCase);
    private List<ScriptDefinition> _scripts = new();
    private static readonly HttpClient _httpClient = new();
    private const string PackageMetaFileName = ".package.json";
    public bool DryRun { get; set; }

    private ScriptLibraryService()
    {
    }

    public static ScriptLibraryService Instance => _instance.Value;

    public IReadOnlyList<ScriptDefinition> Scripts
    {
        get
        {
            lock (_lock)
            {
                return _scripts.ToList();
            }
        }
    }

    public ScriptRunSession? CurrentSession { get; private set; }
    public Func<ScriptDefinition, PreflightResult>? PreflightCheck { get; set; }

    public void SetLatestSnapshot(string key, GameStateSnapshot snapshot)
    {
        lock (_lock)
        {
            _latestSnapshots[key] = snapshot;
        }
    }

    public GameStateSnapshot? GetLatestSnapshot(string key)
    {
        lock (_lock)
        {
            return _latestSnapshots.TryGetValue(key, out var snap) ? snap : null;
        }
    }

    public async Task<ScriptDefinition?> ImportFromGitHubAsync(string sourceUrl, string? branchOrTag = null)
    {
        if (string.IsNullOrWhiteSpace(sourceUrl))
        {
            throw new ArgumentException("Source URL is required.", nameof(sourceUrl));
        }

        string downloadUrl = ResolveGitHubDownloadUrl(sourceUrl, branchOrTag);
        string tempZip = Path.Combine(Path.GetTempPath(), $"w101_script_{Guid.NewGuid():N}.zip");
        string libraryRoot = StorageUtils.GetScriptLibraryPath();
        Directory.CreateDirectory(libraryRoot);

        try
        {
            using var response = await _httpClient.GetAsync(downloadUrl);
            response.EnsureSuccessStatusCode();
            await using (var fs = File.Create(tempZip))
            {
                await response.Content.CopyToAsync(fs);
            }

            string targetFolderName = BuildTargetFolderName(sourceUrl, branchOrTag);
            string destPath = Path.Combine(libraryRoot, targetFolderName);
            await ExtractZipToDestinationAsync(tempZip, destPath, flattenSingleFolder: true);
            WritePackageMetadata(destPath, sourceUrl, branchOrTag);

            ReloadLibrary();
            return _scripts.FirstOrDefault(s => s.RootPath.Equals(destPath, StringComparison.OrdinalIgnoreCase))
                   ?? _scripts.FirstOrDefault(s => s.RootPath.StartsWith(destPath, StringComparison.OrdinalIgnoreCase));
        }
        catch (Exception ex)
        {
            Logger.LogError("[ScriptLibrary] GitHub import failed", ex);
            throw;
        }
        finally
        {
            try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { /* ignore cleanup errors */ }
        }
    }

    public async Task<ScriptDefinition?> UpdateScriptAsync(ScriptDefinition script)
    {
        var meta = script.PackageInfo ?? TryReadPackageMetadata(script.RootPath);
        if (meta == null || string.IsNullOrWhiteSpace(meta.SourceUrl))
        {
            throw new InvalidOperationException("Script does not have source metadata to update.");
        }

        string downloadUrl = ResolveGitHubDownloadUrl(meta.SourceUrl!, meta.BranchOrTag);
        string tempZip = Path.Combine(Path.GetTempPath(), $"w101_script_update_{Guid.NewGuid():N}.zip");
        string tempExtract = Path.Combine(Path.GetTempPath(), $"w101_script_update_{Guid.NewGuid():N}");

        try
        {
            using var response = await _httpClient.GetAsync(downloadUrl);
            response.EnsureSuccessStatusCode();
            await using (var fs = File.Create(tempZip))
            {
                await response.Content.CopyToAsync(fs);
            }

            await ExtractZipToDestinationAsync(tempZip, tempExtract, flattenSingleFolder: true);

            lock (_lock)
            {
                if (CurrentSession?.Script.Manifest.Name == script.Manifest.Name)
                {
                    try { StopCurrentScript(); } catch { /* ignore */ }
                }

                if (Directory.Exists(script.RootPath))
                {
                    Directory.Delete(script.RootPath, recursive: true);
                }
                Directory.CreateDirectory(Path.GetDirectoryName(script.RootPath)!);
                Directory.Move(tempExtract, script.RootPath);
            }

            WritePackageMetadata(script.RootPath, meta.SourceUrl!, meta.BranchOrTag);
            ReloadLibrary();
            return _scripts.FirstOrDefault(s => s.RootPath.Equals(script.RootPath, StringComparison.OrdinalIgnoreCase));
        }
        catch (Exception ex)
        {
            Logger.LogError($"[ScriptLibrary] Update failed for {script.Manifest.Name}", ex);
            throw;
        }
        finally
        {
            try { if (File.Exists(tempZip)) File.Delete(tempZip); } catch { }
            try { if (Directory.Exists(tempExtract)) Directory.Delete(tempExtract, recursive: true); } catch { }
        }
    }

    public void UninstallScript(ScriptDefinition script)
    {
        lock (_lock)
        {
            if (CurrentSession?.Script.Manifest.Name == script.Manifest.Name)
            {
                try { StopCurrentScript(); } catch { /* best effort */ }
            }

            if (Directory.Exists(script.RootPath))
            {
                Directory.Delete(script.RootPath, recursive: true);
            }
        }

        ReloadLibrary();
    }

    private static string BuildTargetFolderName(string sourceUrl, string? branchOrTag)
    {
        try
        {
            var uri = new Uri(sourceUrl);
            var segments = uri.AbsolutePath.Trim('/').Split('/', StringSplitOptions.RemoveEmptyEntries);
            if (segments.Length >= 2)
            {
                var repo = segments[1];
                if (repo.EndsWith(".git", StringComparison.OrdinalIgnoreCase))
                {
                    repo = repo[..^4];
                }
                var suffix = string.IsNullOrWhiteSpace(branchOrTag) ? "main" : branchOrTag.Trim();
                return $"{repo}_{suffix}_{DateTime.UtcNow:yyyyMMddHHmmss}";
            }
        }
        catch
        {
            // fallback below
        }

        return $"github_{DateTime.UtcNow:yyyyMMddHHmmss}";
    }

    private static string ResolveGitHubDownloadUrl(string url, string? branchOrTag)
    {
        if (url.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
        {
            return url;
        }

        string refName = string.IsNullOrWhiteSpace(branchOrTag) ? "main" : branchOrTag.Trim();

        try
        {
            var uri = new Uri(url);
            if (!uri.Host.Contains("github.com", StringComparison.OrdinalIgnoreCase))
            {
                return url; // not GitHub, assume direct zip/asset
            }

            var parts = uri.AbsolutePath.Trim('/').Split('/', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length >= 2)
            {
                string owner = parts[0];
                string repo = parts[1].EndsWith(".git", StringComparison.OrdinalIgnoreCase) ? parts[1][..^4] : parts[1];

                // If /tree/{branch} provided, respect it.
                int treeIndex = Array.IndexOf(parts, "tree");
                if (treeIndex >= 0 && parts.Length > treeIndex + 1)
                {
                    refName = parts[treeIndex + 1];
                }

                return $"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{refName}";
            }
        }
        catch
        {
            // fall through
        }

        return url;
    }

    public void ReloadLibrary()
    {
        lock (_lock)
        {
            var discovered = new List<ScriptDefinition>();
            string libraryPath = StorageUtils.GetScriptLibraryPath();

            if (!Directory.Exists(libraryPath))
            {
                Directory.CreateDirectory(libraryPath);
                _scripts = discovered;
                return;
            }

            foreach (var scriptDir in Directory.GetDirectories(libraryPath))
            {
                var manifestPath = Path.Combine(scriptDir, "manifest.json");
                if (!File.Exists(manifestPath))
                {
                    Logger.Log($"[ScriptLibrary] manifest.json missing in {scriptDir}");
                    continue;
                }

                ScriptManifest? manifest;
                try
                {
                    string manifestText = File.ReadAllText(manifestPath);
                    manifest = JsonSerializer.Deserialize<ScriptManifest>(manifestText, _jsonOptions);
                }
                catch (Exception ex)
                {
                    Logger.LogError($"[ScriptLibrary] Failed to read manifest at {manifestPath}", ex);
                    continue;
                }

                if (manifest == null || string.IsNullOrWhiteSpace(manifest.Name) || string.IsNullOrWhiteSpace(manifest.EntryPoint))
                {
                    Logger.Log($"[ScriptLibrary] Invalid manifest at {manifestPath}");
                    continue;
                }

                var packageMeta = TryReadPackageMetadata(scriptDir);
                var errors = ValidateManifest(scriptDir, manifest);
                var definition = new ScriptDefinition(manifestPath, manifest, scriptDir, packageMeta, errors.ToArray());
                discovered.Add(definition);

                if (errors.Count > 0)
                {
                    Logger.Log($"[ScriptLibrary] Validation warnings for {manifest.Name}: {string.Join("; ", errors)}");
                }
            }

            _scripts = discovered;
        }
    }

    public ScriptRunSession StartScript(ScriptDefinition script)
    {
        lock (_lock)
        {
            if (CurrentSession != null)
            {
                throw new InvalidOperationException("A script is already running. Stop it before starting another.");
            }

            if (PreflightCheck != null)
            {
                var result = PreflightCheck.Invoke(script);
                if (!result.Allowed)
                {
                    var msg = string.IsNullOrWhiteSpace(result.Reason) ? "Preflight check failed." : result.Reason;
                    throw new InvalidOperationException(msg);
                }
            }

            string entryFullPath = Path.Combine(script.RootPath, script.Manifest.EntryPoint);
            if (!File.Exists(entryFullPath))
            {
                throw new FileNotFoundException("Script entry point not found", entryFullPath);
            }

            if (DryRun)
            {
                Logger.LogScriptEvent(script.Manifest.Name, "Dry run enabled - not launching process");
                DevTelemetry.Log("Scripts", $"Dry run start for {script.Manifest.Name} (source={script.PackageInfo?.SourceUrl ?? "unknown"})");
                var fakeProcess = Process.GetCurrentProcess();
                var drySession = new ScriptRunSession(script, fakeProcess, DateTime.UtcNow);
                CurrentSession = drySession;
                return drySession;
            }

            var process = LaunchProcess(entryFullPath, script.Manifest.Arguments ?? string.Empty, script.RootPath);
            var session = new ScriptRunSession(script, process, DateTime.UtcNow);
            CurrentSession = session;
            var src = script.PackageInfo?.SourceUrl;
            if (!string.IsNullOrWhiteSpace(src))
            {
                Logger.LogScriptEvent(script.Manifest.Name, $"Started (source: {src})");
            }
            else
            {
                Logger.LogScriptEvent(script.Manifest.Name, "Started");
            }
            DevTelemetry.Log("Scripts", $"Started {script.Manifest.Name} (source={src ?? "unknown"})");

            process.EnableRaisingEvents = true;
            process.Exited += (sender, args) =>
            {
                lock (_lock)
                {
                    Logger.LogScriptEvent(script.Manifest.Name, $"Exited with code {process.ExitCode}");
                    CurrentSession = null;
                }
            };

            return session;
        }
    }

    public void StopCurrentScript()
    {
        lock (_lock)
        {
            var session = CurrentSession;
            if (session == null)
            {
                return;
            }

            try
            {
                if (!session.Process.HasExited)
                {
                    session.Process.Kill();
                    session.Process.WaitForExit(2000);
                }

                Logger.LogScriptEvent(session.Script.Manifest.Name, "Stopped");
                DevTelemetry.Log("Scripts", $"Stopped {session.Script.Manifest.Name}");
            }
            catch (Exception ex)
            {
                Logger.LogError($"[ScriptLibrary] Failed to stop {session.Script.Manifest.Name}", ex);
                DevTelemetry.Log("Scripts", $"Stop failed for {session.Script.Manifest.Name}: {ex.Message}");
            }
            finally
            {
                CurrentSession = null;
            }
        }
    }

    private static Process LaunchProcess(string entryFullPath, string arguments, string workingDirectory)
    {
        var extension = Path.GetExtension(entryFullPath);
        ProcessStartInfo startInfo;

        if (extension.Equals(".exe", StringComparison.OrdinalIgnoreCase))
        {
            startInfo = new ProcessStartInfo(entryFullPath, arguments)
            {
                WorkingDirectory = workingDirectory,
                UseShellExecute = false,
                CreateNoWindow = true
            };
        }
        else
        {
            startInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"{entryFullPath}\" {arguments}".Trim(),
                WorkingDirectory = workingDirectory,
                UseShellExecute = false,
                CreateNoWindow = true
            };
        }

        var process = new Process { StartInfo = startInfo };
        process.Start();
        return process;
    }

    private static List<string> ValidateManifest(string scriptDir, ScriptManifest manifest)
    {
        var errors = new List<string>();

        if (string.IsNullOrWhiteSpace(manifest.Name))
        {
            errors.Add("Name is required");
        }

        if (string.IsNullOrWhiteSpace(manifest.EntryPoint))
        {
            errors.Add("Entry point is required");
        }
        else
        {
            string entryFullPath = Path.Combine(scriptDir, manifest.EntryPoint);
            if (!File.Exists(entryFullPath))
            {
                errors.Add("Entry point missing");
            }
        }

        if (!string.IsNullOrWhiteSpace(manifest.RequiredResolution))
        {
            string required = manifest.RequiredResolution.Trim();
            bool supported = StateManager.SupportedResolutions.Any(r =>
                r.Equals(required, StringComparison.OrdinalIgnoreCase));

            if (!supported)
            {
                errors.Add($"Unsupported resolution: {required}");
            }
            else if (!string.Equals(required, StateManager.Instance.SelectedResolution, StringComparison.OrdinalIgnoreCase))
            {
                errors.Add($"Requires {required} resolution");
            }
        }

        if (manifest.RequiredTemplates != null && manifest.RequiredTemplates.Length > 0)
        {
            foreach (var template in manifest.RequiredTemplates)
            {
                string templatePath = Path.Combine(StorageUtils.GetAppPath(), template);
                if (!File.Exists(templatePath))
                {
                    errors.Add($"Missing template asset: {template}");
                }
            }
        }

        return errors;
    }

    private ScriptPackageMetadata? TryReadPackageMetadata(string scriptDir)
    {
        try
        {
            var path = Path.Combine(scriptDir, PackageMetaFileName);
            if (!File.Exists(path)) return null;
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<ScriptPackageMetadata>(json, _jsonOptions);
        }
        catch
        {
            return null;
        }
    }

    private void WritePackageMetadata(string scriptDir, string sourceUrl, string? branchOrTag)
    {
        try
        {
            var meta = new ScriptPackageMetadata
            {
                SourceUrl = sourceUrl,
                BranchOrTag = branchOrTag,
                InstalledAtUtc = DateTime.UtcNow
            };
            var path = Path.Combine(scriptDir, PackageMetaFileName);
            File.WriteAllText(path, JsonSerializer.Serialize(meta, _jsonOptions));
        }
        catch
        {
            // best effort
        }
    }

    private static async Task ExtractZipToDestinationAsync(string zipPath, string destination, bool flattenSingleFolder)
    {
        if (Directory.Exists(destination))
        {
            Directory.Delete(destination, recursive: true);
        }
        Directory.CreateDirectory(destination);

        ZipFile.ExtractToDirectory(zipPath, destination, overwriteFiles: true);

        if (flattenSingleFolder)
        {
            var subDirs = Directory.GetDirectories(destination);
            if (!File.Exists(Path.Combine(destination, "manifest.json")) && subDirs.Length == 1)
            {
                var inner = subDirs[0];
                foreach (var file in Directory.GetFiles(inner, "*", SearchOption.AllDirectories))
                {
                    var relative = Path.GetRelativePath(inner, file);
                    var target = Path.Combine(destination, relative);
                    Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                    File.Copy(file, target, overwrite: true);
                }

                Directory.Delete(subDirs[0], recursive: true);
            }
        }
    }
}
