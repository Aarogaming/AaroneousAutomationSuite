using System.Net.Http.Headers;
using System.Text.Json;
using Dapper;
using Microsoft.Data.Sqlite;

namespace MaelstromBot.Server;

internal class GitHubPoller : BackgroundService
{
    private readonly ILogger<GitHubPoller> _logger;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly DatabaseOptions _db;

    public GitHubPoller(ILogger<GitHubPoller> logger, IHttpClientFactory httpClientFactory, DatabaseOptions db)
    {
        _logger = logger;
        _httpClientFactory = httpClientFactory;
        _db = db;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await RunOnce(stoppingToken);
            var delaySeconds = GetIntervalSeconds();
            await Task.Delay(TimeSpan.FromSeconds(delaySeconds), stoppingToken);
        }
    }

    private int GetIntervalSeconds()
    {
        var env = Environment.GetEnvironmentVariable("GITHUB_POLL_INTERVAL_SECONDS");
        return int.TryParse(env, out var v) && v >= 60 ? v : 300;
    }

    private async Task RunOnce(CancellationToken ct)
    {
        var owner = Environment.GetEnvironmentVariable("GITHUB_OWNER");
        var repo = Environment.GetEnvironmentVariable("GITHUB_REPO");
        if (string.IsNullOrWhiteSpace(owner) || string.IsNullOrWhiteSpace(repo))
        {
            _logger.LogDebug("GitHub poller skipped (GITHUB_OWNER/REPO not set).");
            return;
        }

        try
        {
            var sha = await FetchHeadSha(owner, repo, ct);
            if (sha == null)
            {
                _logger.LogWarning("GitHub poller could not resolve HEAD sha for {owner}/{repo}", owner, repo);
                return;
            }

            using var conn = new SqliteConnection(_db.ConnectionString);
            var exists = conn.QuerySingle<int>("SELECT COUNT(*) FROM jobs WHERE source_sha=@s", new { s = sha }) > 0;
            if (exists) return;

            var jobId = Guid.NewGuid().ToString();
            var now = DateTime.UtcNow.ToString("o");
            conn.Execute("""
                INSERT INTO jobs (id, source_sha, github_delivery, status, created_utc, updated_utc, payload)
                VALUES (@i, @s, 'poller', 'queued', @c, @c, '{}');
            """, new { i = jobId, s = sha, c = now });

            _logger.LogInformation("GitHub poller enqueued job {jobId} for sha {sha}", jobId, sha);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "GitHub poller failed.");
        }
    }

    private async Task<string?> FetchHeadSha(string owner, string repo, CancellationToken ct)
    {
        var url = $"https://api.github.com/repos/{owner}/{repo}/branches/main";
        var client = _httpClientFactory.CreateClient();
        client.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("maelstrom-bot", "1.0"));

        var token = Environment.GetEnvironmentVariable("GITHUB_TOKEN");
        if (!string.IsNullOrWhiteSpace(token))
        {
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }

        using var resp = await client.GetAsync(url, ct);
        if (!resp.IsSuccessStatusCode) return null;
        var json = await resp.Content.ReadAsStringAsync(ct);
        using var doc = JsonDocument.Parse(json);
        return doc.RootElement.GetProperty("commit").GetProperty("sha").GetString();
    }
}
