using System.Collections.Generic;

namespace ProjectMaelstrom.Modules;

/// <summary>
/// Static navigation knowledge about Wizard101 hubs and travel behaviors the trainer can use when planning tasks.
/// </summary>
internal static class NavigationKnowledge
{
    public static readonly IReadOnlyDictionary<string, TravelRoute> Routes = new Dictionary<string, TravelRoute>
    {
        {
            "MainHomeToDormLoop",
            new TravelRoute(
                "Teleport home chain",
                "Teleporting home from a main house sends you to that house; teleporting home again from the main house sends you to the Dorm.",
                new[]
                {
                    "Press Home to teleport to main house.",
                    "If already in main house, press Home again to arrive at Dorm."
                })
        },
        {
            "DormToWizardCityHub",
            new TravelRoute(
                "Dorm to Wizard City commons",
                "From Dorm (Riverwood apartments), exit to Wizard City commons.",
                new[]
                {
                    "Walk forward out of Dorm door.",
                    "Zone load to Wizard City commons (Riverwood)."
                })
        },
        {
            "CommonsToBazaar",
            new TravelRoute(
                "Commons to Bazaar",
                "Shortest walk from Riverwood spawn to Bazaar door.",
                new[]
                {
                    "Face left toward Olde Town gate.",
                    "Walk forward through gate into Olde Town.",
                    "Enter Bazaar on the left."
                })
        },
        {
            "CommonsToMiniGames",
            new TravelRoute(
                "Commons to Mini Games Faireground",
                "Path from Riverwood spawn to mini games for potion farming.",
                new[]
                {
                    "Face right from spawn toward Faireground ramp.",
                    "Follow path to Mini Games Faireground.",
                    "Interact with chosen mini game kiosk."
                })
        },
        {
            "CommonsToPetPavilion",
            new TravelRoute(
                "Commons to Pet Pavilion",
                "Path from Riverwood spawn to pet games.",
                new[]
                {
                    "Face straight ahead and angle slightly left.",
                    "Cross bridge toward Pet Pavilion island.",
                    "Enter pet game area."
                })
        }
    };

    public static TravelPlan GetBazaarPlanFromAnywhere() => new TravelPlan(new[]
    {
        Routes["MainHomeToDormLoop"],
        Routes["DormToWizardCityHub"],
        Routes["CommonsToBazaar"]
    });

    public static TravelPlan GetMiniGamePlanFromAnywhere() => new TravelPlan(new[]
    {
        Routes["MainHomeToDormLoop"],
        Routes["DormToWizardCityHub"],
        Routes["CommonsToMiniGames"]
    });

    public static TravelPlan GetPetPavilionPlanFromAnywhere() => new TravelPlan(new[]
    {
        Routes["MainHomeToDormLoop"],
        Routes["DormToWizardCityHub"],
        Routes["CommonsToPetPavilion"]
    });
}

internal sealed class TravelRoute
{
    public TravelRoute(string name, string summary, IEnumerable<string> steps)
    {
        Name = name;
        Summary = summary;
        Steps = new List<string>(steps);
    }

    public string Name { get; }
    public string Summary { get; }
    public IReadOnlyList<string> Steps { get; }
}

internal sealed class TravelPlan
{
    public TravelPlan(IEnumerable<TravelRoute> routes)
    {
        Routes = new List<TravelRoute>(routes);
    }

    public IReadOnlyList<TravelRoute> Routes { get; }
}
