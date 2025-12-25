"""Publisher agent - publishes content to platforms."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp
from utils.logger import get_logger

logger = get_logger(__name__)


class PublisherAgent(BaseAgent):
    async def act(self, shared_data: dict):
        logger.error("🔥🔥🔥 PUBLISHER ACT CALLED 🔥🔥🔥")
        logger.error(f"Shared data keys: {shared_data.keys()}")

        entity = shared_data.get("entity")
        platforms = shared_data.get("platforms")
        content = shared_data.get("content")

        if not entity:
            logger.error("❌ ENTITY NOT FOUND — CANNOT PUBLISH")
            return None

        if not entity.platform_manager:
            logger.error("❌ PLATFORM MANAGER NOT SET")
            return None

        if not platforms:
            logger.error("❌ NO PLATFORMS SPECIFIED")
            return None

        logger.warning(f"Attempting to publish to: {platforms}")

        results = {}

        for platform in platforms:
            try:
                logger.warning(f"→ Publishing to {platform}")
                res = await entity.platform_manager.publish(
                    platform=platform,
                    content=content
                )
                results[platform] = res
            except Exception as e:
                logger.exception(f"Publish failed for {platform}: {e}")

        return {"publish_results": results}
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about publishing."""
        approved = observation.data.get("approved", False)
        platform_versions = observation.data.get("platform_versions", {})
        
        if not approved:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="Content not approved by critic, skipping publication",
                considerations={"skip": True, "publish": False}
            )
        
        if not platform_versions:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No platform versions available",
                considerations={"skip": True, "publish": False}
            )
        
        available_platforms = observation.data.get("available_platforms", [])
        
        # Use available platforms that have content versions
        platforms_to_publish = [p for p in available_platforms if p in platform_versions] or available_platforms
        
        if not platforms_to_publish:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No authenticated platforms available",
                considerations={"publish": False, "skip": True}
            )
        
        available_platforms = observation.data.get("available_platforms", [])
        
        # Use available platforms that have content versions
        platforms_to_publish = [p for p in available_platforms if p in platform_versions] or available_platforms
        
        if not platforms_to_publish:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No authenticated platforms available",
                considerations={"publish": False, "skip": True}
            )
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=f"Ready to publish to {len(platforms_to_publish)} platform(s): {', '.join(platforms_to_publish)}",
            considerations={
                "publish": True,
                "platforms": platforms_to_publish,
                "skip": False
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent to publish."""
        if thought.considerations.get("skip"):
            return Intent(
                timestamp=get_timestamp(),
                thought=thought,
                action_type="skip",
                parameters={},
                confidence=0.0
            )
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type="publish_content",
            parameters={
                "platforms": thought.considerations.get("platforms", []),
                "needs_image": thought.considerations.get("needs_image", False),
                "image_description": thought.considerations.get("image_description")
            },
            confidence=0.9
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute publishing."""
        if intent.action_type == "skip":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("publisher_"),
                executed=False
            )
        
        platforms = intent.parameters.get("platforms", [])
        platform_versions = self.context.shared_data.get("editor_platform_versions", {})
        
        published_platforms = []
        failed_platforms = []
        
        # Get platform manager from entity
        entity = self.context.shared_data.get("entity")
        if entity and hasattr(entity, 'platform_manager'):
            platform_manager = entity.platform_manager
            
            needs_image = self.context.shared_data.get("editor_needs_image", False)
            image_description = self.context.shared_data.get("editor_image_description")
            
            for platform_name in platforms:
                try:
                    content = platform_versions.get(platform_name, platform_versions.get(list(platform_versions.keys())[0] if platform_versions else "", ""))
                    
                    # Prepare metadata based on platform
                    metadata = {}
                    if platform_name == "dzen":
                        # Extract title from content for Dzen
                        lines = content.split('\n', 1)
                        metadata["title"] = lines[0][:100] if lines else "Статья"
                    
                    # Generate and add image if needed
                    platform_images = self.context.shared_data.get("editor_image_descriptions", {})
                    if platform_name in platform_images and platform_images[platform_name].get("needs_image"):
                        image_desc = platform_images[platform_name].get("description")
                        if image_desc and entity and hasattr(entity, 'image_generator'):
                            try:
                                self.logger.info(f"Generating image for {platform_name}: {image_desc[:50]}...")
                                image_data = await entity.image_generator.generate_image(
                                    description=image_desc,
                                    style="realistic"
                                )
                                if image_data:
                                    metadata["image"] = image_data
                                    self.logger.info(f"✅ Image generated successfully for {platform_name} ({len(image_data)} bytes)")
                                else:
                                    self.logger.warning(f"Image generation returned None for {platform_name}")
                            except Exception as e:
                                self.logger.error(f"Error generating image for {platform_name}: {e}", exc_info=True)
                    
                    # Publish
                    result = await platform_manager.publish_to_platform(
                        platform_name=platform_name,
                        content=content,
                        metadata=metadata
                    )
                    
                    if result.get("success"):
                        published_platforms.append(platform_name)
                        self.logger.info(f"Published to {platform_name}: {result.get('url', result.get('message_id', 'OK'))}")
                    else:
                        failed_platforms.append(platform_name)
                        self.logger.error(f"Failed to publish to {platform_name}")
                except Exception as e:
                    self.logger.error(f"Error publishing to {platform_name}: {e}", exc_info=True)
                    failed_platforms.append(platform_name)
        else:
            self.logger.warning("Platform manager not available, skipping publication")
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("publisher_"),
                executed=False
            )
        
        # Store results
        self.context.shared_data["published"] = len(published_platforms) > 0
        self.context.shared_data["published_platforms"] = published_platforms
        self.context.shared_data["failed_platforms"] = failed_platforms
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("publisher_"),
            executed=len(published_platforms) > 0
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on publishing."""
        platforms = action.intent.parameters.get("platforms", [])
        published = self.context.shared_data.get("published_platforms", [])
        failed = self.context.shared_data.get("failed_platforms", [])
        
        learnings = f"Published to {len(published)} platform(s): {', '.join(published) if published else 'none'}"
        if failed:
            learnings += f". Failed: {', '.join(failed)}"
        
        # Add explanation for publishing
        if self.context.explanation_tracker:
            why = f"Публикация контента на платформы: {', '.join(platforms)}"
            why_now = "Контент прошел все проверки (Critic, Banality Filter, Density Check) и готов к публикации"
            why_this_form = f"Контент адаптирован под каждую платформу согласно их требованиям"
            
            self.context.explanation_tracker.add_explanation(
                action_id=action.action_id,
                agent_name=self.name,
                why=why,
                why_now=why_now,
                why_this_form=why_this_form,
                metadata={
                    "platforms": platforms,
                    "published": published,
                    "failed": failed
                }
            )
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=not result.success and len(failed) > 0
        )

