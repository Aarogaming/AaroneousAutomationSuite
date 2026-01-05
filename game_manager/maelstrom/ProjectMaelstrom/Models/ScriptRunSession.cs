using System.Diagnostics;

namespace ProjectMaelstrom.Models;

internal class ScriptRunSession
{
    public ScriptRunSession(ScriptDefinition script, Process process, DateTime startedUtc)
    {
        Script = script;
        Process = process;
        StartedUtc = startedUtc;
    }

    public ScriptDefinition Script { get; }
    public Process Process { get; }
    public DateTime StartedUtc { get; }
}
