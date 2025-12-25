"""Sense Editor - агент, оценивающий значимость мысли, а не стиль."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp

class SenseEditorAgent(BaseAgent):
    """Agent that evaluates the significance of thought, not style."""
    
    def __init__(self, context):
        super().__init__("sense_editor", context)
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe content before style editing."""
        content = self.context.shared_data.get("writer_content", "")
        topic = self.context.shared_data.get("writer_topic", "")
        reasoning = self.context.shared_data.get("thinker_reasoning", "")
        
        observation_data = {
            "content": content,
            "topic": topic,
            "reasoning": reasoning,
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Evaluate significance of the thought."""
        content = observation.data.get("content", "")
        topic = observation.data.get("topic", "")
        reasoning = observation.data.get("reasoning", "")
        
        if not content:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No content to evaluate",
                considerations={"skip": True, "significant": False}
            )
        
        ai_router = self.context.ai_router
        
        prompt = f"""Ты - Sense Editor, агент, который оценивает ЗНАЧИМОСТЬ мысли, а не стиль написания.

Тема: {topic}
Обоснование выбора темы: {reasoning}

Контент (первые 1000 символов):
{content[:1000]}

Оцени ЗНАЧИМОСТЬ этой мысли:
- Есть ли новая идея или инсайт?
- Добавляет ли это что-то ценное?
- Или это просто пересказ очевидного?
- Достаточна ли глубина раскрытия?

НЕ оценивай стиль, грамматику, красоту формулировок.
Оценивай только СМЫСЛОВУЮ ЦЕННОСТЬ.

Ответь в формате JSON:
{{
    "significant": true/false,
    "significance_score": 0.0-1.0,
    "reasoning": "обоснование",
    "has_insight": true/false,
    "depth": "surface/deep/very_deep",
    "value_added": "что нового добавляет"
}}"""

        try:
            response_text = await ai_router.generate(
                prompt=prompt,
                task_type="deep_analysis",
                system_instruction="Ты критический редактор смысла. Оценивай только значимость мысли, игнорируя форму."
            )
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                evaluation = {
                    "significant": False,
                    "significance_score": 0.5,
                    "reasoning": "Could not parse evaluation",
                    "has_insight": False,
                    "depth": "surface",
                    "value_added": ""
                }
        except Exception as e:
            self.logger.error(f"Error in sense editing: {e}")
            evaluation = {
                "significant": False,
                "significance_score": 0.5,
                "reasoning": f"Error: {str(e)}",
                "has_insight": False,
                "depth": "surface",
                "value_added": ""
            }
        
        significant = evaluation.get("significant", False)
        significance_score = evaluation.get("significance_score", 0.5)
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=evaluation.get("reasoning", ""),
            considerations={
                "significant": significant,
                "significance_score": significance_score,
                "has_insight": evaluation.get("has_insight", False),
                "depth": evaluation.get("depth", "surface"),
                "value_added": evaluation.get("value_added", ""),
                "skip": not significant
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent based on significance evaluation."""
        if thought.considerations.get("skip"):
            return Intent(
                timestamp=get_timestamp(),
                thought=thought,
                action_type="reject",
                parameters={
                    "reason": "insufficient_significance",
                    "significance_score": thought.considerations.get("significance_score", 0.0)
                },
                confidence=0.9
            )
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type="approve",
            parameters={
                "significance_score": thought.considerations.get("significance_score", 0.5),
                "has_insight": thought.considerations.get("has_insight", False),
                "depth": thought.considerations.get("depth", "surface")
            },
            confidence=0.9
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute sense editing decision."""
        if intent.action_type == "reject":
            self.context.shared_data["sense_editor_rejected"] = True
            self.context.shared_data["sense_editor_reason"] = intent.parameters.get("reason", "")
        else:
            self.context.shared_data["sense_editor_approved"] = True
            self.context.shared_data["sense_editor_significance_score"] = intent.parameters.get("significance_score", 0.5)
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("sense_editor_"),
            executed=True
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on sense editing."""
        decision = action.intent.action_type
        score = action.intent.parameters.get("significance_score", 0.0) if decision == "approve" else 0.0
        learnings = f"Sense editing: {decision} (significance: {score:.2f})"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=False
        )

