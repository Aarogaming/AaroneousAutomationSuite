from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from core.managers import ManagerHub
from core.ipc.websockets import setup_websocket_routes

def create_app(hub: ManagerHub) -> FastAPI:
    app = FastAPI(title="AAS Mission Control")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket routes
    setup_websocket_routes(app)

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

    # ===== Batch Operations =====
    
    @app.get("/batch/status")
    async def batch_status():
        """Get all active batches and their status."""
        if not hub.batch_manager:
            return {"error": "Batch API not configured"}
        
        active = hub.batch_manager.list_active_batches()
        return {
            "active_batches": active,
            "total": len(active),
            "configured": True,
            "auto_monitor_enabled": hub.config.batch_auto_monitor
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
        hub.db.config.set("batch_auto_monitor", str(enabled).lower())
        
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
