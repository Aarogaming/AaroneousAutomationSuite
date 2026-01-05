using MaelstromToolkit.Handoff;
using MaelstromToolkit;

namespace ProjectMaelstrom.Tests;

internal sealed class StubGitInfoProvider : IGitInfoProvider
{
    public string Commit { get; init; } = "stub-commit";
    public string Branch { get; init; } = "stub-branch";
    public bool IsDirty { get; init; } = true;
}

public class HandoffPromptTests
{
    [Fact]
    public void IncludesCommitBranchAndDirty()
    {
        var stub = new StubGitInfoProvider();

        var text = MaelstromToolkit.Program.BuildHandoffPrompt("./--out", stub);

        Assert.Contains("stub-commit", text);
        Assert.Contains("stub-branch", text);
        Assert.Contains("Dirty: true", text);
    }
}
