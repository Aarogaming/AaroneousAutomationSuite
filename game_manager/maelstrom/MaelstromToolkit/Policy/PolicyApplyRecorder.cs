using System.Globalization;
using System.Text;
using System.Text.Json;

namespace MaelstromToolkit.Policy;

internal sealed record PolicyApplyEvaluation(
    string PreviousHash,
    string NewHash,
    string RiskLevel,
    IReadOnlyList<string> ChangedFields,
    IReadOnlyList<string> Notes);

internal sealed class PolicyApplyRecorder
{
    private readonly PolicyTxtParserFacade _parser = new();

    public PolicyApplyEvaluation Record(string outRoot, string policyPath, PolicyEffectiveResult effective, string newPolicyText, string? previousPolicyText, string? previousHash)
    {
        var historyDir = Path.Combine(outRoot, "policy", "history", effective.Hash);
        Directory.CreateDirectory(historyDir);

        var prevSnapshot = ParseSnapshot(previousPolicyText);
        var eval = Evaluate(effective.Snapshot!, prevSnapshot, previousHash ?? "none", effective.Hash);

        WriteAtomic(Path.Combine(historyDir, "policy.txt"), Normalize(newPolicyText));
        WriteAtomic(Path.Combine(historyDir, "policy.sha256"), effective.Hash);
        WriteAtomic(Path.Combine(historyDir, "effective.txt"), BuildEffectiveText(policyPath, effective));
        WriteAtomic(Path.Combine(historyDir, "eval.md"), BuildEvalMd(eval));
        WriteAtomic(Path.Combine(historyDir, "eval.json"), BuildEvalJson(eval));

        return eval;
    }

    internal PolicyApplyEvaluation Evaluate(PolicySnapshot current, PolicySnapshot? previous, string previousHash, string newHash)
    {
        var changedFields = GetChangedFields(current, previous);
        var riskLevel = GetRiskLevel(current, previous);
        var notes = GetNotes(current, previous);

        return new PolicyApplyEvaluation(
            PreviousHash: previousHash,
            NewHash: newHash,
            RiskLevel: riskLevel,
            ChangedFields: changedFields,
            Notes: notes);
    }

    private PolicySnapshot? ParseSnapshot(string? text)
    {
        if (string.IsNullOrEmpty(text)) return null;
        var parsed = _parser.Parse(text);
        return parsed.Snapshot;
    }

    private static IReadOnlyList<string> GetChangedFields(PolicySnapshot current, PolicySnapshot? previous)
    {
        var fields = new List<string>();

        AddIfChanged(fields, "global.activeProfile", previous?.Global.ActiveProfile, current.Global.ActiveProfile);
        AddIfChanged(fields, "ai.enabled", previous?.Ai.Enabled, current.Ai.Enabled);
        AddIfChanged(fields, "ai.provider", previous?.Ai.Provider, current.Ai.Provider);
        AddIfChanged(fields, "ai.model", previous?.Ai.Model, current.Ai.Model);
        AddIfChanged(fields, "ai.allowedTools", previous?.Ai.AllowedTools, current.Ai.AllowedTools);
        AddIfChanged(fields, "ai.deniedTools", previous?.Ai.DeniedTools, current.Ai.DeniedTools);
        AddIfChanged(fields, "ethics.prohibit", previous?.Ethics.Prohibit, current.Ethics.Prohibit);
        AddIfChanged(fields, "privacy.storeScreenshots", previous?.Ethics.PrivacyStoreScreenshots, current.Ethics.PrivacyStoreScreenshots);
        AddIfChanged(fields, "privacy.storeAudio", previous?.Ethics.PrivacyStoreAudio, current.Ethics.PrivacyStoreAudio);

        foreach (var name in new[] { "live_advisory", "live_pilot" })
        {
            current.Profiles.TryGetValue(name, out var curProfile);
            ProfileSettings? prevProfile = null;
            if (previous != null)
            {
                previous.Profiles.TryGetValue(name, out prevProfile);
            }
            AddIfChanged(fields, $"profile.{name}.mode", prevProfile?.Mode, curProfile?.Mode);
            AddIfChanged(fields, $"profile.{name}.autonomy", prevProfile?.Autonomy, curProfile?.Autonomy);
        }

        return fields.OrderBy(f => f, StringComparer.Ordinal).ToArray();
    }

    private static string GetRiskLevel(PolicySnapshot current, PolicySnapshot? previous)
    {
        var prohibitsCurrent = SplitList(current.Ethics.Prohibit);
        var prohibitsPrev = SplitList(previous?.Ethics.Prohibit);
        var removedProhibits = prohibitsPrev.Except(prohibitsCurrent, StringComparer.OrdinalIgnoreCase).ToList();

        if (current.Ai.AllowSendScreenshotsToModel || current.Ai.AllowSendAudioToModel || removedProhibits.Any())
        {
            return "HIGH";
        }

        var allowedTools = SplitList(current.Ai.AllowedTools);
        var liveRequested = current.Global.ActiveProfile.StartsWith("live_", StringComparison.OrdinalIgnoreCase);
        if (current.Ai.Enabled || liveRequested || allowedTools.Any())
        {
            return "MEDIUM";
        }

        return "LOW";
    }

    private static IReadOnlyList<string> GetNotes(PolicySnapshot current, PolicySnapshot? previous)
    {
        var notes = new List<string>();
        if (current.Ai.Enabled) notes.Add("AI enabled");
        if (current.Ai.AllowSendScreenshotsToModel) notes.Add("Allow send screenshots to model");
        if (current.Ai.AllowSendAudioToModel) notes.Add("Allow send audio to model");
        var allows = SplitList(current.Ai.AllowedTools);
        if (allows.Any()) notes.Add("Allowed tools configured");
        if (current.Global.ActiveProfile.StartsWith("live_", StringComparison.OrdinalIgnoreCase)) notes.Add("LIVE active profile");

        var prohibitsCurrent = SplitList(current.Ethics.Prohibit);
        var prohibitsPrev = SplitList(previous?.Ethics.Prohibit);
        var removed = prohibitsPrev.Except(prohibitsCurrent, StringComparer.OrdinalIgnoreCase).ToList();
        if (removed.Any()) notes.Add($"Prohibit removed: {string.Join(",", removed.OrderBy(x => x, StringComparer.OrdinalIgnoreCase))}");
        else notes.Add("Prohibit list unchanged");

        return notes.OrderBy(n => n, StringComparer.Ordinal).ToArray();
    }

    private static void AddIfChanged(List<string> fields, string name, object? previous, object? current)
    {
        var prev = previous?.ToString() ?? string.Empty;
        var cur = current?.ToString() ?? string.Empty;
        if (!string.Equals(prev, cur, StringComparison.OrdinalIgnoreCase))
        {
            fields.Add(name);
        }
    }

    private static IReadOnlyList<string> SplitList(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return Array.Empty<string>();
        return value.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
    }

    private static string BuildEvalMd(PolicyApplyEvaluation eval)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Policy Apply Evaluation");
        sb.AppendLine($"Previous: {eval.PreviousHash}");
        sb.AppendLine($"New: {eval.NewHash}");
        sb.AppendLine($"Risk: {eval.RiskLevel}");
        sb.AppendLine($"ChangedFields: {(eval.ChangedFields.Count == 0 ? "none" : string.Join(",", eval.ChangedFields))}");
        sb.AppendLine("Notes:");
        foreach (var note in eval.Notes)
        {
            sb.AppendLine($"- {note}");
        }
        return sb.ToString();
    }

    private static string BuildEvalJson(PolicyApplyEvaluation eval)
    {
        var dto = new
        {
            previousHash = eval.PreviousHash,
            newHash = eval.NewHash,
            riskLevel = eval.RiskLevel,
            changedFields = eval.ChangedFields.ToArray(),
            notes = eval.Notes.ToArray()
        };

        return JsonSerializer.Serialize(dto, new JsonSerializerOptions { WriteIndented = true });
    }

    private static string BuildEffectiveText(string policyPath, PolicyEffectiveResult effective)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Source: {effective.Source}");
        sb.AppendLine($"File: {policyPath}");
        sb.AppendLine($"Hash: {effective.Hash}");
        sb.AppendLine($"ActiveProfile: {effective.ActiveProfile}");
        sb.AppendLine($"ProfileMode: {effective.ProfileMode}");
        sb.AppendLine($"OperatingMode: {effective.OperatingMode}");
        sb.AppendLine($"LiveStatus: {effective.LiveStatus}");
        sb.AppendLine($"LiveReasons: {(effective.Reasons.Count == 0 ? "none" : string.Join(",", effective.Reasons))}");
        sb.AppendLine($"AI: enabled={(effective.Snapshot?.Ai.Enabled ?? false).ToString().ToLowerInvariant()} provider={effective.Snapshot?.Ai.Provider ?? "none"} model={effective.Snapshot?.Ai.Model ?? string.Empty} temperature={(effective.Snapshot?.Ai.Temperature ?? 0).ToString(CultureInfo.InvariantCulture)} apiKeyEnv={effective.Snapshot?.Ai.ApiKeyEnv ?? string.Empty} allowSendScreenshotsToModel={(effective.Snapshot?.Ai.AllowSendScreenshotsToModel ?? false).ToString().ToLowerInvariant()} allowSendAudioToModel={(effective.Snapshot?.Ai.AllowSendAudioToModel ?? false).ToString().ToLowerInvariant()}");
        sb.AppendLine($"Ethics: purpose={effective.Snapshot?.Ethics.Purpose ?? string.Empty} requireConsentForEnvironmentControl={(effective.Snapshot?.Ethics.RequireConsentForEnvironmentControl ?? false).ToString().ToLowerInvariant()} prohibit={effective.Snapshot?.Ethics.Prohibit ?? string.Empty} privacy.storeScreenshots={(effective.Snapshot?.Ethics.PrivacyStoreScreenshots ?? false).ToString().ToLowerInvariant()} privacy.storeAudio={(effective.Snapshot?.Ethics.PrivacyStoreAudio ?? false).ToString().ToLowerInvariant()}");
        sb.AppendLine($"Diagnostics: {effective.Diagnostics.Count}");
        foreach (var d in effective.Diagnostics)
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code} | {d.Severity} | {d.Section}.{d.Key} | {line} | {d.Message}");
        }
        return sb.ToString();
    }

    private static void WriteAtomic(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var tmp = path + ".tmp_" + Guid.NewGuid().ToString("N");
        File.WriteAllText(tmp, Normalize(content), new UTF8Encoding(false));
        File.Move(tmp, path, overwrite: true);
    }

    private static string Normalize(string input) =>
        input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\r", "\n", StringComparison.Ordinal);
}
