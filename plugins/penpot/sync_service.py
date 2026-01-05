"""Asset synchronization service."""

from loguru import logger
import asyncio
from typing import Optional
from .penpot_plugin import PenpotPlugin
from .design_asset_manager import DesignAssetManager
from .event_dispatcher import EventDispatcher


class SyncService:
    """Ensures design assets are synchronized with AAS components."""
    
    def __init__(
        self,
        plugin: PenpotPlugin,
        asset_manager: DesignAssetManager,
        event_dispatcher: EventDispatcher,
        sync_interval: int = 300
    ):
        self.plugin = plugin
        self.asset_manager = asset_manager
        self.event_dispatcher = event_dispatcher
        self.sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        logger.info(f"SyncService initialized with {sync_interval}s interval")
    
    async def start(self):
        """Start the synchronization service."""
        if self._running:
            logger.warning("SyncService already running")
            return
        
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("SyncService started")
    
    async def stop(self):
        """Stop the synchronization service."""
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SyncService stopped")
    
    async def _sync_loop(self):
        """Main synchronization loop."""
        while self._running:
            try:
                await self._perform_sync()
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _perform_sync(self):
        """Perform a single synchronization cycle."""
        try:
            logger.debug("Starting asset synchronization")
            
            # Fetch latest assets from Penpot
            assets = await self.plugin.get_design_assets()
            
            if not assets:
                logger.warning("No assets fetched from Penpot")
                return
            
            # Convert list to dict for storage
            asset_dict = {asset['id']: asset for asset in assets}
            
            # Save to local storage
            await self.asset_manager.save_assets(asset_dict)
            
            # Dispatch sync event
            await self.event_dispatcher.dispatch_event(
                'assets_synced',
                {'count': len(assets), 'timestamp': asyncio.get_event_loop().time()}
            )
            
            logger.info(f"Synchronized {len(assets)} assets successfully")
            
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            await self.event_dispatcher.dispatch_event(
                'sync_failed',
                {'error': str(e)}
            )
    
    async def sync_now(self):
        """Trigger an immediate synchronization."""
        logger.info("Manual sync triggered")
        await self._perform_sync()
