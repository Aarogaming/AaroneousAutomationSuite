using System.Windows.Forms;
using ProjectMaelstrom.Utilities;
using ProjectMaelstrom.Utilities.Overlay;

namespace SampleOverlayWidgetsPlugin;

public sealed class Plugin : IMaelstromPlugin
{
    public string Id => "SampleOverlayWidgets";
    public string Name => "Sample Overlay Widgets";
    public Version Version => new Version(1, 0, 0);

    public void Initialize(object context)
    {
        OverlayWidgetRegistry.Register(new ModeStatusWidget());
        OverlayWidgetRegistry.Register(new RecentActionsWidget());
        OverlayWidgetRegistry.Register(new SessionMetricsWidget());
    }
}

internal sealed class ModeStatusWidget : IOverlayWidget
{
    private Label? _label;

    public string Id => "Sample.ModeStatus";
    public string Title => "Mode Status";

    public Control CreateControl()
    {
        _label = new Label
        {
            AutoSize = true,
            Padding = new Padding(4),
            Text = "Mode: -"
        };
        var panel = new GroupBox
        {
            Text = Title,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink
        };
        panel.Controls.Add(_label);
        return panel;
    }

    public void Update(OverlayStateSnapshot snapshot)
    {
        if (_label == null) return;
        _label.Text = $"Profile: {snapshot.Profile}\nMode: {snapshot.Mode}\nLive: {snapshot.AllowLiveAutomation}";
    }
}

internal sealed class RecentActionsWidget : IOverlayWidget
{
    private ListBox? _list;

    public string Id => "Sample.RecentActions";
    public string Title => "Recent Actions";

    public Control CreateControl()
    {
        _list = new ListBox
        {
            Width = 200,
            Height = 120
        };
        var panel = new GroupBox
        {
            Text = Title,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink
        };
        panel.Controls.Add(_list);
        return panel;
    }

    public void Update(OverlayStateSnapshot snapshot)
    {
        if (_list == null) return;
        _list.Items.Clear();
        if (snapshot.RecentActions.Count == 0)
        {
            _list.Items.Add("No actions logged");
            return;
        }
        foreach (var action in snapshot.RecentActions.Take(10))
        {
            _list.Items.Add(action);
        }
    }
}

internal sealed class SessionMetricsWidget : IOverlayWidget
{
    private Label? _label;

    public string Id => "Sample.SessionMetrics";
    public string Title => "Session Metrics";

    public Control CreateControl()
    {
        _label = new Label
        {
            AutoSize = true,
            Padding = new Padding(4),
            Text = "Metrics: -"
        };
        var panel = new GroupBox
        {
            Text = Title,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink
        };
        panel.Controls.Add(_label);
        return panel;
    }

    public void Update(OverlayStateSnapshot snapshot)
    {
        if (_label == null) return;
        _label.Text = $"Actions: {snapshot.ActionsLogged}\nBlocked: {snapshot.ActionsBlocked}\nPlugins: {snapshot.PluginCount}\nLast: {snapshot.ExecutorStatus}";
    }
}
