using System;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;

namespace ProjectMaelstrom.Utilities;

internal class ProcessMemoryWatcher : IDisposable
{
    private static readonly string[] CandidateProcessNames = { "WizardGraphicalClient", "Wizard101" };
    private const string ModuleName = "Wizard101.exe";

    // Provided pointer chain: module base + 0x01234567 -> [0x30, 0x18, 0xA0] -> stat_base
    private const uint BaseOffset = 0x01234567;
    private static readonly uint[] ChainOffsets = { 0x30, 0x18, 0xA0 };

    // wizwalker stat offsets
    private const int BaseHpOffset = 80;
    private const int CurrentHpOffset = 108;
    private const int BonusHpOffset = 216;
    private const int BaseManaOffset = 84;
    private const int CurrentManaOffset = 128;
    private const int BonusManaOffset = 220;
    private const int EnergyMaxOffset = 104;
    private const int BonusEnergyOffset = 236;

    private IntPtr _processHandle = IntPtr.Zero;
    private int _cachedPid = -1;

    public void Dispose()
    {
        CloseHandle();
        GC.SuppressFinalize(this);
    }

    public bool TryUpdateState(out string? error)
    {
        error = null;
        try
        {
            var proc = FindProcess();
            if (proc == null)
            {
                error = "Wizard101 process not found.";
                CloseHandle();
                return false;
            }

            if (proc.Id != _cachedPid || _processHandle == IntPtr.Zero)
            {
                CloseHandle();
                _processHandle = OpenProcess(ProcessAccessFlags.QueryInformation | ProcessAccessFlags.VirtualMemoryRead, false, proc.Id);
                _cachedPid = proc.Id;
                if (_processHandle == IntPtr.Zero)
                {
                    error = "Unable to open process for reading.";
                    return false;
                }
            }

            var moduleBase = GetModuleBase(proc, ModuleName);
            if (moduleBase == IntPtr.Zero)
            {
                error = $"Module {ModuleName} not found.";
                return false;
            }

            ulong statBase = ResolvePtrChain(moduleBase, BaseOffset, ChainOffsets);
            if (statBase == 0)
            {
                error = "Failed to resolve stat base.";
                return false;
            }

            int baseHp = ReadInt32(statBase + BaseHpOffset);
            int currentHp = ReadInt32(statBase + CurrentHpOffset);
            int bonusHp = ReadInt32(statBase + BonusHpOffset);

            int baseMana = ReadInt32(statBase + BaseManaOffset);
            int currentMana = ReadInt32(statBase + CurrentManaOffset);
            int bonusMana = ReadInt32(statBase + BonusManaOffset);

            int energyMaxBase = ReadInt32(statBase + EnergyMaxOffset);
            int bonusEnergy = ReadInt32(statBase + BonusEnergyOffset);

            StateManager.Instance.CurrentHealth = currentHp;
            StateManager.Instance.MaxHealth = SafeAdd(baseHp, bonusHp);

            StateManager.Instance.CurrentMana = currentMana;
            StateManager.Instance.MaxMana = SafeAdd(baseMana, bonusMana);

            StateManager.Instance.CurrentEnergy = SafeAdd(energyMaxBase, bonusEnergy); // no current energy offset provided; assume same as max
            StateManager.Instance.MaxEnergy = SafeAdd(energyMaxBase, bonusEnergy);

            return true;
        }
        catch (Exception ex)
        {
            error = ex.Message;
            return false;
        }
    }

    private static int SafeAdd(int a, int b)
    {
        try
        {
            return checked(a + b);
        }
        catch
        {
            return int.MaxValue;
        }
    }

    private Process? FindProcess(string name)
    {
        return Process.GetProcessesByName(name).FirstOrDefault();
    }

    private Process? FindProcess()
    {
        foreach (var name in CandidateProcessNames)
        {
            var proc = FindProcess(name);
            if (proc != null) return proc;
        }
        return null;
    }

    private static IntPtr GetModuleBase(Process proc, string moduleName)
    {
        foreach (ProcessModule? module in proc.Modules)
        {
            if (module != null && module.ModuleName.Equals(moduleName, StringComparison.OrdinalIgnoreCase))
            {
                return module.BaseAddress;
            }
        }
        return IntPtr.Zero;
    }

    private ulong ResolvePtrChain(IntPtr moduleBase, uint baseOffset, uint[] offsets)
    {
        ulong addr = (ulong)moduleBase + baseOffset;
        for (int i = 0; i < offsets.Length; i++)
        {
            addr = ReadUInt64(addr);
            if (addr == 0) return 0;
            addr += offsets[i];
        }
        return addr;
    }

    private ulong ReadUInt64(ulong address)
    {
        byte[] buffer = new byte[8];
        if (!ReadProcessMemory(_processHandle, new IntPtr((long)address), buffer, buffer.Length, out _))
        {
            return 0;
        }
        return BitConverter.ToUInt64(buffer, 0);
    }

    private int ReadInt32(ulong address)
    {
        byte[] buffer = new byte[4];
        if (!ReadProcessMemory(_processHandle, new IntPtr((long)address), buffer, buffer.Length, out _))
        {
            return 0;
        }
        return BitConverter.ToInt32(buffer, 0);
    }

    private void CloseHandle()
    {
        if (_processHandle != IntPtr.Zero)
        {
            try { CloseHandle(_processHandle); } catch { /* ignore */ }
            _processHandle = IntPtr.Zero;
            _cachedPid = -1;
        }
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(ProcessAccessFlags access, bool inheritHandle, int processId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer, int dwSize, out IntPtr lpNumberOfBytesRead);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    [Flags]
    private enum ProcessAccessFlags : uint
    {
        QueryInformation = 0x0400,
        VirtualMemoryRead = 0x0010
    }
}
