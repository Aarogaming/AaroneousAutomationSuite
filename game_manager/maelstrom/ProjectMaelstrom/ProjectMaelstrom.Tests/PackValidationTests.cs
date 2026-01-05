using MaelstromToolkit.Packs;

namespace ProjectMaelstrom.Tests;

public class PackValidationTests
{
    [Fact]
    public void DetectsMissingScenarioFile()
    {
        var temp = CreatePack("pack.one", scenarioEntry: "scenarios/missing.json");
        var service = new PackService();

        var result = service.ValidatePacks(temp);

        Assert.Contains(result.Diagnostics, d => d.Code == "PACK033");
    }

    [Fact]
    public void ValidPackPasses()
    {
        var temp = CreatePack("pack.two");
        var service = new PackService();

        var result = service.ValidatePacks(temp);

        Assert.False(result.HasErrors);
    }

    private static string CreatePack(string packId, string scenarioEntry = "scenarios/demo.json")
    {
        var root = Path.Combine(Path.GetTempPath(), $"packtest_{Guid.NewGuid():N}");
        Directory.CreateDirectory(root);
        var packDir = Path.Combine(root, packId);
        var scenDir = Path.Combine(packDir, Path.GetDirectoryName(scenarioEntry)!);
        Directory.CreateDirectory(scenDir);

        File.WriteAllText(Path.Combine(packDir, "pack.json"), $$"""
{
  "id": "{{packId}}",
  "name": "Demo",
  "version": "1.0.0",
  "scenarios": [
    { "id": "demo", "name": "Demo", "entry": "{{scenarioEntry}}" }
  ]
}
""");

        if (!scenarioEntry.Contains("missing", StringComparison.OrdinalIgnoreCase))
        {
            File.WriteAllText(Path.Combine(packDir, scenarioEntry.Replace('/', Path.DirectorySeparatorChar)), """
{
  "id": "demo",
  "summary": "demo scenario"
}
""");
        }

        return root;
    }
}
