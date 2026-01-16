"""ngrok tunneling service for development."""

from loguru import logger
from pydantic import BaseModel, Field, SecretStr
import asyncio
import subprocess
from typing import Optional


class NgrokConfig(BaseModel):
    """Configuration for ngrok tunneling."""

    auth_token: Optional[SecretStr] = Field(
        default=None,
        description="ngrok authentication token (optional for free tier)",
        env="NGROK_AUTH_TOKEN",
    )
    region: str = Field(
        default="us", description="ngrok region (us, eu, ap, au, sa, jp, in)"
    )
    port: int = Field(default=8000, description="Local port to expose")
    subdomain: Optional[str] = Field(
        default=None, description="Custom subdomain (requires paid plan)"
    )
    protocol: str = Field(
        default="http", description="Protocol to tunnel (http, tcp, tls)"
    )


class NgrokService:
    """Manages ngrok tunnel for external access during development."""

    def __init__(self, config: NgrokConfig):
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._public_url: Optional[str] = None
        logger.info("NgrokService initialized")

    async def start(self) -> Optional[str]:
        """
        Start ngrok tunnel and return public URL.

        Returns:
            Public ngrok URL or None on failure
        """
        if self._process:
            logger.warning("ngrok tunnel already running")
            return self._public_url

        try:
            logger.info(f"Starting ngrok tunnel for port {self.config.port}")

            # Build command
            cmd = [
                "ngrok",
                self.config.protocol,
                str(self.config.port),
                "--region",
                self.config.region,
                "--log",
                "stdout",
            ]

            if self.config.auth_token:
                cmd.extend(["--authtoken", self.config.auth_token.get_secret_value()])

            if self.config.subdomain:
                cmd.extend(["--subdomain", self.config.subdomain])

            # Start process
            self._process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Wait for tunnel to establish and parse URL
            await asyncio.sleep(2)  # Give ngrok time to start

            # Get ngrok API for tunnel info
            self._public_url = await self._get_tunnel_url()

            if self._public_url:
                logger.info(f"ngrok tunnel established: {self._public_url}")
            else:
                logger.error("Failed to retrieve ngrok tunnel URL")

            return self._public_url

        except FileNotFoundError:
            logger.error(
                "ngrok executable not found. Install ngrok: https://ngrok.com/download"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to start ngrok: {e}")
            return None

    async def _get_tunnel_url(self) -> Optional[str]:
        """Retrieve tunnel URL from ngrok API."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:4040/api/tunnels") as response:
                    if response.status == 200:
                        data = await response.json()
                        tunnels = data.get("tunnels", [])

                        if tunnels:
                            # Return the first public URL
                            return tunnels[0].get("public_url")

            return None

        except Exception as e:
            logger.debug(f"Could not retrieve tunnel URL from API: {e}")
            return None

    async def stop(self):
        """Stop the ngrok tunnel."""
        if not self._process:
            logger.debug("No ngrok process to stop")
            return

        try:
            logger.info("Stopping ngrok tunnel")

            self._process.terminate()

            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("ngrok did not stop gracefully, killing process")
                self._process.kill()
                await self._process.wait()

            self._process = None
            self._public_url = None
            logger.info("ngrok tunnel stopped")

        except Exception as e:
            logger.error(f"Error stopping ngrok: {e}")

    @property
    def public_url(self) -> Optional[str]:
        """Get the current public URL."""
        return self._public_url

    @property
    def is_running(self) -> bool:
        """Check if ngrok tunnel is running."""
        return self._process is not None and self._process.returncode is None


class NgrokPlugin:
    """Plugin wrapper for ngrok service."""

    def __init__(self, config: NgrokConfig):
        self.service = NgrokService(config)

    async def start(self):
        """Start the ngrok tunnel."""
        return await self.service.start()

    async def stop(self):
        """Stop the ngrok tunnel."""
        await self.service.stop()

    @property
    def status(self) -> dict:
        """Get ngrok status."""
        return {
            "is_running": self.service.is_running,
            "public_url": self.service.public_url,
        }
