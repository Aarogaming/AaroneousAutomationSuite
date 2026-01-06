"""ngrok tunneling plugin for development and remote access"""
import asyncio
import subprocess
import re
from typing import Optional
from loguru import logger
from .config import NgrokConfig


class NgrokPlugin:
    """Manages ngrok tunnels for exposing local services"""
    
    def __init__(self, config: NgrokConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tunnel_url: Optional[str] = None
        
    async def start_tunnel(self) -> Optional[str]:
        """
        Start ngrok tunnel and return the public URL
        
        Returns:
            Public URL if successful, None otherwise
        """
        if not self.config.enabled:
            logger.info("ngrok plugin is disabled in config")
            return None
            
        if self.process:
            logger.warning("ngrok tunnel already running")
            return self.tunnel_url
        
        logger.info(f"Starting ngrok tunnel on port {self.config.port}...")
        
        # Build ngrok command
        command = [
            "ngrok", "http", str(self.config.port),
            "--region", self.config.region
        ]
        
        if self.config.authtoken:
            command.extend(["--authtoken", self.config.authtoken])
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.success(f"ngrok tunnel started on port {self.config.port}")
            
            # Wait a moment for ngrok to establish tunnel
            await asyncio.sleep(2)
            
            # Try to get tunnel URL from ngrok API
            self.tunnel_url = await self._get_tunnel_url()
            
            if self.tunnel_url:
                logger.success(f"ngrok tunnel available at: {self.tunnel_url}")
            else:
                logger.warning("Could not retrieve tunnel URL from ngrok API")
            
            return self.tunnel_url
            
        except FileNotFoundError:
            logger.error(
                "ngrok not found. Install: npm install -g ngrok "
                "or download from https://ngrok.com/download"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to start ngrok tunnel: {e}")
            return None
    
    async def _get_tunnel_url(self) -> Optional[str]:
        """Retrieve public tunnel URL from ngrok local API"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://127.0.0.1:4040/api/tunnels') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            return tunnels[0].get('public_url')
        except Exception as e:
            logger.debug(f"Could not fetch tunnel URL from API: {e}")
        
        return None
    
    async def stop_tunnel(self):
        """Stop the ngrok tunnel"""
        if self.process:
            logger.info("Stopping ngrok tunnel...")
            self.process.terminate()
            
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                logger.success("ngrok tunnel stopped")
            except asyncio.TimeoutError:
                logger.warning("ngrok process did not terminate, killing...")
                self.process.kill()
                await self.process.wait()
            
            self.process = None
            self.tunnel_url = None
        else:
            logger.debug("No ngrok tunnel running")
    
    async def restart_tunnel(self) -> Optional[str]:
        """Restart the ngrok tunnel"""
        await self.stop_tunnel()
        await asyncio.sleep(1)
        return await self.start_tunnel()
    
    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL"""
        return self.tunnel_url
    
    def is_running(self) -> bool:
        """Check if ngrok tunnel is currently running"""
        return self.process is not None and self.process.returncode is None


def register(hub):
    """Register plugin with AAS Hub (optional, for future plugin system)"""
    logger.info("ngrok plugin registered")
