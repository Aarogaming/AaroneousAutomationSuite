namespace MaelstromToolkit.Handoff;

internal interface IGitInfoProvider
{
    string Commit { get; }
    string Branch { get; }
    bool IsDirty { get; }
}
