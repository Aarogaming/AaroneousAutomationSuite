namespace ProjectMaelstrom.Models;

internal class ScriptDefinition
{
    public ScriptDefinition(string manifestPath, ScriptManifest manifest, string rootPath, ScriptPackageMetadata? packageInfo = null, string[]? validationErrors = null)
    {
        ManifestPath = manifestPath;
        Manifest = manifest;
        RootPath = rootPath;
        PackageInfo = packageInfo;
        ValidationErrors = validationErrors ?? Array.Empty<string>();
    }

    public string ManifestPath { get; }
    public ScriptManifest Manifest { get; }
    public string RootPath { get; }
    public ScriptPackageMetadata? PackageInfo { get; }
    public string DisplayName
    {
        get
        {
            var name = Manifest.Name;
            if (!string.IsNullOrWhiteSpace(Manifest.Author))
            {
                name = $"{name} (by {Manifest.Author})";
            }
            if (string.IsNullOrWhiteSpace(Manifest.Description))
            {
                return name;
            }
            return $"{name} - {Manifest.Description}";
        }
    }
    public string[] ValidationErrors { get; }
}
