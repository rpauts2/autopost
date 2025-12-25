"""Platform manager."""

from typing import Dict, Any, Optional, List
from platforms.base import BasePlatform
from platforms.vk.platform import VKPlatform
from platforms.telegram.platform import TelegramPlatform
from platforms.dzen.platform import DzenPlatform

from utils.logger import get_logger

logger = get_logger(__name__)


class PlatformManager:
    """Manages platform integrations."""
    
    def __init__(self):
        self.platforms: Dict[str, BasePlatform] = {}
        self.logger = logger
        self._init_platforms()
    
    def _init_platforms(self):
        """Initialize platforms."""
        self.platforms["vk"] = VKPlatform()
        self.platforms["telegram"] = TelegramPlatform()
        self.platforms["dzen"] = DzenPlatform()
        self.logger.info("Platforms initialized")
    
    def get_platform(self, name: str) -> Optional[BasePlatform]:
        """Get platform by name."""
        return self.platforms.get(name)
    
    def get_all_platforms(self) -> Dict[str, BasePlatform]:
        """Get all platforms."""
        return self.platforms.copy()
    
    async def publish_to_platform(
        self,
        platform_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish content to specific platform."""
        platform = self.get_platform(platform_name)
        if not platform:
            raise ValueError(f"Platform {platform_name} not found")
        
        if not platform.is_authenticated():
            raise RuntimeError(f"Platform {platform_name} not authenticated")
        
        return await platform.publish(content, metadata)
    
    async def get_platform_status(self, platform_name: str) -> Dict[str, Any]:
        """Get status of specific platform."""
        platform = self.get_platform(platform_name)
        if not platform:
            return {"error": "Platform not found"}
        
        return await platform.get_status()
    
    async def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all platforms."""
        statuses = {}
        for name, platform in self.platforms.items():
            try:
                statuses[name] = await platform.get_status()
            except Exception as e:
                self.logger.error(f"Error getting status for {name}: {e}")
                statuses[name] = {"error": str(e)}
        return statuses

