"""
Test script for the enhanced Pydantic RCS configuration system.
Tests validation, defaults, and error handling.
"""

from core.config import load_config, AASConfig
from loguru import logger
import os
import sys


def test_basic_load():
    """Test basic configuration loading."""
    print("\n=== Test 1: Basic Configuration Load ===")
    try:
        config = load_config()
        print("✓ Config loaded successfully")
        print(f"  Model: {config.openai_model}")
        print(f"  Debug: {config.debug_mode}")
        print(f"  IPC: {config.ipc_host}:{config.ipc_port}")
        print(f"  Projects: {len(config.projects)}")
        print(f"  Linear: {'Enabled' if config.linear_api_key else 'Disabled'}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        raise


def test_field_types():
    """Test that field types are correctly enforced."""
    print("\n=== Test 2: Field Type Validation ===")
    try:
        config = load_config()

        # Check SecretStr fields
        assert hasattr(
            config.openai_api_key, "get_secret_value"
        ), "API key should be SecretStr"
        print("✓ SecretStr fields properly protected")

        # Check boolean fields
        assert isinstance(config.debug_mode, bool), "debug_mode should be bool"
        print("✓ Boolean fields correctly typed")

        # Check int fields
        assert isinstance(config.ipc_port, int), "ipc_port should be int"
        assert 1024 <= config.ipc_port <= 65535, "ipc_port should be in valid range"
        print("✓ Integer fields validated with constraints")

        # Check list fields
        assert isinstance(config.projects, list), "projects should be list"
        print("✓ List fields correctly parsed")

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


def test_defaults():
    """Test that default values are applied correctly."""
    print("\n=== Test 3: Default Values ===")
    try:
        config = load_config()

        # Check defaults that should exist
        assert config.plugin_dir == "plugins", "Default plugin_dir should be 'plugins'"
        assert (
            config.artifact_dir == "artifacts/guild"
        ), "Default artifact_dir should be 'artifacts/guild'"
        assert config.require_consent is True, "Default require_consent should be True"
        assert (
            config.allow_screenshots is False
        ), "Default allow_screenshots should be False"
        assert (
            config.ollama_url == "http://localhost:11434"
        ), "Default ollama_url should be localhost:11434"

        print("✓ All default values correctly applied")
    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        raise


def test_literal_constraints():
    """Test that Literal type constraints are enforced."""
    print("\n=== Test 4: Literal Type Constraints ===")
    try:
        config = load_config()

        valid_policy_modes = ["live_advisory", "strict", "permissive"]
        valid_autonomy_levels = ["advisory", "semi_autonomous", "fully_autonomous"]

        assert (
            config.policy_mode in valid_policy_modes
        ), f"policy_mode must be one of {valid_policy_modes}"
        assert (
            config.autonomy_level in valid_autonomy_levels
        ), f"autonomy_level must be one of {valid_autonomy_levels}"

        print("✓ Literal constraints properly enforced")
    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        raise


def test_optional_fields():
    """Test that optional fields work correctly."""
    print("\n=== Test 5: Optional Fields ===")
    try:
        config = load_config()

        # These should be optional and might be None
        print(f"  Linear API Key: {'Set' if config.linear_api_key else 'Not set'}")
        print(f"  Linear Team ID: {config.linear_team_id or 'Not set'}")
        print(f"  Home Merlin URL: {config.home_assistant_url or 'Not set'}")
        print(
            f"  Home Merlin Token: {'Set' if config.home_assistant_token else 'Not set'}"
        )

        print("✓ Optional fields handled correctly")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("AAS Pydantic RCS Configuration System Test Suite")
    print("=" * 60)

    results = []
    results.append(("Basic Load", test_basic_load()))
    results.append(("Field Types", test_field_types()))
    results.append(("Default Values", test_defaults()))
    results.append(("Literal Constraints", test_literal_constraints()))
    results.append(("Optional Fields", test_optional_fields()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Pydantic RCS is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        sys.exit(1)
