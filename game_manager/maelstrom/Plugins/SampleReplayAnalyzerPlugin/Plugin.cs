using ProjectMaelstrom.Utilities;

namespace SampleReplayAnalyzerPlugin;

public sealed class Plugin : IMaelstromPlugin
{
    public string Id => "SampleReplayAnalyzer";
    public string Name => "Sample Replay Analyzer";
    public Version Version => new Version(1, 0, 0);

    public void Initialize(object context)
    {
        // Register a placeholder analyzer; core continues to function without this plugin.
        ReplayAnalyzerRegistry.Register("SampleReplayAnalyzer");
    }
}
