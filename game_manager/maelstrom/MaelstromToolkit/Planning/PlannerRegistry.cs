namespace MaelstromToolkit.Planning;

internal sealed class PlannerRegistry
{
    private readonly Dictionary<string, Func<IAgentPlanner>> _factories;

    public PlannerRegistry()
    {
        _factories = new Dictionary<string, Func<IAgentPlanner>>(StringComparer.OrdinalIgnoreCase)
        {
            ["noai"] = () => new NoAiPlanner()
        };
    }

    public void Register(string providerName, Func<IAgentPlanner> factory)
    {
        _factories[providerName] = factory;
    }

    public IAgentPlanner Resolve(string? providerName)
    {
        var key = string.IsNullOrWhiteSpace(providerName) ? "noai" : providerName;
        return _factories.TryGetValue(key, out var factory) ? factory() : _factories["noai"]();
    }
}
