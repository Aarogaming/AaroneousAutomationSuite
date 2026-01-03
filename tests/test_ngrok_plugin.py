"""Unit tests for ngrok plugin"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from plugins.ngrok_plugin import NgrokPlugin, NgrokConfig


@pytest.mark.asyncio
async def test_ngrok_plugin_disabled():
    """Test that plugin does nothing when disabled"""
    config = NgrokConfig(enabled=False)
    plugin = NgrokPlugin(config)
    
    url = await plugin.start_tunnel()
    assert url is None
    assert plugin.is_running() is False


@pytest.mark.asyncio
async def test_ngrok_plugin_not_installed():
    """Test behavior when ngrok is not installed"""
    config = NgrokConfig(enabled=True, port=8080)
    plugin = NgrokPlugin(config)
    
    with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError):
        url = await plugin.start_tunnel()
        assert url is None
        assert plugin.is_running() is False


@pytest.mark.asyncio
async def test_ngrok_tunnel_start_stop():
    """Test starting and stopping ngrok tunnel"""
    config = NgrokConfig(enabled=True, port=8080)
    plugin = NgrokPlugin(config)
    
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.terminate = Mock()
    mock_process.wait = AsyncMock()
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch.object(plugin, '_get_tunnel_url', return_value='https://test.ngrok.io'):
            url = await plugin.start_tunnel()
            
            assert url == 'https://test.ngrok.io'
            assert plugin.is_running() is True
            assert plugin.get_tunnel_url() == 'https://test.ngrok.io'
            
            # Stop tunnel
            await plugin.stop_tunnel()
            assert plugin.is_running() is False
            assert plugin.get_tunnel_url() is None
            mock_process.terminate.assert_called_once()


@pytest.mark.asyncio
async def test_ngrok_restart_tunnel():
    """Test restarting ngrok tunnel"""
    config = NgrokConfig(enabled=True, port=8080)
    plugin = NgrokPlugin(config)
    
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.terminate = Mock()
    mock_process.wait = AsyncMock()
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch.object(plugin, '_get_tunnel_url', return_value='https://new.ngrok.io'):
            url = await plugin.restart_tunnel()
            
            assert url == 'https://new.ngrok.io'
            assert plugin.is_running() is True


@pytest.mark.asyncio
async def test_ngrok_config_validation():
    """Test NgrokConfig validation"""
    # Valid config
    config = NgrokConfig(
        enabled=True,
        authtoken="test_token",
        region="eu",
        port=9000
    )
    assert config.enabled is True
    assert config.authtoken == "test_token"
    assert config.region == "eu"
    assert config.port == 9000
    
    # Default values
    config_default = NgrokConfig()
    assert config_default.enabled is False
    assert config_default.region == "us"
    assert config_default.port == 8000


def test_ngrok_double_start_warning():
    """Test that starting an already running tunnel logs warning"""
    config = NgrokConfig(enabled=True)
    plugin = NgrokPlugin(config)
    
    # Simulate running process
    plugin.process = Mock()
    plugin.tunnel_url = "https://existing.ngrok.io"
    
    # This should return existing URL without starting new process
    result = asyncio.run(plugin.start_tunnel())
    assert result == "https://existing.ngrok.io"
