namespace ProjectMaelstrom.Models;

internal sealed class UpdateManifest
{
    public string Version { get; set; } = string.Empty;
    public string? Changelog { get; set; }
    public string? PackageUrl { get; set; }
    public string? Signature { get; set; }
    public UpdateFile[] Files { get; set; } = Array.Empty<UpdateFile>();
}

internal sealed class UpdateFile
{
    public string Path { get; set; } = string.Empty;
    public string? Sha256 { get; set; }
}
