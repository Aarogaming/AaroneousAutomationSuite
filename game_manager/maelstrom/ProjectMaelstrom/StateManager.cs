namespace ProjectMaelstrom;

internal class StateManager
{
    private static StateManager? _instance;

    // Constants
    public const int BotTimerIntervalMs = 200;
    public const int ManaRefreshIntervalSec = 10;
    public const int MaxGameWindowAttempts = 20;

    public static StateManager Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance= new StateManager();
            }

            return _instance;
        }
    }

    private static readonly string[] ValidResolutions = { "1024x768", "1280x720", "2256x1504" };
    public static IReadOnlyList<string> SupportedResolutions => ValidResolutions;

    public string? SelectedResolution { set; get; } = "1280x720";

    public int CurrentMana { set; get; }
    public int MaxMana { set; get; }

    public int SetMarkerCost { set; get; }

    public bool IsValidResolution(string resolution)
    {
        if (string.IsNullOrEmpty(resolution))
        {
            return false;
        }

        return Array.Exists(ValidResolutions, r => r.Equals(resolution, StringComparison.OrdinalIgnoreCase));
    }

    public bool SetResolution(string resolution)
    {
        if (!IsValidResolution(resolution))
        {
            return false;
        }

        SelectedResolution = resolution;
        return true;
    }
}
