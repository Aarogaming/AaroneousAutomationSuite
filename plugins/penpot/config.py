"""Penpot plugin configuration."""

from pydantic import BaseModel, Field, SecretStr


class PenpotConfig(BaseModel):
    """Configuration for Penpot Design System integration."""
    
    api_key: SecretStr = Field(..., description="Penpot API key")
    api_url: str = Field(
        default="https://design.penpot.app/api",
        description="Penpot API base URL"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching of design assets"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache time-to-live in seconds"
    )
    sync_interval: int = Field(
        default=300,
        description="Asset synchronization interval in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum API retry attempts"
    )
