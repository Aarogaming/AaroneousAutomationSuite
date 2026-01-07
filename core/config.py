from typing import Optional, Any, Literal, Dict
from pydantic import SecretStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path
import json
import os


def find_workspace_env(start: Optional[Path] = None) -> Optional[Path]:
    """
    Locate the topmost .env file in the workspace (root-first search).
    Returns the highest-level .env starting from the provided path (defaults to CWD).
    """
    start_path = (start or Path.cwd()).resolve()
    for candidate in reversed([start_path] + list(start_path.parents)):
        env_file = candidate / ".env"
        if env_file.exists():
            return env_file
    fallback = Path(__file__).resolve().parent.parent / ".env"
    return fallback if fallback.exists() else None

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
    batch_auto_monitor: bool = Field(
        default=False,
        alias="BATCH_AUTO_MONITOR",
        description="Enable automatic background batch monitoring and submission"
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
    
    # ==================== OpenAI Responses API ====================
    responses_api_enabled: bool = Field(
        default=True,
        alias="RESPONSES_API_ENABLED",
        description="Enable the new OpenAI Responses API"
    )
    enable_web_search: bool = Field(
        default=True,
        alias="ENABLE_WEB_SEARCH",
        description="Enable native web search tool"
    )
    enable_file_search: bool = Field(
        default=True,
        alias="ENABLE_FILE_SEARCH",
        description="Enable native file search tool"
    )
    enable_code_interpreter: bool = Field(
        default=True,
        alias="ENABLE_CODE_INTERPRETER",
        description="Enable native code interpreter tool"
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

    # ==================== Distribution & Privacy ====================
    is_private_version: bool = Field(
        default=False,
        alias="IS_PRIVATE_VERSION",
        description="Whether this is the private version with full features"
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
    lm_studio_url: Optional[str] = Field(
        default="http://localhost:1234",
        alias="LM_STUDIO_URL",
        description="LM Studio API endpoint for local LLM"
    )
    
    # ==================== ngrok Development Tunneling ====================
    ngrok_enabled: bool = Field(
        default=False,
        alias="NGROK_ENABLED",
        description="Enable ngrok tunneling for development"
    )
    ngrok_auth_token: Optional[SecretStr] = Field(
        default=None,
        alias="NGROK_AUTH_TOKEN",
        description="ngrok authentication token"
    )
    ngrok_authtoken: Optional[str] = Field(
        default=None,
        alias="NGROK_AUTHTOKEN",
        description="Legacy ngrok token (deprecated, use NGROK_AUTH_TOKEN)"
    )
    ngrok_region: str = Field(
        default="us",
        alias="NGROK_REGION",
        description="ngrok region (us, eu, ap, au, sa, jp, in)"
    )
    ngrok_port: int = Field(
        default=8000,
        alias="NGROK_PORT",
        ge=1024,
        le=65535,
        description="Local port to expose via ngrok"
    )
    
    # ==================== Penpot Design System ====================
    penpot_enabled: bool = Field(
        default=False,
        alias="PENPOT_ENABLED",
        description="Enable Penpot design system integration"
    )
    penpot_api_key: Optional[SecretStr] = Field(
        default=None,
        alias="PENPOT_API_KEY",
        description="Penpot API authentication key"
    )
    penpot_api_url: str = Field(
        default="https://design.penpot.app/api",
        alias="PENPOT_API_URL",
        description="Penpot API base URL"
    )
    
    # ==================== DevToys SDK Extensions ====================
    devtoys_enabled: bool = Field(
        default=False,
        alias="DEVTOYS_ENABLED",
        description="Enable DevToys SDK extensions"
    )
    devtoys_sdk_path: Optional[str] = Field(
        default=None,
        alias="DEVTOYS_SDK_PATH",
        description="Path to DevToys SDK installation"
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

    @model_validator(mode='after')
    def normalize_ngrok_tokens(self):
        """Backfill NGROK_AUTH_TOKEN from legacy NGROK_AUTHTOKEN if needed."""
        if self.ngrok_auth_token is None and self.ngrok_authtoken:
            self.ngrok_auth_token = SecretStr(self.ngrok_authtoken)
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    @classmethod
    def from_db(cls, db_manager=None) -> "AASConfig":
        """
        Load configuration from database, with DB values taking precedence over environment variables.
        """
        from core.db_manager import get_db_manager
        from core.db_repositories import ConfigRepository
        
        db_manager = db_manager or get_db_manager()
        
        # 1. Start with env-based config
        config = cls() # type: ignore
        
        # 2. Override with DB values
        try:
            with db_manager.get_session() as session:
                entries = ConfigRepository.get_all(session)
                for entry in entries:
                    key_str = str(entry.key)
                    value = ConfigRepository.get(session, key_str)
                    if value is None and bool(entry.is_secret):
                        existing = getattr(config, key_str, None)
                        if hasattr(existing, "get_secret_value"):
                            secret_value = existing.get_secret_value()
                            if secret_value:
                                ConfigRepository.set(
                                    session,
                                    key_str,
                                    secret_value,
                                    value_type=str(entry.value_type),
                                    description=str(entry.description) if entry.description else None,
                                    is_secret=True
                                )
                                value = secret_value
                                logger.debug(f"Re-encrypted secret config for {key_str}")
                    if value is not None and hasattr(config, key_str):
                        setattr(config, key_str, value)
                        logger.debug(f"Overrode {key_str} from database")
        except Exception as e:
            logger.warning(f"Failed to load configs from DB: {e}")

        return config

def load_config(use_db: bool = True) -> AASConfig:
    """
    Loads and validates the AAS configuration from environment variables and .env file.
    Optionally merges with configuration from the database.
    
    Minimal mode: set AAS_MINIMAL_CONFIG=1 to bypass DB overrides and load only
    environment/.env values. Useful for lightweight CLI tools and troubleshooting.
    
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
        env_path = find_workspace_env()
        if env_path:
            load_dotenv(dotenv_path=env_path, override=False)
            try:
                # Keep Pydantic aware of the env file we loaded for consistency
                AASConfig.model_config["env_file"] = str(env_path)
            except Exception:
                logger.debug(f"Could not set env_file on AASConfig model_config (path={env_path})")
            logger.debug(f"Loaded environment variables from {env_path}")
        else:
            load_dotenv(override=False)
        if os.getenv("AAS_MINIMAL_CONFIG"):
            use_db = False
        if use_db:
            config = AASConfig.from_db()
        else:
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
            if not os.getenv("OPENAI_API_KEY"):
                logger.critical("Cannot proceed without OPENAI_API_KEY")
                raise SystemExit(1)
            raise  # Re-raise if we have the key but other validation failed
        except SystemExit:
            raise
        except Exception:
            logger.critical("Could not recover from configuration errors")
            raise SystemExit(1)
