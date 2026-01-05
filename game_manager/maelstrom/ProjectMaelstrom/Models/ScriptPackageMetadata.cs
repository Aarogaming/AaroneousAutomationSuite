using System;

namespace ProjectMaelstrom.Models;

internal sealed class ScriptPackageMetadata
{
    public string? SourceUrl { get; set; }
    public string? BranchOrTag { get; set; }
    public DateTime InstalledAtUtc { get; set; }
}
