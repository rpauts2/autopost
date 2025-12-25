"""Image generation for posts."""

from typing import Optional, Dict, Any
import asyncio
import base64
import io
from pathlib import Path

from utils.logger import get_logger
from .router import AIRouter
from .models import get_default_model

logger = get_logger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available, image generation will be limited")


class ImageGenerator:
    """Generates images for content using AI."""
    
    def __init__(self, ai_router: AIRouter):
        self.ai_router = ai_router
        self.logger = logger
        self.enabled = True
        # Note: Gemini API does not support image generation
        # This module provides decision logic and structure for future integration
    
    async def should_generate_image(
        self,
        content: str,
        topic: str,
        platform: str
    ) -> tuple[bool, Optional[str]]:
        """Decide if image should be generated for this content."""
        if not self.enabled:
            return False, None
        
        # Platform-specific logic
        image_required = {
            "vk": False,  # Optional
            "telegram": False,  # Optional
            "dzen": True  # Usually good for articles
        }
        
        if image_required.get(platform, False):
            return True, f"Image for {topic}"
        
        # Ask AI if image would improve the content
        prompt = f"""Проанализируй, нужна ли иллюстрация к этому контенту:

Тема: {topic}
Платформа: {platform}
Контент (первые 500 символов): {content[:500]}

Ответь в формате JSON:
{{
    "needs_image": true/false,
    "reasoning": "обоснование",
    "image_description": "описание изображения или null"
}}

Иллюстрация нужна, если:
- Контент визуальный или технический
- Изображение улучшит понимание
- Это статья (для Dzen)"""

        try:
            response = await self.ai_router.generate(
                prompt=prompt,
                task_type="deep_analysis"
            )
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                needs_image = decision.get("needs_image", False)
                description = decision.get("image_description")
                return needs_image, description
            
            return False, None
        except Exception as e:
            self.logger.error(f"Error deciding on image: {e}")
            return False, None
    
    async def generate_image(
        self,
        description: str,
        style: str = "realistic"
    ) -> Optional[bytes]:
        """Generate image from description using Gemini."""
        try:
            # Use Gemini to create image generation prompt
            prompt = f"""Ты - эксперт по генерации изображений. Создай детальное описание для генерации изображения:

Оригинальное описание: {description}
Стиль: {style}

Создай максимально детальное и точное описание на английском языке.
Включи: композицию, цвета, настроение, детали, освещение, стиль, разрешение, качество.

Ответь только описанием, без дополнительных комментариев."""

            refined_description = await self.ai_router.generate(
                prompt=prompt,
                task_type="default"
            )
            
            self.logger.info(f"Image prompt created: {refined_description[:100]}...")
            
            # Generate image using PIL/Pillow
            if PIL_AVAILABLE:
                import textwrap
                
                # Create image with gradient background
                img = Image.new('RGB', (1200, 800), color='#f0f0f0')
                draw = ImageDraw.Draw(img)
                
                # Draw gradient background
                for i in range(800):
                    color_value = int(240 - (i / 800) * 40)
                    color = (color_value, color_value, color_value)
                    draw.line([(0, i), (1200, i)], fill=color)
                
                # Wrap text
                wrapped_text = textwrap.fill(refined_description[:300], width=60)
                
                # Draw text with shadow
                try:
                    font_large = ImageFont.truetype("arial.ttf", 28)
                    font_small = ImageFont.truetype("arial.ttf", 18)
                except:
                    try:
                        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
                        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
                    except:
                        font_large = ImageFont.load_default()
                        font_small = ImageFont.load_default()
                
                # Draw text shadow
                draw.text((52, 52), wrapped_text, fill='gray', font=font_large)
                draw.text((52, 652), f"Style: {style}", fill='darkgray', font=font_small)
                
                # Draw text
                draw.text((50, 50), wrapped_text, fill='black', font=font_large)
                draw.text((50, 650), f"Style: {style}", fill='#333', font=font_small)
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG', quality=95)
                img_byte_arr = img_byte_arr.getvalue()
                
                self.logger.info("Image generated successfully")
                return img_byte_arr
            else:
                self.logger.warning("PIL not available, creating minimal PNG")
                # Create minimal valid PNG (1x1 white pixel)
                return base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
            
        except Exception as e:
            self.logger.error(f"Error generating image: {e}")
            return None
    
    async def generate_image_base64(
        self,
        description: str,
        style: str = "realistic"
    ) -> Optional[str]:
        """Generate image and return as base64."""
        image_data = await self.generate_image(description, style)
        if image_data:
            return base64.b64encode(image_data).decode('utf-8')
        return None
    
    async def save_image(
        self,
        image_data: bytes,
        filename: str,
        output_dir: Path
    ) -> Optional[Path]:
        """Save image to file."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            self.logger.info(f"Image saved: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            return None

