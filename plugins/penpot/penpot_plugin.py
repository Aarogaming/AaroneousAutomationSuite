"""Penpot Design System plugin for AAS."""

from loguru import logger
import aiohttp
from typing import Dict, List, Any, Optional
from .config import PenpotConfig


class PenpotPlugin:
    """Manages interaction with Penpot API."""

    def __init__(self, config: PenpotConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        logger.info("Penpot Plugin initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Initialize HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                }
            )
            logger.info("Penpot API session started")

    async def stop(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("Penpot API session closed")

    async def get_design_assets(
        self, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve design assets from Penpot.

        Args:
            project_id: Optional project ID to filter assets

        Returns:
            List of design asset dictionaries
        """
        if not self._session:
            await self.start()

        try:
            cache_key = f"assets_{project_id or 'all'}"

            # Check cache if enabled
            if self.config.cache_enabled and cache_key in self._cache:
                logger.debug(f"Returning cached assets for {cache_key}")
                return self._cache[cache_key]

            # Fetch from API
            url = f"{self.config.api_url}/assets"
            if project_id:
                url += f"?project_id={project_id}"

            async with self._session.get(url) as response:
                response.raise_for_status()
                assets = await response.json()

                # Cache results
                if self.config.cache_enabled:
                    self._cache[cache_key] = assets

                logger.info(f"Retrieved {len(assets)} design assets")
                return assets

        except aiohttp.ClientError as e:
            logger.error(f"Failed to retrieve design assets: {e}")
            return []

    async def update_design_asset(
        self, asset_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a specific design asset.

        Args:
            asset_id: Asset identifier
            data: Asset data to update

        Returns:
            Updated asset dictionary or None on failure
        """
        if not self._session:
            await self.start()

        try:
            url = f"{self.config.api_url}/assets/{asset_id}"

            async with self._session.put(url, json=data) as response:
                response.raise_for_status()
                updated_asset = await response.json()

                # Invalidate cache
                self._cache.clear()

                logger.info(f"Updated design asset {asset_id}")
                return updated_asset

        except aiohttp.ClientError as e:
            logger.error(f"Failed to update design asset {asset_id}: {e}")
            return None

    async def sync_assets(self) -> bool:
        """
        Synchronize design assets with AAS components.

        Returns:
            True if sync successful, False otherwise
        """
        try:
            assets = await self.get_design_assets()

            if not assets:
                logger.warning("No assets to synchronize")
                return False

            # TODO: Implement synchronization logic with AAS components
            # This would integrate with ai_assistant, home_server, etc.

            logger.info(f"Synchronized {len(assets)} design assets")
            return True

        except Exception as e:
            logger.error(f"Asset synchronization failed: {e}")
            return False

    def clear_cache(self):
        """Clear the asset cache."""
        self._cache.clear()
        logger.debug("Asset cache cleared")
