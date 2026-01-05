using System.Text;

var argsDict = ParseArgs(args);

var stdout = argsDict.TryGetValue("stdout", out var so) ? so : null;
var stderr = argsDict.TryGetValue("stderr", out var se) ? se : null;
var exitCode = argsDict.TryGetValue("exit", out var ec) && int.TryParse(ec, out var ecParsed) ? ecParsed : 0;
var sleepMs = argsDict.TryGetValue("sleepMs", out var sm) && int.TryParse(sm, out var smParsed) ? smParsed : 0;
var printCwd = argsDict.ContainsKey("printCwd");
var envKey = argsDict.TryGetValue("printEnv", out var env) ? env : null;

if (sleepMs > 0)
{
    Thread.Sleep(Math.Min(sleepMs, 10_000));
}

if (stdout != null)
{
    Console.Out.Write(stdout);
}

if (printCwd)
{
    Console.Out.Write(Environment.CurrentDirectory);
}

if (!string.IsNullOrEmpty(envKey))
{
    var value = Environment.GetEnvironmentVariable(envKey) ?? string.Empty;
    Console.Out.Write(value);
}

if (stderr != null)
{
    Console.Error.Write(stderr);
}

return exitCode;

static Dictionary<string, string?> ParseArgs(string[] input)
{
    var dict = new Dictionary<string, string?>(StringComparer.OrdinalIgnoreCase);
    string? pendingKey = null;
    foreach (var arg in input)
    {
        if (arg.StartsWith("--", StringComparison.Ordinal))
        {
            pendingKey = arg.TrimStart('-');
            dict[pendingKey] = null;
        }
        else if (pendingKey != null)
        {
            dict[pendingKey] = arg;
            pendingKey = null;
        }
    }
    return dict;
}
