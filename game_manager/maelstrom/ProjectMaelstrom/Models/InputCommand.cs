namespace ProjectMaelstrom.Models;

internal sealed class InputCommand
{
    public string? Type { get; set; } // click | key_press | key_down | key_up | delay
    public int X { get; set; }
    public int Y { get; set; }
    public string? Key { get; set; }
    public int DelayMs { get; set; } = 0;
}
