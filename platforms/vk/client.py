"""VK API client."""

import vk_api
from vk_api.exceptions import ApiError, AuthError
from typing import Dict, Any, Optional, List
import asyncio

from utils.logger import get_logger
from config.defaults import VK_API_VERSION

logger = get_logger(__name__)


class VKClient:
    """VK API client wrapper."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.vk_session: Optional[vk_api.VkApi] = None
        self.vk: Optional[Any] = None
        self.logger = logger
        
        if access_token:
            self._init_session()
    
    def _init_session(self):
        """Initialize VK session."""
        try:
            self.vk_session = vk_api.VkApi(token=self.access_token)
            self.vk = self.vk_session.get_api()
            self.logger.debug("VK session initialized")
        except Exception as e:
            self.logger.error(f"Error initializing VK session: {e}")
            self.vk_session = None
            self.vk = None
    
    def set_token(self, access_token: str):
        """Set access token and initialize session."""
        self.access_token = access_token
        self._init_session()
    
    async def get_groups(self) -> List[Dict[str, Any]]:
        """Get user's groups where user is admin."""
        if not self.vk:
            raise RuntimeError("VK not authenticated")
        
        try:
            loop = asyncio.get_event_loop()
            groups = await loop.run_in_executor(
                None,
                lambda: self.vk.groups.get(
                    filter='admin',
                    extended=1,
                    fields='name,screen_name'
                )
            )
            
            result = []
            for group in groups.get('items', []):
                result.append({
                    'id': group.get('id'),
                    'name': group.get('name'),
                    'screen_name': group.get('screen_name'),
                    'is_admin': True
                })
            
            return result
        except ApiError as e:
            self.logger.error(f"VK API error getting groups: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting groups: {e}")
            raise
    
    async def get_group_info(self, group_id: int) -> Dict[str, Any]:
        """Get group information."""
        if not self.vk:
            raise RuntimeError("VK not authenticated")
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self.vk.groups.getById(group_id=abs(group_id))
            )
            
            if info:
                return {
                    'id': info[0].get('id'),
                    'name': info[0].get('name'),
                    'screen_name': info[0].get('screen_name')
                }
            return {}
        except Exception as e:
            self.logger.error(f"Error getting group info: {e}")
            raise
    
    async def check_admin_rights(self, group_id: int) -> bool:
        """Check if user has admin rights in group."""
        try:
            groups = await self.get_groups()
            group_ids = [g['id'] for g in groups]
            return abs(group_id) in group_ids
        except Exception as e:
            self.logger.error(f"Error checking admin rights: {e}")
            return False
    
    async def post_to_wall(
        self,
        group_id: int,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Post to group wall."""
        if not self.vk:
            raise RuntimeError("VK not authenticated")
        
        try:
            # Use negative ID for groups
            owner_id = -abs(group_id)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.vk.wall.post(
                    owner_id=owner_id,
                    message=message,
                    attachments=attachments or []
                )
            )
            
            post_id = result.get('post_id')
            self.logger.info(f"Posted to VK group {group_id}, post_id: {post_id}")
            
            return {
                'success': True,
                'post_id': post_id,
                'group_id': group_id,
                'url': f"https://vk.com/wall{owner_id}_{post_id}"
            }
        except ApiError as e:
            self.logger.error(f"VK API error posting: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error posting to VK: {e}")
            raise
    
    async def validate_token(self) -> bool:
        """Validate access token."""
        if not self.vk:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.vk.account.getProfileInfo()
            )
            return True
        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return False

