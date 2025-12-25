"""AI model router with rate limiting."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque

from utils.logger import get_logger
from .gemini_client import GeminiClient
from .models import ModelConfig, ModelType, get_default_model, get_fallback_model, get_model_config

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: deque = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Try to acquire a request slot."""
        async with self.lock:
            now = datetime.now()
            
            # Remove old requests outside the window
            while self.request_times and (now - self.request_times[0]).total_seconds() > self.window_seconds:
                self.request_times.popleft()
            
            # Check if we can make a request
            if len(self.request_times) < self.max_requests:
                self.request_times.append(now)
                return True
            
            return False
    
    async def wait_for_slot(self) -> None:
        """Wait until a slot is available."""
        while not await self.acquire():
            # Calculate wait time
            if self.request_times:
                oldest_time = self.request_times[0]
                wait_seconds = self.window_seconds - (datetime.now() - oldest_time).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(min(wait_seconds, 1.0))
            else:
                await asyncio.sleep(0.1)


class AIRouter:
    """Routes requests to appropriate AI models with rate limiting."""
    
    def __init__(self, gemini_client: GeminiClient, api_key: Optional[str] = None):
        self.client = gemini_client or GeminiClient(api_key)
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        self.queue = asyncio.Queue()
        self._processing = False
        self.logger = get_logger(__name__)
    
    def select_model(self, task_type: str, context: Optional[Dict[str, Any]] = None) -> ModelConfig:
        """Select appropriate model for the task."""
        context = context or {}
        
        # Use deep model for complex tasks
        if task_type in ["deep_analysis", "memory_search", "news_analysis", "long_context"]:
            return get_fallback_model()  # gemini-1.5-pro
        
        # Use fast model for everything else
        return get_default_model()  # gemini-2.0-flash-exp
    
    async def generate(
        self,
        prompt: str,
        task_type: str = "default",
        model_name: Optional[str] = None,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate text using appropriate model."""
        
        # Select model
        if model_name:
            model_config = get_model_config(model_name)
            if not model_config:
                logger.warning(f"Model {model_name} not found, using default")
                model_config = self.select_model(task_type, context)
        else:
            model_config = self.select_model(task_type, context)
        
        # Wait for rate limit
        await self.rate_limiter.wait_for_slot()
        
        try:
            self.logger.debug(f"Generating with model: {model_config.name} for task: {task_type}")
            result = await self.client.generate_text(
                prompt=prompt,
                model_config=model_config,
                system_instruction=system_instruction
            )
            return result
        except Exception as e:
            self.logger.error(f"Error in AI generation: {e}")
            # Try fallback model if default failed
            if model_config.name != get_fallback_model().name:
                logger.info("Retrying with fallback model")
                fallback_config = get_fallback_model()
                try:
                    return await self.client.generate_text(
                        prompt=prompt,
                        model_config=fallback_config,
                        system_instruction=system_instruction
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    raise
            raise
    
    async def generate_with_context(
        self,
        messages: list,
        task_type: str = "default",
        system_instruction: Optional[str] = None
    ) -> str:
        """Generate with conversation context."""
        model_config = self.select_model(task_type)
        await self.rate_limiter.wait_for_slot()
        
        try:
            return await self.client.generate_with_messages(
                messages=messages,
                model_config=model_config,
                system_instruction=system_instruction
            )
        except Exception as e:
            self.logger.error(f"Error in context generation: {e}")
            raise

