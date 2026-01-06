using ProjectMaelstrom.Models;
using System;
using System.Collections.Generic;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Thin coordinator that funnels script starts, SmartPlay queue actions, and resource guards through a single path.
/// Non-UI consumers can use this to operate the trainer without wiring UI controls directly.
/// </summary>
internal sealed class BridgeCoordinator
{
    private readonly ScriptLibraryService _scripts;
    private readonly SmartPlayManager _smartPlay;
    private Func<ScriptDefinition, PreflightResult>? _preflight;

    public event Action<string>? OnStatus;
    public event Action<string>? OnWarning;
    public event Action<string>? OnRunHistory;

    public BridgeCoordinator(ScriptLibraryService scripts, SmartPlayManager smartPlay)
    {
        _scripts = scripts;
        _smartPlay = smartPlay;
    }

    public void SetPreflight(Func<ScriptDefinition, PreflightResult> preflight)
    {
        _preflight = preflight;
    }

    public bool TryStartScript(ScriptDefinition script)
    {
        if (_preflight != null)
        {
            var result = _preflight(script);
            if (!result.Allowed)
            {
                var msg = string.IsNullOrWhiteSpace(result.Reason) ? "Blocked by preflight." : result.Reason;
                OnWarning?.Invoke(msg);
                return false;
            }
        }

        try
        {
            _scripts.StartScript(script);
            OnStatus?.Invoke($"Started {script.Manifest.Name}");
            return true;
        }
        catch (Exception ex)
        {
            OnWarning?.Invoke($"Start failed: {ex.Message}");
            return false;
        }
    }

    public void StopCurrentScript()
    {
        try
        {
            _scripts.StopCurrentScript();
            OnStatus?.Invoke("Stopped current script");
        }
        catch (Exception ex)
        {
            OnWarning?.Invoke($"Stop failed: {ex.Message}");
        }
    }

    public void EnqueueNavigationToBazaar()
    {
        _smartPlay.EnqueueNavigationToBazaar();
        OnRunHistory?.Invoke("Queued navigation: Bazaar");
    }

    public void EnqueueNavigationToMiniGames()
    {
        _smartPlay.EnqueueNavigationToMiniGames();
        OnRunHistory?.Invoke("Queued navigation: Mini Games");
    }

    public void EnqueueNavigationToPetPavilion()
    {
        _smartPlay.EnqueueNavigationToPetPavilion();
        OnRunHistory?.Invoke("Queued navigation: Pet Pavilion");
    }

    public void EnqueuePotionRefill()
    {
        _smartPlay.EnqueuePotionRefillRun();
        OnRunHistory?.Invoke("Queued potion refill run");
    }

    public void EnqueueScriptRun(string scriptName)
    {
        _smartPlay.EnqueueScriptRun(scriptName);
        OnRunHistory?.Invoke($"Queued script run: {scriptName}");
    }

    public void NotifyWarning(string message)
    {
        if (string.IsNullOrWhiteSpace(message)) return;
        OnWarning?.Invoke(message);
    }

    public void NotifyStatus(string message)
    {
        if (string.IsNullOrWhiteSpace(message)) return;
        OnStatus?.Invoke(message);
    }
}
