using System.Collections;

namespace ProjectMaelstrom.Utilities;

internal sealed class ListViewItemComparer : IComparer
{
    private readonly int _col;
    private readonly bool _asc;

    public ListViewItemComparer(int column, bool ascending)
    {
        _col = column;
        _asc = ascending;
    }

    public int Compare(object? x, object? y)
    {
        if (x is not System.Windows.Forms.ListViewItem a || y is not System.Windows.Forms.ListViewItem b)
        {
            return 0;
        }

        string ax = _col < a.SubItems.Count ? a.SubItems[_col].Text : string.Empty;
        string bx = _col < b.SubItems.Count ? b.SubItems[_col].Text : string.Empty;

        // Try date parse for "Last Run"
        if (_col == 4 && DateTime.TryParse(ax, out var da) && DateTime.TryParse(bx, out var db))
        {
            int cmp = DateTime.Compare(da, db);
            return _asc ? cmp : -cmp;
        }

        int result = string.Compare(ax, bx, StringComparison.OrdinalIgnoreCase);
        return _asc ? result : -result;
    }
}
