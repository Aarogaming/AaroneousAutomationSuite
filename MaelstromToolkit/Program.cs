using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using MaelstromToolkit.Planning;
using MaelstromToolkit.Packs;
using MaelstromToolkit.Policy;
using MaelstromToolkit.Handoff;

namespace MaelstromToolkit;

internal static class Program
{
    private static readonly string DefaultPolicyText = PolicyDefaults.DefaultPolicyText;
    private record CommandOptions(
        string Command,
        string Subcommand,
        Dictionary<string, string> Args,
        bool Force,
        bool DryRun,
        bool Verbose,
        bool ShowHelp,
        bool ShowVersion);

    private static int Main(string[] args)
    {
        var options = Parse(args);
        if (options == null || options.ShowHelp)
        {
            PrintUsage();
            return options == null ? 1 : 0;
        }

        if (options.ShowVersion)
        {
            Console.WriteLine(GetVersion());
            return 0;
        }

        var root = options.Args.TryGetValue("out", out var outDir)
            ? Path.GetFullPath(outDir)
            : Directory.GetCurrentDirectory();

        var summary = new List<string>();
        var warnings = new List<string>();

        try
        {
            if (RequiresOut(options.Command) && !options.Args.ContainsKey("out"))
            {
                Console.Error.WriteLine("ERROR: --out <dir> is required for this command.");
                return 1;
            }
            if (RequiresOut(options.Command) && !ValidateOut(root, options))
            {
                return 2;
            }

            Console.WriteLine($"MaelstromToolkit {GetVersion()} | command={options.Command} {options.Subcommand}".Trim());

            switch (options.Command)
            {
                case "init":
                    RunInit(root, options, summary, warnings);
                    break;
                case "policy" when options.Subcommand == "init":
                    CopyTemplate(root, "POLICY_BOUNDARY.md", options, summary, warnings);
                    CopyTemplate(root, "policy.config.sample", options, summary, warnings);
                    break;
                case "policy" when options.Subcommand == "validate":
                    return RunPolicyValidate(root, options);
                case "policy" when options.Subcommand == "effective":
                    return RunPolicyEffective(root, options);
                case "policy" when options.Subcommand == "watch":
                    return RunPolicyWatch(root, options);
                case "tags" when options.Subcommand == "init":
                    CopyTemplate(root, "TAG_POLICY.md", options, summary, warnings);
                    break;
                case "stewardship" when options.Subcommand == "init":
                    CopyTemplate(root, "STEWARDSHIP_CHECKLIST.md", options, summary, warnings);
                    CopyTemplate(root, "FEEDBACK_LOG.md", options, summary, warnings);
                    break;
                case "packs" when options.Subcommand == "list":
                    return RunPacksList(root, options);
                case "packs" when options.Subcommand == "validate":
                    return RunPacksValidate(root, options);
                case "ai" when options.Subcommand == "status":
                    return RunAiStatus(root, options);
                case "catalog" when options.Subcommand == "export":
                    return RunCatalogExport(root, options);
                case "ux" when options.Subcommand == "init":
                    var framework = options.Args.TryGetValue("framework", out var fw) ? fw : "winforms";
                    CopyTemplate(root, "UX_MAINTENANCE.md", options, summary, warnings);
                    CopyTemplate(root, "UX_STYLE_GUIDE.md", options, summary, warnings, framework);
                    CopyTemplate(root, "UX_CHANGELOG.md", options, summary, warnings, framework);
                    CopyTemplate(root, "UX_TOKENS.md", options, summary, warnings, framework);
                    break;
                case "ci" when options.Subcommand == "add":
                    var provider = options.Args.TryGetValue("provider", out var p) ? p : "github";
                    var profile = options.Args.TryGetValue("profile", out var pr) ? pr : "tools-only";
                    CopyTemplate(root, $"{provider}_{profile}_workflow.yml", options, summary, warnings);
                    break;
                case "handoff" when options.Subcommand == "generate":
                    return RunHandoffGenerate(root, options);
                case "handoff":
                    CopyTemplate(root, "README.md", options, summary, warnings);
                    break;
                case "selftest":
                    return RunSelftest(options, summary, warnings);
                default:
                    PrintUsage();
                    return 1;
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"ERROR: {ex.Message}");
            return 1;
        }

        if (summary.Count > 0)
        {
            Console.WriteLine("Generated:");
            foreach (var line in summary) Console.WriteLine($"- {line}");
        }
        if (warnings.Count > 0)
        {
            Console.WriteLine("Warnings:");
            foreach (var line in warnings) Console.WriteLine($"- {line}");
        }

        return 0;
    }

    private static CommandOptions? Parse(string[] args)
    {
        if (args.Length == 0) return null;
        var showHelp = args.Contains("--help", StringComparer.OrdinalIgnoreCase);
        var showVersion = args.Contains("--version", StringComparer.OrdinalIgnoreCase);
        var dict = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var positional = new List<string>();
        var force = args.Contains("--force", StringComparer.OrdinalIgnoreCase);
        var dryRun = args.Contains("--dry-run", StringComparer.OrdinalIgnoreCase);
        var verbose = args.Contains("--verbose", StringComparer.OrdinalIgnoreCase);

        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            if (arg.StartsWith("--", StringComparison.Ordinal))
            {
                var key = arg[2..];
                if (key is "force" or "dry-run" or "verbose" or "help" or "version") continue;
                if (i + 1 < args.Length && !args[i + 1].StartsWith("--", StringComparison.Ordinal))
                {
                    dict[key] = args[i + 1];
                }
                continue;
            }
            positional.Add(arg);
        }

        if (positional.Count == 0) return null;
        string command = positional[0];
        string sub = positional.Count > 1 ? positional[1] : string.Empty;
        if (command.Equals("aas", StringComparison.OrdinalIgnoreCase) && positional.Count > 1)
        {
            command = positional[1];
            sub = positional.Count > 2 ? positional[2] : string.Empty;
        }

        return new CommandOptions(command, sub, dict, force, dryRun, verbose, showHelp, showVersion);
    }

    private static void PrintUsage()
    {
        Console.WriteLine("MaelstromToolkit (net8.0) - safe, deterministic scaffolds");
        Console.WriteLine("Usage (examples):");
        Console.WriteLine("  maelstromtoolkit init --out ./out");
        Console.WriteLine("  maelstromtoolkit policy init --out ./out");
        Console.WriteLine("  maelstromtoolkit policy validate --out ./out [--file ./aas.policy.txt]");
        Console.WriteLine("  maelstromtoolkit policy effective --out ./out [--file ./aas.policy.txt] [--pack default] [--scenario id]");
        Console.WriteLine("  maelstromtoolkit policy watch --out ./out [--file ./aas.policy.txt]");
        Console.WriteLine("  maelstromtoolkit packs list --root ./packs --out ./out");
        Console.WriteLine("  maelstromtoolkit packs validate --root ./packs --out ./out");
        Console.WriteLine("  maelstromtoolkit ai status --out ./out [--file ./aas.policy.txt]");
        Console.WriteLine("  maelstromtoolkit catalog export --packs ./packs --out ./out [--file ./aas.policy.txt]");
        Console.WriteLine("  maelstromtoolkit tags init --out ./out");
        Console.WriteLine("  maelstromtoolkit stewardship init --out ./out");
        Console.WriteLine("  maelstromtoolkit ux init --framework winforms --out ./out");
        Console.WriteLine("  maelstromtoolkit ci add --provider github --profile tools-only --out ./out");
        Console.WriteLine("  maelstromtoolkit handoff generate --out ./out");
        Console.WriteLine("  maelstromtoolkit handoff --out ./out");
        Console.WriteLine("  maelstromtoolkit selftest");
        Console.WriteLine("Flags: --force (overwrite), --dry-run, --verbose, --help, --version, --out <dir>");
    }

    private static void RunInit(string root, CommandOptions options, List<string> summary, List<string> warnings)
    {
        CopyTemplate(root, "POLICY_BOUNDARY.md", options, summary, warnings);
        CopyTemplate(root, "policy.config.sample", options, summary, warnings);
        CopyTemplate(root, "TAG_POLICY.md", options, summary, warnings);
        CopyTemplate(root, "STEWARDSHIP_CHECKLIST.md", options, summary, warnings);
        CopyTemplate(root, "FEEDBACK_LOG.md", options, summary, warnings);
        CopyTemplate(root, "UX_MAINTENANCE.md", options, summary, warnings);
    }

    private static void CopyTemplate(string targetRoot, string templateName, CommandOptions options, List<string> summary, List<string> warnings, string? framework = null)
    {
        var source = Path.Combine(AppContext.BaseDirectory, "Templates", templateFolderFor(templateName), templateName);
        if (!File.Exists(source))
        {
            warnings.Add($"Template missing: {templateName}");
            return;
        }
        var content = File.ReadAllText(source);
        if (!string.IsNullOrWhiteSpace(framework))
        {
            content = content.Replace("{{FRAMEWORK}}", framework, StringComparison.OrdinalIgnoreCase);
        }
        var dest = Path.Combine(targetRoot, templateName);
        if (File.Exists(dest) && !options.Force)
        {
            warnings.Add($"Skipped existing file: {dest}");
            return;
        }
        WriteFile(dest, content, options, summary, File.Exists(dest));
    }

    private static int RunSelftest(CommandOptions options, List<string> summary, List<string> warnings)
    {
        var templates = new[]
        {
            ("Policy","POLICY_BOUNDARY.md"),
            ("Policy","policy.config.sample"),
            ("Tags","TAG_POLICY.md"),
            ("Stewardship","STEWARDSHIP_CHECKLIST.md"),
            ("Stewardship","FEEDBACK_LOG.md"),
            ("UX","UX_MAINTENANCE.md"),
            ("UX","UX_STYLE_GUIDE.md"),
            ("UX","UX_CHANGELOG.md"),
            ("UX","UX_TOKENS.md"),
            ("CI","github_tools-only_workflow.yml"),
            ("Handoff","README.md"),
        };

        var schemaVersion = Path.Combine(AppContext.BaseDirectory, "Templates", "schema_version.txt");
        var manifest = Path.Combine(AppContext.BaseDirectory, "Templates", "manifest.json");
        if (!File.Exists(schemaVersion))
        {
            Console.Error.WriteLine("SELFTEST FAIL: missing schema_version.txt");
            return 1;
        }
        if (!File.Exists(manifest))
        {
            Console.Error.WriteLine("SELFTEST FAIL: missing manifest.json");
            return 1;
        }

        foreach (var (folder, name) in templates)
        {
            var path = Path.Combine(AppContext.BaseDirectory, "Templates", folder, name);
            if (!File.Exists(path))
            {
                Console.Error.WriteLine($"SELFTEST FAIL: missing template {folder}/{name}");
                return 1;
            }
        }

        var tempDir = Path.Combine(Path.GetTempPath(), $"maelstromtoolkit_selftest_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var testOptions = options with { Force = false };
        CopyTemplate(tempDir, "POLICY_BOUNDARY.md", testOptions, summary, warnings);
        CopyTemplate(tempDir, "policy.config.sample", testOptions, summary, warnings);
        CopyTemplate(tempDir, "TAG_POLICY.md", testOptions, summary, warnings);
        CopyTemplate(tempDir, "STEWARDSHIP_CHECKLIST.md", testOptions, summary, warnings);
        CopyTemplate(tempDir, "FEEDBACK_LOG.md", testOptions, summary, warnings);
        CopyTemplate(tempDir, "UX_MAINTENANCE.md", testOptions, summary, warnings, "winforms");
        CopyTemplate(tempDir, "UX_STYLE_GUIDE.md", testOptions, summary, warnings, "winforms");
        CopyTemplate(tempDir, "UX_CHANGELOG.md", testOptions, summary, warnings, "winforms");
        CopyTemplate(tempDir, "UX_TOKENS.md", testOptions, summary, warnings, "winforms");
        CopyTemplate(tempDir, "github_tools-only_workflow.yml", testOptions, summary, warnings);
        CopyTemplate(tempDir, "README.md", testOptions, summary, warnings);

        try { Directory.Delete(tempDir, true); } catch { /* ignore */ }

        Console.WriteLine("SELFTEST PASS");
        return 0;
    }

    private static int RunPolicyValidate(string root, CommandOptions options)
    {
        var (policyPath, outRoot) = GetPolicyPaths(root, options);
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain the segment \"--out\" (case-insensitive). No files written.");
            return 1;
        }

        Directory.CreateDirectory(Path.Combine(outRoot, "system"));

        var parserFacade = new PolicyTxtParserFacade();
        var validator = new PolicyValidator();
        var diagnostics = new List<PolicyDiagnostic>();
        string policyText = string.Empty;

        if (!File.Exists(policyPath))
        {
            diagnostics.Add(new PolicyDiagnostic("AASPOL001", DiagnosticSeverity.Error, "file", "missing", null, $"File not found: {policyPath}"));
        }
        else
        {
            policyText = File.ReadAllText(policyPath);
        }

        PolicySnapshot? snapshot = null;
        if (!string.IsNullOrEmpty(policyText) || diagnostics.Count == 0)
        {
            var parsed = parserFacade.Parse(policyText);
            diagnostics.AddRange(parsed.Diagnostics);
            if (parsed.Snapshot != null)
            {
                var validation = validator.Validate(parsed.Snapshot);
                diagnostics.AddRange(validation.Diagnostics);
                snapshot = parsed.Snapshot;
            }
        }

        var ordered = diagnostics
            .OrderBy(d => d.Code, StringComparer.Ordinal)
            .ThenBy(d => d.Section, StringComparer.Ordinal)
            .ThenBy(d => d.Key, StringComparer.Ordinal)
            .ThenBy(d => d.LineNumber ?? int.MaxValue)
            .ThenBy(d => d.Message, StringComparer.Ordinal)
            .ToList();

        var hasErrors = ordered.Any(d => d.Severity == DiagnosticSeverity.Error) || snapshot == null;
        var hash = string.IsNullOrEmpty(policyText) ? "none" : ComputeSha256(policyText);
        var activeProfile = snapshot?.Global.ActiveProfile ?? "unknown";

        var mode = "UNKNOWN";
        var liveStatus = "N/A";
        PolicyValidationResult? validationResult = null;
        if (snapshot != null)
        {
            validationResult = validator.Validate(snapshot);
            mode = validationResult.OperatingMode;
            liveStatus = validationResult.LiveStatus;
        }

        WriteValidateFile(outRoot, policyPath, hash, activeProfile, mode, liveStatus, ordered, !hasErrors);

        if (!hasErrors)
        {
            if (validationResult == null || validationResult.Snapshot == null)
            {
                Console.Error.WriteLine("ERROR: Validation unexpectedly missing snapshot.");
                return 1;
            }
            var prevLkgPath = Path.Combine(outRoot, "system", "policy.lkg.txt");
            var prevHashPath = Path.Combine(outRoot, "system", "policy.lkg.sha256");
            var prevText = File.Exists(prevLkgPath) ? File.ReadAllText(prevLkgPath) : null;
            var prevHash = File.Exists(prevHashPath) ? File.ReadAllText(prevHashPath) : "none";
            WriteAtomic(Path.Combine(outRoot, "system", "policy.lkg.txt"), policyText);
            WriteAtomic(Path.Combine(outRoot, "system", "policy.lkg.sha256"), hash);
            var effectiveResult = new PolicyEffectiveResult(
                Source: "FILE",
                Hash: hash,
                Snapshot: validationResult!.Snapshot!,
                ActiveProfile: validationResult.Snapshot.Global.ActiveProfile,
                ProfileMode: validationResult.Snapshot.Profiles.TryGetValue(validationResult.Snapshot.Global.ActiveProfile, out var profile) ? profile.Mode.ToUpperInvariant() : "UNKNOWN",
                OperatingMode: validationResult.OperatingMode,
                LiveStatus: validationResult.LiveStatus,
                Reasons: validationResult.Reasons,
                Diagnostics: ordered,
                FileDiagnostics: Array.Empty<PolicyDiagnostic>(),
                LkgDiagnostics: Array.Empty<PolicyDiagnostic>(),
                RawText: NormalizeLineEndings(policyText));
            var recorder = new PolicyApplyRecorder();
            recorder.Record(outRoot, policyPath, effectiveResult, NormalizeLineEndings(policyText), prevText, prevHash);
            Console.WriteLine($"VALID hash={hash} activeProfile={activeProfile} mode={mode} liveStatus={liveStatus} diagCount={ordered.Count}");
            return 0;
        }

        WriteRejected(outRoot, ordered);
        var top5 = string.Join(",", ordered.Take(5).Select(d => d.Code));
        Console.WriteLine($"INVALID hash={hash} activeProfile={activeProfile} mode={mode} liveStatus={liveStatus} diagCount={ordered.Count} top5={top5}");
        return 1;
    }

    private static int RunPolicyEffective(string root, CommandOptions options)
    {
        var format = options.Args.TryGetValue("format", out var fmt) ? fmt.ToLowerInvariant() : "text";
        if (format is not ("text" or "json"))
        {
            Console.Error.WriteLine("ERROR: --format must be text|json");
            return 1;
        }

        var (policyPath, outRoot) = GetPolicyPaths(root, options);
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var fileText = File.Exists(policyPath) ? File.ReadAllText(policyPath) : string.Empty;
        var lkgPath = Path.Combine(outRoot, "system", "policy.lkg.txt");
        var lkgText = File.Exists(lkgPath) ? File.ReadAllText(lkgPath) : null;

        var resolver = new PolicyEffectiveResolver(DefaultPolicyText);
        var effective = resolver.Resolve(fileText, lkgText);

        var fileTop = effective.FileDiagnostics.Select(d => d.Code).Distinct().Take(5).ToList();
        var lkgTop = effective.LkgDiagnostics.Select(d => d.Code).Distinct().Take(3).ToList();
        var reasons = effective.Reasons.Count > 0 ? string.Join(",", effective.Reasons) : "none";
        var fileTopCodes = fileTop.Count > 0 ? string.Join(",", fileTop) : "none";
        var lkgTopCodes = lkgTop.Count > 0 ? string.Join(",", lkgTop) : "none";

        Console.WriteLine($"Source={effective.Source} hash={effective.Hash} activeProfile={effective.ActiveProfile} profileMode={effective.ProfileMode} operatingMode={effective.OperatingMode} liveStatus={effective.LiveStatus} reasons={reasons} diagCount={effective.Diagnostics.Count} fileTop={fileTopCodes} lkgTop={lkgTopCodes}");

        WriteEffectiveText(outRoot, policyPath, effective, fileTopCodes, lkgTopCodes);
        if (format == "json")
        {
            WriteEffectiveJson(outRoot, policyPath, effective, fileTop, lkgTop);
        }

        return 0;
    }

    private static int RunPolicyWatch(string root, CommandOptions options)
    {
        var (policyPath, outRoot) = GetPolicyPaths(root, options);
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var runner = new PolicyWatchRunner(policyPath, outRoot, DefaultPolicyText);
        Console.WriteLine($"Watching {policyPath} (Ctrl+C to stop)...");
        return runner.Run();
    }

    private static (string policyPath, string outRoot) GetPolicyPaths(string root, CommandOptions options)
    {
        var policyPath = options.Args.TryGetValue("file", out var path)
            ? Path.GetFullPath(path)
            : Path.Combine(Directory.GetCurrentDirectory(), "aas.policy.txt");
        var outRoot = options.Args.TryGetValue("out", out var o) ? Path.GetFullPath(o) : root;
        return (policyPath, outRoot);
    }

    private static void WriteFile(string path, string content, CommandOptions options, List<string> summary, bool existed)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var utf8 = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false);
        var tmp = path + ".tmp";
        File.WriteAllText(tmp, NormalizeLineEndings(content), utf8);
        if (options.DryRun)
        {
            File.Delete(tmp);
            summary.Add($"(dry-run) {(existed ? "would overwrite" : "would create")} {path}");
            return;
        }
        File.Move(tmp, path, overwrite: true);
        summary.Add(path);
        if (options.Verbose)
        {
            Console.WriteLine($"Wrote {path}");
        }
    }

    private static string NormalizeLineEndings(string input) =>
        input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\r", "\n", StringComparison.Ordinal);

    private static string GetVersion() =>
        Assembly.GetExecutingAssembly().GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion ?? "unknown";

    private static bool OutIsSafe(string outRoot) =>
        outRoot.IndexOf("--out", StringComparison.OrdinalIgnoreCase) >= 0;

    private static int RunPacksList(string root, CommandOptions options)
    {
        var packsRoot = options.Args.TryGetValue("root", out var r) ? Path.GetFullPath(r) : Path.Combine(Directory.GetCurrentDirectory(), "packs");
        var outRoot = options.Args.TryGetValue("out", out var o) ? Path.GetFullPath(o) : Path.Combine(Directory.GetCurrentDirectory(), "--out");
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var service = new PackService();
        var list = service.ListPacks(packsRoot);

        foreach (var p in list.Packs)
        {
            Console.WriteLine($"{p.Id} | {p.Name} | {p.Version} | scenarios={p.Scenarios.Count}");
        }
        foreach (var d in list.Diagnostics)
        {
            Console.WriteLine($"DIAG {d.Code} {d.Severity} {d.PackId} {d.ScenarioId} {d.Message}");
        }

        var dir = Path.Combine(outRoot, "packs");
        Directory.CreateDirectory(dir);
        var path = Path.Combine(dir, "list.txt");
        var sb = new StringBuilder();
        sb.AppendLine($"Packs: {list.Packs.Count}");
        foreach (var p in list.Packs)
        {
            sb.AppendLine($"{p.Id} | {p.Name} | {p.Version} | scenarios={p.Scenarios.Count}");
        }
        if (list.Diagnostics.Count > 0)
        {
            sb.AppendLine("Diagnostics:");
            foreach (var d in list.Diagnostics)
            {
                sb.AppendLine($"{d.Code} | {d.Severity} | {d.PackId} | {d.ScenarioId} | {d.Message}");
            }
        }
        WriteAtomic(path, sb.ToString());
        return 0;
    }

    private static int RunPacksValidate(string root, CommandOptions options)
    {
        var packsRoot = options.Args.TryGetValue("root", out var r) ? Path.GetFullPath(r) : Path.Combine(Directory.GetCurrentDirectory(), "packs");
        var outRoot = options.Args.TryGetValue("out", out var o) ? Path.GetFullPath(o) : Path.Combine(Directory.GetCurrentDirectory(), "--out");
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var service = new PackService();
        var validation = service.ValidatePacks(packsRoot);
        var dir = Path.Combine(outRoot, "packs");
        Directory.CreateDirectory(dir);
        var path = Path.Combine(dir, "validate.txt");

        var sb = new StringBuilder();
        var status = validation.HasErrors ? "INVALID" : "VALID";
        sb.AppendLine($"{status}");
        sb.AppendLine($"Diagnostics: {validation.Diagnostics.Count}");
        foreach (var d in validation.Diagnostics)
        {
            sb.AppendLine($"{d.Code} | {d.Severity} | {d.PackId} | {d.ScenarioId} | {d.Message}");
        }
        WriteAtomic(path, sb.ToString());

        Console.WriteLine($"{status} diagCount={validation.Diagnostics.Count}");
        return validation.HasErrors ? 1 : 0;
    }

    private static int RunHandoffGenerate(string root, CommandOptions options)
    {
        var outRoot = options.Args.TryGetValue("out", out var o) ? Path.GetFullPath(o) : Path.Combine(root, "--out");
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var prompt = BuildHandoffPrompt(outRoot, new GitInfoProvider());
        var handoffDir = Path.Combine(outRoot, "handoff");
        Directory.CreateDirectory(handoffDir);
        var path = Path.Combine(handoffDir, "HANDOFF_PROMPT_CHATGPT_5_2_PRO.txt");
        WriteAtomic(path, prompt);

        var artifactsCopy = Path.Combine(root, "artifacts", "handoff");
        try
        {
            Directory.CreateDirectory(artifactsCopy);
            File.Copy(path, Path.Combine(artifactsCopy, Path.GetFileName(path)), overwrite: true);
        }
        catch
        {
            // best-effort; no fail
        }

        Console.WriteLine($"Generated handoff prompt at {path}");
        return 0;
    }

    internal static string BuildHandoffPrompt(string outRoot, IGitInfoProvider gitInfo)
    {
        var repo = "Aarogaming/aaroneous-automation-suite";
        var branch = gitInfo.Branch;
        var commit = gitInfo.Commit;
        var dirty = gitInfo.IsDirty ? "true" : "false";
        var sb = new StringBuilder();
        sb.AppendLine("COPYABLE HANDOFF PROMPT FOR CHATGPT 5.2 PRO");
        sb.AppendLine($"Repo: {repo}");
        sb.AppendLine($"Branch: {branch}");
        sb.AppendLine($"Latest commit: {commit}");
        sb.AppendLine($"Dirty: {dirty}");
        sb.AppendLine();
        sb.AppendLine("Constraints:");
        sb.AppendLine("- Tooling/docs only; no ProjectMaelstrom runtime changes.");
        sb.AppendLine("- Single TXT policy (aas.policy.txt); non-bricking with LKG.");
        sb.AppendLine("- LIVE means LIVE (no fallback), safe writes under --out, no new prod deps.");
        sb.AppendLine();
        sb.AppendLine("Continuity docs:");
        sb.AppendLine("- docs/ROADMAP.md");
        sb.AppendLine("- docs/GOALS.md");
        sb.AppendLine("- docs/COOPERATIVE_EVALUATION.md");
        sb.AppendLine("- docs/POLICY_TXT_SPEC.md");
        sb.AppendLine("- docs/HandoffTray.md and COOP_WORKFLOW.md");
        sb.AppendLine();
        sb.AppendLine("Policy outputs:");
        sb.AppendLine("- --out/system/: policy.validate.txt, policy.effective.txt/json, policy.watch.last.txt, policy.lkg.txt/.sha256, policy.rejected.txt");
        sb.AppendLine("- --out/policy/history/<hash>/: policy.txt, policy.sha256, effective.txt, eval.md/json");
        sb.AppendLine();
        sb.AppendLine("How to verify:");
        sb.AppendLine("- dotnet run --project MaelstromToolkit -- aas policy validate --file ./aas.policy.txt --out ./--out");
        sb.AppendLine("- dotnet run --project MaelstromToolkit -- aas policy effective --file ./aas.policy.txt --out ./--out --format json");
        sb.AppendLine("- dotnet run --project MaelstromToolkit -- aas policy watch --file ./aas.policy.txt --out ./--out");
        sb.AppendLine();
        sb.AppendLine("Next tasks:");
        sb.AppendLine("- Packs scaffold + sample pack listing/validation (packs folder).");
        sb.AppendLine("- AI provider scaffold (pluggable, policy-driven).");
        sb.AppendLine();
        sb.AppendLine("Copy this prompt into ChatGPT 5.2 Pro after restart.");
        return sb.ToString();
    }

    private static string BuildCatalogText(string policyPath, PolicyEffectiveResult effective, EvalSummary? evalSummary, PackListResult packs)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Policy");
        sb.AppendLine($"Source: {effective.Source}");
        sb.AppendLine($"File: {policyPath}");
        sb.AppendLine($"Hash: {effective.Hash}");
        sb.AppendLine($"ActiveProfile: {effective.ActiveProfile}");
        sb.AppendLine($"ProfileMode: {effective.ProfileMode}");
        sb.AppendLine($"OperatingMode: {effective.OperatingMode}");
        sb.AppendLine($"LiveStatus: {effective.LiveStatus}");
        sb.AppendLine($"LiveReasons: {(effective.Reasons.Count == 0 ? "none" : string.Join(",", effective.Reasons))}");
        sb.AppendLine($"AI: enabled={(effective.Snapshot?.Ai.Enabled ?? false).ToString().ToLowerInvariant()} provider={effective.Snapshot?.Ai.Provider ?? "none"} model={effective.Snapshot?.Ai.Model ?? string.Empty} reasoningEffort={effective.Snapshot?.Ai.ReasoningEffort ?? string.Empty} temperature={(effective.Snapshot?.Ai.Temperature ?? 0).ToString(CultureInfo.InvariantCulture)} store={(effective.Snapshot?.Ai.Store ?? false).ToString().ToLowerInvariant()} endpoint={effective.Snapshot?.Ai.Endpoint ?? string.Empty} timeoutSeconds={(effective.Snapshot?.Ai.TimeoutSeconds ?? 0)} maxOutputTokens={(effective.Snapshot?.Ai.MaxOutputTokens ?? 0)} userTag={effective.Snapshot?.Ai.UserTag ?? string.Empty}");
        sb.AppendLine($"Ethics: purpose={effective.Snapshot?.Ethics.Purpose ?? string.Empty} requireConsentForEnvironmentControl={(effective.Snapshot?.Ethics.RequireConsentForEnvironmentControl ?? false).ToString().ToLowerInvariant()} prohibit={effective.Snapshot?.Ethics.Prohibit ?? string.Empty} privacy.storeScreenshots={(effective.Snapshot?.Ethics.PrivacyStoreScreenshots ?? false).ToString().ToLowerInvariant()} privacy.storeAudio={(effective.Snapshot?.Ethics.PrivacyStoreAudio ?? false).ToString().ToLowerInvariant()}");
        if (evalSummary != null)
        {
            var changed = evalSummary.ChangedFields.Count == 0 ? "none" : string.Join(",", evalSummary.ChangedFields);
            var notes = evalSummary.Notes.Count == 0 ? "none" : string.Join(",", evalSummary.Notes);
            sb.AppendLine($"Evaluation: riskLevel={evalSummary.RiskLevel} changedFields={changed} notes={notes}");
        }
        else
        {
            sb.AppendLine("Evaluation: none");
        }

        sb.AppendLine();
        sb.AppendLine("Packs");
        foreach (var pack in packs.Packs.OrderBy(p => p.Id, StringComparer.Ordinal))
        {
            foreach (var scen in pack.Scenarios.OrderBy(s => s.Id, StringComparer.Ordinal))
            {
                var caps = scen.RequiredCapabilities != null && scen.RequiredCapabilities.Count > 0
                    ? string.Join(",", scen.RequiredCapabilities.OrderBy(c => c, StringComparer.Ordinal))
                    : "none";
                sb.AppendLine($"{pack.Id} | {scen.Id} | requiredCapabilities={caps}");
            }
        }
        if (packs.Diagnostics.Count > 0)
        {
            sb.AppendLine("Diagnostics:");
            foreach (var d in packs.Diagnostics)
            {
                sb.AppendLine($"{d.Code} | {d.Severity} | {d.PackId} | {d.ScenarioId} | {d.Message}");
            }
        }
        return sb.ToString();
    }

    private static string BuildCatalogJson(string policyPath, PolicyEffectiveResult effective, EvalSummary? evalSummary, PackListResult packs)
    {
        var dto = new
        {
            policy = new
            {
                source = effective.Source,
                file = policyPath,
                hash = effective.Hash,
                activeProfile = effective.ActiveProfile,
                profileMode = effective.ProfileMode,
                operatingMode = effective.OperatingMode,
                liveStatus = effective.LiveStatus,
                liveReasons = effective.Reasons.ToArray(),
                ai = new
                {
                    enabled = effective.Snapshot?.Ai.Enabled ?? false,
                    provider = effective.Snapshot?.Ai.Provider ?? "none",
                    model = effective.Snapshot?.Ai.Model ?? string.Empty,
                    reasoningEffort = effective.Snapshot?.Ai.ReasoningEffort ?? string.Empty,
                    temperature = effective.Snapshot?.Ai.Temperature ?? 0,
                    store = effective.Snapshot?.Ai.Store ?? false,
                    endpoint = effective.Snapshot?.Ai.Endpoint ?? string.Empty,
                    timeoutSeconds = effective.Snapshot?.Ai.TimeoutSeconds ?? 0,
                    maxOutputTokens = effective.Snapshot?.Ai.MaxOutputTokens ?? 0,
                    userTag = effective.Snapshot?.Ai.UserTag ?? string.Empty
                },
                ethics = new
                {
                    purpose = effective.Snapshot?.Ethics.Purpose ?? string.Empty,
                    requireConsentForEnvironmentControl = effective.Snapshot?.Ethics.RequireConsentForEnvironmentControl ?? false,
                    prohibit = effective.Snapshot?.Ethics.Prohibit ?? string.Empty,
                    privacyStoreScreenshots = effective.Snapshot?.Ethics.PrivacyStoreScreenshots ?? false,
                    privacyStoreAudio = effective.Snapshot?.Ethics.PrivacyStoreAudio ?? false
                }
            },
            evaluation = evalSummary == null ? null : new
            {
                riskLevel = evalSummary.RiskLevel,
                changedFields = evalSummary.ChangedFields.ToArray(),
                notes = evalSummary.Notes.ToArray()
            },
            packs = packs.Packs
                .OrderBy(p => p.Id, StringComparer.Ordinal)
                .Select(p => new
                {
                    id = p.Id,
                    name = p.Name,
                    version = p.Version,
                    scenarios = p.Scenarios
                        .OrderBy(s => s.Id, StringComparer.Ordinal)
                        .Select(s => new
                        {
                            id = s.Id,
                            name = s.Name,
                            requiredCapabilities = (s.RequiredCapabilities ?? new List<string>())
                                .OrderBy(c => c, StringComparer.Ordinal)
                                .ToArray()
                        }).ToArray()
                }).ToArray(),
            diagnostics = packs.Diagnostics.ToArray()
        };

        return JsonSerializer.Serialize(dto, new JsonSerializerOptions { WriteIndented = true });
    }

    private static EvalSummary? LoadEvalSummary(string evalPath)
    {
        if (!File.Exists(evalPath)) return null;
        try
        {
            var doc = JsonDocument.Parse(File.ReadAllText(evalPath));
            var root = doc.RootElement;
            var risk = root.TryGetProperty("riskLevel", out var r) ? r.GetString() ?? "unknown" : "unknown";
            var changed = root.TryGetProperty("changedFields", out var cf) && cf.ValueKind == JsonValueKind.Array
                ? cf.EnumerateArray().Select(e => e.GetString() ?? string.Empty).Where(s => !string.IsNullOrWhiteSpace(s)).OrderBy(s => s, StringComparer.Ordinal).ToList()
                : new List<string>();
            var notes = root.TryGetProperty("notes", out var nf) && nf.ValueKind == JsonValueKind.Array
                ? nf.EnumerateArray().Select(e => e.GetString() ?? string.Empty).Where(s => !string.IsNullOrWhiteSpace(s)).OrderBy(s => s, StringComparer.Ordinal).ToList()
                : new List<string>();
            return new EvalSummary(risk, changed, notes);
        }
        catch
        {
            return null;
        }
    }

    private static void WriteValidateFile(string outRoot, string policyPath, string hash, string activeProfile, string mode, string liveStatus, IReadOnlyList<PolicyDiagnostic> diagnostics, bool isValid)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.validate.txt");
        var sb = new StringBuilder();
        sb.AppendLine(isValid ? "VALID" : "INVALID");
        sb.AppendLine($"File: {policyPath}");
        sb.AppendLine($"Hash: {hash}");
        sb.AppendLine($"ActiveProfile: {activeProfile}");
        sb.AppendLine($"OperatingMode: {mode}");
        sb.AppendLine($"LiveStatus: {liveStatus}");
        sb.AppendLine($"Diagnostics: {diagnostics.Count}");
        foreach (var d in diagnostics)
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code} | {d.Severity} | {d.Section}.{d.Key} | {line} | {d.Message}");
        }
        WriteAtomic(path, sb.ToString());
    }

    private static void WriteRejected(string outRoot, IReadOnlyList<PolicyDiagnostic> diagnostics)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.rejected.txt");
        var sb = new StringBuilder();
        foreach (var d in diagnostics)
        {
            var line = d.LineNumber.HasValue ? d.LineNumber.Value.ToString() : "-";
            sb.AppendLine($"{d.Code} | {d.Severity} | {d.Section}.{d.Key} | {line} | {d.Message}");
        }
        WriteAtomic(path, sb.ToString());
    }

    private static void WriteAtomic(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var tmp = path + ".tmp_" + Guid.NewGuid().ToString("N");
        File.WriteAllText(tmp, NormalizeLineEndings(content), new UTF8Encoding(false));
        File.Move(tmp, path, overwrite: true);
    }

    private static void WriteEffectiveText(string outRoot, string policyPath, PolicyEffectiveResult effective, string fileTopCodes, string lkgTopCodes)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var path = Path.Combine(systemDir, "policy.effective.txt");
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
        sb.AppendLine($"FileDiagnosticsTop: {fileTopCodes}");
        sb.AppendLine($"LkgDiagnosticsTop: {lkgTopCodes}");
        WriteAtomic(path, sb.ToString());
    }

    private static void WriteEffectiveJson(string outRoot, string policyPath, PolicyEffectiveResult effective, IReadOnlyList<string> fileTop, IReadOnlyList<string> lkgTop)
    {
        var systemDir = Path.Combine(outRoot, "system");
        Directory.CreateDirectory(systemDir);
        var dto = new
        {
            source = effective.Source,
            file = policyPath,
            hash = effective.Hash,
            activeProfile = effective.ActiveProfile,
            profileMode = effective.ProfileMode,
            operatingMode = effective.OperatingMode,
            liveStatus = effective.LiveStatus,
            liveReasons = effective.Reasons.ToArray(),
            ai = new
            {
                enabled = effective.Snapshot?.Ai.Enabled ?? false,
                provider = effective.Snapshot?.Ai.Provider ?? "none",
                model = effective.Snapshot?.Ai.Model ?? string.Empty,
                temperature = effective.Snapshot?.Ai.Temperature ?? 0,
                apiKeyEnv = effective.Snapshot?.Ai.ApiKeyEnv ?? string.Empty,
                allowSendScreenshotsToModel = effective.Snapshot?.Ai.AllowSendScreenshotsToModel ?? false,
                allowSendAudioToModel = effective.Snapshot?.Ai.AllowSendAudioToModel ?? false
            },
            ethics = new
            {
                purpose = effective.Snapshot?.Ethics.Purpose ?? string.Empty,
                requireConsentForEnvironmentControl = effective.Snapshot?.Ethics.RequireConsentForEnvironmentControl ?? false,
                prohibit = effective.Snapshot?.Ethics.Prohibit ?? string.Empty,
                privacyStoreScreenshots = effective.Snapshot?.Ethics.PrivacyStoreScreenshots ?? false,
                privacyStoreAudio = effective.Snapshot?.Ethics.PrivacyStoreAudio ?? false
            },
            diagnostics = effective.Diagnostics.Select(d => new
            {
                code = d.Code,
                severity = d.Severity.ToString(),
                section = d.Section,
                key = d.Key,
                line = d.LineNumber,
                message = d.Message
            }).ToArray(),
            fileDiagnosticsTop = fileTop.ToArray(),
            lkgDiagnosticsTop = lkgTop.ToArray()
        };

        var json = JsonSerializer.Serialize(dto, new JsonSerializerOptions
        {
            WriteIndented = true
        });
        var path = Path.Combine(systemDir, "policy.effective.json");
        WriteAtomic(path, json);
    }

    private static int RunAiStatus(string root, CommandOptions options)
    {
        var (policyPath, outRoot) = GetPolicyPaths(root, options);
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var fileText = File.Exists(policyPath) ? File.ReadAllText(policyPath) : string.Empty;
        var lkgPath = Path.Combine(outRoot, "system", "policy.lkg.txt");
        var lkgText = File.Exists(lkgPath) ? File.ReadAllText(lkgPath) : null;
        var resolver = new PolicyEffectiveResolver(DefaultPolicyText);
        var effective = resolver.Resolve(fileText, lkgText);
        var ai = effective.Snapshot?.Ai ?? new AiSettings();

        var reasons = new List<string>();
        if (!ai.Enabled) reasons.Add("AASAI001");
        var provider = ai.Provider ?? "none";
        if (provider.Equals("none", StringComparison.OrdinalIgnoreCase)) reasons.Add("AASAI005");
        if (provider.Equals("openai", StringComparison.OrdinalIgnoreCase))
        {
            if (string.IsNullOrWhiteSpace(ai.ApiKeyEnv)) reasons.Add("AASAI002");
            var present = !string.IsNullOrWhiteSpace(ai.ApiKeyEnv) && !string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable(ai.ApiKeyEnv));
            if (!present) reasons.Add("AASAI003");
        }
        if (provider.Equals("http", StringComparison.OrdinalIgnoreCase))
        {
            if (string.IsNullOrWhiteSpace(ai.Endpoint)) reasons.Add("AASAI004");
        }

        var configValid = reasons.Count == 0;
        reasons = reasons.OrderBy(r => r, StringComparer.Ordinal).ToList();
        var apiPresent = !string.IsNullOrWhiteSpace(ai.ApiKeyEnv) && !string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable(ai.ApiKeyEnv));

        var aiDir = Path.Combine(outRoot, "ai");
        Directory.CreateDirectory(aiDir);
        var statusText = new StringBuilder();
        statusText.AppendLine($"provider={provider}");
        statusText.AppendLine($"enabled={ai.Enabled.ToString().ToLowerInvariant()}");
        statusText.AppendLine($"model={ai.Model}");
        statusText.AppendLine($"reasoningEffort={ai.ReasoningEffort}");
        statusText.AppendLine($"temperature={ai.Temperature.ToString(CultureInfo.InvariantCulture)}");
        statusText.AppendLine($"store={ai.Store.ToString().ToLowerInvariant()}");
        statusText.AppendLine($"apiKeyEnv={ai.ApiKeyEnv}");
        statusText.AppendLine($"apiKeyPresent={apiPresent.ToString().ToLowerInvariant()}");
        statusText.AppendLine($"endpoint={ai.Endpoint ?? string.Empty}");
        statusText.AppendLine($"timeoutSeconds={ai.TimeoutSeconds}");
        statusText.AppendLine($"maxOutputTokens={ai.MaxOutputTokens}");
        statusText.AppendLine($"userTag={ai.UserTag ?? string.Empty}");
        statusText.AppendLine($"configValidForProvider={configValid.ToString().ToLowerInvariant()}");
        statusText.AppendLine($"reasons={(reasons.Count == 0 ? "none" : string.Join(",", reasons))}");
        WriteAtomic(Path.Combine(aiDir, "status.txt"), statusText.ToString());

        var statusJson = new
        {
            provider,
            enabled = ai.Enabled,
            model = ai.Model,
            reasoningEffort = ai.ReasoningEffort,
            temperature = ai.Temperature,
            store = ai.Store,
            apiKeyEnv = ai.ApiKeyEnv,
            apiKeyPresent = apiPresent,
            endpoint = ai.Endpoint,
            timeoutSeconds = ai.TimeoutSeconds,
            maxOutputTokens = ai.MaxOutputTokens,
            userTag = ai.UserTag,
            configValidForProvider = configValid,
            reasons = reasons.ToArray()
        };
        var json = JsonSerializer.Serialize(statusJson, new JsonSerializerOptions { WriteIndented = true });
        WriteAtomic(Path.Combine(aiDir, "status.json"), json);

        Console.WriteLine($"AI status: provider={provider} enabled={ai.Enabled.ToString().ToLowerInvariant()} configValid={configValid.ToString().ToLowerInvariant()} reasons={(reasons.Count == 0 ? "none" : string.Join(",", reasons))}");
        return configValid ? 0 : 1;
    }

    private static int RunCatalogExport(string root, CommandOptions options)
    {
        var packsRoot = options.Args.TryGetValue("packs", out var r) ? Path.GetFullPath(r) : Path.Combine(Directory.GetCurrentDirectory(), "packs");
        var (policyPath, outRoot) = GetPolicyPaths(root, options);
        if (!OutIsSafe(outRoot))
        {
            Console.Error.WriteLine("ERROR: --out must contain \"--out\" segment (safety guard).");
            return 1;
        }

        var fileText = File.Exists(policyPath) ? File.ReadAllText(policyPath) : string.Empty;
        var lkgPath = Path.Combine(outRoot, "system", "policy.lkg.txt");
        var lkgText = File.Exists(lkgPath) ? File.ReadAllText(lkgPath) : null;
        var resolver = new PolicyEffectiveResolver(DefaultPolicyText);
        var effective = resolver.Resolve(fileText, lkgText);

        var evalPath = Path.Combine(outRoot, "policy", "history", effective.Hash, "eval.json");
        var evalSummary = LoadEvalSummary(evalPath);

        var packService = new PackService();
        var packs = packService.ListPacks(packsRoot);

        var catalogDir = Path.Combine(outRoot, "catalog");
        Directory.CreateDirectory(catalogDir);
        WriteAtomic(Path.Combine(catalogDir, "catalog.txt"), BuildCatalogText(policyPath, effective, evalSummary, packs));
        WriteAtomic(Path.Combine(catalogDir, "catalog.json"), BuildCatalogJson(policyPath, effective, evalSummary, packs));

        Console.WriteLine($"Catalog export written to {catalogDir}");
        return 0;
    }

    private static string ComputeSha256(string text)
    {
        using var sha = SHA256.Create();
        var bytes = Encoding.UTF8.GetBytes(NormalizeLineEndings(text));
        var hash = sha.ComputeHash(bytes);
        return BitConverter.ToString(hash).Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string templateFolderFor(string templateName)
    {
        if (templateName.EndsWith(".yml", StringComparison.OrdinalIgnoreCase)) return "CI";
        if (templateName.Contains("POLICY", StringComparison.OrdinalIgnoreCase) || templateName.Contains("policy", StringComparison.OrdinalIgnoreCase)) return "Policy";
        if (templateName.Contains("TAG", StringComparison.OrdinalIgnoreCase)) return "Tags";
        if (templateName.Contains("FEEDBACK", StringComparison.OrdinalIgnoreCase) || templateName.Contains("STEWARDSHIP", StringComparison.OrdinalIgnoreCase)) return "Stewardship";
        if (templateName.StartsWith("UX_", StringComparison.OrdinalIgnoreCase) || templateName.StartsWith("UX ", StringComparison.OrdinalIgnoreCase) || templateName.Contains("UX", StringComparison.OrdinalIgnoreCase)) return "UX";
        if (templateName.Equals("README.md", StringComparison.OrdinalIgnoreCase)) return "Handoff";
        return string.Empty;
    }

    private static bool RequiresOut(string command) =>
        command is "init" or "policy" or "tags" or "stewardship" or "ux" or "ci" or "handoff" or "packs" or "ai" or "catalog";

    private static bool ValidateOut(string outPath, CommandOptions options)
    {
        var full = Path.GetFullPath(outPath);
        var root = Path.GetPathRoot(full);
        if (string.Equals(full.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                root?.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase))
        {
            Console.Error.WriteLine("ERROR: --out cannot be a filesystem root.");
            return false;
        }
        if (IsSymlink(full))
        {
            Console.Error.WriteLine("ERROR: --out cannot be a symlinked directory.");
            return false;
        }
        if (options.Verbose)
        {
            Console.WriteLine($"Using output directory: {full}");
        }
        return true;
    }

    private static bool IsSymlink(string path)
    {
        var dirInfo = new DirectoryInfo(path);
        if (!dirInfo.Exists) return false;
        return dirInfo.Attributes.HasFlag(FileAttributes.ReparsePoint);
    }
}
