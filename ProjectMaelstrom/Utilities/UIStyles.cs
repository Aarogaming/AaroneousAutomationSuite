using System.Drawing.Drawing2D;

namespace ProjectMaelstrom.Utilities;

internal static class UIStyles
{
    public static void ApplyCardStyle(Control control, Color back, Color border)
    {
        control.BackColor = back;
        control.Paint += (s, e) =>
        {
            using var pen = new Pen(border, 1);
            pen.Alignment = PenAlignment.Inset;
            e.Graphics.DrawRectangle(pen, 0, 0, control.Width - 1, control.Height - 1);
        };
    }

    public static void ApplyButtonStyle(Button button, Color back, Color fore, Color border)
    {
        button.BackColor = back;
        button.ForeColor = fore;
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderColor = border;
        button.FlatAppearance.BorderSize = 1;
        button.Padding = new Padding(8, 6, 8, 6);
        button.TextAlign = ContentAlignment.MiddleCenter;
        button.AutoEllipsis = false;
    }
}
