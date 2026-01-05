using ProjectMaelstrom.Utilities;
using System.IO;

namespace ProjectMaelstrom.Tests;

internal static class UtilityTests
{
    public static void RunAllTests()
    {
        string testLogPath = "test_results.txt";
        using (StreamWriter writer = new StreamWriter(testLogPath, false))
        {
            writer.WriteLine("Running Utility Tests...");
            Console.WriteLine("Running Utility Tests...");

            TestStorageUtils(writer);
            TestGeneralUtils(writer);
            TestDanceBotPath(writer);

            writer.WriteLine("All tests completed.");
            Console.WriteLine("All tests completed.");
        }
    }

    private static void TestStorageUtils(StreamWriter writer)
    {
        writer.WriteLine("Testing StorageUtils...");
        Console.WriteLine("Testing StorageUtils...");

        try
        {
            // Test GetAppPath
            string path = StorageUtils.GetAppPath();
            writer.WriteLine($"App path: {path}");
            Console.WriteLine($"App path: {path}");

            if (!string.IsNullOrEmpty(path) && Directory.Exists(path))
            {
                writer.WriteLine("[PASS] GetAppPath test passed");
                Console.WriteLine("[PASS] GetAppPath test passed");
            }
            else
            {
                writer.WriteLine("[FAIL] GetAppPath test failed - invalid path");
                Console.WriteLine("[FAIL] GetAppPath test failed - invalid path");
            }
        }
        catch (Exception ex)
        {
            writer.WriteLine($"[FAIL] GetAppPath test failed with exception: {ex.Message}");
            Console.WriteLine($"[FAIL] GetAppPath test failed with exception: {ex.Message}");
        }
    }

    private static void TestGeneralUtils(StreamWriter writer)
    {
        writer.WriteLine("Testing GeneralUtils...");
        Console.WriteLine("Testing GeneralUtils...");

        try
        {
            // Test RandomString
            string randomStr = GeneralUtils.Instance.RandomString(10);
            writer.WriteLine($"Random string: {randomStr}");
            Console.WriteLine($"Random string: {randomStr}");

            if (!string.IsNullOrEmpty(randomStr) && randomStr.Length == 10)
            {
                writer.WriteLine("[PASS] RandomString test passed");
                Console.WriteLine("[PASS] RandomString test passed");
            }
            else
            {
                writer.WriteLine("[FAIL] RandomString test failed");
                Console.WriteLine("[FAIL] RandomString test failed");
            }

            // Test IsGameVisible (this will likely fail without game running, but tests the method)
            bool visible = GeneralUtils.Instance.IsGameVisible();
            writer.WriteLine($"Game visible: {visible}");
            Console.WriteLine($"Game visible: {visible}");
            writer.WriteLine("[INFO] IsGameVisible test completed (result depends on game state)");
            Console.WriteLine("[INFO] IsGameVisible test completed (result depends on game state)");
        }
        catch (Exception ex)
        {
            writer.WriteLine($"[FAIL] GeneralUtils test failed with exception: {ex.Message}");
            Console.WriteLine($"[FAIL] GeneralUtils test failed with exception: {ex.Message}");
        }
    }

    private static void TestDanceBotPath(StreamWriter writer)
    {
        writer.WriteLine("Testing Wizard101 DanceBot path...");
        Console.WriteLine("Testing Wizard101 DanceBot path...");

        try
        {
            string scriptPath = Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory,
                "Scripts",
                "Wizard101_DanceBot",
                "dist",
                "petdance",
                "petdance.exe");
            writer.WriteLine($"Script path: {scriptPath}");
            Console.WriteLine($"Script path: {scriptPath}");

            if (File.Exists(scriptPath))
            {
                writer.WriteLine("[PASS] Wizard101 DanceBot exists at expected location");
                Console.WriteLine("[PASS] Wizard101 DanceBot exists at expected location");
            }
            else
            {
                writer.WriteLine("[FAIL] Wizard101 DanceBot not found at expected location");
                Console.WriteLine("[FAIL] Wizard101 DanceBot not found at expected location");
            }
        }
        catch (Exception ex)
        {
            writer.WriteLine($"[FAIL] Wizard101 DanceBot path test failed with exception: {ex.Message}");
            Console.WriteLine($"[FAIL] Wizard101 DanceBot path test failed with exception: {ex.Message}");
        }
    }
}
