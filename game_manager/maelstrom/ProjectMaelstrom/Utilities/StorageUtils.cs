using System;
using System.IO;

namespace ProjectMaelstrom.Utilities;

internal class StorageUtils
{
    public static string GetAppRoot()
    {
        try
        {
            if (!string.IsNullOrEmpty(AppDomain.CurrentDomain.BaseDirectory))
            {
                return AppDomain.CurrentDomain.BaseDirectory;
            }

            string currentDir = Directory.GetCurrentDirectory();
            if (!string.IsNullOrEmpty(currentDir))
            {
                return currentDir;
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Error in GetAppRoot", ex);
        }

        return AppContext.BaseDirectory;
    }

    public static string GetScriptsRoot()
    {
        string root = GetAppRoot();
        string scriptsPath = Path.Combine(root, "Scripts");

        try
        {
            if (!Directory.Exists(scriptsPath))
            {
                Directory.CreateDirectory(scriptsPath);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Unable to create Scripts directory", ex);
        }

        return scriptsPath;
    }

    public static string GetCacheDirectory()
    {
        string cachePath = Path.Combine(GetScriptsRoot(), ".cache");
        try
        {
            if (!Directory.Exists(cachePath))
            {
                Directory.CreateDirectory(cachePath);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Unable to create cache directory", ex);
        }

        return cachePath;
    }

    public static string GetScriptLibraryPath()
    {
        string libraryPath = Path.Combine(GetScriptsRoot(), "Library");
        try
        {
            if (!Directory.Exists(libraryPath))
            {
                Directory.CreateDirectory(libraryPath);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Unable to create Script Library directory", ex);
        }

        return libraryPath;
    }

    public static string GetAppPath()
    {
        try
        {
            string basePath = GetAppRoot();
            if (string.IsNullOrEmpty(basePath))
            {
                throw new InvalidOperationException("Base directory is null or empty.");
            }

            string resourcesPath = Path.Combine(basePath, "Resources");
            if (Directory.Exists(resourcesPath))
            {
                string selectedResolution = StateManager.Instance?.SelectedResolution ?? "1280x720";
                return Path.Combine(resourcesPath, selectedResolution);
            }
            else
            {
                string currentDir = Directory.GetCurrentDirectory();
                if (string.IsNullOrEmpty(currentDir))
                {
                    throw new InvalidOperationException("Current directory is null or empty.");
                }

                string selectedResolution = StateManager.Instance?.SelectedResolution ?? "1280x720";
                return Path.Combine(currentDir, "Resources", selectedResolution);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Error in GetAppPath", ex);
            return Path.Combine(Directory.GetCurrentDirectory(), "Resources", "1280x720");
        }
    }

    public static string GetDesignSamplesPath()
    {
        var path = Path.Combine(GetCacheDirectory(), "design_samples");
        try
        {
            if (!Directory.Exists(path))
            {
                Directory.CreateDirectory(path);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Unable to create design samples directory", ex);
        }
        return path;
    }
}
