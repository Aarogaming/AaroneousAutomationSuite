using ProjectMaelstrom.Models;
using System.Collections.Generic;
using System.Linq;
using System;

namespace ProjectMaelstrom.Utilities;

internal enum ExecutionStatus
{
    Simulated,
    LiveDispatched,
    BlockedByPolicy,
    LiveEnabledNoBackend,
    NoCommands
}

internal sealed class ExecutionContext
{
    public string Source { get; init; } = "Unknown";
    public string? TaskName { get; init; }
    public InputBridge? Bridge { get; init; }
}

internal sealed class ExecutionResult
{
    public ExecutionStatus Status { get; init; }
    public int CommandsCount { get; init; }
    public string? Message { get; init; }
}

internal interface IExecutor
{
    ExecutionResult Execute(IEnumerable<InputCommand> commands, ExecutionContext context);
}

internal static class ExecutorFactory
{
    public static IExecutor FromPolicy(ExecutionPolicySnapshot policy)
    {
        if (policy == null) throw new ArgumentNullException(nameof(policy));
        if (policy.AllowLiveAutomation)
        {
            return new LiveExecutor(policy, LiveBackendProvider.Current);
        }
        return new SimulationExecutor();
    }
}

internal sealed class SimulationExecutor : IExecutor
{
    public ExecutionResult Execute(IEnumerable<InputCommand> commands, ExecutionContext context)
    {
        var list = commands?.Where(c => c != null).ToList() ?? new List<InputCommand>();
        if (list.Count == 0)
        {
            var emptyResult = new ExecutionResult { Status = ExecutionStatus.NoCommands, CommandsCount = 0, Message = "No commands" };
            ReplayLogger.Append(context ?? new ExecutionContext(), emptyResult, list);
            return emptyResult;
        }

        foreach (var cmd in list)
        {
            Logger.LogBotAction("SimulationExecutor", $"{context.Source} -> {cmd.Type} ({cmd.X},{cmd.Y})");
            Overlay.OverlaySnapshotHub.AppendAction($"{cmd.Type} ({cmd.X},{cmd.Y})");
        }

        var result = new ExecutionResult
        {
            Status = ExecutionStatus.Simulated,
            CommandsCount = list.Count,
            Message = "Simulated only (live disabled)"
        };
        Overlay.OverlaySnapshotHub.SetExecutorStatus(result.Status.ToString());
        ReplayLogger.Append(context ?? new ExecutionContext(), result, list);
        return result;
    }
}

internal sealed class LiveExecutor : IExecutor
{
    private readonly ExecutionPolicySnapshot _policy;
    private readonly ILiveIntegrationBackend _backend;

    public LiveExecutor(ExecutionPolicySnapshot policy, ILiveIntegrationBackend backend)
    {
        _policy = policy ?? throw new ArgumentNullException(nameof(policy));
        _backend = backend ?? new NullLiveBackend();
    }

    public ExecutionResult Execute(IEnumerable<InputCommand> commands, ExecutionContext context)
    {
        var list = commands?.Where(c => c != null).ToList() ?? new List<InputCommand>();
        if (list.Count == 0)
        {
            var empty = new ExecutionResult { Status = ExecutionStatus.NoCommands, CommandsCount = 0, Message = "No commands" };
            ReplayLogger.Append(context ?? new ExecutionContext(), empty, list);
            return empty;
        }

        if (!_policy.AllowLiveAutomation)
        {
            Logger.LogBotAction("LiveExecutor", "Blocked by policy (live disabled)");
            var blocked = new ExecutionResult
            {
                Status = ExecutionStatus.BlockedByPolicy,
                CommandsCount = list.Count,
                Message = "Blocked by policy (live disabled)"
            };
            Overlay.OverlaySnapshotHub.SetExecutorStatus(blocked.Status.ToString());
            ReplayLogger.Append(context ?? new ExecutionContext(), blocked, list);
            return blocked;
        }

        var backend = _backend ?? new NullLiveBackend();
        var result = backend.Dispatch(list, context ?? new ExecutionContext());
        if (result == null)
        {
            result = new ExecutionResult
            {
                Status = ExecutionStatus.LiveEnabledNoBackend,
                CommandsCount = list.Count,
                Message = "Live allowed but backend returned no result"
            };
        }
        Overlay.OverlaySnapshotHub.SetExecutorStatus(result.Status.ToString());
        ReplayLogger.Append(context ?? new ExecutionContext(), result, list);
        return result;
    }
}
