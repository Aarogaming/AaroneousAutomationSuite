using System;
using System.IO;
using System.Text;

namespace HandoffTray;

internal sealed class LogHelper
{
    private readonly string _logFile;
    private readonly object _gate = new();

    public LogHelper(string root)
    {
        var dir = Path.Combine(root, "artifacts", "handoff", "logs");
        Directory.CreateDirectory(dir);
        _logFile = Path.Combine(dir, "handofftray.log");
    }

    public void Info(string message)
    {
        Write("INFO", message);
    }

    public void Error(string message)
    {
        Write("ERROR", message);
    }

    private void Write(string level, string message)
    {
        var line = $"{DateTime.UtcNow:o} [{level}] {message}";
        lock (_gate)
        {
            File.AppendAllText(_logFile, line + Environment.NewLine, Encoding.UTF8);
        }
    }
}
