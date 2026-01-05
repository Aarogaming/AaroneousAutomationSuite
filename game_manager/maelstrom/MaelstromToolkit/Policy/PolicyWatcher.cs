using System.Text;

namespace MaelstromToolkit.Policy;

internal sealed class PolicyWatcher : IDisposable
{
    private readonly string _policyPath;
    private readonly string _lkgPath;
    private readonly PolicyParser _parser = new();
    private FileSystemWatcher? _watcher;
    private PolicyDocument? _current;
    private readonly object _lock = new();

    public PolicyWatcher(string policyPath, string lkgDirectory)
    {
        _policyPath = Path.GetFullPath(policyPath);
        Directory.CreateDirectory(lkgDirectory);
        _lkgPath = Path.Combine(lkgDirectory, "lkg.policy.txt");
    }

    public PolicyDocument? Current
    {
        get
        {
            lock (_lock) return _current;
        }
    }

    public PolicyLoadResult Load()
    {
        var text = File.Exists(_policyPath) ? File.ReadAllText(_policyPath) : string.Empty;
        var result = _parser.Parse(text);
        if (!result.HasErrors && result.Document != null)
        {
            lock (_lock) _current = result.Document;
            WriteAtomic(_lkgPath, text);
        }
        else
        {
            TryLoadLkg(result);
        }
        return result;
    }

    public void Watch(Action<string> onInfo, Action<string> onError)
    {
        Load();
        var directory = Path.GetDirectoryName(_policyPath);
        if (string.IsNullOrWhiteSpace(directory))
        {
            onError($"Cannot watch policy path; invalid directory for {_policyPath}");
            return;
        }

        _watcher = new FileSystemWatcher(directory, Path.GetFileName(_policyPath))
        {
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size | NotifyFilters.FileName
        };

        _watcher.Changed += (_, __) => HandleReload(onInfo, onError);
        _watcher.Created += (_, __) => HandleReload(onInfo, onError);
        _watcher.Renamed += (_, __) => HandleReload(onInfo, onError);
        _watcher.EnableRaisingEvents = true;
    }

    private void HandleReload(Action<string> onInfo, Action<string> onError)
    {
        var result = Load();
        if (result.HasErrors)
        {
            var errs = result.SortedDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).Select(d => d.Message);
            onError(string.Join(Environment.NewLine, errs));
        }
        else
        {
            onInfo($"Reloaded policy at {DateTimeOffset.UtcNow:o}");
        }
    }

    private void TryLoadLkg(PolicyLoadResult result)
    {
        if (!File.Exists(_lkgPath))
        {
            return;
        }

        var text = File.ReadAllText(_lkgPath);
        var lkg = _parser.Parse(text);
        if (lkg.Document != null && !lkg.HasErrors)
        {
            lock (_lock) _current = lkg.Document;
            result.Diagnostics.Add(new PolicyDiagnostic("AASPOL010", DiagnosticSeverity.Warning, "lkg", "fallback", null, "Fell back to last known good policy."));
        }
    }

    private static void WriteAtomic(string target, string content)
    {
        var directory = Path.GetDirectoryName(target);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }
        var tmp = target + ".tmp_" + Guid.NewGuid().ToString("N");
        File.WriteAllText(tmp, content, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.Move(tmp, target, overwrite: true);
    }

    public void Dispose()
    {
        _watcher?.Dispose();
    }
}
