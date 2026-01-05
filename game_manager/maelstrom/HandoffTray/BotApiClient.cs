using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text;

namespace HandoffTray;

public sealed class BotApiClient
{
    private readonly HttpClient _http;
    private string _token;

    public BotApiClient(string baseUrl, string? token)
    {
        _http = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(4)
        };
        _token = token ?? string.Empty;
        SetBaseUrl(baseUrl);
    }

    public void SetBaseUrl(string baseUrl)
    {
        if (!baseUrl.EndsWith("/")) baseUrl += "/";
        _http.BaseAddress = new Uri(baseUrl);
    }

    public void SetToken(string? token)
    {
        _token = token ?? string.Empty;
    }

    private void ApplyAuth()
    {
        _http.DefaultRequestHeaders.Authorization = null;
        if (!string.IsNullOrWhiteSpace(_token))
        {
            _http.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _token);
        }
    }

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true
    };

    public async Task<StatusDto?> GetStatusAsync(CancellationToken ct)
    {
        ApplyAuth();
        var resp = await _http.GetAsync("bot/api/status", ct);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<StatusDto>(JsonOptions, ct);
    }

    public async Task<List<JobDto>?> GetJobsAsync(int limit, CancellationToken ct)
    {
        ApplyAuth();
        var resp = await _http.GetAsync($"bot/api/jobs?limit={Math.Clamp(limit, 1, 50)}", ct);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<List<JobDto>>(JsonOptions, ct);
    }

    public async Task<List<AutomationDto>?> GetAutomationsAsync(CancellationToken ct)
    {
        ApplyAuth();
        var resp = await _http.GetAsync("bot/api/automations", ct);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<List<AutomationDto>>(JsonOptions, ct);
    }

    public async Task<bool> SetAutomationAsync(string id, bool enabled, CancellationToken ct)
    {
        ApplyAuth();
        var resp = await _http.PutAsJsonAsync($"bot/api/automations/{Uri.EscapeDataString(id)}", new SetAutomationRequest(enabled), JsonOptions, ct);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        if (resp.StatusCode == System.Net.HttpStatusCode.Forbidden)
            throw new InvalidOperationException("Forbidden");
        resp.EnsureSuccessStatusCode();
        return true;
    }

    public async Task<bool> CancelJobAsync(string jobId, CancellationToken ct)
    {
        ApplyAuth();
        var resp = await _http.PostAsync($"bot/api/jobs/{Uri.EscapeDataString(jobId)}/cancel", content: null, ct);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        if (resp.StatusCode == System.Net.HttpStatusCode.Forbidden)
            throw new InvalidOperationException("Forbidden");
        return resp.IsSuccessStatusCode;
    }
}

public sealed record StatusDto(int Queued, int Running, int Awaiting, int Completed, int Failed, string? LastJobId);

public sealed record JobDto(
    string JobId,
    string Status,
    string? Sha,
    string? Trigger,
    string? OpenaiResponseId,
    string? OpenaiStatus,
    DateTime? OpenaiSubmittedAtUtc,
    DateTime? OpenaiCompletedAtUtc,
    DateTime CreatedAtUtc,
    DateTime UpdatedAtUtc,
    string? ResultSnippet,
    string? Error
);

public sealed record AutomationDto(string Id, bool Enabled, string? Description);
public sealed record SetAutomationRequest(bool Enabled);
