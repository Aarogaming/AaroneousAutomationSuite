"""DevToys plugin configuration."""

from pydantic import BaseModel, Field
from pathlib import Path


class DevToysConfig(BaseModel):
    """Configuration for DevToys SDK Extensions."""
    
    enabled: bool = Field(
        default=True,
        description="Enable DevToys plugin"
    )
    sdk_path: Path = Field(
        ...,
        description="Path to DevToys SDK installation"
    )
    max_concurrent_tasks: int = Field(
        default=5,
        description="Maximum concurrent tasks"
    )
    timeout: int = Field(
        default=30,
        description="Task timeout in seconds"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level for DevToys operations"
    )
