using System.Data;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Dapper;
using Microsoft.Data.Sqlite;
using StandardWebhooks;
using MaelstromBot.Server;

var builder = WebApplication.CreateBuilder(args);

// Logging (console only for now)
builder.Logging.ClearProviders();
builder.Logging.AddConsole();

string GetCfg(string envName, string configKey, string defaultValue)
{
    var env = Environment.GetEnvironmentVariable(envName);
    if (!string.IsNullOrWhiteSpace(env)) return env;
    var cfg = builder.Configuration[configKey];
    return string.IsNullOrWhiteSpace(cfg) ? defaultValue : cfg;
}

int GetCfgInt(string envName, string configKey, int defaultValue)
{
    if (int.TryParse(Environment.GetEnvironmentVariable(envName), out var envVal)) return envVal;
    if (int.TryParse(builder.Configuration[configKey], out var cfgVal)) return cfgVal;
    return defaultValue;
}

var portMode = GetCfg("MAELSTROM_PORT_MODE", "MaelstromBot:PortMode", "single");
var isDualPort = portMode.Equals("dual", StringComparison.OrdinalIgnoreCase);
var webhooksPort = GetCfgInt("MAELSTROM_WEBHOOKS_PORT", "MaelstromBot:WebhooksPort", 9410);
var adminPort = GetCfgInt("MAELSTROM_ADMIN_PORT", "MaelstromBot:AdminPort", 9411);

if (isDualPort)
{
    builder.WebHost.ConfigureKestrel(k =>
    {
        k.ListenLocalhost(webhooksPort);
        k.ListenLocalhost(adminPort);
    });
}

var dbPath = Path.Combine(builder.Environment.ContentRootPath, "artifacts", "bot", "db", "maelstrombot.db");
Directory.CreateDirectory(Path.GetDirectoryName(dbPath)!);
var connString = $"Data Source={dbPath}";

builder.Services.AddSingleton(new DatabaseOptions(connString));
builder.Services.AddHttpClient();
builder.Services.AddHostedService<GitHubPoller>();
builder.Services.AddHostedService<JobSubmitter>();
builder.Services.AddHostedService<OpenAiReconciler>();
builder.Services.AddSingleton<OpenAiClient>();

var app = builder.Build();

// Global strict path/port gate in dual-port mode
if (isDualPort)
{
    app.Use(async (ctx, next) =>
    {
        var port = ctx.Connection.LocalPort;
        if (port == webhooksPort)
        {
            if (!ctx.Request.Path.StartsWithSegments("/webhooks"))
            {
                ctx.Response.StatusCode = StatusCodes.Status404NotFound;
                return;
            }
        }
        else if (port == adminPort)
        {
            if (!(ctx.Request.Path.StartsWithSegments("/bot") || ctx.Request.Path.StartsWithSegments("/healthz")))
            {
                ctx.Response.StatusCode = StatusCodes.Status404NotFound;
                return;
            }
        }
        await next();
    });
}

// Initialize schema
using (var conn = new SqliteConnection(connString))
{
    conn.Execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source_sha TEXT,
    github_delivery TEXT,
    openai_response_id TEXT,
    openai_status TEXT,
    openai_submitted_at_utc TEXT,
    openai_completed_at_utc TEXT,
    openai_raw_json TEXT,
    result_text TEXT,
    status TEXT,
    created_utc TEXT,
    updated_utc TEXT,
    payload TEXT
);
""");

    conn.Execute("""
CREATE TABLE IF NOT EXISTS dedupe (
    source TEXT,
    key TEXT,
    created_utc TEXT,
    PRIMARY KEY (source, key)
);
""");

    conn.Execute("""
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT,
    salt BLOB,
    hash BLOB,
    created_utc TEXT,
    revoked_utc TEXT
);
""");

    conn.Execute("""
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
);
""");

    EnsureColumn(conn, "api_keys", "name", "TEXT");
    EnsureColumn(conn, "api_keys", "salt", "BLOB");
    EnsureColumn(conn, "api_keys", "hash", "BLOB");
    EnsureColumn(conn, "api_keys", "created_utc", "TEXT");
    EnsureColumn(conn, "api_keys", "revoked_utc", "TEXT");
    EnsureColumn(conn, "jobs", "openai_status", "TEXT");
    EnsureColumn(conn, "jobs", "openai_submitted_at_utc", "TEXT");
    EnsureColumn(conn, "jobs", "openai_completed_at_utc", "TEXT");
    EnsureColumn(conn, "jobs", "openai_raw_json", "TEXT");
    EnsureColumn(conn, "jobs", "result_text", "TEXT");

    conn.Execute("""
CREATE TABLE IF NOT EXISTS automations (
    id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL,
    description TEXT NOT NULL,
    updated_utc TEXT NOT NULL
);
""");
    SeedAutomation(conn, "openai.analysis", true, "Run OpenAI background analysis");
    SeedAutomation(conn, "report.disk", true, "Write report JSON to disk");
    SeedAutomation(conn, "github.poller", false, "Fallback polling for missed webhooks");
}

// Helpers
bool VerifyGitHubSignature(byte[] body, string? sigHeader, string secret)
{
    if (string.IsNullOrWhiteSpace(sigHeader) || !sigHeader.StartsWith("sha256=", StringComparison.OrdinalIgnoreCase))
        return false;
    var expectedHex = sigHeader.Substring("sha256=".Length);
    using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
    var hash = hmac.ComputeHash(body);
    var actualHex = Convert.ToHexString(hash).ToLowerInvariant();
    return CryptographicOperations.FixedTimeEquals(
        Encoding.ASCII.GetBytes(actualHex),
        Encoding.ASCII.GetBytes(expectedHex.ToLowerInvariant()));
}

static bool EnsureColumn(SqliteConnection conn, string table, string column, string type)
{
    var exists = conn.QuerySingle<int>("SELECT COUNT(*) FROM pragma_table_info(@t) WHERE name=@c;", new { t = table, c = column }) > 0;
    if (!exists)
    {
        conn.Execute($"ALTER TABLE {table} ADD COLUMN {column} {type};");
    }
    return !exists;
}

static void SeedAutomation(SqliteConnection conn, string id, bool enabled, string description)
{
    conn.Execute("""
INSERT INTO automations(id, enabled, description, updated_utc)
VALUES (@i, @e, @d, @t)
ON CONFLICT(id) DO NOTHING;
""", new { i = id, e = enabled ? 1 : 0, d = description, t = DateTime.UtcNow.ToString("o") });
}

byte[] GetPepper(IDbConnection conn)
{
    var val = conn.QuerySingleOrDefault<string>("SELECT value FROM state WHERE key='api_key_pepper_b64';");
    if (!string.IsNullOrWhiteSpace(val))
    {
        return Convert.FromBase64String(val);
    }
    var pepper = RandomNumberGenerator.GetBytes(32);
    conn.Execute("INSERT OR REPLACE INTO state(key,value) VALUES('api_key_pepper_b64', @v);", new { v = Convert.ToBase64String(pepper) });
    return pepper;
}

string CreateApiKey(IDbConnection conn, string name, string role)
{
    var pepper = GetPepper(conn);
    var keyId = Guid.NewGuid().ToString("N");
    var secret = Convert.ToBase64String(RandomNumberGenerator.GetBytes(32));
    var token = $"maelstrom_{keyId}.{secret}";

    var salt = RandomNumberGenerator.GetBytes(16);
    var hash = Rfc2898DeriveBytes.Pbkdf2(secret, salt.Concat(pepper).ToArray(), 150_000, HashAlgorithmName.SHA256, 32);

    var now = DateTime.UtcNow.ToString("o");
    conn.Execute("""
        INSERT OR REPLACE INTO api_keys (id, name, role, salt, hash, created_utc)
        VALUES (@i, @n, @r, @s, @h, @c);
    """, new { i = keyId, n = name, r = role, s = salt, h = hash, c = now });

    return token;
}

ClaimsPrincipal? ValidateToken(IDbConnection conn, string token)
{
    const string prefix = "maelstrom_";
    if (!token.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) return null;
    var rest = token[prefix.Length..];
    var idx = rest.IndexOf('.');
    if (idx <= 0) return null;
    var keyId = rest[..idx];
    var secret = rest[(idx + 1)..];

    var row = conn.QuerySingleOrDefault<(string Role, byte[] Salt, byte[] Hash)>(
        "SELECT role, salt, hash FROM api_keys WHERE id=@i AND revoked_utc IS NULL;",
        new { i = keyId });
    if (row == default) return null;

    var pepper = GetPepper(conn);
    var calc = Rfc2898DeriveBytes.Pbkdf2(secret, row.Salt.Concat(pepper).ToArray(), 150_000, HashAlgorithmName.SHA256, 32);
    if (!CryptographicOperations.FixedTimeEquals(calc, row.Hash)) return null;

    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, keyId),
        new Claim(ClaimTypes.Role, row.Role)
    };
    return new ClaimsPrincipal(new ClaimsIdentity(claims, "ApiKey"));
}

bool RequireApiKey(HttpContext ctx, IDbConnection conn, out ClaimsPrincipal? principal)
{
    principal = null;
    var auth = ctx.Request.Headers.Authorization.ToString();
    if (!auth.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)) return false;
    var token = auth["Bearer ".Length..].Trim();
    if (string.IsNullOrWhiteSpace(token)) return false;
    principal = ValidateToken(conn, token);
    return principal is not null;
}

// CLI init mode
if (args.Contains("--init-admin-key"))
{
    using var conn = new SqliteConnection(connString);
    conn.Open();
    var token = CreateApiKey(conn, "initial-admin", "admin");
    Console.WriteLine("=== INITIAL ADMIN TOKEN ===");
    Console.WriteLine(token);
    Console.WriteLine("===========================");
    return;
}

// Health endpoints
app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));

// Port-partitioned groups
var webhooks = app.MapGroup("/webhooks");
if (isDualPort) webhooks.AddEndpointFilter(new PortFilter(webhooksPort));

var bot = app.MapGroup("/bot");
if (isDualPort) bot.AddEndpointFilter(new PortFilter(adminPort));

// Webhook health
webhooks.MapGet("/healthz", () => Results.Ok(new { ok = true, utc = DateTime.UtcNow }));

webhooks.MapPost("/github", async (HttpContext ctx) =>
{
    var secret = Environment.GetEnvironmentVariable("GITHUB_WEBHOOK_SECRET");
    if (string.IsNullOrWhiteSpace(secret)) return Results.Problem("Missing GITHUB_WEBHOOK_SECRET", statusCode: 500);

    using var ms = new MemoryStream();
    await ctx.Request.Body.CopyToAsync(ms);
    var bodyBytes = ms.ToArray();
    var sig = ctx.Request.Headers["X-Hub-Signature-256"].ToString();
    if (!VerifyGitHubSignature(bodyBytes, sig, secret)) return Results.Unauthorized();

    var eventType = ctx.Request.Headers["X-GitHub-Event"].ToString();
    if (!string.Equals(eventType, "push", StringComparison.OrdinalIgnoreCase)) return Results.Ok();

    var delivery = ctx.Request.Headers["X-GitHub-Delivery"].ToString();
    using var conn = new SqliteConnection(connString);
    var deduped = conn.Execute("INSERT OR IGNORE INTO dedupe (source, key, created_utc) VALUES ('github', @k, @c)",
        new { k = delivery, c = DateTime.UtcNow.ToString("o") });
    if (deduped == 0) return Results.Ok();

    var payload = Encoding.UTF8.GetString(bodyBytes);
    var doc = System.Text.Json.JsonDocument.Parse(payload);
    var sha = doc.RootElement.GetProperty("after").GetString();
    var jobId = Guid.NewGuid().ToString();

    conn.Execute("""
        INSERT INTO jobs (id, source_sha, github_delivery, status, created_utc, updated_utc, payload)
        VALUES (@i, @s, @g, 'submitted', @c, @c, @p);
    """, new { i = jobId, s = sha, g = delivery, c = DateTime.UtcNow.ToString("o"), p = payload });

    conn.Execute("UPDATE jobs SET status='queued' WHERE id=@i", new { i = jobId });
    conn.Execute("INSERT OR REPLACE INTO state(key,value) VALUES('last_github_webhook_at_utc', @t);", new { t = DateTime.UtcNow.ToString("o") });

    return Results.Accepted($"/api/jobs/{jobId}", new { jobId });
});

webhooks.MapPost("/openai", async (HttpContext ctx) =>
{
    var secret = Environment.GetEnvironmentVariable("OPENAI_WEBHOOK_SECRET");
    if (string.IsNullOrWhiteSpace(secret)) return Results.Problem("Missing OPENAI_WEBHOOK_SECRET", statusCode: 500);

    using var reader = new StreamReader(ctx.Request.Body, Encoding.UTF8);
    var body = await reader.ReadToEndAsync();
    var webhook = new StandardWebhook(secret);
    try
    {
        webhook.Verify(body, ctx.Request.Headers);
    }
    catch
    {
        return Results.Unauthorized();
    }

    var doc = System.Text.Json.JsonDocument.Parse(body);
    var type = doc.RootElement.GetProperty("type").GetString();
    if (!string.Equals(type, "response.completed", StringComparison.OrdinalIgnoreCase)) return Results.Ok();

    var webhookId = ctx.Request.Headers["webhook-id"].ToString();
    using var conn = new SqliteConnection(connString);
    var deduped = conn.Execute("INSERT OR IGNORE INTO dedupe (source, key, created_utc) VALUES ('openai', @k, @c)",
        new { k = webhookId, c = DateTime.UtcNow.ToString("o") });
    if (deduped == 0) return Results.Ok();

    var data = doc.RootElement.GetProperty("data");
    var responseId = data.GetProperty("id").GetString();
    var metadata = data.GetProperty("metadata");
    var jobId = metadata.TryGetProperty("job_id", out var jv) ? jv.GetString() : null;
    if (string.IsNullOrWhiteSpace(jobId)) return Results.Ok();

    conn.Execute("""
        UPDATE jobs
        SET status='completed_pending_fetch',
            openai_status='completed',
            openai_response_id=@r,
            openai_completed_at_utc=@u,
            updated_utc=@u
        WHERE id=@i;
    """, new { r = responseId, u = DateTime.UtcNow.ToString("o"), i = jobId });
    conn.Execute("INSERT OR REPLACE INTO state(key,value) VALUES('last_openai_webhook_at_utc', @t);", new { t = DateTime.UtcNow.ToString("o") });

    return Results.Ok();
});

// legacy /api routes (keep as-is)
app.MapGet("/api/jobs", (HttpContext ctx) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var jobs = conn.Query("""
        SELECT id, source_sha, status, openai_response_id, created_utc, updated_utc
        FROM jobs
        ORDER BY updated_utc DESC
        LIMIT 50;
    """);
    return Results.Ok(jobs);
});

app.MapGet("/api/jobs/{id}", (HttpContext ctx, string id) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var job = conn.Query("""
        SELECT id, source_sha, status, openai_response_id, created_utc, updated_utc, payload
        FROM jobs
        WHERE id=@i;
    """, new { i = id }).FirstOrDefault();
    return job is null ? Results.NotFound() : Results.Ok(job);
});

app.MapGet("/api/status", (HttpContext ctx) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var queued = conn.QuerySingle<int>("SELECT COUNT(*) FROM jobs WHERE status IN ('submitted','queued','running')");
    return Results.Ok(new { status = "ok", queued });
});

// new protected endpoint group /bot/api
var botApi = bot.MapGroup("/api");
botApi.MapGet("/whoami", (HttpContext ctx) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out var principal)) return Results.Unauthorized();
    return Results.Ok(new
    {
        keyId = principal?.FindFirst(ClaimTypes.NameIdentifier)?.Value,
        role = principal?.FindFirst(ClaimTypes.Role)?.Value
    });
});

// status
botApi.MapGet("/status", (HttpContext ctx) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var counts = conn.QuerySingle("""
        SELECT
        SUM(CASE WHEN status IN ('submitted','queued') THEN 1 ELSE 0 END) AS queued,
        SUM(CASE WHEN status='running' THEN 1 ELSE 0 END) AS running,
        SUM(CASE WHEN status='awaiting_openai' THEN 1 ELSE 0 END) AS awaiting,
        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed
        FROM jobs;
    """);
    var lastJobId = conn.QuerySingleOrDefault<string>("SELECT id FROM jobs ORDER BY updated_utc DESC LIMIT 1;");
    var lastGithub = conn.QuerySingleOrDefault<string>("SELECT value FROM state WHERE key='last_github_webhook_at_utc';");
    var lastOpenai = conn.QuerySingleOrDefault<string>("SELECT value FROM state WHERE key='last_openai_webhook_at_utc';");
    return Results.Ok(new StatusDto(
        queued: (int)(counts.queued ?? 0),
        running: (int)(counts.running ?? 0),
        awaiting: (int)(counts.awaiting ?? 0),
        completed: (int)(counts.completed ?? 0),
        failed: (int)(counts.failed ?? 0),
        lastJobId: lastJobId,
        lastGithubWebhookAtUtc: lastGithub,
        lastOpenAiWebhookAtUtc: lastOpenai));
});

// jobs list
botApi.MapGet("/jobs", (HttpContext ctx, int? limit) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var lim = Math.Clamp(limit ?? 50, 1, 200);
    var rows = conn.Query("""
        SELECT id, source_sha, status, created_utc, updated_utc, openai_response_id, openai_status, github_delivery, error, result_text, openai_submitted_at_utc, openai_completed_at_utc
        FROM jobs
        ORDER BY updated_utc DESC
        LIMIT @l;
    """, new { l = lim });
    var list = rows.Select(r => new JobDto(
        jobId: r.id,
        sha: r.source_sha,
        status: r.status,
        trigger: r.github_delivery ?? "github_push",
        openaiResponseId: r.openai_response_id,
        openaiStatus: r.openai_status,
        openaiSubmittedAtUtc: r.openai_submitted_at_utc,
        openaiCompletedAtUtc: r.openai_completed_at_utc,
        createdAtUtc: r.created_utc,
        updatedAtUtc: r.updated_utc,
        error: r.error,
        resultSnippet: string.IsNullOrWhiteSpace((string?)r.result_text) ? null : ((string)r.result_text).Length > 200 ? ((string)r.result_text)[..200] : (string)r.result_text
    ));
    return Results.Ok(list);
});

// job detail
botApi.MapGet("/jobs/{id}", (HttpContext ctx, string id) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var r = conn.QuerySingleOrDefault("""
        SELECT id, source_sha, status, created_utc, updated_utc, openai_response_id, openai_status, github_delivery, error, result_text, openai_raw_json, openai_completed_at_utc, openai_submitted_at_utc
        FROM jobs WHERE id=@i;
    """, new { i = id });
    if (r == null) return Results.NotFound();
    return Results.Ok(new
    {
        jobId = r.id,
        sha = r.source_sha,
        status = r.status,
        trigger = r.github_delivery ?? "github_push",
        openaiResponseId = r.openai_response_id,
        openaiStatus = r.openai_status,
        openaiSubmittedAtUtc = r.openai_submitted_at_utc,
        openaiCompletedAtUtc = r.openai_completed_at_utc,
        createdAtUtc = r.created_utc,
        updatedAtUtc = r.updated_utc,
        error = r.error,
        resultText = r.result_text,
        openai_raw_json = r.openai_raw_json
    });
});

// automations
botApi.MapGet("/automations", (HttpContext ctx) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out _)) return Results.Unauthorized();
    var rows = conn.Query("SELECT id, enabled, description FROM automations ORDER BY id;");
    var list = rows.Select(r => new AutomationDto((string)r.id, ((long)r.enabled) != 0, (string)r.description));
    return Results.Ok(list);
});

botApi.MapPut("/automations/{id}", (HttpContext ctx, string id, AutomationDto body) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out var principal)) return Results.Unauthorized();
    if (!(principal?.IsInRole("admin") ?? false)) return Results.StatusCode(StatusCodes.Status403Forbidden);
    conn.Execute("UPDATE automations SET enabled=@e, updated_utc=@t WHERE id=@i;", new { e = body.enabled ? 1 : 0, t = DateTime.UtcNow.ToString("o"), i = id });
    var row = conn.QuerySingleOrDefault("SELECT id, enabled, description FROM automations WHERE id=@i;", new { i = id });
    if (row == null) return Results.NotFound();
    return Results.Ok(new AutomationDto((string)row.id, ((long)row.enabled) != 0, (string)row.description));
});

// minimal local UI
bot.MapGet("/ui", (HttpContext ctx) =>
{
    if (!(ctx.Connection.RemoteIpAddress?.Equals(System.Net.IPAddress.Loopback) ?? false))
        return Results.StatusCode(StatusCodes.Status403Forbidden);

    var html = """
<!doctype html>
<html><head><meta charset="utf-8"><title>MaelstromBot</title></head>
<body>
  <h2>MaelstromBot (local)</h2>
  <div>
    <label>API token:</label>
    <input id="tok" type="password" style="width:320px" />
    <button onclick="save()">Save</button>
    <button onclick="refresh()">Refresh</button>
  </div>
  <pre id="status"></pre>
  <h3>Automations</h3>
  <div id="autos"></div>
  <h3>Jobs</h3>
  <table id="jobs" border="1" cellpadding="4" cellspacing="0"></table>
<script>
const base = "/bot/api";
function token(){ return localStorage.getItem("bot_token")||""; }
function hdrs(){ return { "Authorization":"Bearer "+token() }; }
function save(){ localStorage.setItem("bot_token", document.getElementById("tok").value.trim()); refresh(); }

async function refresh(){
  document.getElementById("tok").value = token();
  const st = await fetch(base+"/status",{headers:hdrs()});
  document.getElementById("status").textContent = await st.text();

  const a = await fetch(base+"/automations",{headers:hdrs()});
  const autos = await a.json();
  const div = document.getElementById("autos");
  div.innerHTML = "";
  autos.forEach(x=>{
    const c = document.createElement("input"); c.type="checkbox"; c.checked=x.enabled;
    c.onchange=async()=>{await fetch(base+"/automations/"+encodeURIComponent(x.id),{method:"PUT",headers:{...hdrs(),"Content-Type":"application/json"},body:JSON.stringify({...x,enabled:c.checked})}); refresh();};
    const label=document.createElement("label"); label.textContent=" "+x.id+" - "+x.description;
    const wrap=document.createElement("div"); wrap.appendChild(c); wrap.appendChild(label); div.appendChild(wrap);
  });

  const j = await fetch(base+"/jobs?limit=20",{headers:hdrs()});
  const jobs = await j.json();
  const t = document.getElementById("jobs");
  t.innerHTML="<tr><th>Id</th><th>Status</th><th>OpenAI</th><th>SHA</th><th>Updated</th><th>Summary</th></tr>";
  jobs.forEach(x=>{
    const tr=document.createElement("tr");
    const summary = x.resultSnippet ?? "";
    tr.innerHTML=`<td>${x.jobId}</td><td>${x.status}</td><td>${x.openaiStatus ?? ""}</td><td>${x.sha ?? ""}</td><td>${x.updatedAtUtc}</td><td>${summary}</td>`;
    t.appendChild(tr);
  });
}
refresh();
</script>
</body></html>
""";
    return Results.Content(html, "text/html");
});

// cancel background response (admin)
botApi.MapPost("/jobs/{id}/cancel", async (HttpContext ctx, string id) =>
{
    using var conn = new SqliteConnection(connString);
    if (!RequireApiKey(ctx, conn, out var principal)) return Results.Unauthorized();
    if (!(principal?.IsInRole("admin") ?? false)) return Results.StatusCode(StatusCodes.Status403Forbidden);

    var row = conn.QuerySingleOrDefault("SELECT openai_response_id FROM jobs WHERE id=@i;", new { i = id });
    if (row == null) return Results.NotFound();
    string? respId = row.openai_response_id;
    if (string.IsNullOrWhiteSpace(respId)) return Results.BadRequest(new { error = "job has no OpenAI response id" });

    var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
    if (string.IsNullOrWhiteSpace(apiKey)) return Results.Problem("OPENAI_API_KEY not set", statusCode: 500);

    var client = app.Services.GetRequiredService<OpenAiClient>();
    await client.CancelAsync(apiKey, respId, ctx.RequestAborted);
    conn.Execute("UPDATE jobs SET status='cancel_requested', updated_utc=@u WHERE id=@i;", new { u = DateTime.UtcNow.ToString("o"), i = id });
    return Results.Accepted();
});

app.Run();

public record DatabaseOptions(string ConnectionString);



