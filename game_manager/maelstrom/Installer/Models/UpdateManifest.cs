namespace Installer.Models;

internal sealed class UpdateManifest
{
    public string? Version { get; set; }
    public string? PackageUrl { get; set; }
    public string? Changelog { get; set; }
}
