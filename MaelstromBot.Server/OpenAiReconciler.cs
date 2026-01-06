using Dapper;
using Microsoft.Data.Sqlite;

namespace MaelstromBot.Server;

internal class OpenAiReconciler : BackgroundService
{
    private readonly ILogger<OpenAiReconciler> _logger;
    private readonly DatabaseOptions _db;
    private readonly OpenAiClient _openAi;

    public OpenAiReconciler(ILogger<OpenAiReconciler> logger, DatabaseOptions db, OpenAiClient openAi)
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
                await Tick(stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "OpenAI reconcile tick failed");
            }
            await Task.Delay(2000, stoppingToken);
        }
    }

    private async Task Tick(CancellationToken ct)
    {
        var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
        if (string.IsNullOrWhiteSpace(apiKey))
            return;

        using var conn = new SqliteConnection(_db.ConnectionString);
        conn.Open();

        var rows = conn.Query("""
            SELECT id, openai_response_id, status
            FROM jobs
            WHERE status IN ('awaiting_openai','completed_pending_fetch')
              AND openai_response_id IS NOT NULL
            ORDER BY updated_utc
            LIMIT 10;
        """);

        foreach (var r in rows)
        {
            var respId = (string)r.openai_response_id;
            var (status, raw, output) = await _openAi.RetrieveAsync(apiKey, respId, ct);

            if (status.Equals("queued", StringComparison.OrdinalIgnoreCase) || status.Equals("in_progress", StringComparison.OrdinalIgnoreCase))
            {
                conn.Execute("UPDATE jobs SET openai_status=@s, updated_utc=@u WHERE id=@i;", new { s = status, u = DateTime.UtcNow.ToString("o"), i = (string)r.id });
                continue;
            }

            var finalStatus = status.Equals("completed", StringComparison.OrdinalIgnoreCase) ? "completed" : "failed";
            conn.Execute("""
                UPDATE jobs
                SET status=@st,
                    openai_status=@os,
                    openai_raw_json=@raw,
                    result_text=@res,
                    openai_completed_at_utc=@c,
                    updated_utc=@u
                WHERE id=@i;
            """, new
            {
                st = finalStatus,
                os = status,
                raw,
                res = output,
                c = DateTime.UtcNow.ToString("o"),
                u = DateTime.UtcNow.ToString("o"),
                i = (string)r.id
            });
            if (!string.IsNullOrWhiteSpace(output) && IsReportDiskEnabled(conn))
            {
                WriteReport((string)r.id, output, raw);
            }
        }
    }

    private static bool IsReportDiskEnabled(SqliteConnection conn)
        => conn.QuerySingleOrDefault<int>("SELECT enabled FROM automations WHERE id='report.disk';") != 0;

    private static void WriteReport(string jobId, string text, string raw)
    {
        var dir = Path.Combine("artifacts", "maelstrombot");
        Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, $"{jobId}.txt"), text ?? "");
        File.WriteAllText(Path.Combine(dir, $"{jobId}.json"), raw ?? "");
    }
}
