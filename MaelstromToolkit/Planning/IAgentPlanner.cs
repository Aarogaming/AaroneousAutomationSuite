namespace MaelstromToolkit.Planning;

internal sealed record PlanningRequest(string PackId, string ScenarioId, IReadOnlyDictionary<string, string> Parameters);

internal sealed record PlanStep(string Description);

internal sealed record PlanResult(string Planner, IReadOnlyList<PlanStep> Steps, string Message)
{
    public static PlanResult NoOp(string planner) =>
        new(planner, new List<PlanStep> { new("noop") }, "No-op plan (planner disabled)");
}

internal interface IAgentPlanner
{
    PlanResult Plan(PlanningRequest request);
}
