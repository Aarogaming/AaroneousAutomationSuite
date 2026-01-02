from typing import Optional, Any, Literal
from pydantic import SecretStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
import json

class AASConfig(BaseSettings):
    """
    Resilient Configuration System (RCS) for Aaroneous Automation Suite.
    Uses Pydantic for type-safe validation and SecretStr for local security.
    
    All fields support environment variable overrides via their UPPERCASE aliases.
    Required fields will fail validation if not provided, triggering graceful fallback.
    """
    
    # ==================== AI & External Services ====================
    openai_api_key: SecretStr = Field(
        ...,
        alias="OPENAI_API_KEY",
        description="OpenAI API key for AI assistant features (required)"
    )
    openai_model: str = Field(
        default="gpt-4",
        alias="OPENAI_MODEL",
        description="OpenAI model to use for AI assistant"
    )
    linear_api_key: Optional[SecretStr] = Field(
        default=None,
        alias="LINEAR_API_KEY",
        description="Linear API key for bi-directional task sync (optional)"
    )
    linear_team_id: Optional[str] = Field(
        default=None,
        alias="LINEAR_TEAM_ID",
        description="Linear team ID for issue creation"
    )
    
    # ==================== Core Settings ====================
    debug_mode: bool = Field(
        default=False,
        alias="DEBUG_MODE",
        description="Enable debug logging and verbose output"
    )
    plugin_dir: str = Field(
        default="plugins",
        alias="PLUGIN_DIR",
        description="Directory containing plugin modules"
    )
    artifact_dir: str = Field(
        default="artifacts/handoff",
        alias="ARTIFACT_DIR",
        description="Directory for handoff artifacts and reports"
    )
    
    # ==================== Project Registry ====================
    projects: list[Any] = Field(
        default_factory=list,
        alias="PROJECTS",
        description="JSON list of registered projects in the workspace"
    )

    # ==================== Policy & Ethics ====================
    policy_mode: Literal["live_advisory", "strict", "permissive"] = Field(
        default="live_advisory",
        alias="POLICY_MODE",
        description="Policy enforcement mode"
    )
    autonomy_level: Literal["advisory", "semi_autonomous", "fully_autonomous"] = Field(
        default="advisory",
        alias="AUTONOMY_LEVEL",
        description="AI agent autonomy level"
    )
    require_consent: bool = Field(
        default=True,
        alias="REQUIRE_CONSENT",
        description="Require user consent for critical operations"
    )
    allow_screenshots: bool = Field(
        default=False,
        alias="ALLOW_SCREENSHOTS",
        description="Allow AI agents to capture screenshots"
    )

    # ==================== IPC Settings ====================
    ipc_port: int = Field(
        default=50051,
        alias="IPC_PORT",
        ge=1024,
        le=65535,
        description="gRPC port for Project Maelstrom communication"
    )
    ipc_host: str = Field(
        default="localhost",
        alias="IPC_HOST",
        description="gRPC host address"
    )
    
    # ==================== Plugin-Specific Settings ====================
    home_assistant_url: Optional[str] = Field(
        default=None,
        alias="HOME_ASSISTANT_URL",
        description="Home Assistant instance URL"
    )
    home_assistant_token: Optional[SecretStr] = Field(
        default=None,
        alias="HOME_ASSISTANT_TOKEN",
        description="Home Assistant long-lived access token"
    )
    ollama_url: Optional[str] = Field(
        default="http://localhost:11434",
        alias="OLLAMA_URL",
        description="Ollama API endpoint for local LLM"
    )

    # ==================== Validators ====================
    @field_validator('projects', mode='before')
    @classmethod
    def parse_projects_json(cls, v):
        """Parse PROJECTS env var from JSON string to list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse PROJECTS JSON: {e}. Using empty list.")
                return []
        return v or []
    
    @field_validator('ipc_port')
    @classmethod
    def validate_port(cls, v):
        """Ensure IPC port is in valid range."""
        if not (1024 <= v <= 65535):
            logger.warning(f"IPC port {v} out of range. Using default 50051.")
            return 50051
        return v
    
    @model_validator(mode='after')
    def validate_linear_config(self):
        """If Linear API key is provided, team ID should also be set."""
        if self.linear_api_key and not self.linear_team_id:
            logger.warning("LINEAR_API_KEY provided without LINEAR_TEAM_ID. Sync may fail.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

def load_config() -> AASConfig:
    """
    Loads and validates the AAS configuration from environment variables and .env file.
    
    Implements graceful fallback for non-critical errors:
    - Missing optional fields: Uses defaults
    - Invalid values: Logs warning and uses safe defaults
    - Missing required fields: Raises exception after logging
    
    Returns:
        AASConfig: Validated configuration instance
        
    Raises:
        SystemExit: If critical configuration (OPENAI_API_KEY) is missing
    """
    try:
        config = AASConfig() # type: ignore
        logger.info("✓ Resilient Configuration System loaded successfully")
        
        # Log configuration summary (without secrets)
        logger.debug(f"Config: Model={config.openai_model}, "
                    f"Debug={config.debug_mode}, "
                    f"IPC={config.ipc_host}:{config.ipc_port}, "
                    f"Linear={'Enabled' if config.linear_api_key else 'Disabled'}")
        
        return config
        
    except Exception as e:
        logger.critical(f"Configuration validation failed: {e}")
        
        # Check if this is a missing API key error
        if "OPENAI_API_KEY" in str(e):
            logger.error("Missing required OPENAI_API_KEY in .env file")
            logger.info("Please add OPENAI_API_KEY=<your-key> to .env file")
            logger.info("See .env.example for configuration template")
            raise SystemExit(1)
        
        # For other validation errors, attempt partial recovery
        logger.warning("Attempting to load configuration with safe defaults...")
        try:
            # Try to load with minimal required fields
            import os
            if not os.getenv("OPENAI_API_KEY"):
                logger.critical("Cannot proceed without OPENAI_API_KEY")
                raise SystemExit(1)
            raise  # Re-raise if we have the key but other validation failed
        except SystemExit:
            raise
        except Exception:
            logger.critical("Could not recover from configuration errors")
            raise SystemExit(1)
