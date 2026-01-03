# ngrok Plugin Usage Example

## Quick Start

### 1. Install ngrok
```bash
# Via npm
npm install -g ngrok

# Or download from https://ngrok.com/download
```

### 2. Configure (Optional - Basic tunnels work without auth)
Add to your `.env`:
```bash
NGROK_ENABLED=true
NGROK_PORT=8000           # Port to expose
NGROK_REGION=us           # us, eu, ap, au, sa, jp, in
NGROK_AUTHTOKEN=your_token_here  # Optional for free tier
```

### 3. Use in Code

#### Basic Usage
```python
from plugins.ngrok_plugin import NgrokPlugin, NgrokConfig

# Create plugin
config = NgrokConfig(
    enabled=True,
    port=8000,
    region='us'
)
plugin = NgrokPlugin(config)

# Start tunnel
url = await plugin.start_tunnel()
print(f"Service available at: {url}")

# Check status
if plugin.is_running():
    print(f"Tunnel URL: {plugin.get_tunnel_url()}")

# Stop tunnel when done
await plugin.stop_tunnel()
```

#### With AAS Config Manager
```python
from core.config.manager import load_config
from plugins.ngrok_plugin import NgrokPlugin, NgrokConfig

# Load from environment
config = load_config()

# Create ngrok config from AAS config
ngrok_config = NgrokConfig(
    enabled=config.ngrok_enabled,
    authtoken=config.ngrok_authtoken,
    region=config.ngrok_region,
    port=config.ngrok_port
)

plugin = NgrokPlugin(ngrok_config)

if ngrok_config.enabled:
    tunnel_url = await plugin.start_tunnel()
    print(f"🌐 Remote access: {tunnel_url}")
```

#### Auto-Start on Hub Launch
```python
# In core/main.py or plugin initialization
async def initialize_dev_tools():
    """Initialize development tools including ngrok"""
    config = load_config()
    
    if config.ngrok_enabled:
        ngrok_config = NgrokConfig(
            enabled=True,
            authtoken=config.ngrok_authtoken,
            region=config.ngrok_region,
            port=config.ipc_port  # Expose IPC server
        )
        
        ngrok_plugin = NgrokPlugin(ngrok_config)
        tunnel_url = await ngrok_plugin.start_tunnel()
        
        if tunnel_url:
            logger.success(f"gRPC server accessible at: {tunnel_url}")
        
        return ngrok_plugin
```

## Use Cases

### 1. Remote IPC Testing
Expose your gRPC server for remote Maelstrom instances:
```python
ngrok_config = NgrokConfig(enabled=True, port=50051)  # IPC port
```

### 2. Web Service Development
Test webhooks and external integrations:
```python
ngrok_config = NgrokConfig(enabled=True, port=8000)
```

### 3. Collaboration
Share your local development instance with teammates:
```python
plugin = NgrokPlugin(NgrokConfig(enabled=True, port=5000))
url = await plugin.start_tunnel()
# Share 'url' with teammates
```

## Features

✅ **Automatic URL retrieval** - Gets public URL from ngrok API  
✅ **Async/await support** - Non-blocking tunnel management  
✅ **Graceful shutdown** - Proper process cleanup  
✅ **Error handling** - Handles missing ngrok installation  
✅ **Multi-region support** - Choose closest ngrok server  
✅ **Status checking** - Query tunnel state and URL  

## Testing

Run the test suite:
```bash
pytest tests/test_ngrok_plugin.py -v
```

## Security Notes

⚠️ **Public exposure**: ngrok tunnels expose your local service to the internet  
🔒 **Use authentication**: Add auth to your services when using ngrok  
🔑 **Token management**: Store `NGROK_AUTHTOKEN` in `.env`, never commit  
⏰ **Temporary use**: Free ngrok tunnels expire after 2 hours  

## Troubleshooting

### "ngrok not found"
Install ngrok: `npm install -g ngrok`

### Tunnel fails to start
- Check if port is already in use: `netstat -ano | findstr :8000`
- Verify authtoken if using premium features
- Check ngrok service status: `ngrok version`

### Can't retrieve public URL
- Wait a few seconds for tunnel establishment
- Check ngrok web interface: http://127.0.0.1:4040
- Ensure aiohttp is installed: `pip install aiohttp`

## Advanced: gRPC Tunneling

For Project Maelstrom remote access:
```python
# Expose IPC server via ngrok
ipc_config = load_config()
ngrok = NgrokPlugin(NgrokConfig(
    enabled=True,
    port=ipc_config.ipc_port,
    authtoken=ipc_config.ngrok_authtoken
))

tunnel_url = await ngrok.start_tunnel()

# Update Maelstrom connection string
# From: localhost:50051
# To:   extracted_host_from_tunnel_url:443
```

## Integration with Handoff System

```python
from core.handoff.manager import HandoffManager

# Report tunnel status
if ngrok.is_running():
    handoff.report_event(
        task_id="DEV-001",
        event_type="info",
        message=f"Development tunnel active: {ngrok.get_tunnel_url()}"
    )
```
