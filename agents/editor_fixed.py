"""Editor agent - adapts content for platforms."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp
from utils.logger import get_logger

logger = get_logger(__name__)


class EditorAgent(BaseAgent):
    """Agent that edits content for platforms."""
    
    def __init__(self, context):
        super().__init__("editor", context)
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe writer's content."""
        content = self.context.shared_data.get("writer_content", "")
        topic = self.context.shared_data.get("writer_topic", "")
        settings = self.context.settings
        
        observation_data = {
            "content": content,
            "topic": topic,
            "enabled_platforms": settings.enabled_platforms if settings else [],
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about platform adaptation."""
        content = observation.data.get("content", "")
        platforms = observation.data.get("enabled_platforms", [])
        needs_image = self.context.shared_data.get("needs_image", False)
        image_description = self.context.shared_data.get("image_description", "")
        
        if not content:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No content to edit",
                considerations={"skip": True}
            )
        
        # Get available platforms from entity
        entity = self.context.shared_data.get("entity")
        available_platforms = []
        if entity and hasattr(entity, 'platform_manager'):
            for name, platform in entity.platform_manager.get_all_platforms().items():
                try:
                    # Quick check without full async status
                    if hasattr(platform, 'authenticated') and platform.authenticated:
                        available_platforms.append(name)
                except:
                    pass
        
        if not available_platforms:
            available_platforms = platforms  # Fallback to enabled platforms
        
        # Create platform-specific versions
        platform_versions = {}
        platform_images = {}
        
        # Store platform-specific image needs
        if needs_image and image_description:
            # For each platform, decide if image needed
            entity = self.context.shared_data.get("entity")
            topic = self.context.shared_data.get("writer_topic", "")
            
            if entity and hasattr(entity, 'image_generator') and entity.image_generator.enabled:
                for platform in available_platforms:
                    try:
                        platform_needs, platform_desc = await entity.image_generator.should_generate_image(
                            content=content,
                            topic=topic,
                            platform=platform
                        )
                        if platform_needs:
                            platform_images[platform] = {
                                "needs_image": True,
                                "description": platform_desc or image_description
                            }
                            logger.info(f"Image needed for {platform}: {platform_desc[:50] if platform_desc else image_description[:50]}...")
                    except Exception as e:
                        logger.error(f"Error checking image for {platform}: {e}")
                        # Fallback - use general description
                        platform_images[platform] = {
                            "needs_image": True,
                            "description": image_description
                        }
            else:
                # Fallback - mark all platforms if image was decided
                for platform in available_platforms:
                    platform_images[platform] = {
                        "needs_image": True,
                        "description": image_description
                    }
        
        for platform in available_platforms:
            # Platform-specific adaptations
            adapted_content = content
            
            if platform == "telegram":
                # Telegram: split into thread if long
                if len(content) > 3000:
                    # Mark for threading (will be handled by publisher)
                    adapted_content = content
                else:
                    adapted_content = content
            
            elif platform == "vk":
                # VK: keep as is, moderate formatting
                adapted_content = content
            
            elif platform == "dzen":
                # Dzen: article format
                adapted_content = content
            
            platform_versions[platform] = adapted_content
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=f"Prepared content for {len(platform_versions)} platform(s)",
            considerations={
                "platform_versions": platform_versions,
                "platform_images": platform_images,
                "needs_image": len(platform_images) > 0,
                "skip": False
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent to edit."""
        if thought.considerations.get("skip"):
            return Intent(
                timestamp=get_timestamp(),
                thought=thought,
                action_type="skip",
                parameters={},
                confidence=0.0
            )
        
        platform_versions = thought.considerations.get("platform_versions", {})
        platform_images = thought.considerations.get("platform_images", {})
        needs_image = thought.considerations.get("needs_image", False)
        image_description = self.context.shared_data.get("image_description", "")
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type="edit",
            parameters={
                "platform_versions": platform_versions,
                "platform_images": platform_images,
                "needs_image": needs_image,
                "image_description": image_description,
            },
            confidence=0.9
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute editing."""
        if intent.action_type == "skip":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("editor_"),
                executed=False
            )
        
        platform_versions = intent.parameters.get("platform_versions", {})
        platform_images = intent.parameters.get("platform_images", {})
        
        self.context.shared_data["editor_platform_versions"] = platform_versions
        self.context.shared_data["editor_needs_image"] = intent.parameters.get("needs_image", False)
        self.context.shared_data["editor_image_description"] = intent.parameters.get("image_description", "")
        self.context.shared_data["editor_image_descriptions"] = platform_images
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("editor_"),
            executed=bool(platform_versions)
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on editing."""
        learnings = f"Edited content for {len(action.intent.parameters.get('platform_versions', {}))} platform(s)"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=not result.success
        )

