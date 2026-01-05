using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight global input recorder for macro capture (keyboard + left mouse clicks).
/// Captures relative delays between events as InputCommand entries.
/// </summary>
internal sealed class InputRecorder : IDisposable
{
    private IntPtr _keyboardHook = IntPtr.Zero;
    private IntPtr _mouseHook = IntPtr.Zero;
    private HookProc? _kbCallback;
    private HookProc? _mouseCallback;
    private readonly List<InputCommand> _commands = new();
    private readonly Stopwatch _stopwatch = new();
    private bool _recording;

    public IReadOnlyList<InputCommand> Commands => _commands.ToList();

    public void Start()
    {
        if (_recording) return;
        _commands.Clear();
        _stopwatch.Restart();
        _kbCallback = KeyboardProc;
        _mouseCallback = MouseProc;
        _keyboardHook = SetHook(WH_KEYBOARD_LL, _kbCallback);
        _mouseHook = SetHook(WH_MOUSE_LL, _mouseCallback);
        _recording = true;
    }

    public void Stop()
    {
        if (!_recording) return;
        UnhookWindowsHookEx(_keyboardHook);
        UnhookWindowsHookEx(_mouseHook);
        _keyboardHook = IntPtr.Zero;
        _mouseHook = IntPtr.Zero;
        _stopwatch.Stop();
        _recording = false;
    }

    public void Dispose()
    {
        Stop();
    }

    private IntPtr KeyboardProc(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && _recording)
        {
            int msg = wParam.ToInt32();
            var kb = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
            // Only record down/up events
            if (msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN)
            {
                AddCommand(new InputCommand
                {
                    Type = "key_down",
                    Key = ((Keys)kb.vkCode).ToString()
                });
            }
            else if (msg == WM_KEYUP || msg == WM_SYSKEYUP)
            {
                AddCommand(new InputCommand
                {
                    Type = "key_up",
                    Key = ((Keys)kb.vkCode).ToString()
                });
            }
        }
        return CallNextHookEx(_keyboardHook, nCode, wParam, lParam);
    }

    private IntPtr MouseProc(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && _recording)
        {
            int msg = wParam.ToInt32();
            if (msg == WM_LBUTTONDOWN)
            {
                var ms = Marshal.PtrToStructure<MSLLHOOKSTRUCT>(lParam);
                AddCommand(new InputCommand
                {
                    Type = "click",
                    X = ms.pt.x,
                    Y = ms.pt.y
                });
            }
        }
        return CallNextHookEx(_mouseHook, nCode, wParam, lParam);
    }

    private void AddCommand(InputCommand cmd)
    {
        var elapsed = (int)_stopwatch.ElapsedMilliseconds;
        _stopwatch.Restart();
        if (elapsed > 0)
        {
            _commands.Add(new InputCommand { Type = "delay", DelayMs = elapsed });
        }
        _commands.Add(cmd);
    }

    #region WinAPI
    private delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

    private const int WH_KEYBOARD_LL = 13;
    private const int WH_MOUSE_LL = 14;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_KEYUP = 0x0101;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int WM_SYSKEYUP = 0x0105;
    private const int WM_LBUTTONDOWN = 0x0201;

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT
    {
        public int x;
        public int y;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MSLLHOOKSTRUCT
    {
        public POINT pt;
        public int mouseData;
        public int flags;
        public int time;
        public IntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KBDLLHOOKSTRUCT
    {
        public int vkCode;
        public int scanCode;
        public int flags;
        public int time;
        public IntPtr dwExtraInfo;
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, HookProc lpfn, IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string lpModuleName);

    private static IntPtr SetHook(int idHook, HookProc callback)
    {
        using var curProcess = Process.GetCurrentProcess();
        using var curModule = curProcess.MainModule!;
        return SetWindowsHookEx(idHook, callback, GetModuleHandle(curModule.ModuleName), 0);
    }
    #endregion
}
