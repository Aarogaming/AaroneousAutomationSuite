using System.IO.Compression;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace HandoffUtility;

internal static class Program
{
        private const string Redacted = "REDACTED_SECRET";

        [STAThread]
        private static int Main(string[] args)
        {
            try
        {
            var options = ParseArgs(args);
            var inputText = ReadInput(options);

            var (redactedText, secretHits) = RedactSecrets(inputText, options.AllowSecrets);
            if (secretHits.Count > 0 && !options.AllowSecrets)
            {
                Console.WriteLine($"[WARN] Redacted {secretHits.Sum(kvp => kvp.Value)} potential secrets.");
            }
            else if (secretHits.Count > 0)
            {
                Console.WriteLine($"[WARN] Detected potential secrets but left unredacted (--allow-secrets).");
            }

            // Normalize line endings and trim trailing whitespace
            redactedText = NormalizeText(redactedText);

            // Enforce single code block
            var codeBlockCount = CountCodeFences(redactedText);
            if (codeBlockCount > 2 || codeBlockCount == 1)
            {
                Console.Error.WriteLine("[ERROR] Input contains an invalid number of code fences. Expected 0 or exactly 2 (single block).");
                return 1;
            }

            string nextPrompt;
            if (codeBlockCount == 2)
            {
                nextPrompt = ExtractSingleCodeBlock(redactedText);
            }
            else
            {
                nextPrompt = redactedText.Trim();
            }

            if (string.IsNullOrWhiteSpace(nextPrompt))
            {
                Console.Error.WriteLine("[ERROR] No content available for Next Codex prompt.");
                return 1;
            }

            string handoff;
            if (options.PromptOnly)
            {
                handoff = BuildPromptOnly(nextPrompt);
                Console.WriteLine(handoff);
                if (!string.IsNullOrWhiteSpace(options.OutputPath))
                {
                    File.WriteAllText(options.OutputPath!, handoff, Encoding.UTF8);
                    Console.WriteLine($"[INFO] Wrote prompt-only output to {options.OutputPath}");
                }
                else
                {
                    Console.WriteLine("[INFO] Prompt-only mode; no file written (use --out <path> to save).");
                }

                if (options.Zip && !string.IsNullOrWhiteSpace(options.OutputPath))
                {
                    var zipPath = Path.Combine(Path.GetDirectoryName(options.OutputPath!) ?? ".", "handoff_pack.zip");
                    if (File.Exists(zipPath)) File.Delete(zipPath);
                    using var archive = ZipFile.Open(zipPath, ZipArchiveMode.Create);
                    archive.CreateEntryFromFile(options.OutputPath!, "HANDOFF.md");
                    Console.WriteLine($"[INFO] Created {zipPath}");
                }

                if (options.Clipboard)
                {
                    Clipboard.SetText(handoff);
                    Console.WriteLine("[INFO] Copied prompt-only output to clipboard.");
                }

                return 0;
            }
            else
            {
                var contextSummary = BuildContextSummary(redactedText, lines: 8);
                var filesTouched = ExtractFilesTouched(redactedText);
                handoff = BuildHandoffMarkdown(contextSummary, filesTouched, nextPrompt);
            }

            var outputPathFinal = string.IsNullOrWhiteSpace(options.OutputPath) ? "HANDOFF.md" : options.OutputPath!;
            File.WriteAllText(outputPathFinal, handoff, Encoding.UTF8);
            Console.WriteLine($"[INFO] Wrote HANDOFF.md to {outputPathFinal}");

            if (options.Zip)
            {
                var zipPath = Path.Combine(Path.GetDirectoryName(outputPathFinal) ?? ".", "handoff_pack.zip");
                if (File.Exists(zipPath)) File.Delete(zipPath);
                using var archive = ZipFile.Open(zipPath, ZipArchiveMode.Create);
                archive.CreateEntryFromFile(outputPathFinal, "HANDOFF.md");
                Console.WriteLine($"[INFO] Created {zipPath}");
            }

            if (options.Clipboard)
            {
                Clipboard.SetText(handoff);
                Console.WriteLine("[INFO] Copied HANDOFF.md contents to clipboard.");
            }

            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[ERROR] {ex.Message}");
            return 1;
        }
    }

    private static (string redacted, Dictionary<string, int> hits) RedactSecrets(string input, bool allow)
    {
        var patterns = new Dictionary<string, string>
        {
            { "GITHUB_TOKEN", @"ghp_[A-Za-z0-9]+" },
            { "GOOGLE_API_KEY", @"AIza[0-9A-Za-z\-_]{20,}" },
            { "PRIVATE_KEY", @"-----BEGIN PRIVATE KEY-----.+?-----END PRIVATE KEY-----" }
        };

        var hits = new Dictionary<string, int>();
        var text = input;

        foreach (var kvp in patterns)
        {
            var regex = new Regex(kvp.Value, RegexOptions.IgnoreCase | RegexOptions.Singleline);
            var count = regex.Matches(text).Count;
            if (count > 0)
            {
                hits[kvp.Key] = count;
                if (!allow)
                {
                    text = regex.Replace(text, Redacted);
                }
            }
        }

        return (text, hits);
    }

    private static string NormalizeText(string text)
    {
        var normalized = text.Replace("\r\n", "\n").Replace("\r", "\n");
        var lines = normalized.Split('\n').Select(l => l.TrimEnd());
        return string.Join("\n", lines).Trim();
    }

    private static int CountCodeFences(string text)
    {
        return Regex.Matches(text, "^```", RegexOptions.Multiline).Count;
    }

    private static string ExtractSingleCodeBlock(string text)
    {
        var match = Regex.Match(text, "^```[^\n]*\n(.*?)\n```", RegexOptions.Singleline | RegexOptions.Multiline);
        if (!match.Success) return string.Empty;
        return match.Groups[1].Value.Trim();
    }

    private static string BuildContextSummary(string text, int lines)
    {
        var summaryLines = text.Split('\n')
            .Select(l => l.Trim())
            .Where(l => !string.IsNullOrWhiteSpace(l))
            .Take(lines)
            .ToArray();
        return summaryLines.Length == 0 ? "N/A" : string.Join("\n", summaryLines);
    }

    private static List<string> ExtractFilesTouched(string text)
    {
        var lines = text.Split('\n');
        var list = new List<string>();
        var startIndex = -1;
        for (int i = 0; i < lines.Length; i++)
        {
            if (Regex.IsMatch(lines[i], @"^\s*Files touched", RegexOptions.IgnoreCase))
            {
                startIndex = i + 1;
                break;
            }
        }

        if (startIndex == -1) return list;

        for (int i = startIndex; i < lines.Length; i++)
        {
            var line = lines[i];
            if (string.IsNullOrWhiteSpace(line)) break;
            if (Regex.IsMatch(line, @"^\s*[-*•]\s*(.+)$"))
            {
                var m = Regex.Match(line, @"^\s*[-*•]\s*(.+)$");
                list.Add(m.Groups[1].Value.Trim());
            }
            else if (Regex.IsMatch(line, @"^\s*\S"))
            {
                // tolerate plain lines if not bullet
                list.Add(line.Trim());
            }
            else
            {
                break;
            }
        }

        return list;
    }

    private static string BuildHandoffMarkdown(string context, List<string> filesTouched, string nextPrompt)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# Handoff");
        sb.AppendLine();
        sb.AppendLine("## Context summary");
        sb.AppendLine(context);
        sb.AppendLine();
        sb.AppendLine("## Files touched");
        if (filesTouched.Count == 0)
        {
            sb.AppendLine("- None noted");
        }
        else
        {
            foreach (var f in filesTouched) sb.AppendLine($"- {f}");
        }
        sb.AppendLine();
        sb.AppendLine("## Next Codex prompt");
        sb.AppendLine("```");
        sb.AppendLine(nextPrompt);
        sb.AppendLine("```");
        return sb.ToString().Trim() + "\n";
    }

    private static string BuildPromptOnly(string nextPrompt)
    {
        var sb = new StringBuilder();
        sb.AppendLine("```");
        sb.AppendLine(nextPrompt);
        sb.AppendLine("```");
        return sb.ToString().Trim() + "\n";
    }

    private static Options ParseArgs(string[] args)
    {
        var opts = new Options();
        for (int i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            switch (arg)
            {
                case "--clipboard":
                    opts.Clipboard = true;
                    break;
                case "--zip":
                    opts.Zip = true;
                    break;
                case "--stdin":
                    opts.UseStdin = true;
                    break;
                case "--allow-secrets":
                    opts.AllowSecrets = true;
                    break;
                case "--prompt-only":
                    opts.PromptOnly = true;
                    break;
                case "--out":
                    if (i + 1 >= args.Length) throw new ArgumentException("Missing value for --out");
                    opts.OutputPath = args[++i];
                    break;
                case "--help":
                case "-h":
                    PrintHelp();
                    Environment.Exit(0);
                    break;
                default:
                    if (arg.StartsWith("-"))
                    {
                        throw new ArgumentException($"Unknown option: {arg}");
                    }
                    if (opts.InputPath == null)
                    {
                        opts.InputPath = arg;
                    }
                    else
                    {
                        throw new ArgumentException("Only one input file is supported.");
                    }
                    break;
            }
        }

        if (string.IsNullOrWhiteSpace(opts.InputPath) && !opts.UseStdin && !Console.IsInputRedirected)
        {
            throw new ArgumentException("No input provided. Specify a file or use --stdin.");
        }

        return opts;
    }

    private static string ReadInput(Options options)
    {
        if (options.UseStdin || (options.InputPath == null && Console.IsInputRedirected))
        {
            return Console.In.ReadToEnd();
        }

        if (!File.Exists(options.InputPath!))
        {
            throw new FileNotFoundException($"Input file not found: {options.InputPath}");
        }

        return File.ReadAllText(options.InputPath!, Encoding.UTF8);
    }

    private static void PrintHelp()
    {
        Console.WriteLine("handoff <input-file> [--stdin] [--clipboard] [--zip] [--allow-secrets] [--prompt-only] [--out <path>]");
        Console.WriteLine("Examples:");
        Console.WriteLine("  handoff codex_output.txt");
        Console.WriteLine("  handoff codex_output.txt --clipboard");
        Console.WriteLine("  handoff codex_output.txt --clipboard --zip");
        Console.WriteLine("  cat codex_output.txt | handoff --stdin");
        Console.WriteLine("  handoff codex_output.txt --prompt-only --out prompt.md");
    }

    private sealed class Options
    {
        public string? InputPath { get; set; }
        public string? OutputPath { get; set; }
        public bool Clipboard { get; set; }
        public bool Zip { get; set; }
        public bool AllowSecrets { get; set; }
        public bool UseStdin { get; set; }
        public bool PromptOnly { get; set; }
    }
}
