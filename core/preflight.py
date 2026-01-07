import importlib
import os
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from loguru import logger


@dataclass
class PreflightResult:
    web_host: str
    web_port: int
    ipc_port: int
    ipc_ports: List[int]
    warnings: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    preferred_python: Optional[Path] = None
    needs_reexec: bool = False

    def log(self) -> None:
        for msg in self.warnings:
            logger.warning(msg)
        for msg in self.actions:
            logger.info(msg)
        if self.issues:
            for msg in self.issues:
                logger.critical(msg)


def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if a TCP port can be bound."""
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
        return True
    except OSError:
        return False


def _find_free_port(start: int, attempts: int = 10) -> Optional[int]:
    """Find the first available port starting at `start` within `attempts` range."""
    for offset in range(attempts):
        candidate = start + offset
        if _is_port_free(candidate):
            return candidate
    return None


def _dedupe_preserve(seq: Iterable[int]) -> List[int]:
    seen = set()
    result = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _check_required_modules(modules: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Return (missing, loaded) module names for workspace dependencies."""
    missing = []
    loaded = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            loaded.append(mod)
        except Exception:
            missing.append(mod)
    return missing, loaded


def run_preflight(
    config,
    workspace_root: Optional[Path] = None,
    web_host: str = "0.0.0.0",
    web_port: int = 8000,
) -> PreflightResult:
    """
    Perform startup preflight checks and apply safe self-healing defaults.

    The checker prefers workspace-scoped dependencies (local venv, requirements.txt)
    and ensures ports are available before servers start.
    """
    root = workspace_root or Path.cwd()
    result = PreflightResult(
        web_host=web_host,
        web_port=web_port,
        ipc_port=config.ipc_port,
        ipc_ports=[],
    )

    # Workspace dependency hygiene
    venv_dir = root / ".venv"
    exe_path = Path(sys.executable).resolve()
    current_prefix = Path(sys.prefix).resolve()
    preferred_python = None

    # Detect if we are already using the workspace venv even if python resolves to /usr/bin (common on WSL).
    if venv_dir.exists() and current_prefix == venv_dir.resolve():
        preferred_python = exe_path
    else:
        if os.name == "nt":
            candidates = [
                venv_dir / "Scripts" / "python.exe",
                venv_dir / "bin" / "python",  # fallback if using WSL-style venv
            ]
        else:
            candidates = [
                venv_dir / "bin" / "python",
                venv_dir / "Scripts" / "python.exe",  # avoid choosing Windows exe on WSL, but keep as last resort
            ]
        for candidate in candidates:
            if candidate.exists():
                preferred_python = candidate
                break

        if venv_dir.exists() and venv_dir.resolve() not in exe_path.parents:
            result.warnings.append(
                f"Running interpreter {exe_path} is outside workspace venv; prefer {venv_dir} for bundled deps."
            )
            if preferred_python:
                result.actions.append(f"Re-launching with workspace interpreter is recommended: {preferred_python}")
                result.preferred_python = preferred_python
                result.needs_reexec = True
            else:
                result.actions.append(f"Activate {venv_dir} to ensure workspace-managed packages are used.")

    # Dependency presence (lightweight import check)
    required_modules = ("fastapi", "uvicorn", "grpc", "pydantic", "sqlalchemy", "loguru", "psutil")
    missing, _ = _check_required_modules(required_modules)
    if missing:
        req_file = root / "requirements.txt"
        result.issues.append(f"Missing Python modules: {', '.join(missing)}")
        result.actions.append(f"Install workspace deps: {root / '.venv' / 'Scripts' / 'python.exe'} -m pip install -r {req_file}")

    # Required files/directories
    for path in (root / "requirements.txt", root / ".env"):
        if not path.exists():
            result.warnings.append(f"{path.name} not found at {path} (will fall back to environment variables only).")
    artifacts_root = root / "artifacts"
    handoff_root = root / config.artifact_dir
    for path in (artifacts_root, handoff_root):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            result.issues.append(f"Cannot create workspace path {path}: {e}")

    # Ports: Web
    resolved_web = web_port
    if not _is_port_free(resolved_web):
        fallback = _find_free_port(resolved_web + 1, attempts=10)
        if fallback:
            result.warnings.append(f"Web port {resolved_web} busy; shifting to {fallback}.")
            result.actions.append("Set AAS_WEB_PORT to an open port to avoid auto-shift.")
            resolved_web = fallback
        else:
            result.issues.append(f"No available web port near {web_port} (checked +10).")
    result.web_port = resolved_web

    # Ports: IPC list (primary + env + fallbacks)
    env_ipc_ports = []
    env_raw = os.getenv("AAS_IPC_PORTS")
    if env_raw:
        for raw in env_raw.split(","):
            try:
                env_ipc_ports.append(int(raw.strip()))
            except ValueError:
                result.warnings.append(f"Ignoring invalid AAS_IPC_PORTS entry: {raw}")
    ipc_candidates = _dedupe_preserve(
        [config.ipc_port] + env_ipc_ports + [50052, 50053]
    )

    available_ipc = [p for p in ipc_candidates if _is_port_free(p)]
    if not available_ipc:
        fallback_ipc = _find_free_port(config.ipc_port + 1, attempts=10)
        if fallback_ipc:
            available_ipc.append(fallback_ipc)
            result.warnings.append(f"IPC port {config.ipc_port} busy; using fallback {fallback_ipc}.")
            result.actions.append("Set AAS_IPC_PORT or AAS_IPC_PORTS to a free port to avoid auto-shift.")
        else:
            result.issues.append(f"No available IPC ports near {config.ipc_port} (checked +10).")
            available_ipc = ipc_candidates

    result.ipc_port = available_ipc[0]
    result.ipc_ports = available_ipc

    return result
