"""VK image upload helper."""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
import io

from utils.logger import get_logger

logger = get_logger(__name__)


async def upload_image_to_vk(
    access_token: str,
    group_id: int,
    image_data: bytes
) -> Optional[str]:
    """Upload image to VK and get attachment string."""
    try:
        # Step 1: Get upload server
        async with aiohttp.ClientSession() as session:
            url = "https://api.vk.com/method/photos.getWallUploadServer"
            params = {
                "access_token": access_token,
                "group_id": group_id,
                "v": "5.154"
            }
            
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if "error" in data:
                    logger.error(f"VK API error: {data['error']}")
                    return None
                
                upload_url = data["response"]["upload_url"]
            
            # Step 2: Upload image
            upload_data = aiohttp.FormData()
            upload_data.add_field('photo', image_data, filename='photo.jpg', content_type='image/jpeg')
            
            async with session.post(upload_url, data=upload_data) as resp:
                upload_result = await resp.json()
                if "error" in upload_result:
                    logger.error(f"VK upload error: {upload_result['error']}")
                    return None
                
                server = upload_result["server"]
                photo = upload_result["photo"]
                hash_val = upload_result["hash"]
            
            # Step 3: Save photo
            save_url = "https://api.vk.com/method/photos.saveWallPhoto"
            save_params = {
                "access_token": access_token,
                "group_id": group_id,
                "server": server,
                "photo": photo,
                "hash": hash_val,
                "v": "5.154"
            }
            
            async with session.get(save_url, params=save_params) as resp:
                save_result = await resp.json()
                if "error" in save_result:
                    logger.error(f"VK save error: {save_result['error']}")
                    return None
                
                photo_obj = save_result["response"][0]
                photo_id = photo_obj["id"]
                owner_id = photo_obj["owner_id"]
                
                # Return attachment string
                return f"photo{owner_id}_{photo_id}"
    
    except Exception as e:
        logger.error(f"Error uploading image to VK: {e}", exc_info=True)
        return None

