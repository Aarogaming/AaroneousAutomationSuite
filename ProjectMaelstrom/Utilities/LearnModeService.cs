using System.Text.Json;
using ProjectMaelstrom.Models;
using ProjectMaelstrom.Modules.ImageRecognition;

namespace ProjectMaelstrom.Utilities;

internal sealed class LearnModeService : IDisposable
{
    private readonly SmartPlayManager _smartPlay;
    private readonly WizWikiDataService _wikiData = WizWikiDataService.Instance;
    private readonly string _logDir;
    private System.Threading.Timer? _timer;
    private bool _running;
    private readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = true };
    private readonly string[] _snackKeywords = new[] { "snack", "treat" };
    private readonly string[] _schoolKeywords = new[] { "fire", "ice", "storm", "myth", "balance", "life", "death" };
    private readonly string[] _reagentKeywords = new[] { "reagent", "ore", "scrap", "onyx", "peridot", "opal", "sapphire", "stone", "wood", "resin", "scale", "pearl" };
    private readonly string[] _questKeywords = new[] { "quest", "goal", "talk to", "defeat", "collect" };
    private readonly HashSet<string> _assetHits = new(StringComparer.OrdinalIgnoreCase);
    private LearnModeProfile _profile = LearnModeProfile.Mixed;

    public bool IsRunning => _running;

    public LearnModeService(SmartPlayManager smartPlay)
    {
        _smartPlay = smartPlay;
        _logDir = Path.Combine(AppContext.BaseDirectory, "logs", "learn_mode");
    }

    public void Start(TimeSpan? interval = null)
    {
        if (_running) return;
        Directory.CreateDirectory(_logDir);
        _running = true;
        EnqueueScanCycle();
        _timer = new System.Threading.Timer(async _ => await TickAsync(), null, interval ?? TimeSpan.FromMinutes(2), interval ?? TimeSpan.FromMinutes(2));
        DevTelemetry.Log("LearnMode", "Started");

        // Build WAD index once per session for quick lookups.
        WadIndexService.BuildIndex();
        WadIndexService.BuildAssetManifests();
    }

    public void SetProfile(LearnModeProfile profile)
    {
        _profile = profile;
        DevTelemetry.Log("LearnMode", $"Profile set to {_profile}");
    }

    public void Stop()
    {
        if (!_running) return;
        _running = false;
        _timer?.Dispose();
        _timer = null;
        DevTelemetry.Log("LearnMode", "Stopped");
    }

    private async Task TickAsync()
    {
        if (!_running) return;
        try
        {
            EnqueueScanCycle();
            await CaptureSnapshotAsync();
        }
        catch (Exception ex)
        {
            DevTelemetry.Log("LearnMode", $"Tick failed: {ex.Message}");
        }
    }

    private void EnqueueScanCycle()
    {
        switch (_profile)
        {
            case LearnModeProfile.Seek:
                // Favor encounters/targets: hit mini-games and pet pavilion more aggressively.
                _smartPlay.EnqueueNavigationToMiniGames();
                _smartPlay.EnqueueNavigationToPetPavilion();
                _smartPlay.EnqueueNavigationToBazaar();
                _smartPlay.EnqueueNavigationToMiniGames();
                if (_wikiData.HasData)
                {
                    var zones = _wikiData.GetZones().Take(3).ToArray();
                    if (zones.Length > 0)
                    {
                        DevTelemetry.Log("LearnMode", $"Seek profile hints (WizWiki zones): {string.Join(", ", zones)}");
                    }
                }
                break;
            case LearnModeProfile.Avoid:
                // Minimize encounters: keep it light, avoid extra loops.
                _smartPlay.EnqueueNavigationToBazaar();
                break;
            case LearnModeProfile.Mixed:
            default:
                // Balanced loop: Bazaar -> Pet Pavilion -> Mini Games.
                _smartPlay.EnqueueNavigationToBazaar();
                _smartPlay.EnqueueNavigationToPetPavilion();
                _smartPlay.EnqueueNavigationToMiniGames();
                break;
        }

        // Future: add commons loop/quest focus and explicit monster seek/avoid waypoints.
    }

    private async Task CaptureSnapshotAsync()
    {
        try
        {
            var snap = await GameStateService.CaptureSnapshotAsync(StateManager.Instance.SelectedResolution);
            var stamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
            var jsonPath = Path.Combine(_logDir, $"learn_{stamp}.json");

            string? screenshot = ScreenCaptureService.CaptureWizardWindow();
            var findings = await AnalyzeScreenshotAsync(screenshot);

            var payload = new
            {
                Snapshot = snap,
                Screenshot = screenshot,
                Findings = findings,
                AssetsMatched = _assetHits.ToList()
            };

            File.WriteAllText(jsonPath, JsonSerializer.Serialize(payload, _jsonOptions));
            RecordFindings(findings);
            DevTelemetry.Log("LearnMode", $"Snapshot saved {Path.GetFileName(jsonPath)}");
        }
        catch (Exception ex)
        {
            DevTelemetry.Log("LearnMode", $"Snapshot failed: {ex.Message}");
        }
    }

    private void RecordFindings(LearnFindings findings)
    {
        // Best-effort logging of observed resources for routing. Zone/coords are unknown here; we tag as "Unknown".
        try
        {
            if (findings.Reagents.Count > 0)
            {
                foreach (var line in findings.Reagents.Take(3))
                {
                    _wikiData.RecordObservedSpawn(type: line, zone: "Unknown", source: "ocr");
                }
            }
        }
        catch
        {
            // Non-fatal; ignore recording errors.
        }
    }

    private async Task<LearnFindings> AnalyzeScreenshotAsync(string? screenshotPath)
    {
        var findings = new LearnFindings();
        if (string.IsNullOrWhiteSpace(screenshotPath) || !File.Exists(screenshotPath))
        {
            return findings;
        }

        try
        {
            WadAssetCache.EnsureLoaded();

            var text = await ImageHelpers.ExtractTextFromImage(screenshotPath);
            var lines = text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries)
                .Select(l => l.Trim())
                .Where(l => l.Length > 1)
                .ToList();
            findings.OcrLines = lines;

            foreach (var line in lines)
            {
                var lower = line.ToLowerInvariant();
                if (_snackKeywords.Any(k => lower.Contains(k)) || _schoolKeywords.Any(k => lower.Contains(k)))
                {
                    findings.Snacks.Add(line);
                }
                if (_reagentKeywords.Any(k => lower.Contains(k)))
                {
                    findings.Reagents.Add(line);
                }
                if (_questKeywords.Any(k => lower.Contains(k)))
                {
                    findings.Quests.Add(line);
                }

                var assetMatches = WadAssetCache.MatchLine(line);
                foreach (var hit in assetMatches)
                {
                    _assetHits.Add(hit);
                }
            }
        }
        catch (Exception ex)
        {
            DevTelemetry.Log("LearnMode", $"OCR analyze failed: {ex.Message}");
        }

        return findings;
    }

    private sealed class LearnFindings
    {
        public List<string> OcrLines { get; set; } = new();
        public List<string> Snacks { get; set; } = new();
        public List<string> Reagents { get; set; } = new();
        public List<string> Quests { get; set; } = new();
    }

    public void Dispose()
    {
        Stop();
    }
}
