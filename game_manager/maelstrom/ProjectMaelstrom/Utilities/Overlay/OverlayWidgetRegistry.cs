namespace ProjectMaelstrom.Utilities.Overlay;

public static class OverlayWidgetRegistry
{
    private static readonly List<IOverlayWidget> _widgets = new();
    private static readonly object _lock = new();

    public static IReadOnlyList<IOverlayWidget> Current
    {
        get
        {
            lock (_lock) { return _widgets.ToList(); }
        }
    }

    public static void Register(IOverlayWidget widget)
    {
        if (widget == null) return;
        lock (_lock)
        {
            if (_widgets.Any(w => w.Id.Equals(widget.Id, StringComparison.OrdinalIgnoreCase))) return;
            _widgets.Add(widget);
        }
    }

    public static void Clear()
    {
        lock (_lock)
        {
            _widgets.Clear();
        }
    }
}
