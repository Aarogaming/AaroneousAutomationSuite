using System.Text.Json.Serialization;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Basic model for extracted WAD asset entries (future expansion).
/// </summary>
internal sealed class WadAssetIndex
{
    [JsonPropertyName("wad")]
    public string WadName { get; set; } = "";

    [JsonPropertyName("entries")]
    public List<WadAssetEntry> Entries { get; set; } = new();
}

internal sealed class WadAssetEntry
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("path")]
    public string Path { get; set; } = "";

    [JsonPropertyName("size")]
    public long Size { get; set; }
}
