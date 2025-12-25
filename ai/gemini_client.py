"""Gemini API client."""

import asyncio
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from utils.logger import get_logger
from .models import ModelConfig, get_default_model

logger = get_logger(__name__)


class GeminiClient:
    """Client for Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._configured = False
        if api_key:
            self.configure(api_key)
    
    def configure(self, api_key: str):
        """Configure Gemini API."""
        try:
            genai.configure(api_key=api_key)
            self.api_key = api_key
            self._configured = True
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise
    
    def is_configured(self) -> bool:
        """Check if API is configured."""
        return self._configured and self.api_key is not None
    
    def get_model(self, model_config: ModelConfig):
        """Get a model instance."""
        if not self.is_configured():
            raise RuntimeError("Gemini API not configured. Set API key first.")
        
        generation_config = {
            "temperature": model_config.temperature,
            "top_p": model_config.top_p,
            "top_k": model_config.top_k,
            "max_output_tokens": model_config.max_tokens,
        }
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        return genai.GenerativeModel(
            model_name=model_config.name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    
    async def generate_text(
        self,
        prompt: str,
        model_config: Optional[ModelConfig] = None,
        system_instruction: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text asynchronously."""
        if not self.is_configured():
            raise RuntimeError("Gemini API not configured")
        
        model_config = model_config or get_default_model()
        
        try:
            model = self.get_model(model_config)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    prompt,
                    system_instruction=system_instruction
                )
            )
            
            if response and response.text:
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        model_config: Optional[ModelConfig] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """Generate text with conversation history."""
        if not self.is_configured():
            raise RuntimeError("Gemini API not configured")
        
        model_config = model_config or get_default_model()
        
        try:
            model = self.get_model(model_config)
            
            # Convert messages to chat format
            chat = model.start_chat(history=[])
            
            # Add system instruction if provided
            if system_instruction:
                # For Gemini, system instruction is set at model creation
                # We'll include it in the first message
                if messages:
                    messages[0]["content"] = f"{system_instruction}\n\n{messages[0]['content']}"
            
            # Send messages
            loop = asyncio.get_event_loop()
            
            last_response = None
            for msg in messages:
                response = await loop.run_in_executor(
                    None,
                    lambda m=msg: chat.send_message(m["content"])
                )
                last_response = response
            
            if last_response and last_response.text:
                return last_response.text
            else:
                logger.warning("Empty response from Gemini API")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating with messages: {e}")
            raise

