import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from core.managers import ManagerHub
from core.ws_manager import setup_websocket_routes, manager as ws_manager

def create_app(hub: ManagerHub) -> FastAPI:
    app = FastAPI(title="AAS Mission Control")
    auth_token = os.getenv("AAS_API_TOKEN")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def enforce_token(request: Request, call_next):
        if auth_token and request.url.path not in ("/health",):
            provided = request.headers.get("x-aas-token")
            if not provided:
                auth_header = request.headers.get("authorization", "")
                if auth_header.lower().startswith("bearer "):
                    provided = auth_header.split(" ", 1)[1]
            if provided != auth_token:
                raise HTTPException(status_code=401, detail="Invalid or missing token")
        response = await call_next(request)
        return response

    # WebSocket routes
    setup_websocket_routes(app)
    hub.ws = ws_manager

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
            await hub.ws.broadcast({
                "event_type": "CONFIG_UPDATED",
                "key": "lm_studio_url",
                "value": url,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })
        
        logger.info(f"LM Studio URL updated to {url}")
        
        return {"url": url, "message": "LM Studio URL updated successfully"}

    @app.get("/config/all")
    async def get_all_config():
        """Get all public configuration."""
        import os
        ngrok_configured = bool(hub.config.ngrok_auth_token or hub.config.ngrok_authtoken)
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
            "encryption_enabled": os.getenv("AAS_ENCRYPTION_KEY") is not None
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
            await hub.ws.broadcast({
                "event_type": "CONFIG_UPDATED",
                "key": key,
                "value": value,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })
            
        logger.info(f"Config updated: {key} = {value}")
        return {"key": key, "value": value, "message": "Configuration updated successfully"}

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
            "cost_savings": savings
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
            ConfigRepository.set(session, "batch_auto_monitor", enabled, value_type="bool")
        
        # Broadcast event
        if hub.ws:
            await hub.ws.broadcast({
                "event_type": "AUTO_MONITOR_TOGGLED",
                "enabled": enabled,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })
        
        logger.info(f"Batch auto-monitor {'enabled' if enabled else 'disabled'} (runtime toggle)")
        
        return {
            "enabled": enabled,
            "message": f"Auto-monitor {'enabled' if enabled else 'disabled'}. Change is active immediately."
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
                await hub.ws.broadcast({
                    "event_type": "BATCH_SUBMITTED",
                    "batch_id": batch_id,
                    "task_count": len(unbatched),
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })
            
            return {
                "batch_id": batch_id,
                "tasks_submitted": len(unbatched),
                "task_ids": [t["id"] for t in unbatched]
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
                await hub.ws.broadcast({
                    "event_type": "PATCH_APPLIED",
                    "target": result["target"],
                    "type": result["type"],
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })
                
            return result
        except Exception as e:
            logger.error(f"Patch application failed: {e}")
            return {"success": False, "error": str(e)}

    @app.get("/patch/status")
    async def patch_status():
        """Get status of live patching system."""
        return hub.patch.get_status()

    return app
