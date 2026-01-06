using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Xunit;

namespace ProjectMaelstrom.Tests;

public class OcrParsingTests
{
    private static readonly Type GameStateServiceType = typeof(ProjectMaelstrom.Utilities.GameStateService);
    private static readonly MethodInfo ParsePair = GameStateServiceType.GetMethod("ParsePair", BindingFlags.NonPublic | BindingFlags.Static)!;
    private static readonly MethodInfo ParseSingle = GameStateServiceType.GetMethod("ParseSingle", BindingFlags.NonPublic | BindingFlags.Static)!;
    private static readonly MethodInfo ClampToRange = GameStateServiceType.GetMethod("ClampToRange", BindingFlags.NonPublic | BindingFlags.Static)!;

    [Theory]
    [InlineData("123/456", 123, 456)]
    [InlineData("  12 / 34 ", 12, 34)]
    public void ParsePair_ReturnsPair_WhenValid(string text, int expectedCurrent, int expectedMax)
    {
        var result = ParsePair.Invoke(null, new object[] { text });
        Assert.NotNull(result);
        var tuple = ((int current, int max))result!;
        Assert.Equal(expectedCurrent, tuple.current);
        Assert.Equal(expectedMax, tuple.max);
    }

    [Fact]
    public void ParsePair_ReturnsNull_OnInvalid()
    {
        var result = ParsePair.Invoke(null, new object[] { "abc/xyz" });
        Assert.Null(result);
    }

    [Theory]
    [InlineData("123/456 extra", 123, 456)]
    [InlineData("hp 9999/10000", 9999, 10000)]
    public void ParsePair_ParsesWithTrailingText(string text, int expectedCurrent, int expectedMax)
    {
        var result = ParsePair.Invoke(null, new object[] { text });
        Assert.NotNull(result);
        var tuple = ((int current, int max))result!;
        Assert.Equal(expectedCurrent, tuple.current);
        Assert.Equal(expectedMax, tuple.max);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void ParsePair_ReturnsNull_OnEmptyOrWhitespace(string text)
    {
        var result = ParsePair.Invoke(null, new object[] { text });
        Assert.Null(result);
    }

    [Theory]
    [InlineData("Energy 250", 250)]
    [InlineData(" 42 ", 42)]
    [InlineData("Value=77", 77)]
    [InlineData("gold 10 mana 20", 10)]
    public void ParseSingle_ReturnsValue_WhenValid(string text, int expected)
    {
        var value = (int?)ParseSingle.Invoke(null, new object[] { text });
        Assert.Equal(expected, value);
    }

    [Fact]
    public void ParseSingle_ReturnsNull_OnInvalid()
    {
        var value = (int?)ParseSingle.Invoke(null, new object[] { "none here" });
        Assert.Null(value);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void ParseSingle_ReturnsNull_OnEmptyOrWhitespace(string text)
    {
        var value = (int?)ParseSingle.Invoke(null, new object[] { text });
        Assert.Null(value);
    }

    [Theory]
    [InlineData(-5, 0, 10, 0)]
    [InlineData(15, 0, 10, 10)]
    [InlineData(5, 0, 10, 5)]
    public void ClampToRange_ClampsAsExpected(int value, int min, int max, int expected)
    {
        var result = (int)ClampToRange.Invoke(null, new object[] { value, min, max })!;
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ParsePair_MatchesSampleFiles()
    {
        var baseDir = Path.Combine(AppContext.BaseDirectory, "TestData", "ocr");
        var files = Directory.GetFiles(baseDir, "*.txt").OrderBy(f => f, StringComparer.Ordinal);
        foreach (var file in files)
        {
            var text = File.ReadAllText(file);
            var result = ParsePair.Invoke(null, new object[] { text });
            if (Path.GetFileName(file).StartsWith("invalid", StringComparison.OrdinalIgnoreCase))
            {
                Assert.Null(result);
            }
            else if (Path.GetFileName(file).StartsWith("empty", StringComparison.OrdinalIgnoreCase) ||
                     Path.GetFileName(file).StartsWith("whitespace", StringComparison.OrdinalIgnoreCase) ||
                     Path.GetFileName(file).StartsWith("partial", StringComparison.OrdinalIgnoreCase))
            {
                Assert.Null(result);
            }
            else
            {
                Assert.NotNull(result);
            }
        }
    }

    [Fact]
    public void ParsePair_UsesFirstPairInNoisyFixture()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "TestData", "ocr", "noisy_mixed.txt");
        var text = File.ReadAllText(path);
        var result = ParsePair.Invoke(null, new object[] { text });
        Assert.NotNull(result);
        var tuple = ((int current, int max))result!;
        Assert.Equal(10, tuple.current);
        Assert.Equal(20, tuple.max);
    }

    [Fact]
    public void ParseSingle_UsesFirstNumberInMixedFixture()
    {
        var text = "hp 300 mana 400";
        var value = (int?)ParseSingle.Invoke(null, new object[] { text });
        Assert.Equal(300, value);
    }
}
