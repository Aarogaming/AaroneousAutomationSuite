"""
AAS Hub System Tray Application
Provides a taskbar icon for monitoring and controlling the AAS Hub.
"""
import subprocess
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import threading
import time
import webbrowser

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
PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
DB_FILE = ROOT_DIR / "artifacts" / "aas_hub.db"
LOG_FILE = ROOT_DIR / "artifacts" / "hub.log"
DASHBOARD_URL = "http://localhost:5174"


def create_icon():
    """Create letter A icon for the system tray matching desktop icon."""
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
            text=True
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
                                     capture_output=True)
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
                                     capture_output=True)
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
        
        # Start Hub directly - use PIPE to keep process detached but alive
        process = subprocess.Popen(
            [str(PYTHON_EXE), "-u", "core/main.py"],  # -u for unbuffered output
            cwd=str(ROOT_DIR),
            env={**os.environ, 'PYTHONPATH': str(ROOT_DIR)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        )
        
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
            capture_output=True
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
            subprocess.run(["notepad", str(log_file)])
        else:
            icon.notify("No logs found", "Log file does not exist yet")
    except Exception as e:
        icon.notify("Failed to open logs", str(e))


def setup(icon):
    """Setup callback when tray icon is ready."""
    icon.visible = True


def exit_app(icon):
    """Exit the tray application."""
    icon.visible = False
    icon.stop()


def create_menu(icon):
    """Create the context menu."""
    running = is_hub_running()
    
    return pystray.Menu(
        item(
            '🚀 AAS Hub',
            lambda: None,
            enabled=False
        ),
        pystray.Menu.SEPARATOR,
        item(
            '▶️  Start Hub',
            lambda: start_hub(icon),
            enabled=not running
        ),
        item(
            '⏸️  Stop Hub',
            lambda: stop_hub(icon),
            enabled=running
        ),
        item(
            '🔄 Restart Hub',
            lambda: restart_hub(icon),
            enabled=running
        ),
        pystray.Menu.SEPARATOR,
        item(
            '📊 Mission Control',
            lambda: open_dashboard(icon)
        ),
        item(
            '📋 View Logs',
            lambda: open_logs(icon)
        ),
        item(
            'ℹ️  Status',
            lambda: show_status(icon)
        ),
        pystray.Menu.SEPARATOR,
        item(
            '❌ Exit',
            lambda: exit_app(icon)
        )
    )


def main():
    """Main entry point for the tray application."""
    icon = pystray.Icon(
        "aas_hub",
        create_icon(),
        "AAS Hub"
    )
    
    # Set initial menu
    icon.menu = create_menu(icon)
    
    # Update menu dynamically every 5 seconds
    def update_menu():
        try:
            while icon.visible:
                time.sleep(5)
                if icon.visible:
                    icon.menu = create_menu(icon)
        except Exception:
            pass
    
    threading.Thread(target=update_menu, daemon=True).start()
    
    # Show initial status
    if is_hub_running():
        icon.notify("AAS Hub Tray", "Hub is running")
    else:
        icon.notify("AAS Hub Tray", "Hub is not running - click to start")
    
    icon.run(setup=setup)


if __name__ == "__main__":
    main()
