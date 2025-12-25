"""Base platform interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePlatform(ABC):
    """Base class for platform integrations."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"platform.{name}")
        self.authenticated = False
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the platform."""
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate current credentials."""
        pass
    
    @abstractmethod
    async def publish(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publish content to the platform."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status."""
        pass
    
    def is_authenticated(self) -> bool:
        """Check if platform is authenticated."""
        return self.authenticated

