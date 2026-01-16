import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from core.managers import ManagerHub
from core.ws_manager import setup_websocket_routes, manager as ws_manager
from core.security.auth import AuthGate
from core.coordination.routes import build_coordination_router


def create_app(hub: ManagerHub) -> FastAPI:
    app = FastAPI(
        title="AAS Mission Control",
        openapi_tags=[
            {"name": "Maelstrom", "description": "Project Maelstrom API endpoints."}
        ],
    )
    auth_gate = AuthGate(hub.config)
    snapshot_cache = {
        "data": None,
        "updated": None,
        "source": None,
        "valid": None,
        "errors": [],
    }
    wizwiki_zone_cache = {"data": None, "path": None}
    schema_path = (
        Path(__file__).resolve().parents[1] / "docs" / "maelstrom_snapshot.schema.json"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def enforce_token(request: Request, call_next):
        if not auth_gate.is_exempt(request.url.path):
            auth_gate.authenticate_request(request)
        response = await call_next(request)
        return response

    # WebSocket routes
    setup_websocket_routes(app, auth_gate=auth_gate)
    hub.ws = ws_manager
    app.include_router(build_coordination_router(hub))

    @app.get("/health")
    async def health():
        return hub.get_health_summary()

    @app.get("/tasks")
    async def list_tasks():
        return hub.tasks.get_all_tasks()

    @app.get("/agents")
    async def list_agents():
        if not hub.collaboration:
            return []
        return hub.collaboration.get_active_agents()

    def _resolve_snapshot_path() -> Path | None:
        snapshot_path = os.getenv("MAELSTROM_SNAPSHOT_PATH")
        candidates = [
            Path(snapshot_path) if snapshot_path else None,
            Path("Maelstrom/src/ProjectMaelstrom/Scripts/.cache/snapshot.json"),
            Path("Maelstrom/src/Scripts/.cache/snapshot.json"),
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _resolve_wizwiki_zones_path() -> Path | None:
        env_path = os.getenv("MAELSTROM_WIZWIKI_PATH")
        candidates = [
            Path(env_path) if env_path else None,
        ]
        scripts_root = os.getenv("MAELSTROM_SCRIPTS_ROOT")
        if scripts_root:
            candidates.append(
                Path(scripts_root)
                / "Library"
                / "WizWikiAPI-main"
                / "wizwiki_zones.json"
            )
        candidates.extend(
            [
                Path(
                    "Maelstrom/src/ProjectMaelstrom/Scripts/Library/WizWikiAPI-main/wizwiki_zones.json"
                ),
                Path(
                    "Maelstrom/src/Scripts/Library/WizWikiAPI-main/wizwiki_zones.json"
                ),
            ]
        )
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _load_wizwiki_zones() -> dict:
        path = _resolve_wizwiki_zones_path()
        if not path:
            return {}
        cached = wizwiki_zone_cache["data"]
        if cached is not None and wizwiki_zone_cache["path"] == str(path):
            return cached
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            wizwiki_zone_cache["data"] = {}
            wizwiki_zone_cache["path"] = str(path)
            return {}
        zones = {}
        if isinstance(raw, list):
            for entry in raw:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("Zone") or entry.get("zone")
                if not name:
                    continue
                zones[str(name).lower()] = entry
        wizwiki_zone_cache["data"] = zones
        wizwiki_zone_cache["path"] = str(path)
        return zones

    def _refresh_snapshot_cache() -> None:
        path = _resolve_snapshot_path()
        if not path:
            return
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        errors = _validate_snapshot_schema(snapshot)
        snapshot_cache["data"] = snapshot
        snapshot_cache["source"] = str(path)
        snapshot_cache["updated"] = snapshot.get("CapturedUtc")
        snapshot_cache["errors"] = errors
        snapshot_cache["valid"] = len(errors) == 0

    def _validate_snapshot_schema(snapshot: dict) -> list[str]:
        errors = []
        try:
            if schema_path.exists():
                import jsonschema

                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(instance=snapshot, schema=schema)
                return []
        except ImportError:
            pass
        except Exception as exc:
            errors.append(f"schema_validation_failed: {exc}")
            return errors

        if "CapturedUtc" in snapshot and not isinstance(snapshot["CapturedUtc"], str):
            errors.append("CapturedUtc must be a string")
        for key in ("WindowPresent", "HasFocus"):
            if key in snapshot and not isinstance(snapshot[key], bool):
                errors.append(f"{key} must be a boolean")
        if "Warnings" in snapshot and not isinstance(snapshot["Warnings"], list):
            errors.append("Warnings must be a list")
        return errors

    async def _snapshot_poller() -> None:
        interval_ms = int(os.getenv("MAELSTROM_SNAPSHOT_POLL_MS", "2000"))
        if interval_ms <= 0:
            return
        while True:
            _refresh_snapshot_cache()
            await asyncio.sleep(interval_ms / 1000.0)

    @app.on_event("startup")
    async def start_snapshot_poller():
        asyncio.create_task(_snapshot_poller())

    @app.on_event("startup")
    async def start_coordination():
        try:
            await hub.coordination.start()
        except Exception as exc:
            logger.warning(f"Coordination startup failed: {exc}")

    @app.get("/maelstrom/status", tags=["Maelstrom"])
    async def maelstrom_status():
        """Expose latest Maelstrom snapshot status for UI ribbons."""
        if snapshot_cache["data"] is None:
            _refresh_snapshot_cache()

        snapshot_data = snapshot_cache["data"]
        if not snapshot_data:
            zones = _load_wizwiki_zones()
            return {
                "success": False,
                "sync": "NO DATA",
                "zone": os.getenv("MAELSTROM_ZONE", "N/A"),
                "zone_world": None,
                "zones_available": sorted(zones.keys()) if zones else [],
                "guards": "UNKNOWN",
                "source": "none",
                "warnings": [],
                "warning_count": 0,
                "stale": True,
                "age_seconds": None,
            }

        raw_warnings = [str(w) for w in (snapshot_data.get("Warnings") or [])]
        warnings = [w.lower() for w in raw_warnings]
        window_present = snapshot_data.get("WindowPresent", False)
        has_focus = snapshot_data.get("HasFocus", False)
        zone_label = (
            snapshot_data.get("Zone")
            or snapshot_data.get("zone")
            or os.getenv("MAELSTROM_ZONE", "N/A")
        )

        if not window_present:
            sync = "WINDOW MISSING"
        elif not has_focus:
            sync = "FOCUS LOST"
        elif any("resolution" in w or "mismatch" in w for w in warnings):
            sync = "RESOLUTION MISMATCH"
        else:
            sync = "IN SYNC"

        guard_map = {
            "health": "HEALTH",
            "mana": "MANA",
            "energy": "ENERGY",
            "gold": "GOLD",
            "potion": "POTIONS",
            "roi": "OCR",
            "ocr": "OCR",
        }
        guards = []
        for keyword, label in guard_map.items():
            if any(keyword in w for w in warnings):
                guards.append(label)

        updated = snapshot_data.get("CapturedUtc") or snapshot_cache["updated"]
        age_seconds = None
        stale = False
        try:
            from datetime import datetime, timezone

            if updated:
                updated_dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                age_seconds = (datetime.now(timezone.utc) - updated_dt).total_seconds()
                ttl_seconds = int(os.getenv("MAELSTROM_SNAPSHOT_TTL_SECONDS", "15"))
                stale = age_seconds > ttl_seconds
        except Exception:
            stale = False

        zones = _load_wizwiki_zones()
        zone_world = None
        if zone_label:
            match = zones.get(str(zone_label).lower())
            if match:
                zone_world = match.get("World") or match.get("world")

        return {
            "success": True,
            "sync": sync,
            "sync_state": _normalize_state(sync),
            "zone": zone_label,
            "zone_world": zone_world,
            "zones_available": sorted(zones.keys()) if zones else [],
            "guards": "OK" if not guards else ", ".join(sorted(set(guards))),
            "guards_state": "ok" if not guards else "triggered",
            "source": "snapshot",
            "updated": updated,
            "warnings": raw_warnings,
            "warning_count": len(raw_warnings),
            "stale": stale,
            "age_seconds": age_seconds,
            "schema_valid": snapshot_cache["valid"],
            "schema_errors": snapshot_cache["errors"],
        }

    def _resolve_script_library_path() -> Path | None:
        env_path = os.getenv("MAELSTROM_SCRIPT_LIBRARY_PATH")
        candidates = [
            Path(env_path) if env_path else None,
            Path("Maelstrom/src/ProjectMaelstrom/Scripts/Library"),
            Path("Maelstrom/src/Scripts/Library"),
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _resolve_scripts_root(library_path: Path | None) -> Path | None:
        env_path = os.getenv("MAELSTROM_SCRIPTS_ROOT")
        candidates = [
            Path(env_path) if env_path else None,
            library_path.parent if library_path else None,
            Path("Maelstrom/src/ProjectMaelstrom/Scripts"),
            Path("Maelstrom/src/Scripts"),
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _get_case(data: dict, *keys):
        for key in keys:
            if key in data:
                return data[key]
        return None

    def _resolve_maelstrom_source_root() -> Path | None:
        env_path = os.getenv("MAELSTROM_SOURCE_ROOT")
        candidates = [
            Path(env_path) if env_path else None,
            Path("Maelstrom/src/ProjectMaelstrom"),
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _resolve_plugins_root() -> Path | None:
        env_path = os.getenv("MAELSTROM_PLUGINS_PATH")
        candidates = [
            Path(env_path) if env_path else None,
            Path("Maelstrom/plugins"),
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _is_reference_name(name: str) -> bool:
        lowered = name.lower()
        return (
            "wizwalker" in lowered
            or "wizsdk" in lowered
            or "wizproxy" in lowered
            or "wizwiki" in lowered
            or "wizwad" in lowered
            or "wiz-packet" in lowered
            or "wad-reader" in lowered
            or "proto" in lowered
            or "sample" in lowered
            or "utilities" in lowered
            or "trivia" in lowered
            or "gallery" in lowered
        )

    def _derive_kind(manifest: dict) -> str:
        status = (manifest.get("status") or "").strip()
        if status:
            return status
        name = (manifest.get("name") or "").strip()
        if name and _is_reference_name(name):
            return "reference"
        source_url = (manifest.get("source_url") or "").strip()
        if source_url:
            return "external"
        return "native"

    def _normalize_state(value: str | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower().replace(" ", "_")

    def _load_manifest(manifest_path: Path) -> dict | None:
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(raw, dict):
            return None
        data = {}
        data["name"] = raw.get("name") or raw.get("Name")
        data["description"] = raw.get("description") or raw.get("Description")
        data["author"] = raw.get("author") or raw.get("Author")
        data["source_url"] = raw.get("sourceUrl") or raw.get("SourceUrl")
        data["status"] = raw.get("status") or raw.get("Status")
        data["entry_point"] = raw.get("entryPoint") or raw.get("EntryPoint")
        data["arguments"] = raw.get("arguments") or raw.get("Arguments")
        data["required_resolution"] = raw.get("requiredResolution") or raw.get(
            "RequiredResolution"
        )
        data["required_templates"] = raw.get("requiredTemplates") or raw.get(
            "RequiredTemplates"
        )
        return data

    @app.get("/maelstrom/scripts", tags=["Maelstrom"])
    async def maelstrom_scripts(client_id: str | None = None):
        """Expose script library inventory and status."""
        library_path = _resolve_script_library_path()
        if not library_path:
            return {
                "success": False,
                "source": "none",
                "scripts": [],
                "library_path": None,
            }

        scripts = []
        for script_dir in sorted(library_path.iterdir()):
            if not script_dir.is_dir():
                continue
            manifest_path = script_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            manifest = _load_manifest(manifest_path)
            if not manifest:
                continue

            validation_errors = []
            if not manifest.get("name"):
                validation_errors.append("Name is required")
            entry_point = manifest.get("entry_point")
            if not entry_point:
                validation_errors.append("Entry point is required")
            else:
                entry_full = script_dir / entry_point
                if not entry_full.exists():
                    validation_errors.append("Entry point missing")

            scripts.append(
                {
                    "name": manifest.get("name"),
                    "description": manifest.get("description"),
                    "author": manifest.get("author"),
                    "source_url": manifest.get("source_url"),
                    "status": manifest.get("status"),
                    "entry_point": entry_point,
                    "arguments": manifest.get("arguments"),
                    "required_resolution": manifest.get("required_resolution"),
                    "required_templates": manifest.get("required_templates"),
                    "manifest_path": str(manifest_path),
                    "root_path": str(script_dir),
                    "package": None,
                    "validation_errors": validation_errors,
                    "kind": _derive_kind(manifest),
                }
            )

        heartbeat = hub.get_maelstrom_heartbeat(client_id) or {}
        payload = heartbeat.get("payload") if isinstance(heartbeat, dict) else None
        if isinstance(payload, dict):
            snapshot = payload
        else:
            snapshot = heartbeat if isinstance(heartbeat, dict) else {}

        active_script = _get_case(snapshot, "activeScript", "ActiveScript")
        script_running = _get_case(snapshot, "scriptRunning", "ScriptRunning")
        current_session = None
        if active_script:
            current_session = {
                "script_name": active_script,
                "running": bool(script_running),
            }

        for entry in scripts:
            run_state = "Ready"
            if entry["validation_errors"]:
                run_state = "Needs setup"
            if active_script and entry.get("name") == active_script and script_running:
                run_state = "Running"
            entry["run_state"] = run_state
            entry["run_state_code"] = _normalize_state(run_state)

        from datetime import datetime, timezone

        return {
            "success": True,
            "source": "filesystem",
            "library_path": str(library_path),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": bool(os.getenv("MAELSTROM_DRY_RUN", "false").lower() == "true"),
            "player_preview_mode": bool(
                os.getenv("MAELSTROM_PLAYER_PREVIEW", "false").lower() == "true"
            ),
            "current_session": current_session,
            "scripts": scripts,
            "count": len(scripts),
        }

    @app.get("/maelstrom/macros", tags=["Maelstrom"])
    async def maelstrom_macros():
        """Expose available macro files."""
        library_path = _resolve_script_library_path()
        scripts_root = _resolve_scripts_root(library_path)
        if not scripts_root:
            return {
                "success": False,
                "source": "none",
                "macros": [],
                "macros_path": None,
            }

        macros_path = scripts_root / "Macros"
        macros = []
        if macros_path.exists():
            for macro_file in sorted(macros_path.glob("*.json")):
                try:
                    stat = macro_file.stat()
                    updated_at = (
                        __import__("datetime")
                        .datetime.fromtimestamp(
                            stat.st_mtime, __import__("datetime").timezone.utc
                        )
                        .isoformat()
                    )
                except Exception:
                    updated_at = None
                macros.append(
                    {
                        "name": macro_file.stem,
                        "path": str(macro_file),
                        "updated_at": updated_at,
                    }
                )

        return {
            "success": True,
            "source": "filesystem",
            "scripts_root": str(scripts_root),
            "macros_path": str(macros_path),
            "macros": macros,
            "count": len(macros),
        }

    @app.get("/maelstrom/settings", tags=["Maelstrom"])
    async def maelstrom_settings(client_id: str | None = None):
        """Expose Maelstrom policy/profile settings from heartbeat."""
        heartbeat = hub.get_maelstrom_heartbeat(client_id) or {}
        payload = heartbeat.get("payload") if isinstance(heartbeat, dict) else None
        if isinstance(payload, dict):
            snapshot = payload
        else:
            snapshot = heartbeat if isinstance(heartbeat, dict) else {}

        if not snapshot:
            return {
                "success": False,
                "source": "none",
                "settings": None,
            }

        return {
            "success": True,
            "source": "heartbeat",
            "settings": {
                "client_id": _get_case(snapshot, "ClientId", "clientId"),
                "profile": _get_case(snapshot, "Profile", "profile"),
                "policy_mode": _get_case(snapshot, "PolicyMode", "policyMode"),
                "policy_path": _get_case(snapshot, "PolicyPath", "policyPath"),
                "policy_loaded_utc": _get_case(
                    snapshot, "PolicyLoadedUtc", "policyLoadedUtc"
                ),
                "allow_live_automation": bool(
                    _get_case(snapshot, "AllowLiveAutomation", "allowLiveAutomation")
                ),
                "resolution": _get_case(snapshot, "Resolution", "resolution"),
            },
        }

    @app.get("/maelstrom/telemetry", tags=["Maelstrom"])
    async def maelstrom_telemetry(client_id: str | None = None):
        """Expose Maelstrom telemetry metrics from heartbeat."""
        heartbeat = hub.get_maelstrom_heartbeat(client_id) or {}
        payload = heartbeat.get("payload") if isinstance(heartbeat, dict) else None
        if isinstance(payload, dict):
            snapshot = payload
        else:
            snapshot = heartbeat if isinstance(heartbeat, dict) else {}

        if not snapshot:
            return {
                "success": False,
                "source": "none",
                "metrics": None,
            }

        from datetime import datetime, timezone

        return {
            "success": True,
            "source": "heartbeat",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "health": _get_case(snapshot, "Health", "health"),
                "mana": _get_case(snapshot, "Mana", "mana"),
                "energy": _get_case(snapshot, "Energy", "energy"),
                "gold": _get_case(snapshot, "Gold", "gold"),
            },
        }

    @app.get("/maelstrom/bots", tags=["Maelstrom"])
    async def maelstrom_bots():
        """Expose known bot definitions."""
        source_root = _resolve_maelstrom_source_root()
        if not source_root:
            return {
                "success": False,
                "source": "none",
                "bots": [],
            }

        def parse_bot(
            file_name: str, fallback_id: str, fallback_name: str
        ) -> dict | None:
            path = source_root / file_name
            if not path.exists():
                return None
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return None
            import re

            id_match = re.search(r'BotId\s*=>\s*"([^"]+)"', text)
            name_match = re.search(r'BotName\s*=>\s*"([^"]+)"', text)
            if not name_match:
                text_match = re.search(r'Text\s*=\s*"([^"]+)"', text)
                name_match = text_match
            return {
                "bot_id": id_match.group(1) if id_match else fallback_id,
                "name": name_match.group(1) if name_match else fallback_name,
                "source_file": str(path),
                "status": "unknown",
            }

        bots = []
        for entry in [
            ("HalfangFarmingBot.cs", "halfang-farming-bot", "Halfang Farming Bot"),
            ("BazaarReagentBot.cs", "bazaar-reagent-bot", "Bazaar Reagent Bot"),
            ("PetDanceBot.cs", "pet-dance-bot", "Wizard101 DanceBot"),
        ]:
            bot = parse_bot(*entry)
            if bot:
                bots.append(bot)

        return {
            "success": True,
            "source": "source_files",
            "bots": bots,
            "count": len(bots),
        }

    @app.get("/maelstrom/overlay", tags=["Maelstrom"])
    async def maelstrom_overlay(client_id: str | None = None):
        """Expose overlay widget metadata and snapshot state."""
        overlay_snapshot_path = os.getenv("MAELSTROM_OVERLAY_SNAPSHOT_PATH")
        snapshot_data = None
        if overlay_snapshot_path:
            candidate = Path(overlay_snapshot_path)
            try:
                if candidate.exists():
                    snapshot_data = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                snapshot_data = None

        heartbeat = hub.get_maelstrom_heartbeat(client_id) or {}
        payload = heartbeat.get("payload") if isinstance(heartbeat, dict) else None
        if isinstance(payload, dict):
            hb_snapshot = payload
        else:
            hb_snapshot = heartbeat if isinstance(heartbeat, dict) else {}

        if not snapshot_data:
            snapshot_data = {
                "TimestampUtc": __import__("datetime").datetime.utcnow().isoformat()
                + "Z",
                "Profile": _get_case(hb_snapshot, "Profile", "profile") or "Public",
                "Mode": _get_case(hb_snapshot, "PolicyMode", "policyMode")
                or "SimulationOnly",
                "AllowLiveAutomation": bool(
                    _get_case(hb_snapshot, "AllowLiveAutomation", "allowLiveAutomation")
                ),
                "LastExecutorStatus": "Unknown",
                "RecentActions": [],
                "LoadedPluginsCount": None,
                "BlockedPluginsCount": None,
            }

        plugins_root = _resolve_plugins_root()
        widgets = []
        if plugins_root:
            for manifest_path in plugins_root.rglob("plugin.manifest.json"):
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(manifest, dict):
                    continue
                capabilities = (
                    manifest.get("declaredCapabilities")
                    or manifest.get("DeclaredCapabilities")
                    or []
                )
                if "OverlayWidgets" not in capabilities:
                    continue
                widgets.append(
                    {
                        "plugin_id": manifest.get("pluginId")
                        or manifest.get("PluginId"),
                        "name": manifest.get("name") or manifest.get("Name"),
                        "version": manifest.get("version") or manifest.get("Version"),
                        "required_profile": manifest.get("requiredProfile")
                        or manifest.get("RequiredProfile"),
                        "manifest_path": str(manifest_path),
                    }
                )

        return {
            "success": True,
            "source": "snapshot" if overlay_snapshot_path else "heartbeat",
            "snapshot": snapshot_data,
            "widgets": widgets,
            "count": len(widgets),
        }

    @app.post("/maelstrom/heartbeat", tags=["Maelstrom"])
    async def maelstrom_heartbeat(request: Request):
        """Receive and store latest Maelstrom heartbeat payload."""
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        hub.set_maelstrom_heartbeat(payload)
        snapshot = payload.get("payload") if isinstance(payload, dict) else None
        if not isinstance(snapshot, dict):
            snapshot = payload if isinstance(payload, dict) else {}

        if hub.ws:
            from datetime import datetime, timezone

            try:
                await hub.ws.broadcast(
                    {
                        "event_type": "MAELSTROM_SCRIPT_UPDATE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "active_script": _get_case(
                            snapshot, "ActiveScript", "activeScript"
                        ),
                        "script_running": _get_case(
                            snapshot, "ScriptRunning", "scriptRunning"
                        ),
                    }
                )
                await hub.ws.broadcast(
                    {
                        "event_type": "MAELSTROM_SYNC_UPDATE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "sync_status": _get_case(snapshot, "SyncStatus", "syncStatus"),
                        "sync_message": _get_case(
                            snapshot, "SyncMessage", "syncMessage"
                        ),
                        "guards": _get_case(snapshot, "Guards", "guards"),
                        "zone": _get_case(snapshot, "Zone", "zone"),
                    }
                )
            except Exception as exc:
                logger.warning(f"Failed to broadcast Maelstrom heartbeat: {exc}")
        return {"success": True}

    # ===== Configuration =====

    @app.get("/config/lm-studio")
    async def get_lm_studio_config():
        """Get LM Studio configuration."""
        return {"url": hub.config.lm_studio_url}

    @app.post("/config/lm-studio")
    async def set_lm_studio_config(request: Request):
        """Update LM Studio URL."""
        body = await request.json()
        url = body.get("url")
        if not url:
            return {"error": "URL is required"}

        # Update config
        hub.config.lm_studio_url = url

        # Persist to database
        from core.db_repositories import ConfigRepository

        with hub.db.get_session() as session:
            ConfigRepository.set(session, "lm_studio_url", url)

        # Broadcast event
        if hub.ws:
            await hub.ws.broadcast(
                {
                    "event_type": "CONFIG_UPDATED",
                    "key": "lm_studio_url",
                    "value": url,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            )

        logger.info(f"LM Studio URL updated to {url}")

        return {"url": url, "message": "LM Studio URL updated successfully"}

    @app.get("/config/all")
    async def get_all_config():
        """Get all public configuration."""
        import os

        ngrok_configured = bool(
            hub.config.ngrok_auth_token or hub.config.ngrok_authtoken
        )
        return {
            "openai_model": hub.config.openai_model,
            "debug_mode": hub.config.debug_mode,
            "policy_mode": hub.config.policy_mode,
            "autonomy_level": hub.config.autonomy_level,
            "require_consent": hub.config.require_consent,
            "allow_screenshots": hub.config.allow_screenshots,
            "ollama_url": hub.config.ollama_url,
            "lm_studio_url": hub.config.lm_studio_url,
            "batch_auto_monitor": hub.config.batch_auto_monitor,
            "responses_api_enabled": hub.config.responses_api_enabled,
            "enable_web_search": hub.config.enable_web_search,
            "enable_file_search": hub.config.enable_file_search,
            "enable_code_interpreter": hub.config.enable_code_interpreter,
            "ngrok_enabled": hub.config.ngrok_enabled,
            "ngrok_region": hub.config.ngrok_region,
            "ngrok_port": hub.config.ngrok_port,
            "ngrok_configured": ngrok_configured,
            "encryption_enabled": os.getenv("AAS_ENCRYPTION_KEY") is not None,
        }

    @app.post("/config/update")
    async def update_config(request: Request):
        """Update any configuration key."""
        body = await request.json()
        key = body.get("key")
        value = body.get("value")

        if not key or value is None:
            return {"error": "Key and value are required"}

        if not hasattr(hub.config, key):
            return {"error": f"Invalid config key: {key}"}

        # Update runtime config
        setattr(hub.config, key, value)

        # Persist to database
        from core.db_repositories import ConfigRepository

        value_type = "string"
        if isinstance(value, bool):
            value_type = "bool"
        elif isinstance(value, int):
            value_type = "int"

        with hub.db.get_session() as session:
            ConfigRepository.set(session, key, value, value_type=value_type)

        # Broadcast event
        if hub.ws:
            await hub.ws.broadcast(
                {
                    "event_type": "CONFIG_UPDATED",
                    "key": key,
                    "value": value,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            )

        logger.info(f"Config updated: {key} = {value}")
        return {
            "key": key,
            "value": value,
            "message": "Configuration updated successfully",
        }

    # ===== Batch Operations =====

    @app.get("/batch/status")
    async def batch_status():
        """Get all active batches and their status."""
        if not hub.batch_manager:
            return {"error": "Batch API not configured"}

        active = hub.batch_manager.list_active_batches()

        # Calculate mock cost savings based on completed tasks
        # In a real scenario, we'd track tokens and compare pricing
        completed_tasks = 0
        for b in active:
            if b.get("status") == "completed":
                completed_tasks += b.get("request_counts", {}).get("completed", 0)

        savings = "50%" if completed_tasks > 0 else "0%"

        return {
            "active_batches": active,
            "total": len(active),
            "configured": True,
            "auto_monitor_enabled": hub.config.batch_auto_monitor,
            "cost_savings": savings,
        }

    @app.get("/batch/auto-monitor")
    async def get_auto_monitor():
        """Get auto-monitor status."""
        return {"enabled": hub.config.batch_auto_monitor}

    @app.post("/batch/auto-monitor")
    async def set_auto_monitor(request: Request):
        """Enable or disable batch auto-monitoring."""
        body = await request.json()
        enabled = body.get("enabled", False)

        # Update config
        hub.config.batch_auto_monitor = enabled

        # Persist to database
        from core.db_repositories import ConfigRepository

        with hub.db.get_session() as session:
            ConfigRepository.set(
                session, "batch_auto_monitor", enabled, value_type="bool"
            )

        # Broadcast event
        if hub.ws:
            await hub.ws.broadcast(
                {
                    "event_type": "AUTO_MONITOR_TOGGLED",
                    "enabled": enabled,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            )

        logger.info(
            f"Batch auto-monitor {'enabled' if enabled else 'disabled'} (runtime toggle)"
        )

        return {
            "enabled": enabled,
            "message": f"Auto-monitor {'enabled' if enabled else 'disabled'}. Change is active immediately.",
        }

    @app.get("/batch/{batch_id}")
    async def get_batch(batch_id: str):
        """Get detailed status of a specific batch."""
        if not hub.batch_manager:
            return {"error": "Batch API not configured"}

        try:
            status = hub.batch_manager.get_batch_status(batch_id)
            return status
        except Exception as e:
            return {"error": str(e)}

    @app.post("/batch/submit")
    async def submit_batch(request: Request):
        """Submit eligible tasks for batch processing."""
        if not hub.batch_manager:
            return {"error": "Batch API not configured"}

        body = await request.json()
        max_tasks = body.get("max_tasks", 10)

        # Find unbatched tasks
        unbatched = hub.tasks.find_unbatched_tasks(max_count=max_tasks)

        if not unbatched:
            return {"message": "No eligible tasks for batching", "count": 0}

        # Submit batch
        try:
            batch_id = await hub.tasks.batch_multiple_tasks(max_tasks=max_tasks)

            # Broadcast event
            if batch_id and hub.ws:
                await hub.ws.broadcast(
                    {
                        "event_type": "BATCH_SUBMITTED",
                        "batch_id": batch_id,
                        "task_count": len(unbatched),
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                    }
                )

            return {
                "batch_id": batch_id,
                "tasks_submitted": len(unbatched),
                "task_ids": [t["id"] for t in unbatched],
            }
        except Exception as e:
            logger.error(f"Batch submission failed: {e}")
            return {"error": str(e)}

    # ===== Live Patching =====

    @app.post("/patch/apply")
    async def apply_patch(request: Request):
        """Apply a live patch to the system."""
        body = await request.json()
        try:
            result = await hub.patch.apply_patch(body)

            # Broadcast event
            if result["success"] and hub.ws:
                await hub.ws.broadcast(
                    {
                        "event_type": "PATCH_APPLIED",
                        "target": result["target"],
                        "type": result["type"],
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Patch application failed: {e}")
            return {"success": False, "error": str(e)}

    @app.get("/patch/status")
    async def patch_status():
        """Get status of live patching system."""
        return hub.patch.get_status()

    return app
