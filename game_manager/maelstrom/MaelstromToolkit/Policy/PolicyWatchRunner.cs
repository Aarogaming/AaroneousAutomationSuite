using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace MaelstromToolkit.Policy;

internal sealed class PolicyWatchRunner
{
    private readonly string _policyPath;
    private readonly string _outRoot;
    private readonly PolicyEffectiveResolver _resolver;
    private readonly PolicyApplyRecorder _recorder = new();
    private PolicyEffectiveResult _current;

    public PolicyWatchRunner(string policyPath, string outRoot, string defaultPolicyText)
    {
        _policyPath = policyPath;
        _outRoot = outRoot;
        _resolver = new PolicyEffectiveResolver(defaultPolicyText);
        _current = ResolveInitial();
    }

    public int Run()
    {
        PrintCurrent("INIT", _current);
        WriteWatchLast(_current);

        var directory = Path.GetDirectoryName(_policyPath);
        var fileName = Path.GetFileName(_policyPath);
        if (string.IsNullOrEmpty(directory)) directory = ".";

        using var watcher = new FileSystemWatcher(directory, fileName)
        {
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size | NotifyFilters.FileName | NotifyFilters.Attributes,
            EnableRaisingEvents = true
        };

        var exit = new ManualResetEventSlim(false);
        Console.CancelKeyPress += (_, e) => { e.Cancel = true; exit.Set(); };

        Timer? debounce = null;
        FileSystemEventHandler handler = (_, __) =>
        {
            debounce?.Dispose();
            debounce = new Timer(_ =>
            {
                EvaluateChange();
            }, null, 400, Timeout.Infinite);
        };

        watcher.Changed += handler;
        watcher.Created += handler;
        watcher.Renamed += (_, __) => EvaluateChange();

        exit.Wait();
        debounce?.Dispose();
        return 0;
    }

    private PolicyEffectiveResult ResolveInitial()
    {
        var fileText = SafeReadFile(_policyPath);
        var lkgPath = Path.Combine(_outRoot, "system", "policy.lkg.txt");
        var lkgText = File.Exists(lkgPath) ? SafeReadFile(lkgPath) : null;
        var result = _resolver.Resolve(fileText ?? string.Empty, lkgText);
        if (result.IsValid && result.Source is "FILE" or "LKG")
        {
            WriteLkg(result.RawText, result.Hash);
        }
        return result;
    }

    private void EvaluateChange()
    {
        var previousText = _current.RawText;
        var previousHash = _current.Hash;
        var fileText = TryReadWithRetry(_policyPath, 5, 100);
        if (fileText == null)
        {
            Console.WriteLine($"REJECTED fileLockedOrUnreadable kept={_current.Hash}");
            return;
        }

        var parser = new PolicyParser();
        var load = parser.Parse(fileText);
        var diagnostics = load.SortedDiagnostics().ToList();

        PolicyValidationResult? validation = null;
        if (load.Document != null && !load.HasErrors)
        {
            var snapshot = PolicySnapshot.FromDocument(load.Document);
            validation = new PolicyValidator().Validate(snapshot);
            diagnostics.AddRange(validation.Diagnostics);
        }

        var ordered = diagnostics
            .OrderBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.Section, StringComparer.Ordinal)
            .ThenBy(d => d.Key, StringComparer.Ordinal)
            .ThenBy(d => d.LineNumber ?? int.MaxValue)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();

        var hasErrors = ordered.Any(d => d.Severity == DiagnosticSeverity.Error);
        if (hasErrors || validation == null || validation.Snapshot == null)
        {
            WriteRejected(_outRoot, ordered);
            var top5 = string.Join(",", ordered.Take(5).Select(d => d.Code));
            Console.WriteLine($"REJECTED kept={_current.Hash} codes={top5}");
            return;
        }

        var textNormalized = Normalize(fileText);
        var hash = ComputeSha256(textNormalized);
        var next = new PolicyEffectiveResult(
            Source: "FILE",
            Hash: hash,
            Snapshot: validation.Snapshot,
            ActiveProfile: validation.Snapshot.Global.ActiveProfile,
            ProfileMode: validation.Snapshot.Profiles.TryGetValue(validation.Snapshot.Global.ActiveProfile, out var p) ? p.Mode.ToUpperInvariant() : "UNKNOWN",
            OperatingMode: validation.OperatingMode,
            LiveStatus: validation.LiveStatus,
            Reasons: validation.Reasons,
            Diagnostics: ordered,
            FileDiagnostics: Array.Empty<PolicyDiagnostic>(),
            LkgDiagnostics: Array.Empty<PolicyDiagnostic>(),
            RawText: textNormalized);

        _recorder.Record(_outRoot, _policyPath, next, textNormalized, previousText, previousHash);
        _current = next;
        WriteLkg(textNormalized, hash);
        WriteWatchLast(_current);
        Console.WriteLine($"ACCEPTED hash={hash} profile={_current.ActiveProfile} mode={_current.OperatingMode} liveStatus={_current.LiveStatus}");
    }

    private static string? TryReadWithRetry(string path, int attempts, int delayMs)
    {
        for (var i = 0; i < attempts; i++)
        {
            try
            {
                return File.ReadAllText(path);
            }
            catch (IOException)
            {
                Thread.Sleep(delayMs);
            }
        }
        return null;
    }

    private static string? SafeReadFile(string path)
    {
        try
        {
            return File.ReadAllText(path);
        }
        catch
        {
            return null;
        }
    }

    private void PrintCurrent(string label, PolicyEffectiveResult result)
    {
        Console.WriteLine($"{label} Source={result.Source} hash={result.Hash} activeProfile={result.ActiveProfile} profileMode={result.ProfileMode} operatingMode={result.OperatingMode} liveStatus={result.LiveStatus}");
    }

    private void WriteLkg(string content, string hash)
    {
        var systemDir = Path.Combine(_outRoot, "system");
        Directory.CreateDirectory(systemDir);
        WriteAtomic(Path.Combine(systemDir, "policy.lkg.txt"), content);
        WriteAtomic(Path.Combine(systemDir, "policy.lkg.sha256"), hash);
    }

    private void WriteWatchLast(PolicyEffectiveResult result)
    {
        var systemDir = Path.Combine(_outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.watch.last.txt");
        var sb = new StringBuilder();
        sb.AppendLine($"Source: {result.Source}");
        sb.AppendLine($"Hash: {result.Hash}");
        sb.AppendLine($"ActiveProfile: {result.ActiveProfile}");
        sb.AppendLine($"ProfileMode: {result.ProfileMode}");
        sb.AppendLine($"OperatingMode: {result.OperatingMode}");
        sb.AppendLine($"LiveStatus: {result.LiveStatus}");
        sb.AppendLine($"LiveReasons: {(result.Reasons.Count == 0 ? "none" : string.Join(",", result.Reasons))}");
        WriteAtomic(path, sb.ToString());
    }

    private static void WriteRejected(string outRoot, IReadOnlyList<PolicyDiagnostic> diagnostics)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.rejected.txt");
        var sb = new StringBuilder();
        foreach (var d in diagnostics)
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code} | {d.Severity} | {d.Section}.{d.Key} | {line} | {d.Message}");
        }
        WriteAtomic(path, sb.ToString());
    }

    private static void WriteAtomic(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var tmp = path + ".tmp_" + Guid.NewGuid().ToString("N");
        File.WriteAllText(tmp, Normalize(content), new UTF8Encoding(false));
        File.Move(tmp, path, overwrite: true);
    }

    private static string Normalize(string input) =>
        input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\r", "\n", StringComparison.Ordinal);

    private static string ComputeSha256(string text)
    {
        using var sha = SHA256.Create();
        var bytes = Encoding.UTF8.GetBytes(Normalize(text));
        var hash = sha.ComputeHash(bytes);
        return BitConverter.ToString(hash).Replace("-", string.Empty).ToLowerInvariant();
    }
}
