using System;
using System.Windows.Forms;

namespace HandoffTray;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new TrayForm());
    }
}
