namespace ProjectMaelstrom.Models;

internal class ScriptManifest
{
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Author { get; set; }
    public string? SourceUrl { get; set; }
    public string? Status { get; set; } // optional: native, external, deprecated, reference
    public string EntryPoint { get; set; } = string.Empty;
    public string? Arguments { get; set; }
    public string? RequiredResolution { get; set; }
    public string[]? RequiredTemplates { get; set; }
}
