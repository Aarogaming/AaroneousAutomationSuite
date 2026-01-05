using System.Collections.Concurrent;

namespace ProjectMaelstrom.Modules.ImageRecognition;

/// <summary>
/// Discovers template image files under Resources/Templates and exposes lookup by key.
/// </summary>
internal sealed class TemplateLibrary
{
    private static readonly Lazy<TemplateLibrary> _instance = new(() => new TemplateLibrary());
    public static TemplateLibrary Instance => _instance.Value;

    private readonly ConcurrentDictionary<string, string> _templates = new(StringComparer.OrdinalIgnoreCase);
    private readonly string _root;

    private TemplateLibrary()
    {
        _root = Path.Combine(AppContext.BaseDirectory, "Resources", "Templates");
        Load();
    }

    public void Load()
    {
        _templates.Clear();
        if (!Directory.Exists(_root)) return;

        foreach (var file in Directory.EnumerateFiles(_root, "*.*", SearchOption.AllDirectories))
        {
            var ext = Path.GetExtension(file).ToLowerInvariant();
            if (ext is not ".png" and not ".jpg" and not ".jpeg") continue;
            var key = Path.GetFileNameWithoutExtension(file);
            _templates[key] = file;
        }
    }

    public string? FindTemplatePath(string key)
    {
        if (string.IsNullOrWhiteSpace(key)) return null;
        return _templates.TryGetValue(key, out var path) ? path : null;
    }

    public IEnumerable<string> Keys => _templates.Keys;
}
