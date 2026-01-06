using System.Collections.Generic;

namespace ProjectMaelstrom.Models;

internal sealed class GameStateSnapshot
{
    public DateTime CapturedUtc { get; init; }
    public bool WindowPresent { get; init; }
    public bool HasFocus { get; init; }
    public string? Resolution { get; init; }
    public MetricPair? Health { get; init; }
    public MetricPair? Mana { get; init; }
    public MetricPair? Energy { get; init; }
    public MetricSingle? Gold { get; init; }
    public MetricSingle? Potions { get; init; }
    public IReadOnlyList<string> Warnings { get; init; } = Array.Empty<string>();

    public sealed class MetricPair
    {
        public int? Current { get; init; }
        public int? Max { get; init; }
        public double Confidence { get; init; }
        public string Source { get; init; } = string.Empty;
    }

    public sealed class MetricSingle
    {
        public int? Value { get; init; }
        public double Confidence { get; init; }
        public string Source { get; init; } = string.Empty;
    }
}
