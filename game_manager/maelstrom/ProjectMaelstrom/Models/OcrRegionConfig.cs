namespace ProjectMaelstrom.Models;

internal sealed class OcrRegionConfig
{
    public string Name { get; set; } = string.Empty;
    public double X { get; set; }    // normalized [0..1]
    public double Y { get; set; }    // normalized [0..1]
    public double Width { get; set; }  // normalized [0..1]
    public double Height { get; set; } // normalized [0..1]
}
