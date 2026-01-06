using System;
using System.IO;
using System.Linq;
using System.Threading;
using Timer = System.Threading.Timer;

namespace HandoffTray;

internal class HandoffWatcher : IDisposable
{
    private readonly FileSystemWatcher _toWatcher;
    private readonly FileSystemWatcher _fromWatcher;
    private readonly Timer _debounceTimer;
    private readonly object _lock = new();
    private bool _changed;

    public event EventHandler<string>? PromptDetected;
    public event EventHandler<string>? ResultDetected;

    public HandoffWatcher(string toCodexDir, string fromCodexDir)
    {
        Directory.CreateDirectory(toCodexDir);
        Directory.CreateDirectory(fromCodexDir);

        _toWatcher = BuildWatcher(toCodexDir);
        _fromWatcher = BuildWatcher(fromCodexDir);
        _debounceTimer = new Timer(OnTimer, null, Timeout.Infinite, Timeout.Infinite);
    }

    private FileSystemWatcher BuildWatcher(string path)
    {
        var watcher = new FileSystemWatcher(path)
        {
            IncludeSubdirectories = false,
            EnableRaisingEvents = false,
            NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite,
            Filter = "*.*"
        };
        watcher.Created += OnChanged;
        watcher.Changed += OnChanged;
        watcher.Renamed += OnChanged;
        return watcher;
    }

    public void SetEnabled(bool watchTo, bool watchFrom)
    {
        _toWatcher.EnableRaisingEvents = watchTo;
        _fromWatcher.EnableRaisingEvents = watchFrom;
    }

    private void OnChanged(object? sender, FileSystemEventArgs e)
    {
        lock (_lock)
        {
            _changed = true;
            _debounceTimer.Change(300, Timeout.Infinite);
        }
    }

    private void OnTimer(object? state)
    {
        string? latestTo = null;
        string? latestFrom = null;
        lock (_lock)
        {
            if (!_changed) return;
            _changed = false;
            latestTo = GetLatest(_toWatcher.Path);
            latestFrom = GetLatest(_fromWatcher.Path);
        }

        if (latestTo != null)
        {
            PromptDetected?.Invoke(this, latestTo);
        }
        if (latestFrom != null)
        {
            ResultDetected?.Invoke(this, latestFrom);
        }
    }

    private static string? GetLatest(string path)
    {
        var dir = new DirectoryInfo(path);
        var file = dir.GetFiles("*", SearchOption.TopDirectoryOnly)
            .OrderByDescending(f => f.LastWriteTimeUtc)
            .FirstOrDefault();
        return file?.FullName;
    }

    public void Dispose()
    {
        _toWatcher.Dispose();
        _fromWatcher.Dispose();
        _debounceTimer.Dispose();
    }
}
