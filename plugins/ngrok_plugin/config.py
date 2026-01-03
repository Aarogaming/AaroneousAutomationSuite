"""Configuration for ngrok tunneling plugin"""
from pydantic import BaseModel, Field
from typing import Optional


class NgrokConfig(BaseModel):
    """Configuration for ngrok tunnel setup"""
    
    authtoken: Optional[str] = Field(
        default=None,
        description="ngrok authentication token (optional for basic usage)"
    )
    region: str = Field(
        default='us',
        description="ngrok server region (us, eu, ap, au, sa, jp, in)"
    )
    port: int = Field(
        default=8000,
        description="Local port to expose via ngrok tunnel"
    )
    enabled: bool = Field(
        default=False,
        description="Whether ngrok tunneling is enabled"
    )
