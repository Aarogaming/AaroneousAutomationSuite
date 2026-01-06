namespace MaelstromToolkit.Planning;

internal static class PlanSchemaProvider
{
    private const string SchemaPath = "docs/AI_PLAN_SCHEMA.json";

    public static string LoadSchema()
    {
        if (File.Exists(SchemaPath))
        {
            return File.ReadAllText(SchemaPath);
        }
        return "{}";
    }
}
