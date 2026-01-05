namespace MaelstromBot.Server;

public record StatusDto(int queued, int running, int awaiting, int completed, int failed, string? lastJobId, string? lastGithubWebhookAtUtc, string? lastOpenAiWebhookAtUtc);
public record JobDto(
    string jobId,
    string? sha,
    string status,
    string trigger,
    string? openaiResponseId,
    string? openaiStatus,
    string? openaiSubmittedAtUtc,
    string? openaiCompletedAtUtc,
    string? createdAtUtc,
    string? updatedAtUtc,
    string? error,
    string? resultSnippet);
public record AutomationDto(string id, bool enabled, string description);
