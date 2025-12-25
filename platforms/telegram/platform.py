"""Telegram platform implementation."""

from typing import Dict, Any, Optional
from platforms.base import BasePlatform
from platforms.telegram.client import TelegramClient
from security.token_storage import TokenStorage

from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramPlatform(BasePlatform):
    """Telegram platform integration."""
    
    def __init__(self):
        super().__init__("telegram")
        self.token_storage = TokenStorage()
        self.client: Optional[TelegramClient] = None
        self.selected_chat_id: Optional[str] = None
        
        # Load token if exists
        token = self.token_storage.get_token("telegram")
        if token:
            self.client = TelegramClient(bot_token=token)
            metadata = self.token_storage.get_metadata("telegram")
            self.selected_chat_id = metadata.get("chat_id")
            self.authenticated = True
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Telegram using bot token."""
        bot_token = credentials.get("bot_token")
        if not bot_token:
            self.logger.error("No bot token provided")
            return False
        
        try:
            self.client = TelegramClient(bot_token=bot_token)
            
            # Validate token
            if await self.client.validate_token():
                bot_info = await self.client.get_me()
                self.logger.info(f"Telegram bot authenticated: @{bot_info.get('username')}")
                
                # Store token
                self.token_storage.store_token(
                    "telegram",
                    bot_token,
                    metadata={"bot_username": bot_info.get("username")}
                )
                self.authenticated = True
                return True
            else:
                self.logger.error("Invalid Telegram bot token")
                return False
        except Exception as e:
            self.logger.error(f"Telegram authentication error: {e}")
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
    
    async def select_chat(self, chat_id: str) -> bool:
        """Select chat/channel for publishing."""
        if not self.client:
            raise RuntimeError("Not authenticated")
        
        # Check admin rights
        if await self.client.check_chat_admin(chat_id):
            self.selected_chat_id = chat_id
            
            # Update metadata
            token = self.token_storage.get_token("telegram")
            metadata = self.token_storage.get_metadata("telegram")
            metadata["chat_id"] = chat_id
            self.token_storage.store_token("telegram", token, metadata=metadata)
            
            self.logger.info(f"Selected Telegram chat: {chat_id}")
            return True
        else:
            self.logger.error(f"Bot is not admin in chat {chat_id}")
            return False
    
    async def publish(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Publish content to Telegram."""
        if not self.client:
            raise RuntimeError("Not authenticated")
        
        if not self.selected_chat_id:
            raise RuntimeError("No chat selected")
        
        metadata = metadata or {}
        parse_mode = metadata.get("parse_mode", "Markdown")
        
        # Handle image if provided
        image_data = None
        if "image" in metadata and metadata["image"]:
            image_data = metadata["image"]
            if not isinstance(image_data, bytes):
                self.logger.warning(f"Telegram image is not bytes: {type(image_data)}")
                image_data = None
        
        # Split into messages if too long
        max_length = 4096
        messages = []
        if len(content) > max_length:
            # Simple split by sentences
            sentences = content.split('. ')
            current_message = ""
            for sentence in sentences:
                if len(current_message) + len(sentence) + 2 < max_length:
                    current_message += sentence + ". "
                else:
                    if current_message:
                        messages.append(current_message.strip())
                    current_message = sentence + ". "
            if current_message:
                messages.append(current_message.strip())
        else:
            messages = [content]
        
        # Send messages with image in first message if available
        sent_message_ids = []
        for i, message in enumerate(messages):
            try:
                if i == 0 and image_data:
                    # Send photo with caption (first message)
                    import io
                    photo_file = io.BytesIO(image_data)
                    photo_file.name = "photo.jpg"
                    
                    result = await self.client.send_photo(
                        chat_id=self.selected_chat_id,
                        photo=photo_file,
                        caption=message[:1024] if len(message) <= 1024 else message[:1020] + "...",
                        parse_mode=parse_mode
                    )
                    sent_message_ids.append(result.get("message_id"))
                    self.logger.info("✅ Image sent with first message to Telegram")
                    
                    # Send remaining text if caption was truncated
                    if len(message) > 1024:
                        remaining = message[1020:]
                        result = await self.client.send_message(
                            chat_id=self.selected_chat_id,
                            text=remaining,
                            parse_mode=None
                        )
                        sent_message_ids.append(result.get("message_id"))
                else:
                    # Regular text message
                    result = await self.client.send_message(
                        chat_id=self.selected_chat_id,
                        text=message,
                        parse_mode=parse_mode if i == 0 and not image_data else None
                    )
                    sent_message_ids.append(result.get("message_id"))
                
                # Small delay between messages
                if i < len(messages) - 1:
                    await asyncio.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error sending Telegram message {i+1}: {e}", exc_info=True)
                raise
        
        return {
            "success": True,
            "message_id": sent_message_ids[0] if sent_message_ids else None,
            "message_ids": sent_message_ids
        }
    
    def _split_into_messages(self, content: str, max_length: int = 4000) -> list[str]:
        """Split content into multiple messages for thread."""
        if len(content) <= max_length:
            return [content]
        
        # Try to split by paragraphs
        paragraphs = content.split('\n\n')
        messages = []
        current_message = ""
        
        for para in paragraphs:
            if len(current_message) + len(para) + 2 <= max_length:
                if current_message:
                    current_message += "\n\n" + para
                else:
                    current_message = para
            else:
                if current_message:
                    messages.append(current_message)
                # If paragraph itself is too long, split it
                if len(para) > max_length:
                    while len(para) > max_length:
                        messages.append(para[:max_length])
                        para = para[max_length:]
                    current_message = para
                else:
                    current_message = para
        
        if current_message:
            messages.append(current_message)
        
        return messages
    
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status."""
        status = {
            "authenticated": self.authenticated,
            "has_chat": self.selected_chat_id is not None,
            "chat_id": self.selected_chat_id
        }
        
        if self.client and self.authenticated:
            try:
                if await self.client.validate_token():
                    bot_info = await self.client.get_me()
                    status["bot_username"] = bot_info.get("username")
                else:
                    status["authenticated"] = False
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                status["authenticated"] = False
        
        return status

