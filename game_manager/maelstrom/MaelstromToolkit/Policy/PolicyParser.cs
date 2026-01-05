using System.Globalization;
using System.Text;

namespace MaelstromToolkit.Policy;

internal sealed class PolicyParser
{
    private sealed record Entry(string Section, string Key, string Value, int Line);

    public PolicyLoadResult Parse(string text)
    {
        var result = new PolicyLoadResult();
        var entries = ParseLines(text, result);
        if (result.HasErrors) return result;

        var doc = new PolicyDocument();
        ApplyEntries(doc, entries, result);
        result.Document = result.HasErrors ? null : doc;
        return result;
    }

    private static List<Entry> ParseLines(string text, PolicyLoadResult result)
    {
        var entries = new List<Entry>();
        var lines = text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None);
        var currentSection = string.Empty;

        for (var i = 0; i < lines.Length; i++)
        {
            var raw = lines[i];
            var line = raw.Trim();
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#", StringComparison.Ordinal) || line.StartsWith(";", StringComparison.Ordinal))
            {
                continue;
            }

            if (line.StartsWith("[", StringComparison.Ordinal) && line.EndsWith("]", StringComparison.Ordinal))
            {
                currentSection = line[1..^1].Trim();
                continue;
            }

            var kvp = line.Split('=', 2);
            if (kvp.Length != 2)
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL001", DiagnosticSeverity.Error, currentSection, string.Empty, i + 1, $"Invalid entry \"{raw}\" (expected key=value)."));
                continue;
            }

            entries.Add(new Entry(currentSection, kvp[0].Trim(), kvp[1].Trim(), i + 1));
        }

        return entries;
    }

    private static void ApplyEntries(PolicyDocument doc, List<Entry> entries, PolicyLoadResult result)
    {
        foreach (var entry in entries)
        {
            switch (entry.Section.ToLowerInvariant())
            {
                case "global":
                    ApplyGlobal(doc.Global, entry, result);
                    break;
                case "ethics":
                    ApplyEthics(doc.Ethics, entry, result);
                    break;
                case "ai":
                    ApplyAi(doc.Ai, entry, result);
                    break;
                default:
                    if (entry.Section.StartsWith("profile", StringComparison.OrdinalIgnoreCase))
                    {
                        var profileName = entry.Section["profile".Length..].Trim();
                        if (profileName.StartsWith(" ", StringComparison.Ordinal)) profileName = profileName.Trim();
                        if (string.IsNullOrWhiteSpace(profileName))
                        {
                        result.Diagnostics.Add(new PolicyDiagnostic("AASPOL010", DiagnosticSeverity.Error, entry.Section, entry.Key, entry.Line, "Profile section missing name (use [profile <name>])."));
                            break;
                        }
                        if (!doc.Profiles.TryGetValue(profileName, out var profile))
                        {
                            profile = new ProfileSettings { Name = profileName };
                            doc.Profiles[profileName] = profile;
                        }
                        ApplyProfile(profile, entry, doc.Global.DenyUnknownKeys, result);
                    }
                    else
                    {
                var severity = doc.Global.DenyUnknownKeys ? DiagnosticSeverity.Error : DiagnosticSeverity.Warning;
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL011", severity, entry.Section, entry.Key, entry.Line, $"Unknown section [{entry.Section}]."));
                    }
                    break;
            }
        }

        Validate(doc, result);
    }

    private static void ApplyGlobal(GlobalSettings global, Entry entry, PolicyLoadResult result)
    {
        switch (entry.Key.ToLowerInvariant())
        {
            case "schemaversion":
                if (int.TryParse(entry.Value, out var ver)) global.SchemaVersion = ver;
                else AddInvalid(result, entry, "AASPOL001", "schemaVersion must be an integer.");
                break;
            case "activeprofile":
                global.ActiveProfile = entry.Value;
                break;
            case "oninvalidconfig":
                global.OnInvalidConfig = entry.Value;
                break;
            case "requireallprofilesvalid":
                AssignBool(entry, v => global.RequireAllProfilesValid = v, result);
                break;
            case "denyunknowncapabilities":
                AssignBool(entry, v => global.DenyUnknownCapabilities = v, result);
                break;
            case "denyunknownkeys":
                AssignBool(entry, v => global.DenyUnknownKeys = v, result);
                break;
            case "livemeanslive":
                AssignBool(entry, v => global.LiveMeansLive = v, result);
                break;
            case "safewrites":
                global.SafeWrites = entry.Value;
                break;
            default:
                AddUnknown(entry, result, "AASPOL011");
                break;
        }
    }

    private static void ApplyEthics(EthicsSettings ethics, Entry entry, PolicyLoadResult result)
    {
        switch (entry.Key.ToLowerInvariant())
        {
            case "purpose":
                ethics.Purpose = entry.Value;
                break;
            case "requireconsentforenvironmentcontrol":
                AssignBool(entry, v => ethics.RequireConsentForEnvironmentControl = v, result);
                break;
            case "prohibit":
                ethics.Prohibit = entry.Value;
                break;
            case "privacy.nosecretsinlogs":
                AssignBool(entry, v => ethics.PrivacyNoSecretsInLogs = v, result);
                break;
            case "privacy.storescreenshots":
                AssignBool(entry, v => ethics.PrivacyStoreScreenshots = v, result);
                break;
            case "privacy.storeaudio":
                AssignBool(entry, v => ethics.PrivacyStoreAudio = v, result);
                break;
            default:
                AddUnknown(entry, result, "AASPOL011");
                break;
        }
    }

    private static void ApplyProfile(ProfileSettings profile, Entry entry, bool denyUnknownKeys, PolicyLoadResult result)
    {
        switch (entry.Key.ToLowerInvariant())
        {
            case "mode":
                profile.Mode = entry.Value;
                break;
            case "autonomy":
                profile.Autonomy = entry.Value;
                break;
            default:
                var severity = denyUnknownKeys ? DiagnosticSeverity.Error : DiagnosticSeverity.Warning;
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL011", severity, $"profile {profile.Name}", entry.Key, entry.Line, $"Unknown key {entry.Key}"));
                break;
        }
    }

    private static void ApplyAi(AiSettings ai, Entry entry, PolicyLoadResult result)
    {
        switch (entry.Key.ToLowerInvariant())
        {
            case "enabled":
                AssignBool(entry, v => ai.Enabled = v, result);
                break;
            case "provider":
                ai.Provider = entry.Value;
                break;
            case "apikeyenv":
                ai.ApiKeyEnv = entry.Value;
                break;
            case "endpoint":
                ai.Endpoint = entry.Value;
                break;
            case "model":
                ai.Model = entry.Value;
                break;
            case "temperature":
                if (double.TryParse(entry.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out var t))
                    ai.Temperature = t;
                else AddInvalid(result, entry, "AASPOL001", "temperature must be numeric.");
                break;
            case "allowsendscreenshotstomodel":
                AssignBool(entry, v => ai.AllowSendScreenshotsToModel = v, result);
                break;
            case "allowsendaudiotomodel":
                AssignBool(entry, v => ai.AllowSendAudioToModel = v, result);
                break;
            case "store":
                AssignBool(entry, v => ai.Store = v, result);
                break;
            case "reasoningeffort":
                ai.ReasoningEffort = entry.Value;
                break;
            case "timeoutseconds":
                if (int.TryParse(entry.Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var tsec))
                    ai.TimeoutSeconds = tsec;
                else AddInvalid(result, entry, "AASPOL001", "timeoutSeconds must be integer.");
                break;
            case "maxoutputtokens":
                if (int.TryParse(entry.Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var tokens))
                    ai.MaxOutputTokens = tokens;
                else AddInvalid(result, entry, "AASPOL001", "maxOutputTokens must be integer.");
                break;
            case "usertag":
                ai.UserTag = entry.Value;
                break;
            case "allowedtools":
                ai.AllowedTools = entry.Value;
                break;
            case "deniedtools":
                ai.DeniedTools = entry.Value;
                break;
            default:
                AddUnknown(entry, result, "AASPOL011");
                break;
        }
    }

    private static void Validate(PolicyDocument doc, PolicyLoadResult result)
    {
        if (doc.Global.SchemaVersion != 1)
        {
            result.Diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "global", "schemaVersion", null, "Unsupported schemaVersion (expected 1)."));
        }

        var requiredProfiles = new[] { "catalog", "simulation", "live_advisory", "live_pilot" };
        foreach (var rp in requiredProfiles)
        {
            if (!doc.Profiles.ContainsKey(rp))
            {
                var severity = doc.Global.RequireAllProfilesValid ? DiagnosticSeverity.Error : DiagnosticSeverity.Warning;
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL010", severity, "profiles", rp, null, $"Missing required profile \"{rp}\"."));
            }
        }

        foreach (var p in doc.Profiles.Values)
        {
            if (!IsValidMode(p.Mode))
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, $"profile {p.Name}", "mode", null, $"Invalid mode \"{p.Mode}\" (expected catalog|simulation|live)."));
            }
            if (p.Mode.Equals("live", StringComparison.OrdinalIgnoreCase) && string.IsNullOrWhiteSpace(p.Autonomy))
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL030", DiagnosticSeverity.Error, $"profile {p.Name}", "autonomy", null, "Autonomy is required for live profiles."));
            }
        }

        if (!doc.Profiles.ContainsKey(doc.Global.ActiveProfile))
        {
            result.Diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Error, "global", "activeProfile", null, $"Active profile \"{doc.Global.ActiveProfile}\" is not defined."));
        }

        if (doc.Ai.Enabled)
        {
            var provider = doc.Ai.Provider.ToLowerInvariant();
            if (provider is not ("openai" or "http" or "none"))
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL020", DiagnosticSeverity.Error, "ai", "provider", null, "Provider must be openai|http|none."));
            }
            if (provider == "openai" && string.IsNullOrWhiteSpace(doc.Ai.ApiKeyEnv))
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Error, "ai", "apiKeyEnv", null, "apiKeyEnv is required when provider=openai."));
            }
            if (provider == "http" && string.IsNullOrWhiteSpace(doc.Ai.Endpoint))
            {
                result.Diagnostics.Add(new PolicyDiagnostic("AASPOL011", DiagnosticSeverity.Warning, "ai", "endpoint", null, "endpoint should be set when provider=http."));
            }
        }
    }

    private static bool IsValidMode(string mode) =>
        mode.Equals("catalog", StringComparison.OrdinalIgnoreCase) ||
        mode.Equals("simulation", StringComparison.OrdinalIgnoreCase) ||
        mode.Equals("live", StringComparison.OrdinalIgnoreCase);

    private static void AssignBool(Entry entry, Action<bool> setter, PolicyLoadResult result)
    {
        if (bool.TryParse(entry.Value, out var v))
        {
            setter(v);
        }
        else
        {
            AddInvalid(result, entry, "POL099", "Expected boolean (true/false).");
        }
    }

    private static void AddInvalid(PolicyLoadResult result, Entry entry, string code, string msg) =>
        result.Diagnostics.Add(new PolicyDiagnostic(code, DiagnosticSeverity.Error, entry.Section, entry.Key, entry.Line, msg));

    private static void AddUnknown(Entry entry, PolicyLoadResult result, string code) =>
        result.Diagnostics.Add(new PolicyDiagnostic(code, DiagnosticSeverity.Warning, entry.Section, entry.Key, entry.Line, $"Unknown key {entry.Key}."));
}
