"""
Lightweight plugin registry and loader utilities.

Provides a single source of truth for available plugins, their locations,
and enabled state without scattering import logic across the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import importlib.util
import json
from loguru import logger


@dataclass
class PluginMeta:
    name: str
    path: Path
    enabled: bool = True
    description: str = ""


DEFAULT_PLUGINS: Dict[str, PluginMeta] = {
    "ai_assistant": PluginMeta(
        name="ai_assistant",
        path=Path("plugins/ai_assistant/assistant.py"),
        description="Core AI assistant utilities",
    ),
    "home_assistant": PluginMeta(
        name="home_assistant",
        path=Path("plugins/home_assistant/connector.py"),
        description="Home Assistant bridge",
    ),
    "dev_studio": PluginMeta(
        name="dev_studio",
        path=Path("plugins/dev_studio/studio.py"),
        description="Dev studio helpers and audits",
    ),
}


def _load_manifest_plugins(root: Path) -> Dict[str, PluginMeta]:
    """Load plugins defined by aas-plugin.json manifests under the root plugins directory."""
    registry: Dict[str, PluginMeta] = {}
    if not root.exists():
        return registry
    for manifest in root.glob("*/aas-plugin.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            name = data.get("name") or manifest.parent.name
            enabled = bool(data.get("enabled", True))
            path_value = data.get("entry") or data.get("path")
            path = manifest.parent / path_value if path_value else manifest.parent
            registry[name] = PluginMeta(
                name=name,
                path=Path(path),
                enabled=enabled,
                description=data.get("description", ""),
            )
        except Exception as e:
            logger.warning(f"Failed to load plugin manifest {manifest}: {e}")
    return registry


def get_plugin_registry(extra: Optional[Dict[str, PluginMeta]] = None) -> List[PluginMeta]:
    """Return the current registry, merging any extra entries."""
    registry = DEFAULT_PLUGINS.copy()
    manifest_plugins = _load_manifest_plugins(Path("plugins"))
    registry.update(manifest_plugins)
    if extra:
        registry.update(extra)
    # Only return enabled plugins
    return [p for p in registry.values() if p.enabled]


def safe_import_plugin(plugin: PluginMeta):
    """
    Try to import a plugin module from the provided path.
    Returns the module or None on failure, logging a warning instead of raising.
    """
    try:
        if not plugin.path.exists():
            logger.warning(f"Plugin path missing: {plugin.path}")
            return None
        spec = importlib.util.spec_from_file_location(plugin.name, plugin.path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            logger.debug(f"Loaded plugin module: {plugin.name} ({plugin.path})")
            return module
    except Exception as e:
        logger.warning(f"Failed to load plugin {plugin.name}: {e}")
    return None


def summarize_plugins(plugins: List[PluginMeta]) -> List[dict]:
    """Return metadata summaries for UI/CLI consumption."""
    return [
        {
            "name": p.name,
            "path": str(p.path),
            "enabled": p.enabled,
            "description": p.description,
        }
        for p in plugins
    ]
