using System.Security.Cryptography;
using System.Text;

namespace MaelstromToolkit.Policy;

internal sealed class PolicyService
{
    private readonly PolicyParser _parser = new();

    public PolicyLoadResult Load(string policyPath)
    {
        var text = File.Exists(policyPath) ? File.ReadAllText(policyPath) : string.Empty;
        return _parser.Parse(text);
    }

    public void WriteDiagnostics(string outRoot, PolicyLoadResult result)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var diagPath = Path.Combine(systemDir, "policy.diagnostics.txt");
        var sb = new StringBuilder();
        foreach (var d in result.SortedDiagnostics())
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code}|{d.Severity}|{d.Section}|{d.Key}|{line}|{d.Message}");
        }
        WriteAtomic(diagPath, sb.ToString());
    }

    public void WriteRejected(string outRoot, PolicyLoadResult result)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.rejected.txt");
        var sb = new StringBuilder();
        foreach (var d in result.SortedDiagnostics())
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code}|{d.Severity}|{d.Section}|{d.Key}|{line}|{d.Message}");
        }
        WriteAtomic(path, sb.ToString());
    }

    public string WriteLkg(string outRoot, string content)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var lkgPath = Path.Combine(systemDir, "policy.lkg.txt");
        WriteAtomic(lkgPath, content);
        var hash = ComputeSha256(content);
        WriteAtomic(Path.Combine(systemDir, "policy.lkg.sha256"), hash);
        return hash;
    }

    private static string ComputeSha256(string text)
    {
        using var sha = SHA256.Create();
        var bytes = Encoding.UTF8.GetBytes(NormalizeLineEndings(text));
        var hash = sha.ComputeHash(bytes);
        return BitConverter.ToString(hash).Replace("-", string.Empty).ToLowerInvariant();
    }

    private static void WriteAtomic(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var tmp = path + ".tmp_" + Guid.NewGuid().ToString("N");
        File.WriteAllText(tmp, NormalizeLineEndings(content), new UTF8Encoding(false));
        File.Move(tmp, path, overwrite: true);
    }

    private static string NormalizeLineEndings(string input) =>
        input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\r", "\n", StringComparison.Ordinal);
}
