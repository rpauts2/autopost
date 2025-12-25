"""Thinker agent - decides what to create."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp

class ThinkerAgent(BaseAgent):
    """Agent that decides what content to create."""
    
    def __init__(self, context):
        super().__init__("thinker", context)
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe current state and goals."""
        # Gather information about goals, recent content, and opportunities
        goals = self.context.goals
        memory = self.context.memory
        
        # Get recent content to avoid repetition
        recent_topics = []
        blocked_topics = []
        if memory and memory.storage:
            recent_content = memory.storage.get_recent_content(limit=10)
            recent_topics = [c.topic for c in recent_content]
            
            # Check for memory pressure (topics that should be blocked)
            for content in recent_content:
                if content.topic and memory.check_repetition(content.topic, threshold=0.85)[0]:
                    blocked_topics.append(content.topic)
        
        observation_data = {
            "goals": {
                "preferred_topics": goals.preferred_topics,
                "avoid_topics": goals.avoid_topics,
                "posting_frequency": goals.posting_frequency,
            },
            "recent_topics": recent_topics,
            "blocked_topics": blocked_topics,  # Memory pressure
            "current_time": get_timestamp(),
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about what to create."""
        ai_router = self.context.ai_router
        goals = self.context.goals
        
        # Memory pressure: blocked topics
        blocked_topics = observation.data.get('blocked_topics', [])
        recent_topics = observation.data.get('recent_topics', [])[:5]
        
        # Get cluster information for context
        cluster_context = ""
        if cluster_manager:
            active_clusters = cluster_manager.get_active_clusters()
            if active_clusters:
                cluster_names = [c.name for c in active_clusters[:3]]
                cluster_context = f"\nАктивные тематические кластеры: {', '.join(cluster_names)}"
        
        # Check for ready deferred ideas
        deferred_context = ""
        if deferred_thinking:
            ready_ideas = deferred_thinking.get_ready_ideas()
            if ready_ideas:
                idea = ready_ideas[0]
                deferred_context = f"\nОтложенная идея готова: {idea.topic}"
        
        # Build thinking prompt
        prompt = f"""Ты - Thinker, агент, который решает, какую тему выбрать для контента.

Текущие цели:
- Предпочитаемые темы: {', '.join(goals.preferred_topics) if goals.preferred_topics else 'любые'}
- Избегай тем: {', '.join(goals.avoid_topics) if goals.avoid_topics else 'нет'}
- Частота публикаций: {goals.posting_frequency}
- Качество: {goals.global_quality}

Недавние темы (избегай повторений):
{chr(10).join(f"- {topic}" for topic in recent_topics)}

ЗАБЛОКИРОВАННЫЕ ТЕМЫ (память запрещает повтор):
{chr(10).join(f"- {topic}" for topic in blocked_topics) if blocked_topics else "Нет"}
{"⚠️ Если хочешь использовать заблокированную тему - найди более глубокий или другой угол!" if blocked_topics else ""}
{cluster_context}
{deferred_context}

ВАЖНО: Самоограничение - публикуй только если есть что сказать, не публикуй ради публикации.
Проверь смысловую ценность темы перед выбором. Учитывай смысловую плотность - если нет глубокой мысли, лучше отложить идею.

Проанализируй ситуацию и реши:
1. Стоит ли сейчас создавать контент? (только если есть ценная мысль)
2. Если да, какую тему выбрать?
3. Почему именно эта тема? (обоснование смысловой ценности)
4. Какая смысловая ценность этой темы?

Ответь в формате JSON:
{{
    "should_create": true/false,
    "topic": "тема или null",
    "reasoning": "обоснование",
    "confidence": 0.0-1.0
}}"""

        try:
            response_text = await ai_router.generate(
                prompt=prompt,
                task_type="deep_analysis",
                system_instruction="Ты эксперт по выбору контентных тем. Думай критически и учитывай контекст."
            )
            
            # Parse response (simple JSON extraction)
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                # Fallback
                decision = {
                    "should_create": False,
                    "topic": None,
                    "reasoning": "Could not parse AI response",
                    "confidence": 0.0
                }
        except Exception as e:
            self.logger.error(f"Error in thinking: {e}")
            decision = {
                "should_create": False,
                "topic": None,
                "reasoning": f"Error: {str(e)}",
                "confidence": 0.0
            }
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=decision.get("reasoning", ""),
            considerations={
                "should_create": decision.get("should_create", False),
                "topic": decision.get("topic"),
                "confidence": decision.get("confidence", 0.0)
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent based on thought."""
        should_create = thought.considerations.get("should_create", False)
        topic = thought.considerations.get("topic")
        confidence = thought.considerations.get("confidence", 0.0)
        reasoning = thought.analysis
        
        if should_create and topic:
            action_type = "create_content"
            parameters = {
                "topic": topic,
                "confidence": confidence,
                "reasoning": reasoning
            }
        else:
            action_type = "skip_creation"
            should_defer = confidence > 0.3
            parameters = {
                "reason": reasoning,
                "should_defer": should_defer
            }
            
            # Defer idea if it has some value
            if deferred_thinking and should_defer and topic:
                deferred_thinking.defer_idea(
                    topic=topic or "неизвестная тема",
                    reasoning=reasoning,
                    defer_days=3
                )
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type=action_type,
            parameters=parameters,
            confidence=confidence
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute the intent."""
        action = Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("thinker_"),
            executed=True
        )
        
        # Store decision in context for next agents
        self.context.shared_data["thinker_decision"] = intent.parameters
        self.context.shared_data["thinker_intent"] = intent.action_type
        
        # Self-explanation
        if self.context.explanation_tracker:
            topic = intent.parameters.get("topic", "N/A")
            why = f"Selected topic: {topic}" if intent.action_type == "create_content" else "Decided to skip content creation"
            why_now = intent.thought.analysis if intent.thought else "Based on current state"
            why_this_form = f"Confidence: {intent.confidence:.2f}"
            
            self.context.explanation_tracker.add_explanation(
                action_id=action.action_id,
                agent_name=self.name,
                why=why,
                why_now=why_now,
                why_this_form=why_this_form,
                metadata={"topic": topic, "confidence": intent.confidence}
            )
        
        return action
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on the decision."""
        learnings = f"Decided to {action.intent.action_type} with topic: {action.intent.parameters.get('topic', 'N/A')}"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=False
        )

