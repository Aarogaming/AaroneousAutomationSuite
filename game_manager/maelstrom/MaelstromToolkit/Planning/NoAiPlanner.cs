namespace MaelstromToolkit.Planning;

internal sealed class NoAiPlanner : IAgentPlanner
{
    private const string PlannerName = "noai";

    public PlanResult Plan(PlanningRequest request)
    {
        return PlanResult.NoOp(PlannerName);
    }
}
