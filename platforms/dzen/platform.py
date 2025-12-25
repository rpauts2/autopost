"""Dzen platform implementation."""

from typing import Dict, Any, Optional
from platforms.base import BasePlatform
from platforms.dzen.browser import DzenBrowser
import asyncio

from utils.logger import get_logger

logger = get_logger(__name__)


class DzenPlatform(BasePlatform):
    """Dzen platform integration."""
    
    def __init__(self):
        super().__init__("dzen")
        self.browser: Optional[DzenBrowser] = None
        self.authenticated = False
    
    async def authenticate(self, credentials: Dict[str, Any] = None) -> bool:
        """Authenticate with Dzen (manual browser authentication)."""
        try:
            if not self.browser:
                self.browser = DzenBrowser()
                await self.browser.start()
            
            # Check if already authenticated
            if await self.browser.check_authenticated():
                self.authenticated = True
                self.logger.info("Dzen already authenticated")
                return True
            
            # Wait for manual authentication
            self.logger.info("Please authenticate in the browser window")
            authenticated = await self.browser.wait_for_authentication(timeout=300)
            
            if authenticated:
                self.authenticated = True
                self.logger.info("Dzen authenticated successfully")
                return True
            else:
                self.logger.error("Dzen authentication timeout")
                return False
        except Exception as e:
            self.logger.error(f"Dzen authentication error: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validate current credentials."""
        if not self.browser:
            return False
        
        try:
            return await self.browser.check_authenticated()
        except Exception as e:
            self.logger.error(f"Credential validation error: {e}")
            return False
    
    async def publish(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish article to Dzen."""
        if not self.browser:
            raise RuntimeError("Browser not started")
        
        if not self.authenticated:
            if not await self.validate_credentials():
                raise RuntimeError("Not authenticated")
        
        metadata = metadata or {}
        title = metadata.get("title", "Статья")
        tags = metadata.get("tags", [])
        
        # Split content into title and body if not provided
        if metadata.get("title") is None:
            lines = content.split('\n', 1)
            title = lines[0][:100]  # First line as title, max 100 chars
            content = lines[1] if len(lines) > 1 else content
        
        # Handle image if provided
        image_path = None
        if "image" in metadata and metadata["image"]:
            # Save image temporarily
            from pathlib import Path
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "autoposst_images"
            temp_dir.mkdir(exist_ok=True)
            image_path = temp_dir / f"article_{get_timestamp()}.png"
            with open(image_path, 'wb') as f:
                if isinstance(metadata["image"], bytes):
                    f.write(metadata["image"])
                else:
                    f.write(metadata["image"].encode() if isinstance(metadata["image"], str) else bytes(metadata["image"]))
        
        result = await self.browser.create_article(
            title=title,
            content=content,
            tags=tags,
            image_path=str(image_path) if image_path else None
        )
        
        return result
    
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status."""
        status = {
            "authenticated": self.authenticated,
            "browser_running": self.browser is not None
        }
        
        if self.browser:
            try:
                browser_status = await self.browser.get_status()
                status.update(browser_status)
            except Exception as e:
                self.logger.error(f"Error getting browser status: {e}")
        
        return status
    
    async def stop(self):
        """Stop browser."""
        if self.browser:
            await self.browser.stop()
            self.browser = None
            self.authenticated = False

