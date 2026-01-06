using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace HandoffTray;

internal class ApiSender
{
    private readonly HttpClient _http = new();

    private static readonly Regex SecretPatterns = new(
        "(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AIza[0-9A-Za-z\\-_]{20,}|BEGIN RSA PRIVATE KEY|BEGIN PRIVATE KEY)",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private static readonly Regex FenceRegex = new("```(.*?)```", RegexOptions.Singleline | RegexOptions.Compiled);

    public async Task<ApiSendResult> SendAsync(string content, string model, string outDir)
    {
        var key = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
        if (string.IsNullOrWhiteSpace(key))
        {
            return ApiSendResult.Fail("OPENAI_API_KEY env var is missing.");
        }

        var fenced = ExtractFenced(content);
        if (fenced == null)
        {
            return ApiSendResult.Fail("Could not find a single fenced code block to send.");
        }

        var redacted = SecretPatterns.Replace(fenced, "[REDACTED]");
        if (SecretPatterns.IsMatch(fenced))
        {
            redacted += "\n\n[Note: content redacted before send]";
        }

        var req = new
        {
            model = string.IsNullOrWhiteSpace(model) ? "gpt-4o-mini" : model,
            messages = new object[]
            {
                new { role = "user", content = redacted }
            },
            max_tokens = 512
        };

        var json = JsonSerializer.Serialize(req);
        using var msg = new HttpRequestMessage(HttpMethod.Post, "https://api.openai.com/v1/chat/completions")
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        };
        msg.Headers.Authorization = new AuthenticationHeaderValue("Bearer", key);

        var resp = await _http.SendAsync(msg).ConfigureAwait(false);
        var body = await resp.Content.ReadAsStringAsync().ConfigureAwait(false);
        if (!resp.IsSuccessStatusCode)
        {
            return ApiSendResult.Fail($"API error {(int)resp.StatusCode}: {resp.ReasonPhrase}\n{body}");
        }

        var stamped = $"# OpenAI Response\nTimestamp (UTC): {DateTime.UtcNow:o}\nModel: {req.model}\n\n{body}\n";
        Directory.CreateDirectory(outDir);
        var path = Path.Combine(outDir, $"OPENAI_RESPONSE_{DateTime.UtcNow:yyyyMMdd_HHmmss}.md");
        await File.WriteAllTextAsync(path, stamped, Encoding.UTF8).ConfigureAwait(false);

        return ApiSendResult.Ok(path);
    }

    private static string? ExtractFenced(string content)
    {
        var matches = FenceRegex.Matches(content);
        if (matches.Count != 1) return null;
        return matches[0].Value;
    }
}

internal record ApiSendResult(bool Success, string Message, string? OutputPath)
{
    public static ApiSendResult Ok(string path) => new(true, $"Saved response to {path}", path);
    public static ApiSendResult Fail(string message) => new(false, message, null);
}
