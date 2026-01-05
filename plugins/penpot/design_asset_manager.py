"""Design asset storage and retrieval manager."""

from loguru import logger
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import asyncio


class DesignAssetManager:
    """Handles storage and retrieval of design assets."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._assets: Dict[str, Any] = {}
        logger.info(f"DesignAssetManager initialized with storage: {storage_path}")
    
    async def load_assets(self) -> Dict[str, Any]:
        """Load assets from disk storage."""
        try:
            asset_file = self.storage_path / "assets.json"
            
            if asset_file.exists():
                async with asyncio.Lock():
                    with open(asset_file, 'r', encoding='utf-8') as f:
                        self._assets = json.load(f)
                
                logger.info(f"Loaded {len(self._assets)} assets from storage")
            else:
                logger.debug("No existing asset storage found")
            
            return self._assets
            
        except Exception as e:
            logger.error(f"Failed to load assets: {e}")
            return {}
    
    async def save_assets(self, assets: Dict[str, Any]) -> bool:
        """Save assets to disk storage."""
        try:
            asset_file = self.storage_path / "assets.json"
            
            async with asyncio.Lock():
                with open(asset_file, 'w', encoding='utf-8') as f:
                    json.dump(assets, f, indent=2)
            
            self._assets = assets
            logger.info(f"Saved {len(assets)} assets to storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save assets: {e}")
            return False
    
    def get_asset(self, asset_id: str) -> Optional[Any]:
        """Retrieve a specific asset by ID."""
        return self._assets.get(asset_id)
    
    def get_assets_by_type(self, asset_type: str) -> List[Any]:
        """Retrieve all assets of a specific type."""
        return [
            asset for asset in self._assets.values()
            if asset.get('type') == asset_type
        ]
    
    def update_asset(self, asset_id: str, asset_data: Any) -> bool:
        """Update a specific asset."""
        try:
            self._assets[asset_id] = asset_data
            logger.debug(f"Updated asset {asset_id} in memory")
            return True
        except Exception as e:
            logger.error(f"Failed to update asset {asset_id}: {e}")
            return False
