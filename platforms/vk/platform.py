"""VK platform implementation."""

from typing import Dict, Any, Optional
from platforms.base import BasePlatform
from platforms.vk.client import VKClient
from security.token_storage import TokenStorage

from utils.logger import get_logger

logger = get_logger(__name__)


class VKPlatform(BasePlatform):
    """VK platform integration."""
    
    def __init__(self):
        super().__init__("vk")
        self.token_storage = TokenStorage()
        self.client: Optional[VKClient] = None
        self.selected_group_id: Optional[int] = None
        
        # Load token if exists
        token = self.token_storage.get_token("vk")
        if token:
            self.client = VKClient(access_token=token)
            metadata = self.token_storage.get_metadata("vk")
            self.selected_group_id = metadata.get("group_id")
            self.authenticated = True
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with VK using access token."""
        access_token = credentials.get("access_token")
        if not access_token:
            self.logger.error("No access token provided")
            return False
        
        try:
            self.client = VKClient(access_token=access_token)
            
            # Validate token
            if await self.client.validate_token():
                # Store token
                self.token_storage.store_token("vk", access_token, metadata={})
                self.authenticated = True
                self.logger.info("VK authenticated successfully")
                return True
            else:
                self.logger.error("Invalid VK token")
                return False
        except Exception as e:
            self.logger.error(f"VK authentication error: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validate current credentials."""
        if not self.client:
            return False
        
        try:
            return await self.client.validate_token()
        except Exception as e:
            self.logger.error(f"Credential validation error: {e}")
            return False
    
    async def get_groups(self) -> list[Dict[str, Any]]:
        """Get available groups."""
        if not self.client:
            raise RuntimeError("Not authenticated")
        
        return await self.client.get_groups()
    
    async def select_group(self, group_id: int) -> bool:
        """Select group for publishing."""
        if not self.client:
            raise RuntimeError("Not authenticated")
        
        # Check admin rights
        if await self.client.check_admin_rights(group_id):
            self.selected_group_id = group_id
            
            # Update metadata
            token = self.token_storage.get_token("vk")
            metadata = self.token_storage.get_metadata("vk")
            metadata["group_id"] = group_id
            self.token_storage.store_token("vk", token, metadata=metadata)
            
            self.logger.info(f"Selected VK group: {group_id}")
            return True
        else:
            self.logger.error(f"No admin rights for group {group_id}")
            return False
    
    async def publish(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish content to VK."""
        if not self.client:
            raise RuntimeError("Not authenticated")
        
        if not self.selected_group_id:
            raise RuntimeError("No group selected")
        
        metadata = metadata or {}
        attachments = metadata.get("attachments", [])
        
        # Handle image if provided
        if "image" in metadata and metadata["image"]:
            try:
                from platforms.vk.image_upload import upload_image_to_vk
                from security.token_storage import TokenStorage
                
                token_storage = TokenStorage()
                token_data = token_storage.get_token("vk")
                
                if token_data:
                    image_data = metadata["image"]
                    if isinstance(image_data, bytes):
                        photo_attachment = await upload_image_to_vk(
                            access_token=token_data,
                            group_id=self.selected_group_id,
                            image_data=image_data
                        )
                        if photo_attachment:
                            attachments.append(photo_attachment)
                            self.logger.info(f"Image uploaded to VK: {photo_attachment}")
                    else:
                        self.logger.warning(f"VK image is not bytes: {type(image_data)}")
            except Exception as e:
                self.logger.error(f"Error uploading image to VK: {e}", exc_info=True)
                # Continue without image
        
        result = await self.client.post_to_wall(
            group_id=self.selected_group_id,
            message=content,
            attachments=attachments
        )
        
        return result
    
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status."""
        status = {
            "authenticated": self.authenticated,
            "has_group": self.selected_group_id is not None,
            "group_id": self.selected_group_id
        }
        
        if self.client and self.authenticated:
            try:
                if await self.client.validate_token():
                    groups = await self.get_groups()
                    status["available_groups"] = len(groups)
                else:
                    status["authenticated"] = False
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                status["authenticated"] = False
        
        return status

