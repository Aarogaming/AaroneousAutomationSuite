namespace MaelstromToolkit.Policy;

internal sealed class PolicyTxtParserFacade
{
    public ParsedPolicy Parse(string text)
    {
        var parser = new PolicyParser();
        var result = parser.Parse(text);
        var diagnostics = result.SortedDiagnostics().ToList();
        PolicySnapshot? snapshot = null;
        if (!result.HasErrors && result.Document != null)
        {
            snapshot = PolicySnapshot.FromDocument(result.Document);
        }
        return new ParsedPolicy(snapshot, diagnostics);
    }
}
