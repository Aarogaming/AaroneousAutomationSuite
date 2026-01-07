"""
AAS Hub System Tray Application
Provides a taskbar icon for monitoring and controlling the AAS Hub.
"""
import subprocess
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import threading
import time
import webbrowser
import pyperclip
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback

# Paths
# When running as PyInstaller exe, __file__ points to temp dir
# Use the exe's parent directory as ROOT_DIR when frozen
if getattr(sys, 'frozen', False):
    # Running as compiled exe in dist/ - go up one level to project root
    ROOT_DIR = Path(sys.executable).parent.parent
else:
    # Running as script in scripts/ - go up one level to project root
    ROOT_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
PID_FILE = ROOT_DIR / "artifacts" / "hub.pid"
ENV_FILE = ROOT_DIR / ".env"
PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "pythonw.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    # Fallback for non-Windows or different venv structure
    PYTHON_EXE = ROOT_DIR / ".venv" / "bin" / "python"
DB_FILE = ROOT_DIR / "artifacts" / "aas_hub.db"
LOG_FILE = ROOT_DIR / "artifacts" / "hub.log"
HUB_CONSOLE_LOG = ROOT_DIR / "artifacts" / "hub_console.log"
ICON_FILE = ROOT_DIR / "artifacts" / "aas_hub.ico"

# Simple crash/error logging
TRAY_LOG = ROOT_DIR / "artifacts" / "tray.log"
TRAY_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_exception(prefix: str, exc: Exception):
    """Append exceptions to tray log for diagnostics."""
    try:
        with TRAY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}Z] {prefix}: {exc}\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        pass

# Prefer compiled Hub executable when present (fallback to Python)
HUB_EXE_CANDIDATES = [
    ROOT_DIR / "AAS Hub.exe",
    ROOT_DIR / "dist" / "AAS Hub.exe",
]
if os.getenv("AAS_FORCE_PYTHON"):
    HUB_EXE = None
else:
    HUB_EXE = next((p for p in HUB_EXE_CANDIDATES if p.exists()), None)

# Load Dashboard URL from environment or use default
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5174")

# Handoff Paths
HANDOFF_TO_DIR = ROOT_DIR / "artifacts" / "handoff" / "to_codex"
HANDOFF_FROM_DIR = ROOT_DIR / "artifacts" / "handoff" / "from_codex"
REPORTS_DIR = ROOT_DIR / "artifacts" / "handoff" / "reports"

# Ensure handoff directories exist
HANDOFF_TO_DIR.mkdir(parents=True, exist_ok=True)
HANDOFF_FROM_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def create_icon():
    """Create letter A icon for the system tray matching desktop icon."""
    # Try to load high-quality icon first
    if ICON_FILE.exists():
        try:
            return Image.open(ICON_FILE)
        except Exception:
            pass

    size = 64  # Tray icon size
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Solid indigo background circle
    draw.ellipse([0, 0, size - 1, size - 1], fill=(67, 56, 202))
    
    # Draw a bold letter "A"
    margin = int(size * 0.15)
    letter_width = size - (2 * margin)
    letter_height = int(size * 0.7)
    top = int(size * 0.15)
    left = margin
    
    # Letter A as a triangle outline
    peak_x = size // 2
    peak_y = top
    left_bottom = (left, top + letter_height)
    right_bottom = (left + letter_width, top + letter_height)
    
    # Outer triangle
    draw.polygon([
        (peak_x, peak_y),
        left_bottom,
        right_bottom
    ], fill='white')
    
    # Inner triangle (cut out to make it hollow)
    inner_offset = int(size * 0.12)
    draw.polygon([
        (peak_x, peak_y + inner_offset * 1.5),
        (left_bottom[0] + inner_offset, left_bottom[1] - inner_offset),
        (right_bottom[0] - inner_offset, right_bottom[1] - inner_offset)
    ], fill=(67, 56, 202))
    
    # Cross bar for A
    bar_y = top + int(letter_height * 0.6)
    bar_thickness = int(size * 0.08)
    bar_left = left + int(letter_width * 0.25)
    bar_right = left + int(letter_width * 0.75)
    draw.rectangle([
        bar_left, bar_y,
        bar_right, bar_y + bar_thickness
    ], fill='white')
    
    return img


def check_prerequisites():
    """Check if environment is ready to start Hub."""
    issues = []
    
    # Check virtual environment
    if not PYTHON_EXE.exists():
        issues.append("Virtual environment not found at .venv\\")
    
    # Check .env file
    if not ENV_FILE.exists():
        issues.append(".env file not found")
    
    # Check/create artifacts directory
    artifacts_dir = ROOT_DIR / "artifacts"
    if not artifacts_dir.exists():
        try:
            artifacts_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create artifacts directory: {e}")
    
    # Rotate large log files
    if LOG_FILE.exists():
        try:
            log_size_mb = LOG_FILE.stat().st_size / (1024 * 1024)
            if log_size_mb > 100:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                archive_log = ROOT_DIR / "artifacts" / f"hub_{timestamp}.log"
                LOG_FILE.rename(archive_log)
        except Exception:
            pass
    
    return issues


def clear_zombie_processes():
    """Kill any zombie processes holding Hub ports."""
    killed = []
    
    try:
        # Check port 50051 (gRPC)
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        for line in result.stdout.split('\n'):
            if ":50051" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pid = int(parts[-1])
                    # Check if it's a Python process
                    proc_check = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", 
                         f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if "python" in proc_check.stdout.lower():
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                     capture_output=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                        killed.append(f"port 50051 (PID {pid})")
                        time.sleep(0.5)
            
            elif ":8000" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pid = int(parts[-1])
                    proc_check = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", 
                         f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if "python" in proc_check.stdout.lower():
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                     capture_output=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                        killed.append(f"port 8000 (PID {pid})")
                        time.sleep(0.5)
    except Exception:
        pass
    
    # Clean stale PID file
    if PID_FILE.exists():
        pid = get_pid()
        if pid:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", 
                 f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode != 0:
                try:
                    PID_FILE.unlink()
                    killed.append("stale PID file")
                except Exception:
                    pass
    
    return killed


def get_pid():
    """Robustly read PID from file, handling various encodings."""
    try:
        if not PID_FILE.exists():
            return None
        
        # Read PID file as bytes to handle potential encoding issues from PowerShell's Out-File
        content = PID_FILE.read_bytes()
        
        # Try to decode as UTF-16 (common for PowerShell Out-File) or UTF-8
        try:
            if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
                pid_text = content.decode('utf-16').strip()
            else:
                pid_text = content.decode('utf-8').strip()
        except UnicodeDecodeError:
            pid_text = content.decode('latin-1').strip()

        # Extract only digits
        pid_text = ''.join(filter(str.isdigit, pid_text))
        if not pid_text:
            return None
            
        return int(pid_text)
    except Exception:
        return None


def is_hub_running():
    """Check if Hub is running by reading PID file and checking process."""
    try:
        pid = get_pid()
        if not pid:
            return False
        
        # Check if process exists (Windows)
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # If process doesn't exist, clean up stale PID file
        if result.returncode != 0:
            try:
                PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
            return False
            
        return True
    except Exception:
        return False


def start_hub(icon):
    """Start the AAS Hub with validation and cleanup."""
    try:
        # Check prerequisites
        issues = check_prerequisites()
        if issues:
            icon.notify("Cannot Start Hub", "\n".join(issues[:3]))
            return
        
        # Clear zombie processes
        killed = clear_zombie_processes()
        if killed:
            icon.notify("Cleaned up zombies", "\n".join(killed[:3]))
            time.sleep(1)
        
        # Start Hub directly; capture early startup errors without opening a console.
        log_handle = None
        try:
            log_handle = open(HUB_CONSOLE_LOG, "ab", buffering=0)
        except Exception:
            log_handle = None

        stdout_target = log_handle if log_handle else subprocess.DEVNULL
        stderr_target = log_handle if log_handle else subprocess.DEVNULL

        if HUB_EXE and HUB_EXE.exists():
            cmd = [str(HUB_EXE)]
        else:
            cmd = [str(PYTHON_EXE), "-u", "hub.py"]  # -u for unbuffered output

        creation_flags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creation_flags |= subprocess.CREATE_NO_WINDOW
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creation_flags |= subprocess.DETACHED_PROCESS

        process = subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR),
            env={
                **os.environ,
                "PYTHONPATH": str(ROOT_DIR),
                # Flag so Hub only runs when launched by the tray controller
                "AAS_LAUNCHED_VIA_TRAY": "1",
            },
            stdout=stdout_target,
            stderr=stderr_target,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags
        )
        if log_handle:
            log_handle.close()
        
        # Save PID
        PID_FILE.write_text(str(process.pid))
        
        # Wait and verify startup
        time.sleep(3)
        
        if is_hub_running():
            icon.notify(
                "AAS Hub Started",
                f"PID: {process.pid}\nWeb: http://localhost:8000\ngRPC: localhost:50051"
            )
        else:
            icon.notify("Hub Startup Issue", f"Process started but may have crashed.\nCheck: {LOG_FILE}")
            
    except Exception as e:
        log_exception("start_hub", e)
        icon.notify("Failed to start Hub", str(e))


def stop_hub(icon):
    """Stop the AAS Hub."""
    try:
        pid = get_pid()
        if not pid:
            icon.notify("Hub Not Running", "No PID file found")
            return
        
        # Check if process exists
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        time.sleep(1)
        
        # Clean up PID file
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        
        icon.notify("AAS Hub Stopped", f"Hub shut down (was PID {pid})")
    except Exception as e:
        icon.notify("Failed to stop Hub", str(e))


def restart_hub(icon):
    """Restart the AAS Hub."""
    try:
        pid = get_pid()
        if pid:
            icon.notify("Restarting Hub", "Stopping current instance...")
            stop_hub(icon)
            time.sleep(2)
        
        start_hub(icon)
    except Exception as e:
        icon.notify("Failed to restart Hub", str(e))


def show_status(icon):
    """Show Hub status."""
    try:
        pid = get_pid()
        if pid and is_hub_running():
            icon.notify("AAS Hub Status", f"Running (PID: {pid})\nWeb: http://localhost:8000\ngRPC: localhost:50051")
        else:
            icon.notify("AAS Hub Status", "Not Running")
    except Exception as e:
        icon.notify("Status Check Failed", str(e))


def open_dashboard(icon):
    """Open the Mission Control dashboard in default browser."""
    try:
        webbrowser.open(DASHBOARD_URL)
    except Exception as e:
        icon.notify("Failed to open dashboard", str(e))


def open_logs(icon):
    """Open the Hub log file."""
    log_file = ROOT_DIR / "artifacts" / "hub.log"
    try:
        if log_file.exists():
            os.startfile(log_file)
        else:
            icon.notify("No logs found", "Log file does not exist yet")
    except Exception as e:
        icon.notify("Failed to open logs", str(e))


def open_project_folder(icon):
    """Open the project root folder in explorer."""
    try:
        os.startfile(ROOT_DIR)
    except Exception as e:
        icon.notify("Error", f"Failed to open folder: {e}")


def edit_env(icon):
    """Open .env file for editing."""
    try:
        if ENV_FILE.exists():
            os.startfile(ENV_FILE)
        else:
            icon.notify("Error", ".env file not found")
    except Exception as e:
        icon.notify("Error", f"Failed to open .env: {e}")


# --- Handoff Integration ---

class HandoffHandler(FileSystemEventHandler):
    def __init__(self, icon, message):
        self.icon = icon
        self.message = message

    def on_created(self, event):
        if not event.is_directory:
            self.icon.notify("Handoff Detected", self.message)

def get_latest_file(directory):
    files = list(directory.glob("*"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def copy_latest_prompt(icon):
    latest = get_latest_file(HANDOFF_TO_DIR)
    if not latest:
        icon.notify("Handoff", "No prompt found in to_codex.")
        return
    
    try:
        text = latest.read_text(encoding="utf-8")
        pyperclip.copy(text)
        icon.notify("Handoff", "Copied latest prompt to clipboard.")
    except Exception as e:
        icon.notify("Handoff Error", f"Failed to copy: {e}")

def run_import(icon):
    def do_import():
        try:
            # Using dotnet toolkit as in original HandoffTray
            process = subprocess.Popen(
                ["dotnet", "run", "--project", "MaelstromToolkit/MaelstromToolkit.csproj", "--", "handoff", "import", "--out", "artifacts/handoff/reports"],
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                icon.notify("Handoff", "Import completed. Check CODEX_REPORT.md in reports.")
            else:
                icon.notify("Handoff Error", f"Import failed (exit {process.returncode})")
        except Exception as e:
            icon.notify("Handoff Error", f"Import exception: {e}")
    
    threading.Thread(target=do_import, daemon=True).start()

def open_reports(icon):
    try:
        os.startfile(REPORTS_DIR)
    except Exception as e:
        icon.notify("Error", f"Failed to open reports: {e}")

def send_latest_prompt_api(icon):
    latest = get_latest_file(HANDOFF_TO_DIR)
    if not latest:
        icon.notify("Handoff", "No prompt found in to_codex.")
        return
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        icon.notify("Handoff Error", "OPENAI_API_KEY env var is missing.")
        return

    try:
        content = latest.read_text(encoding="utf-8")
        # Extract fenced block
        matches = re.findall(r"```(.*?)```", content, re.DOTALL)
        if not matches:
            icon.notify("Handoff Error", "No fenced code block found.")
            return
        
        fenced = f"```{matches[0]}```"
        
        # Redact secrets
        secret_patterns = re.compile(r"(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AIza[0-9A-Za-z\-_]{20,}|BEGIN RSA PRIVATE KEY|BEGIN PRIVATE KEY)", re.IGNORECASE)
        redacted = secret_patterns.sub("[REDACTED]", fenced)
        if secret_patterns.search(fenced):
            redacted += "\n\n[Note: content redacted before send]"

        # Use notification instead of messagebox for non-blocking flow
        icon.notify("Handoff", "Sending latest block to OpenAI API...")

        def do_send():
            try:
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": redacted}],
                        "max_tokens": 512
                    },
                    timeout=30
                )
                
                if resp.status_code == 200:
                    body = resp.json()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = REPORTS_DIR / f"OPENAI_RESPONSE_{timestamp}.md"
                    
                    stamped = f"# OpenAI Response\nTimestamp (UTC): {datetime.utcnow().isoformat()}\nModel: {model}\n\n{json.dumps(body, indent=2)}\n"
                    out_path.write_text(stamped, encoding="utf-8")
                    
                    icon.notify("Handoff", f"Saved response to {out_path.name}")
                else:
                    icon.notify("Handoff Error", f"API error {resp.status_code}")
            except Exception as e:
                icon.notify("Handoff Error", f"API send exception: {e}")

        threading.Thread(target=do_send, daemon=True).start()

    except Exception as e:
        icon.notify("Handoff Error", str(e))

# --- End Handoff Integration ---


def setup(icon):
    """Setup callback when tray icon is ready."""
    icon.visible = True
    
    # Auto-start Hub when tray initializes so server always runs under controller
    if not is_hub_running():
        start_hub(icon)


def exit_app(icon):
    """Exit the tray application."""
    try:
        if is_hub_running():
            stop_hub(icon)
    except Exception:
        pass
    icon.visible = False
    icon.stop()


def create_menu(icon):
    """Create the context menu."""
    running = is_hub_running()

    return pystray.Menu(
        item(
            "🚀 AAS Hub",
            lambda: None,
            enabled=False
        ),
        pystray.Menu.SEPARATOR,
        item(
            "▶️  Start Hub",
            lambda: start_hub(icon),
            enabled=not running
        ),
        item(
            "⏸️  Stop Hub",
            lambda: stop_hub(icon),
            enabled=running
        ),
        item(
            "🔄 Restart Hub",
            lambda: restart_hub(icon),
            enabled=running
        ),
        pystray.Menu.SEPARATOR,
        item(
            "📊 Mission Control",
            lambda: open_dashboard(icon)
        ),
        item(
            "📋 View Logs",
            lambda: open_logs(icon)
        ),
        item(
            "ℹ️  Status",
            lambda: show_status(icon)
        ),
        pystray.Menu.SEPARATOR,
        item(
            "📝 Handoff",
            pystray.Menu(
                item("📋 Copy Latest Prompt", lambda: copy_latest_prompt(icon)),
                item("🚀 Send Latest to API", lambda: send_latest_prompt_api(icon)),
                item("📥 Run Handoff Import", lambda: run_import(icon)),
                item("📂 Open Reports", lambda: open_reports(icon))
            )
        ),
        pystray.Menu.SEPARATOR,
        item(
            "📂 Open Project Folder",
            lambda: open_project_folder(icon)
        ),
        item(
            "⚙️  Edit .env",
            lambda: edit_env(icon)
        ),
        pystray.Menu.SEPARATOR,
        item(
            "❌ Exit",
            lambda: exit_app(icon)
        )
    )


def main():
    """Main entry point for the tray application."""
    sys.excepthook = lambda exc_type, exc, tb: log_exception("unhandled", exc)

    try:
        icon = pystray.Icon(
            "aas_hub",
            create_icon(),
            "AAS Hub"
        )
        
        # Set initial menu
        icon.menu = create_menu(icon)
        
        # Start Handoff Watchers
        to_handler = HandoffHandler(icon, "New HANDOFF_TO_CODEX detected.")
        from_handler = HandoffHandler(icon, "New RESULT.md detected.")
        
        observer = Observer()
        observer.schedule(to_handler, str(HANDOFF_TO_DIR), recursive=False)
        observer.schedule(from_handler, str(HANDOFF_FROM_DIR), recursive=False)
        observer.start()
        
        # Update menu dynamically every 5 seconds
        def update_menu():
            try:
                while icon.visible:
                    time.sleep(5)
                    if icon.visible:
                        icon.menu = create_menu(icon)
            except Exception as e:
                log_exception("update_menu", e)
        
        threading.Thread(target=update_menu, daemon=True).start()
        
        # Show initial status
        if is_hub_running():
            icon.notify("AAS Hub Tray", "Hub is running")
        else:
            icon.notify("AAS Hub Tray", "Hub is not running - click to start")
        
        icon.run(setup=setup)
    except Exception as e:
        log_exception("main", e)
        raise
    finally:
        try:
            observer.stop()
            observer.join()
        except Exception:
            pass


if __name__ == "__main__":
    main()
