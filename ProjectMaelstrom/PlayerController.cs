using WindowsInput;
using WindowsInput.Native;
using ProjectMaelstrom.Utilities;
using System.Diagnostics;
using System.Text;
using System.Linq;

namespace ProjectMaelstrom;

internal class PlayerController
{
    private InputSimulator _inputSimulator = new InputSimulator();
    private const string GameWindowHint = "Wizard101";

    public void MoveForward()
    {
        try
        {
            _inputSimulator.Keyboard.KeyDown(VirtualKeyCode.UP);
            Logger.LogBotAction("PlayerController", "MoveForward executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("MoveForward failed", ex);
        }
    }

    public void MoveBackward()
    {
        try
        {
            _inputSimulator.Keyboard.KeyDown(VirtualKeyCode.BACK);
            Logger.LogBotAction("PlayerController", "MoveBackward executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("MoveBackward failed", ex);
        }
    }

    public void MoveLeft()
    {
        try
        {
            _inputSimulator.Keyboard.KeyDown(VirtualKeyCode.LEFT);
            Logger.LogBotAction("PlayerController", "MoveLeft executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("MoveLeft failed", ex);
        }
    }

    public void MoveRight()
    {
        try
        {
            _inputSimulator.Keyboard.KeyDown(VirtualKeyCode.RIGHT);
            Logger.LogBotAction("PlayerController", "MoveRight executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("MoveRight failed", ex);
        }
    }

    public void Interact()
    {
        try
        {
            _inputSimulator.Keyboard.KeyPress(VirtualKeyCode.VK_X);
            Logger.LogBotAction("PlayerController", "Interact executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("Interact failed", ex);
        }
    }

    public void PressNumber9()
    {
        try
        {
            _inputSimulator.Keyboard.KeyPress(VirtualKeyCode.NUMPAD9);
            Logger.LogBotAction("PlayerController", "PressNumber9 executed");
        }
        catch (Exception ex)
        {
            Logger.LogError("PressNumber9 failed", ex);
        }
    }

    public void Click(Point clickPoint)
    {
        try
        {
            WinAPI.click(clickPoint);
            Logger.LogBotAction("PlayerController", $"Click executed at ({clickPoint.X}, {clickPoint.Y})");
        }
        catch (Exception ex)
        {
            Logger.LogError($"Click failed at ({clickPoint.X}, {clickPoint.Y})", ex);
        }
    }

    public void KeyPress(string keyName)
    {
        if (string.IsNullOrWhiteSpace(keyName))
        {
            return;
        }

        try
        {
            if (Enum.TryParse<VirtualKeyCode>(keyName, true, out var code))
            {
                _inputSimulator.Keyboard.KeyPress(code);
                Logger.LogBotAction("PlayerController", $"KeyPress executed: {keyName}");
            }
            else
            {
                Logger.LogError($"KeyPress failed: unknown key '{keyName}'");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"KeyPress failed: {keyName}", ex);
        }
    }

    public void KeyDown(string keyName)
    {
        if (string.IsNullOrWhiteSpace(keyName))
        {
            return;
        }

        try
        {
            if (Enum.TryParse<VirtualKeyCode>(keyName, true, out var code))
            {
                _inputSimulator.Keyboard.KeyDown(code);
                Logger.LogBotAction("PlayerController", $"KeyDown executed: {keyName}");
            }
            else
            {
                Logger.LogError($"KeyDown failed: unknown key '{keyName}'");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"KeyDown failed: {keyName}", ex);
        }
    }

    public void KeyUp(string keyName)
    {
        if (string.IsNullOrWhiteSpace(keyName))
        {
            return;
        }

        try
        {
            if (Enum.TryParse<VirtualKeyCode>(keyName, true, out var code))
            {
                _inputSimulator.Keyboard.KeyUp(code);
                Logger.LogBotAction("PlayerController", $"KeyUp executed: {keyName}");
            }
            else
            {
                Logger.LogError($"KeyUp failed: unknown key '{keyName}'");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"KeyUp failed: {keyName}", ex);
        }
    }

    public bool EnsureGameForeground()
    {
        try
        {
            // Check current foreground window first
            var fg = WinAPI.GetForegroundWindow();
            if (WindowTitleContains(fg, GameWindowHint))
            {
                return true;
            }

            // Attempt to bring Wizard101 to foreground by window title
            var proc = Process.GetProcesses()
                .FirstOrDefault(p => !p.HasExited &&
                                     !string.IsNullOrWhiteSpace(p.MainWindowTitle) &&
                                     p.MainWindowTitle.IndexOf(GameWindowHint, StringComparison.OrdinalIgnoreCase) >= 0);
            if (proc != null && proc.MainWindowHandle != IntPtr.Zero)
            {
                WinAPI.SetForegroundWindow(proc.MainWindowHandle);
                Thread.Sleep(50);
                return WindowTitleContains(WinAPI.GetForegroundWindow(), GameWindowHint);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("EnsureGameForeground failed", ex);
        }

        return false;
    }

    private bool WindowTitleContains(IntPtr hWnd, string hint)
    {
        if (hWnd == IntPtr.Zero || string.IsNullOrWhiteSpace(hint)) return false;
        int length = WinAPI.GetWindowTextLength(hWnd);
        if (length <= 0) return false;
        var sb = new StringBuilder(length + 1);
        WinAPI.GetWindowText(hWnd, sb, sb.Capacity);
        return sb.ToString().IndexOf(hint, StringComparison.OrdinalIgnoreCase) >= 0;
    }
}
