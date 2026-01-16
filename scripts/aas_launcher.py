"""
AAS Launcher - wraps preflight, workspace prep, and Hub start/stop helpers.

Usage examples:
  python scripts/aas_launcher.py launch           # prep + preflight + start
  python scripts/aas_launcher.py launch --no-clean-temp --no-kill-zombies
  python scripts/aas_launcher.py status
  python scripts/aas_launcher.py stop
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import psutil
from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
HUB_LOG = ARTIFACTS_DIR / "hub.log"
PID_FILE = ARTIFACTS_DIR / "hub.pid"

# Ensure workspace modules are importable even when launched from elsewhere.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ensure_artifact_dirs() -> None:
    """Create required artifact directories."""
    targets = [
        ARTIFACTS_DIR,
        ARTIFACTS_DIR / "guild",
        ARTIFACTS_DIR / "batch",
    ]
    for path in targets:
        path.mkdir(parents=True, exist_ok=True)


def rotate_log(max_mb: int = 100) -> Optional[Path]:
    """
    Rotate hub.log if it exceeds max_mb. Returns archive path when rotated.
    """
    if not HUB_LOG.exists():
        return None
    size_mb = HUB_LOG.stat().st_size / (1024 * 1024)
    if size_mb <= max_mb:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = ARTIFACTS_DIR / f"hub_{timestamp}.log"
    HUB_LOG.replace(archive)
    return archive


def stale_pid_cleanup() -> Optional[int]:
    """
    Remove stale PID file and return PID if it was stale.
    """
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        PID_FILE.unlink(missing_ok=True)
        return None
    if psutil.pid_exists(pid):
        return None
    PID_FILE.unlink(missing_ok=True)
    return pid


def find_listener_pids(ports: Iterable[int]) -> List[int]:
    """Return process IDs listening on any of the given ports."""
    pids = set()
    for conn in psutil.net_connections(kind="inet"):
        if (
            conn.laddr
            and conn.status == psutil.CONN_LISTEN
            and conn.laddr.port in ports
        ):
            if conn.pid:
                pids.add(conn.pid)
    return sorted(pids)


def kill_pids(pids: Iterable[int]) -> List[int]:
    """Kill the provided PIDs, returning the ones terminated."""
    killed = []
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            killed.append(pid)
        except Exception as e:
            logger.warning(f"Failed to kill PID {pid}: {e}")
    return killed


def clean_temp_files(delete: bool = True) -> int:
    """
    Remove simple temp files (pattern-based) to avoid heavy scans.
    Returns count removed.
    """
    patterns = ("temp_", "tmp_", ".tmp", "~", ".bak", ".write_test")
    removed = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
        ]
        for name in files:
            if any(pat in name for pat in patterns):
                path = Path(root) / name
                try:
                    if delete:
                        path.unlink()
                    removed += 1
                except Exception:
                    continue
    return removed


def pick_python_executable() -> Path:
    """
    Prefer workspace venv Python. Fall back to current interpreter.
    """
    if sys.platform.startswith("win"):
        candidates = [
            PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
            Path(sys.executable),
        ]
    else:
        candidates = [
            PROJECT_ROOT / ".venv" / "bin" / "python",
            Path(sys.executable),
            PROJECT_ROOT
            / ".venv"
            / "Scripts"
            / "python.exe",  # last resort on WSL if bin missing
        ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def run_preflight(web_host: str = "0.0.0.0", web_port: int = 8000):
    """
    Run the existing preflight and return the result object.
    """
    from core.config import load_config
    from core.preflight import run_preflight

    config = load_config()
    result = run_preflight(
        config=config, workspace_root=PROJECT_ROOT, web_host=web_host, web_port=web_port
    )
    result.log()
    if result.issues:
        raise SystemExit("Preflight failed; see issues above.")
    return result


def start_hub(python_exe: Path, inline_tray: bool = False) -> int:
    """
    Start hub.py detached and return the child PID.
    """
    env = os.environ.copy()
    env.setdefault("AAS_PREFLIGHT_REEXEC", "1")
    if inline_tray:
        env["AAS_INLINE_TRAY"] = "1"

    proc = subprocess.Popen(
        [str(python_exe), "hub.py"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 15.0) -> bool:
    """Wait for a TCP port to start listening."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.5)
    return False


def do_launch(args: argparse.Namespace) -> None:
    ensure_artifact_dirs()

    archive = rotate_log(max_mb=args.log_max_mb)
    if archive:
        logger.info(f"Rotated hub.log to {archive.name}")

    stale = stale_pid_cleanup()
    if stale:
        logger.info(f"Removed stale PID file (pid {stale})")

    if args.clean_temp:
        removed = clean_temp_files(delete=True)
        logger.info(f"Removed {removed} temp files (pattern-based)")

    if args.kill_zombies:
        zombies = find_listener_pids(ports=[50051, 8000])
        if zombies:
            killed = kill_pids(zombies)
            logger.info(f"Killed listeners on ports 50051/8000: {killed}")

    preflight_result = run_preflight(web_port=args.web_port)
    ipc_port = preflight_result.ipc_port
    web_port = preflight_result.web_port
    preferred_python = preflight_result.preferred_python
    warnings = preflight_result.warnings
    actions = preflight_result.actions
    if warnings:
        for w in warnings:
            logger.warning(w)
    if actions:
        for a in actions:
            logger.info(a)

    python_exe = preferred_python or pick_python_executable()
    pid = start_hub(python_exe, inline_tray=args.inline_tray)
    PID_FILE.write_text(str(pid), encoding="utf-8")
    logger.success(f"AAS Hub launching with PID {pid} using {python_exe}")

    if args.wait:
        attempts = max(1, args.wait_retries)
        web_ready = ipc_ready = False
        for attempt in range(1, attempts + 1):
            web_ready = wait_for_port(
                web_port, host="127.0.0.1", timeout=args.wait_timeout
            )
            ipc_ready = wait_for_port(
                ipc_port, host="127.0.0.1", timeout=args.wait_timeout
            )
            if web_ready and ipc_ready:
                break
            if attempt < attempts:
                time.sleep(args.wait_interval)
        if web_ready and ipc_ready:
            logger.info(f"Web server responding on port {web_port}; IPC on {ipc_port}")
        else:
            logger.error(
                f"Readiness timed out after {attempts} attempts (web_ready={web_ready}, ipc_ready={ipc_ready}); check artifacts/hub.log"
            )
            raise SystemExit(1)


def do_status() -> None:
    if PID_FILE.exists():
        pid = PID_FILE.read_text(encoding="utf-8").strip()
        running = psutil.pid_exists(int(pid))
        status = "running" if running else "stopped"
        print(f"Hub {status} (pid {pid})")
    else:
        print("Hub not running (no PID file)")


def do_stop() -> None:
    if not PID_FILE.exists():
        print("No PID file found; nothing to stop.")
        return
    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    if psutil.pid_exists(pid):
        try:
            psutil.Process(pid).terminate()
            print(f"Sent terminate to PID {pid}")
        except Exception as e:
            print(f"Failed to stop PID {pid}: {e}")
    PID_FILE.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AAS Launcher (prep + preflight + hub start)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    launch = sub.add_parser(
        "launch", help="Prep workspace, run preflight, and start the Hub"
    )
    launch.add_argument(
        "--no-clean-temp", action="store_true", help="Skip temp file cleanup"
    )
    launch.add_argument(
        "--no-kill-zombies",
        action="store_true",
        help="Skip killing listeners on 50051/8000",
    )
    launch.add_argument(
        "--inline-tray", action="store_true", help="Start tray inline if available"
    )
    launch.add_argument(
        "--wait", action="store_true", help="Wait for web server to come up"
    )
    launch.add_argument(
        "--wait-timeout",
        type=float,
        default=15.0,
        help="Seconds to wait when --wait is set",
    )
    launch.add_argument(
        "--wait-retries", type=int, default=3, help="Number of readiness retry attempts"
    )
    launch.add_argument(
        "--wait-interval",
        type=float,
        default=2.0,
        help="Seconds between readiness retries",
    )
    launch.add_argument(
        "--log-max-mb", type=int, default=100, help="Rotate hub.log above this size"
    )
    launch.add_argument(
        "--web-port",
        type=int,
        default=8000,
        help="Port to probe when waiting for readiness",
    )

    sub.add_parser("status", help="Show Hub status via PID file")
    sub.add_parser("stop", help="Stop Hub using PID file")
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "launch":
        args.clean_temp = not args.no_clean_temp
        args.kill_zombies = not args.no_kill_zombies
        do_launch(args)
    elif args.command == "status":
        do_status()
    elif args.command == "stop":
        do_stop()


if __name__ == "__main__":
    main()
