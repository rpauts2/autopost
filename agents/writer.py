"""Writer agent - creates content."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp

class WriterAgent(BaseAgent):
    """Agent that writes content."""
    
    def __init__(self, context):
        super().__init__("writer", context)
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe thinker's decision."""
        thinker_decision = self.context.shared_data.get("thinker_decision", {})
        thinker_intent = self.context.shared_data.get("thinker_intent", "skip_creation")
        
        observation_data = {
            "topic": thinker_decision.get("topic"),
            "should_create": thinker_intent == "create_content",
            "confidence": thinker_decision.get("confidence", 0.0),
            "goals": self.context.goals.model_dump() if hasattr(self.context.goals, 'model_dump') else {},
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about how to write the content."""
        if not observation.data.get("should_create"):
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No content creation requested",
                considerations={"skip": True}
            )
        
        topic = observation.data.get("topic")
        if not topic:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No topic provided",
                considerations={"skip": True}
            )
        
        ai_router = self.context.ai_router
        goals = self.context.goals
        personality = self.context.personality
        style_profile_manager = self.context.style_profile_manager
        
        # Get style profile
        style_profile = None
        style_instructions = ""
        if style_profile_manager:
            # Get recent profiles to avoid repetition
            recent_profiles = style_profile_manager.profile_history[-3:] if hasattr(style_profile_manager, 'profile_history') else []
            style_profile = style_profile_manager.select_profile_for_topic(topic, recent_profiles)
            style_instructions = style_profile_manager.get_profile_instructions(style_profile)
            self.context.shared_data["writer_style_profile"] = style_profile.value if style_profile else None
        
        # Get personality modifiers
        style_modifiers = {}
        if personality and hasattr(personality, 'get_style_modifiers'):
            style_modifiers = personality.get_style_modifiers()
        
        # Build style guidance from personality
        personality_guidance = ""
        if personality:
            if personality.boldness > 0.7:
                personality_guidance += " Будь смелым и экспериментальным. "
            elif personality.boldness < 0.3:
                personality_guidance += " Будь осторожным и проверенным. "
            
            if personality.depth > 0.7:
                personality_guidance += " Копай глубже в тему. "
            elif personality.depth < 0.3:
                personality_guidance += " Держись на поверхности. "
            
            if personality.tension > 0.7:
                personality_guidance += " Создай срочность и напряжение. "
        
        prompt = f"""Ты - Writer, агент, который создаёт контент.

{style_instructions}

Тема: {topic}
Стиль: {goals.style_preference}
Качество: {goals.global_quality}
{personality_guidance}

Создай качественный контент на эту тему. Контент должен быть:
- Интересным и оригинальным
- Соответствующим выбранному стилю
- Высокого качества
- Отражающим текущее состояние личности системы

Пока что создай базовый текст контента. Он будет адаптирован под платформу позже.

Ответь только текстом контента, без дополнительных комментариев."""

        try:
            content = await ai_router.generate(
                prompt=prompt,
                task_type="default",
                system_instruction="Ты опытный копирайтер, создающий качественный и оригинальный контент."
            )
        except Exception as e:
            self.logger.error(f"Error in writing: {e}")
            content = ""
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=f"Created content for topic: {topic}",
            considerations={
                "content": content,
                "topic": topic,
                "length": len(content) if content else 0
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent to write."""
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
            action_type="write_content",
            parameters={
                "content": thought.considerations.get("content", ""),
                "topic": thought.considerations.get("topic", ""),
            },
            confidence=0.9
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute writing."""
        if intent.action_type == "skip":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("writer_"),
                executed=False
            )
        
        content = intent.parameters.get("content", "")
        topic = intent.parameters.get("topic", "")
        
        # Store in context
        self.context.shared_data["writer_content"] = content
        self.context.shared_data["writer_topic"] = topic
        
        # Decide if image needed (store decision for later)
        entity = self.context.shared_data.get("entity")
        needs_image = False
        image_description = None
        
        if entity and hasattr(entity, 'image_generator') and entity.image_generator.enabled:
            try:
                needs_image, image_description = await entity.image_generator.should_generate_image(
                    content=content,
                    topic=topic,
                    platform="general"  # Will be refined by Editor for each platform
                )
                self.logger.info(f"Image decision: needs={needs_image}, desc={image_description[:50] if image_description else 'None'}...")
            except Exception as e:
                self.logger.error(f"Error deciding on image: {e}", exc_info=True)
        
        self.context.shared_data["needs_image"] = needs_image
        self.context.shared_data["image_description"] = image_description
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("writer_"),
            executed=bool(content)
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on writing."""
        learnings = f"Created content of length {len(action.intent.parameters.get('content', ''))} characters"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=not result.success
        )

