using System.Text.Json;
using Dapper;
using Microsoft.Data.Sqlite;

namespace MaelstromBot.Server;

internal class JobSubmitter : BackgroundService
{
    private readonly ILogger<JobSubmitter> _logger;
    private readonly DatabaseOptions _db;
    private readonly OpenAiClient _openAi;

    public JobSubmitter(ILogger<JobSubmitter> logger, DatabaseOptions db, OpenAiClient openAi)
    {
        _logger = logger;
        _db = db;
        _openAi = openAi;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await ProcessNext(stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Submitter loop error");
            }
            await Task.Delay(500, stoppingToken);
        }
    }

    private async Task ProcessNext(CancellationToken ct)
    {
        using var conn = new SqliteConnection(_db.ConnectionString);
        conn.Open();

        var row = conn.QuerySingleOrDefault<dynamic>("""
            SELECT id, source_sha, payload
            FROM jobs
            WHERE status='queued'
            ORDER BY created_utc
            LIMIT 1;
        """);
        if (row == null) return;

        // check automation toggle
        var enabled = conn.QuerySingleOrDefault<int>("SELECT enabled FROM automations WHERE id='openai.analysis';");
        if (enabled == 0)
        {
            conn.Execute("UPDATE jobs SET status='completed', result_text='Skipped: openai.analysis disabled', updated_utc=@u WHERE id=@i;",
                new { u = DateTime.UtcNow.ToString("o"), i = (string)row.id });
            return;
        }

        var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
        var model = Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "gpt-5.2";
        if (string.IsNullOrWhiteSpace(apiKey))
        {
            conn.Execute("UPDATE jobs SET status='failed', error='Missing OPENAI_API_KEY', updated_utc=@u WHERE id=@i;", new { u = DateTime.UtcNow.ToString("o"), i = (string)row.id });
            return;
        }

        var sha = (string?)row.source_sha ?? "";
        var payload = (string?)row.payload ?? "{}";
        var prompt = BuildPrompt(sha, payload);

        try
        {
            var (respId, status) = await _openAi.CreateBackgroundAsync(apiKey, model, prompt, (string)row.id, sha, ct);
            conn.Execute("""
                UPDATE jobs
                SET status='awaiting_openai',
                    openai_response_id=@r,
                    openai_status=@s,
                    openai_submitted_at_utc=@t,
                    updated_utc=@t
                WHERE id=@i;
            """, new { r = respId, s = status, t = DateTime.UtcNow.ToString("o"), i = (string)row.id });
            _logger.LogInformation("Submitted job {Job} to OpenAI {Resp}", (string)row.id, respId);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "OpenAI submission failed for job {Job}", (string)row.id);
            conn.Execute("UPDATE jobs SET status='failed', error=@e, updated_utc=@u WHERE id=@i;", new { e = ex.Message, u = DateTime.UtcNow.ToString("o"), i = (string)row.id });
        }
    }

    private static string BuildPrompt(string sha, string payload)
    {
        string? msg = null;
        try
        {
            var doc = JsonDocument.Parse(payload);
            msg = doc.RootElement.TryGetProperty("head_commit", out var hc) && hc.TryGetProperty("message", out var m) ? m.GetString() : null;
        }
        catch { }

        return $"""
You are MaelstromBot, a local CI assistant.
Analyze push:
SHA: {sha}
Commit message: {msg ?? "(unknown)"}
Provide: summary, potential risks, and suggested tests (short bullets).
""";
    }
}
