"""Telegram bot client."""

from typing import Dict, Any, Optional, List
import asyncio
from telegram import Bot
from telegram.error import TelegramError

from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """Telegram bot client wrapper."""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot: Optional[Bot] = None
        self.logger = logger
        
        if bot_token:
            self._init_bot()
    
    def _init_bot(self):
        """Initialize Telegram bot."""
        try:
            self.bot = Bot(token=self.bot_token)
            self.logger.debug("Telegram bot initialized")
        except Exception as e:
            self.logger.error(f"Error initializing Telegram bot: {e}")
            self.bot = None
    
    async def get_me(self) -> Dict[str, Any]:
        """Get bot information."""
        if not self.bot:
            raise RuntimeError("Bot not initialized")
        
        try:
            bot_info = await self.bot.get_me()
            return {
                'id': bot_info.id,
                'username': bot_info.username,
                'first_name': bot_info.first_name
            }
        except TelegramError as e:
            self.logger.error(f"Telegram error getting bot info: {e}")
            raise
    
    async def get_chats(self) -> List[Dict[str, Any]]:
        """Get chats where bot is admin."""
        # Note: Telegram Bot API doesn't have direct method to get chats
        # This requires storing chat IDs manually or using getUpdates
        # For now, return empty list - channels should be configured manually
        return []
    
    async def check_chat_admin(self, chat_id: str) -> bool:
        """Check if bot is admin in chat."""
        if not self.bot:
            return False
        
        try:
            member = await self.bot.get_chat_member(chat_id=chat_id, user_id=(await self.bot.get_me()).id)
            return member.status in ['administrator', 'creator']
        except TelegramError as e:
            self.logger.error(f"Error checking admin status: {e}")
            return False
    
    async def send_photo(
        self,
        chat_id: str,
        photo: Any,  # Can be file-like, bytes, or file path
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send photo to chat."""
        if not self.bot:
            raise RuntimeError("Bot not initialized")
        
        try:
            message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode
            )
            return {
                "message_id": message.message_id,
                "chat_id": message.chat.id
            }
        except TelegramError as e:
            self.logger.error(f"Telegram error sending photo: {e}")
            raise
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "HTML",
        disable_web_page_preview: bool = True
    ) -> Dict[str, Any]:
        """Send message to chat/channel."""
        if not self.bot:
            raise RuntimeError("Bot not initialized")
        
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            
            self.logger.info(f"Sent message to Telegram chat {chat_id}, message_id: {message.message_id}")
            
            return {
                'success': True,
                'message_id': message.message_id,
                'chat_id': chat_id
            }
        except TelegramError as e:
            self.logger.error(f"Telegram error sending message: {e}")
            raise
    
    async def send_message_thread(
        self,
        chat_id: str,
        messages: List[str],
        parse_mode: Optional[str] = "HTML"
    ) -> Dict[str, Any]:
        """Send thread of messages (for Telegram threads)."""
        if not self.bot:
            raise RuntimeError("Bot not initialized")
        
        if not messages:
            raise ValueError("No messages to send")
        
        try:
            # Send first message
            first_message = await self.bot.send_message(
                chat_id=chat_id,
                text=messages[0],
                parse_mode=parse_mode
            )
            
            first_id = first_message.message_id
            
            # Send remaining messages as replies
            for msg in messages[1:]:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    reply_to_message_id=first_id,
                    parse_mode=parse_mode
                )
            
            self.logger.info(f"Sent thread of {len(messages)} messages to Telegram chat {chat_id}")
            
            return {
                'success': True,
                'message_id': first_id,
                'chat_id': chat_id,
                'thread_length': len(messages)
            }
        except TelegramError as e:
            self.logger.error(f"Telegram error sending thread: {e}")
            raise
    
    async def validate_token(self) -> bool:
        """Validate bot token."""
        if not self.bot:
            return False
        
        try:
            await self.bot.get_me()
            return True
        except TelegramError:
            return False

