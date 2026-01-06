using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace MaelstromBot.Server;

internal sealed class OpenAiClient
{
    private readonly IHttpClientFactory _httpClientFactory;

    public OpenAiClient(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }

    private HttpClient CreateClient(string apiKey)
    {
        var client = _httpClientFactory.CreateClient();
        client.BaseAddress = new Uri("https://api.openai.com/v1/");
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
        client.Timeout = TimeSpan.FromSeconds(30);
        return client;
    }

    public async Task<(string Id, string Status)> CreateBackgroundAsync(string apiKey, string model, string prompt, string jobId, string? sha, CancellationToken ct)
    {
        using var client = CreateClient(apiKey);
        var payload = new
        {
            model,
            input = prompt,
            background = true,
            store = true, // required when background=true per OpenAI docs :contentReference[oaicite:2]{index=2}
            metadata = new { job_id = jobId, sha }
        };

        using var req = new HttpRequestMessage(HttpMethod.Post, "responses");
        req.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        using var resp = await client.SendAsync(req, ct);
        var json = await resp.Content.ReadAsStringAsync(ct);
        resp.EnsureSuccessStatusCode();

        using var doc = JsonDocument.Parse(json);
        var id = doc.RootElement.GetProperty("id").GetString() ?? throw new InvalidOperationException("Missing response id");
        var status = doc.RootElement.GetProperty("status").GetString() ?? "";
        return (id, status);
    }

    public async Task<(string Status, string RawJson, string OutputText)> RetrieveAsync(string apiKey, string responseId, CancellationToken ct)
    {
        using var client = CreateClient(apiKey);
        using var req = new HttpRequestMessage(HttpMethod.Get, $"responses/{responseId}");
        using var resp = await client.SendAsync(req, ct);
        var json = await resp.Content.ReadAsStringAsync(ct);
        resp.EnsureSuccessStatusCode();

        using var doc = JsonDocument.Parse(json);
        var status = doc.RootElement.GetProperty("status").GetString() ?? "";
        var outputText = TryExtractOutput(doc);
        return (status, json, outputText);
    }

    public async Task CancelAsync(string apiKey, string responseId, CancellationToken ct)
    {
        using var client = CreateClient(apiKey);
        using var req = new HttpRequestMessage(HttpMethod.Post, $"responses/{responseId}/cancel");
        using var resp = await client.SendAsync(req, ct);
        resp.EnsureSuccessStatusCode();
    }

    private static string TryExtractOutput(JsonDocument doc)
    {
        if (!doc.RootElement.TryGetProperty("output", out var output) || output.ValueKind != JsonValueKind.Array)
            return "";
        var sb = new StringBuilder();
        foreach (var item in output.EnumerateArray())
        {
            if (!item.TryGetProperty("type", out var t) || t.GetString() != "message")
                continue;
            if (!item.TryGetProperty("content", out var content) || content.ValueKind != JsonValueKind.Array)
                continue;
            foreach (var c in content.EnumerateArray())
            {
                if (!c.TryGetProperty("type", out var ct) || ct.GetString() != "output_text")
                    continue;
                if (c.TryGetProperty("text", out var text))
                    sb.Append(text.GetString());
            }
        }
        return sb.ToString();
    }
}
