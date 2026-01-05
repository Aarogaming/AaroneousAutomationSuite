using Emgu.CV;
using Emgu.CV.CvEnum;
using Emgu.CV.Structure;
using Newtonsoft.Json.Linq;
using System.Net.Http.Headers;
using System.Drawing;
using Tesseract;

namespace ProjectMaelstrom.Modules.ImageRecognition;

internal static class ImageHelpers
{
    public class OcrPreprocessOptions
    {
        public bool ConvertToGray { get; set; } = true;
        public bool Invert { get; set; } = false;
        public bool ApplyThreshold { get; set; } = true;
        public double Threshold { get; set; } = 128;
        public double MaxValue { get; set; } = 255;
        public bool ApplyBlur { get; set; } = true;
        public Size? ResizeTo { get; set; }
        public string? CharacterWhitelist { get; set; }
        public PageSegMode PageSegMode { get; set; } = PageSegMode.Auto;
    }

    public static async Task<string> ExtractTextFromImage(string imagePath, OcrPreprocessOptions? options = null)
    {
        var opts = options ?? new OcrPreprocessOptions();
        string preprocessedPath = PreprocessForOcr(imagePath, opts);
        string apiKey = Properties.Settings.Default["OCR_SPACE_APIKEY"]?.ToString() ?? string.Empty;
        if (string.IsNullOrEmpty(apiKey))
        {
            return ExtractTextWithLocalOcr(preprocessedPath, opts);
        }
        string apiUrl = "https://api.ocr.space/parse/image";

        using var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("apikey", apiKey);

        using var formData = new MultipartFormDataContent();

        using FileStream fileStream = File.OpenRead(preprocessedPath);
        using var streamContent = new StreamContent(fileStream);
        using var fileContent = new ByteArrayContent(await streamContent.ReadAsByteArrayAsync());

        string fileExtension = Path.GetExtension(preprocessedPath).ToLower();
        string contentType = fileExtension switch
        {
            ".jpg" or ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            ".gif" => "image/gif",
            ".bmp" => "image/bmp",
            ".tiff" or ".tif" => "image/tiff",
            _ => throw new NotSupportedException($"File extension {fileExtension} is not supported")
        };

        fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse(contentType);
        formData.Add(fileContent, "file", Path.GetFileName(imagePath));

        var response = await httpClient.PostAsync(apiUrl, formData);
        response.EnsureSuccessStatusCode();

        string jsonResponse = await response.Content.ReadAsStringAsync();
        JObject parsedResponse = JObject.Parse(jsonResponse);
        if (parsedResponse["ParsedResults"] is JArray results && results.Count > 0 && results[0]["ParsedText"] is JToken textToken)
        {
            string text = textToken.ToString();
            return text;
        }
        else
        {
            throw new Exception("OCR response parsing failed: Invalid JSON structure.");
        }
    }

    private static string ExtractTextWithLocalOcr(string imagePath, OcrPreprocessOptions opts)
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string? tessdataPath = FindTessdataPath(baseDir);

        if (tessdataPath == null)
        {
            throw new InvalidOperationException("Local OCR fallback failed: tessdata folder not found. Place English trained data in a 'tessdata' folder next to the executable.");
        }

        try
        {
            var config = string.IsNullOrWhiteSpace(opts.CharacterWhitelist)
                ? string.Empty
                : $"tessedit_char_whitelist={opts.CharacterWhitelist}";
            using var engine = new TesseractEngine(tessdataPath, "eng", EngineMode.Default, config);
            using var img = Pix.LoadFromFile(imagePath);
            using var page = engine.Process(img, opts.PageSegMode);
            return page.GetText();
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Local OCR fallback failed: {ex.Message}", ex);
        }
    }

    private static string? FindTessdataPath(string baseDir)
    {
        string candidate = Path.Combine(baseDir, "tessdata");
        if (Directory.Exists(candidate))
        {
            return candidate;
        }

        candidate = Path.Combine(Directory.GetCurrentDirectory(), "tessdata");
        if (Directory.Exists(candidate))
        {
            return candidate;
        }

        return null;
    }

    public static void ConvertImageToGrayscale(string imagePath)
    {
        using var img = new Mat(imagePath);
        using var grayImg = new Mat();
        CvInvoke.CvtColor(img, grayImg, Emgu.CV.CvEnum.ColorConversion.Bgr2Gray);
        grayImg.Clone().Save(imagePath);
    }

    public static string PreprocessForOcr(string imagePath, OcrPreprocessOptions options)
    {
        var opts = options ?? new OcrPreprocessOptions();
        using var src = new Mat(imagePath);
        Mat working = src.Clone();

        if (opts.ConvertToGray)
        {
            CvInvoke.CvtColor(working, working, ColorConversion.Bgr2Gray);
        }

        if (opts.ResizeTo.HasValue && opts.ResizeTo.Value.Width > 0 && opts.ResizeTo.Value.Height > 0)
        {
            CvInvoke.Resize(working, working, opts.ResizeTo.Value, 0, 0, Inter.Cubic);
        }

        if (opts.ApplyBlur)
        {
            CvInvoke.GaussianBlur(working, working, new Size(3, 3), 0);
        }

        if (opts.ApplyThreshold)
        {
            CvInvoke.Threshold(working, working, opts.Threshold, opts.MaxValue, ThresholdType.Binary);
        }

        if (opts.Invert)
        {
            CvInvoke.BitwiseNot(working, working);
        }

        string tempPath = Path.Combine(Path.GetTempPath(), $"ocr_{Guid.NewGuid():N}.png");
        working.Save(tempPath);
        return tempPath;
    }
}
