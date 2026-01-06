using System.Diagnostics;

namespace MaelstromToolkit.Handoff;

internal sealed class GitInfoProvider : IGitInfoProvider
{
    public string Commit { get; }
    public string Branch { get; }
    public bool IsDirty { get; }

    public GitInfoProvider()
    {
        Commit = ResolveCommit();
        Branch = TryGit("rev-parse --abbrev-ref HEAD") ?? "unknown";
        IsDirty = ResolveDirty();
    }

    private static string ResolveCommit()
    {
        var fromEnv = Environment.GetEnvironmentVariable("GITHUB_SHA");
        if (!string.IsNullOrWhiteSpace(fromEnv)) return fromEnv.Trim();
        return TryGit("rev-parse HEAD") ?? "unknown";
    }

    private static bool ResolveDirty()
    {
        var status = TryGit("status --porcelain");
        if (status == null) return false;
        return status.Split('\n', StringSplitOptions.RemoveEmptyEntries).Length > 0;
    }

    private static string? TryGit(string arguments)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "git",
                Arguments = arguments,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using var proc = Process.Start(psi);
            if (proc == null) return null;
            proc.WaitForExit(2000);
            if (proc.ExitCode == 0)
            {
                return proc.StandardOutput.ReadToEnd().Trim();
            }
        }
        catch
        {
            // ignore
        }
        return null;
    }
}
