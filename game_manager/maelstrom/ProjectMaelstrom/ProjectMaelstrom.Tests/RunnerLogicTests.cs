using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using ProjectMaelstrom.Models;
using Xunit;

namespace ProjectMaelstrom.Tests;

public class RunnerLogicTests
{
    private static readonly Type ScriptLibrary = typeof(ProjectMaelstrom.Utilities.ScriptLibraryService);
    private static readonly MethodInfo BuildTargetFolderName = ScriptLibrary.GetMethod("BuildTargetFolderName", BindingFlags.NonPublic | BindingFlags.Static)!;
    private static readonly MethodInfo ResolveGitHubDownloadUrl = ScriptLibrary.GetMethod("ResolveGitHubDownloadUrl", BindingFlags.NonPublic | BindingFlags.Static)!;
    private static readonly MethodInfo ValidateManifest = ScriptLibrary.GetMethod("ValidateManifest", BindingFlags.NonPublic | BindingFlags.Static)!;

    [Theory]
    [InlineData("https://github.com/owner/repo", null, "repo_main_")]
    [InlineData("https://github.com/owner/repo.git", "dev", "repo_dev_")]
    public void BuildTargetFolderName_UsesRepoAndRef(string url, string? branch, string expectedPrefix)
    {
        var result = (string)BuildTargetFolderName.Invoke(null, new object?[] { url, branch })!;
        Assert.StartsWith(expectedPrefix, result, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("https://github.com/owner/repo", null, "owner/repo", "refs/heads/main")]
    [InlineData("https://github.com/owner/repo", "dev", "owner/repo", "refs/heads/dev")]
    [InlineData("https://github.com/owner/repo/tree/feature", null, "owner/repo", "refs/heads/feature")]
    public void ResolveGitHubDownloadUrl_MapsGitHubInputsToCodeload(string url, string? branch, string expectedPathPrefix, string expectedRef)
    {
        var result = (string)ResolveGitHubDownloadUrl.Invoke(null, new object?[] { url, branch })!;
        var uri = new Uri(result);

        Assert.Equal("https", uri.Scheme);
        Assert.Equal("codeload.github.com", uri.Host, StringComparer.OrdinalIgnoreCase);
        Assert.Equal($"/{expectedPathPrefix}/zip/{expectedRef}", uri.AbsolutePath, StringComparer.Ordinal);
    }

    [Fact]
    public void ResolveGitHubDownloadUrl_ReturnsNonGitHubUrlUnchanged()
    {
        const string url = "https://example.com/custom.zip";
        var result = (string)ResolveGitHubDownloadUrl.Invoke(null, new object?[] { url, null })!;
        Assert.Equal(url, result);
    }

    [Fact]
    public void LaunchProcess_RunsBatchInWorkingDirectory()
    {
        using var temp = new TempFolder();
        var script = temp.WriteScript("@echo %cd%>wd.txt\r\nexit /b 0");

        var process = InvokeLaunchProcess(script, arguments: string.Empty, temp.Path);
        Assert.True(process.WaitForExit(5000));
        Assert.Equal(0, process.ExitCode);

        var wdText = File.ReadAllText(Path.Combine(temp.Path, "wd.txt")).Trim();
        Assert.Equal(temp.Path, wdText, ignoreCase: true);
    }

    [Fact]
    public void LaunchProcess_PassesArgumentsWithSpaces()
    {
        using var temp = new TempFolder();
        var argsPath = Path.Combine(temp.Path, "args.txt");
        var script = temp.WriteScript($"""
@echo off
setlocal
echo %1 %2>"{argsPath}"
exit /b 0
""");

        var process = InvokeLaunchProcess(script, "arg1 arg2", temp.Path);
        Assert.True(process.WaitForExit(5000));
        Assert.Equal(0, process.ExitCode);

        Assert.True(File.Exists(argsPath), $"args file was not created; exit {process.ExitCode}");

        var args = File.ReadAllText(argsPath).Trim();
        Assert.Contains("arg1", args, StringComparison.Ordinal);
        Assert.Contains("arg2", args, StringComparison.Ordinal);
    }

    [Fact]
    public void LaunchProcess_HandlesLargeStdoutViaFile()
    {
        using var temp = new TempFolder();
        var script = temp.WriteScript("@for /l %%i in (1,1,400) do @echo LINE%%i>>out.txt\r\nexit /b 0");

        var process = InvokeLaunchProcess(script, string.Empty, temp.Path);
        Assert.True(process.WaitForExit(10000));
        Assert.Equal(0, process.ExitCode);

        var lines = File.ReadAllLines(Path.Combine(temp.Path, "out.txt"));
        Assert.True(lines.Length >= 400, "expected at least 400 lines of output");
    }

    [Fact]
    public void LaunchProcess_CanWriteStdErrToFile()
    {
        using var temp = new TempFolder();
        var script = temp.WriteScript("@echo ERR_MSG 1>&2\r\n@echo ERR_MSG>err.txt\r\nexit /b 0");

        var process = InvokeLaunchProcess(script, string.Empty, temp.Path);
        Assert.True(process.WaitForExit(5000));
        Assert.Equal(0, process.ExitCode);

        var err = File.ReadAllText(Path.Combine(temp.Path, "err.txt")).Trim();
        Assert.Equal("ERR_MSG", err);
    }

    [Fact]
    public void LaunchProcess_PreservesNonZeroExitCodes()
    {
        using var temp = new TempFolder();
        var script = temp.WriteScript("@exit /b 7");

        var process = InvokeLaunchProcess(script, string.Empty, temp.Path);
        Assert.True(process.WaitForExit(3000));
        Assert.Equal(7, process.ExitCode);
    }

    [Fact]
    public void LaunchProcess_WritesOutAndErrSeparately()
    {
        using var temp = new TempFolder();
        var script = temp.WriteScript("@echo OUTLINE>out.txt\r\n@echo ERRLINE 1>&2\r\n@echo ERRLINE>err.txt\r\nexit /b 0");

        var process = InvokeLaunchProcess(script, string.Empty, temp.Path);
        Assert.True(process.WaitForExit(3000));
        Assert.Equal(0, process.ExitCode);

        Assert.Equal("OUTLINE", File.ReadAllText(Path.Combine(temp.Path, "out.txt")).Trim());
        Assert.Equal("ERRLINE", File.ReadAllText(Path.Combine(temp.Path, "err.txt")).Trim());
    }

    private static Process InvokeLaunchProcess(string entryFullPath, string arguments, string workingDirectory)
    {
        var method = ScriptLibrary.GetMethod("LaunchProcess", BindingFlags.NonPublic | BindingFlags.Static)!;
        var process = (Process)method.Invoke(null, new object?[] { entryFullPath, arguments, workingDirectory })!;
        return process;
    }

    [Fact]
    public void ValidateManifest_ReturnsErrors_ForMissingFields()
    {
        using var temp = new TempFolder();
        var manifest = new ScriptManifest { Name = "", EntryPoint = "" };
        var errors = (System.Collections.IEnumerable)ValidateManifest.Invoke(null, new object[] { temp.Path, manifest })!;
        var errorList = errors.Cast<string>().ToList();
        Assert.Contains("Name is required", errorList);
        Assert.Contains("Entry point is required", errorList);
    }

    [Fact]
    public void ValidateManifest_FlagsMissingEntryPointFile()
    {
        using var temp = new TempFolder();
        var manifest = new ScriptManifest { Name = "sample", EntryPoint = "missing.exe" };
        var errors = (System.Collections.IEnumerable)ValidateManifest.Invoke(null, new object[] { temp.Path, manifest })!;
        Assert.Contains("Entry point missing", errors.Cast<string>());
    }

    private sealed class TempFolder : IDisposable
    {
        public string Path { get; }
        public TempFolder()
        {
            Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), $"maelstrom_test_{Guid.NewGuid():N}");
            Directory.CreateDirectory(Path);
        }

        public string WriteScript(string content)
        {
            var scriptPath = System.IO.Path.Combine(Path, "script.bat");
            File.WriteAllText(scriptPath, content);
            return scriptPath;
        }

        public void Dispose()
        {
            try { Directory.Delete(Path, recursive: true); } catch { /* ignore */ }
        }
    }
}
