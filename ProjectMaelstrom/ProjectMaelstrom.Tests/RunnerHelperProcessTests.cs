using System;
using System.Diagnostics;
using System.IO;
using Xunit;

namespace ProjectMaelstrom.Tests;

public class RunnerHelperProcessTests
{
    private static string HelperPath => Path.Combine(AppContext.BaseDirectory, "Maelstrom.TestProcess.dll");

    [Fact]
    public void Helper_WritesLargeStdout()
    {
        var payload = new string('A', 1_000);
        var output = RunHelper($"--stdout \"{payload}\"");
        Assert.Equal(payload, output.stdout);
        Assert.Equal(0, output.exit);
    }

    [Fact]
    public void Helper_WritesLargeStderr()
    {
        var payload = new string('B', 1_000);
        var output = RunHelper($"--stderr \"{payload}\" --exit 5");
        Assert.Equal(payload, output.stderr);
        Assert.Equal(5, output.exit);
    }

    [Fact]
    public void Helper_PrintsWorkingDirectory()
    {
        using var temp = new TempFolder();
        var output = RunHelper("--printCwd", workingDir: temp.Path);
        Assert.Equal(temp.Path, output.stdout);
    }

    [Fact]
    public void Helper_PrintsEnvironmentVariable()
    {
        var envKey = "MTK_TEST_ENV";
        var envVal = Guid.NewGuid().ToString("N");
        var output = RunHelper($"--printEnv {envKey}", envVars: new() { [envKey] = envVal });
        Assert.Equal(envVal, output.stdout);
    }

    [Fact]
    public void Helper_HandlesInterleavedOutAndErr()
    {
        var output = RunHelper("--stdout OUT --stderr ERR");
        Assert.Equal("OUT", output.stdout);
        Assert.Equal("ERR", output.stderr);
    }

    [Fact]
    public void Helper_RespectsSleepForTimeoutCheck()
    {
        var sw = Stopwatch.StartNew();
        var output = RunHelper("--stdout done --sleepMs 200");
        sw.Stop();
        Assert.True(sw.ElapsedMilliseconds >= 180);
        Assert.Equal("done", output.stdout);
    }

    private static (string stdout, string stderr, int exit) RunHelper(string arguments, string? workingDir = null, Dictionary<string, string>? envVars = null)
    {
        Assert.True(File.Exists(HelperPath), $"Helper not found at {HelperPath}");

        var psi = new ProcessStartInfo("dotnet", $"\"{HelperPath}\" {arguments}")
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        if (!string.IsNullOrWhiteSpace(workingDir))
        {
            psi.WorkingDirectory = workingDir;
        }

        if (envVars != null)
        {
            foreach (var kvp in envVars)
            {
                psi.Environment[kvp.Key] = kvp.Value;
            }
        }

        using var proc = Process.Start(psi)!;
        var stdout = proc.StandardOutput.ReadToEnd();
        var stderr = proc.StandardError.ReadToEnd();
        if (!proc.WaitForExit(5000))
        {
            try { proc.Kill(entireProcessTree: true); } catch { /* ignore */ }
            throw new TimeoutException("Helper process did not exit within timeout.");
        }

        return (stdout, stderr, proc.ExitCode);
    }

    private sealed class TempFolder : IDisposable
    {
        public string Path { get; }
        public TempFolder()
        {
            Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), $"maelstrom_helper_{Guid.NewGuid():N}");
            Directory.CreateDirectory(Path);
        }

        public void Dispose()
        {
            try { Directory.Delete(Path, recursive: true); } catch { /* ignore */ }
        }
    }
}
