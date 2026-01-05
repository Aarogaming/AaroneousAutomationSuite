# AAS Hub Launcher Architecture

## Primary Entry Point: System Tray Application

As of Jan 2026, the **AAS Tray** (`aas_tray.py`) is the unified entry point for starting and managing the AAS Hub.

### Why Consolidate?

1. **No Console Windows** - Tray launches Hub silently in background
2. **Windows Notifications** - Status updates via native notifications instead of terminal output
3. **Single EXE Path** - One application to compile for distribution
4. **GUI Foundation** - Future desktop GUI will extend this same codebase
5. **Better UX** - Right-click tray icon for all Hub operations

### How It Works

```
User Double-Clicks "AAS Tray.bat"
    ↓
Activates Python venv
    ↓
Launches aas_tray.py (using pythonw for no console)
    ↓
Tray icon appears in system tray
    ↓
On "Start Hub" click:
    1. Validates prerequisites (.env, venv, artifacts dir)
    2. Kills zombie processes on ports 50051 & 8000
    3. Rotates logs if > 100MB
    4. Launches Hub directly (python core/main.py)
    5. Shows Windows notification with status
```

### Startup Validation (Built-In)

The tray performs these checks before starting Hub:

- ✅ Virtual environment exists (`.venv/Scripts/python.exe`)
- ✅ Configuration file present (`.env`)
- ✅ Artifacts directory writable
- ✅ Log rotation (auto-archives logs > 100MB)
- ✅ Zombie process cleanup (ports 50051, 8000)
- ✅ Stale PID file removal

### Files

| File | Purpose |
|------|---------|
| `AAS Tray.bat` | Primary launcher - double-click this to start everything |
| `aas_tray.py` | Tray application with integrated startup logic |
| `start_hub.ps1` | **DEPRECATED** - Kept for backwards compatibility, but tray bypasses this |

### User Workflow

**Starting AAS:**
1. Double-click `AAS Tray.bat` (or pin to taskbar)
2. Tray icon appears in notification area
3. Right-click → "▶️ Start Hub"
4. Get notification when ready

**Daily Use:**
- Right-click tray icon for all operations
- ℹ️ Status - Check if Hub is running
- 🔄 Restart - Apply code changes
- ⏸️ Stop - Shut down gracefully
- 📊 Mission Control - Open dashboard
- 📋 View Logs - Troubleshooting

### Future: Desktop GUI

When implementing the full desktop GUI:

1. **Extend `aas_tray.py`** - Add windowed interface alongside tray icon
2. **Reuse startup logic** - All validation functions already present
3. **Share icon/branding** - `create_icon()` becomes logo generator
4. **Package as EXE** - PyInstaller/cx_Freeze on same codebase

The tray was designed from the start to be the GUI's foundation.

### Migration Notes

**For developers:**
- Start Hub via tray, not PowerShell script
- Tray handles all prerequisite checks automatically
- No need to manually clean zombie processes
- Logs still go to `artifacts/hub.log`

**For automation:**
- Can still call `python scripts/aas_tray.py` directly
- Use `start_hub.ps1` for CLI-based workflows if needed
- Tray will self-launch Hub on first start if configured

### Troubleshooting

**Tray won't start:**
```powershell
# Check virtual environment
.venv\Scripts\python.exe --version

# Check dependencies
pip install -r requirements.txt
```

**Hub fails to start from tray:**
- Right-click → "📋 View Logs"
- Check `artifacts/hub.log` for errors
- Verify `.env` file has required keys

**Tray icon missing:**
- May be hidden in overflow area (^ icon near clock)
- Reinstall Pillow: `pip install --force-reinstall pillow pystray`

### Technical Details

**Process Architecture:**
```
AAS Tray.bat (launcher)
  └─ pythonw.exe (no console)
      └─ aas_tray.py (system tray app)
          └─ powershell.exe -WindowStyle Hidden
              └─ python.exe core/main.py (AAS Hub)
```

**Why `pythonw`?**
- `python` = console window appears
- `pythonw` = silent background execution
- Perfect for tray applications

**Detached Process Flags:**
- `CREATE_NO_WINDOW` - No console for child processes
- `DETACHED_PROCESS` - Hub survives if tray closes

**IPC Between Tray & Hub:**
- Tray reads `artifacts/hub.pid` for process ID
- Checks process with `Get-Process` (PowerShell)
- No direct IPC needed for control flow
