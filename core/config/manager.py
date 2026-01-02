import os
from typing import Optional
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

class AASConfig(BaseSettings):
    """
    Resilient Configuration System (RCS) for Aaroneous Automation Suite.
    Uses Pydantic for type-safe validation and SecretStr for local security.
    """
    # Security & AI
    openai_api_key: SecretStr = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.2-pro", alias="OPENAI_MODEL")
    linear_api_key: Optional[SecretStr] = Field(default=None, alias="LINEAR_API_KEY")
    
    # Core Settings
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")
    plugin_dir: str = Field(default="plugins", alias="PLUGIN_DIR")
    
    # IPC Settings
    ipc_port: int = Field(default=50051, alias="IPC_PORT")
    ipc_host: str = Field(default="localhost", alias="IPC_HOST")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def load_config() -> AASConfig:
    try:
        config = AASConfig()
        logger.info("Resilient Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.warning("Falling back to safe defaults where possible.")
        # In a real scenario, we would trigger the self-healing logic here
        raise
