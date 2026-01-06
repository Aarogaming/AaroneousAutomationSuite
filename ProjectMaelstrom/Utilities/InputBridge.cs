using System.Text.Json;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Polls the cache for input commands and dispatches them through PlayerController.
/// External scripts can drop a JSON array of InputCommand objects at Scripts/.cache/commands.json.
/// </summary>
internal sealed class InputBridge : IDisposable
{
    private readonly string _commandPath;
    private readonly PlayerController _controller;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };
    private System.Threading.Timer? _timer;
    private bool _disposing;
    private readonly Queue<InputCommand> _queue = new();
    private readonly object _lock = new();
    private readonly int _minDelayMs = 35; // small throttle to avoid spamming inputs
    private DateTime _lastDispatchUtc = DateTime.MinValue;
    public bool IsIdle
    {
        get
        {
            lock (_lock) return _queue.Count == 0;
        }
    }

    public InputBridge(PlayerController controller)
    {
        _controller = controller;
        _commandPath = Path.Combine(StorageUtils.GetCacheDirectory(), "commands.json");
    }

    public void Start(TimeSpan interval)
    {
        Stop();
        _timer = new System.Threading.Timer(_ => ProcessCommandsSafe(), null, TimeSpan.Zero, interval);
    }

    public void Stop()
    {
        _timer?.Dispose();
        _timer = null;
    }

    public void Enqueue(InputCommand command)
    {
        if (command == null) return;
        lock (_lock)
        {
            _queue.Enqueue(command);
        }
        DrainQueue();
    }

    public void EnqueueRange(IEnumerable<InputCommand> commands)
    {
        if (commands == null) return;
        lock (_lock)
        {
            foreach (var cmd in commands)
            {
                if (cmd != null) _queue.Enqueue(cmd);
            }
        }
        DrainQueue();
    }

    public void Dispose()
    {
        _disposing = true;
        Stop();
    }

    private void ProcessCommandsSafe()
    {
        if (_disposing) return;
        var policy = ExecutionPolicyManager.Current;
        List<InputCommand>? commands = null;
        try
        {
            if (!File.Exists(_commandPath))
            {
                return;
            }

            string json = File.ReadAllText(_commandPath);
            commands = JsonSerializer.Deserialize<List<InputCommand>>(json, _jsonOptions);
        }
        catch (Exception ex)
        {
            Logger.LogError("[InputBridge] Failed to read commands", ex);
        }
        finally
        {
            try
            {
                if (File.Exists(_commandPath))
                {
                    File.Delete(_commandPath);
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("[InputBridge] Failed to delete commands file", ex);
            }
        }

        if (commands == null || commands.Count == 0)
        {
            return;
        }

        if (!policy.AllowLiveAutomation)
        {
            Logger.LogBotAction("InputBridge", $"Blocked {commands.Count} commands by policy (live disabled).");
            return;
        }

        lock (_lock)
        {
            foreach (var cmd in commands)
            {
                _queue.Enqueue(cmd);
            }
        }

        DrainQueue();
    }

    private void DrainQueue()
    {
        while (true)
        {
            InputCommand? cmd = null;
            lock (_lock)
            {
                if (_queue.Count == 0) break;
                cmd = _queue.Dequeue();
            }

            if (cmd == null) continue;

            // simple rate limiter between dispatched commands
            var now = DateTime.UtcNow;
            var sinceLast = (now - _lastDispatchUtc).TotalMilliseconds;
            if (sinceLast < _minDelayMs)
            {
                Thread.Sleep(_minDelayMs - (int)sinceLast);
            }

            if (Dispatch(cmd) && cmd.DelayMs > 0)
            {
                Thread.Sleep(cmd.DelayMs);
            }
            _lastDispatchUtc = DateTime.UtcNow;
        }
    }

    private bool Dispatch(InputCommand command)
    {
        if (command == null || string.IsNullOrWhiteSpace(command.Type))
        {
            return false;
        }

        switch (command.Type.Trim().ToLowerInvariant())
        {
            case "click":
                if (!_controller.EnsureGameForeground())
                {
                    Logger.LogBotAction("InputBridge", "Skipped click: Wizard101 not focused");
                    return false;
                }
                _controller.Click(new Point(command.X, command.Y));
                return true;
            case "key_press":
                if (!_controller.EnsureGameForeground())
                {
                    Logger.LogBotAction("InputBridge", "Skipped key_press: Wizard101 not focused");
                    return false;
                }
                _controller.KeyPress(command.Key ?? string.Empty);
                return true;
            case "key_down":
                if (!_controller.EnsureGameForeground())
                {
                    Logger.LogBotAction("InputBridge", "Skipped key_down: Wizard101 not focused");
                    return false;
                }
                _controller.KeyDown(command.Key ?? string.Empty);
                return true;
            case "key_up":
                if (!_controller.EnsureGameForeground())
                {
                    Logger.LogBotAction("InputBridge", "Skipped key_up: Wizard101 not focused");
                    return false;
                }
                _controller.KeyUp(command.Key ?? string.Empty);
                return true;
            case "delay":
                if (command.DelayMs > 0)
                {
                    Thread.Sleep(command.DelayMs);
                }
                return true;
            default:
                Logger.LogError($"[InputBridge] Unknown command type: {command.Type}");
                return false;
        }
    }
}
