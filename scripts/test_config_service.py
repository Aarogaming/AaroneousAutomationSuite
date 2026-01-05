import asyncio
import grpc
import json
from core.ipc.protos import bridge_pb2
from core.ipc.protos import bridge_pb2_grpc
from core.config.manager import load_config
from loguru import logger

async def test_config_service():
    # 1. Test local config loading (should pull from .env initially)
    config = load_config(use_db=False)
    logger.info(f"Initial local config (OpenAI Model): {config.openai_model}")

    # 2. Connect to gRPC server (assuming it's running or we start it)
    # For this test, we'll just use the repository directly to simulate the server logic
    # or try to connect if a server is active.
    
    from core.database.manager import get_db_manager
    from core.database.repositories import ConfigRepository
    
    db_manager = get_db_manager()
    
    logger.info("--- Testing Repository Directly ---")
    with db_manager.get_session() as session:
        # Set a config value
        ConfigRepository.set(session, "openai_model", "gpt-4-turbo-preview", value_type="string")
        ConfigRepository.set(session, "debug_mode", True, value_type="bool")
        ConfigRepository.set(session, "projects", ["ProjectA", "ProjectB"], value_type="json")
        ConfigRepository.set(session, "home_assistant_token", "super-secret-token", value_type="string", is_secret=True)

    # 3. Test loading config from DB
    config_db = load_config(use_db=True)
    logger.info(f"Config from DB (OpenAI Model): {config_db.openai_model}")
    logger.info(f"Config from DB (Debug Mode): {config_db.debug_mode}")
    logger.info(f"Config from DB (Projects): {config_db.projects}")
    
    # Verify secret decryption
    with db_manager.get_session() as session:
        secret_val = ConfigRepository.get(session, "home_assistant_token")
        logger.info(f"Decrypted Secret: {secret_val}")

    assert config_db.openai_model == "gpt-4-turbo-preview"
    assert config_db.debug_mode is True
    assert "ProjectA" in config_db.projects
    assert secret_val == "super-secret-token"
    
    logger.success("Config Service Verification Successful!")

if __name__ == "__main__":
    asyncio.run(test_config_service())
