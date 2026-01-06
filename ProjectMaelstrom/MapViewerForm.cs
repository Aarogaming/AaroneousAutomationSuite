using ProjectMaelstrom.Utilities;

namespace ProjectMaelstrom;

public partial class MapViewerForm : Form
{
    private readonly WizWikiDataService _wiki = WizWikiDataService.Instance;
    private List<WikiZone> _zones = new();

    public MapViewerForm()
    {
        InitializeComponent();
    }

    private void MapViewerForm_Load(object sender, EventArgs e)
    {
        ThemeManager.ApplyTheme(this);
        ApplyPalette();
        LoadZones();
    }

    private void ApplyPalette()
    {
        var palette = ThemeManager.GetActivePalette();
        UIStyles.ApplyButtonStyle(refreshButton, palette.ControlBack, palette.ControlFore, palette.Border);
        worldCombo.BackColor = palette.ControlBack;
        worldCombo.ForeColor = palette.ControlFore;
        zoneList.BackColor = palette.ControlBack;
        zoneList.ForeColor = palette.ControlFore;
        statusLabel.ForeColor = palette.Fore;
        BackColor = palette.Surface;
        ForeColor = palette.Fore;
    }

    private void LoadZones()
    {
        _zones = _wiki.GetZonesData().ToList();
        if (_zones.Count == 0)
        {
            statusLabel.Text = "Status: No zone data found. Add wizwiki_zones.json and map images.";
            worldCombo.Items.Clear();
            zoneList.Items.Clear();
            mapPicture.Image = null;
            return;
        }

        var worlds = _zones
            .Select(z => z.World)
            .Where(w => !string.IsNullOrWhiteSpace(w))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(w => w)
            .ToList();

        worldCombo.Items.Clear();
        foreach (var w in worlds)
        {
            worldCombo.Items.Add(w);
        }
        if (worldCombo.Items.Count > 0)
        {
            worldCombo.SelectedIndex = 0;
        }

        statusLabel.Text = $"Status: Loaded {_zones.Count} zones across {worlds.Count} worlds.";
    }

    private void worldCombo_SelectedIndexChanged(object sender, EventArgs e)
    {
        var world = worldCombo.SelectedItem?.ToString();
        zoneList.Items.Clear();
        mapPicture.Image = null;
        if (string.IsNullOrWhiteSpace(world)) return;
        var zones = _zones.Where(z => string.Equals(z.World, world, StringComparison.OrdinalIgnoreCase))
            .OrderBy(z => z.Zone)
            .ToList();
        foreach (var z in zones)
        {
            zoneList.Items.Add(z.Zone);
        }
        statusLabel.Text = $"Status: {zones.Count} zones in {world}.";
    }

    private void zoneList_SelectedIndexChanged(object sender, EventArgs e)
    {
        var selectedZone = zoneList.SelectedItem?.ToString();
        if (string.IsNullOrWhiteSpace(selectedZone)) return;
        var zone = _zones.FirstOrDefault(z => string.Equals(z.Zone, selectedZone, StringComparison.OrdinalIgnoreCase));
        if (zone == null) return;

        if (!string.IsNullOrWhiteSpace(zone.Image))
        {
            try
            {
                var path = zone.Image;
                if (!Path.IsPathRooted(path))
                {
                    path = Path.Combine(AppContext.BaseDirectory, path);
                }
                if (File.Exists(path))
                {
                    mapPicture.Image = Image.FromFile(path);
                }
                else
                {
                    mapPicture.Image = null;
                }
            }
            catch
            {
                mapPicture.Image = null;
            }
        }
        else
        {
            mapPicture.Image = null;
        }

        var neighbors = zone.Neighbors != null && zone.Neighbors.Count > 0
            ? $"Neighbors: {string.Join(", ", zone.Neighbors)}"
            : "Neighbors: (none listed)";
        statusLabel.Text = $"World: {zone.World} | Zone: {zone.Zone} | {neighbors}";
    }

    private void refreshButton_Click(object sender, EventArgs e)
    {
        _wiki.Refresh();
        LoadZones();
    }
}
