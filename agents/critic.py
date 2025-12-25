"""Critic agent - evaluates content quality."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp

class CriticAgent(BaseAgent):
    """Agent that critiques content."""
    
    def __init__(self, context):
        super().__init__("critic", context)
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe edited content."""
        platform_versions = self.context.shared_data.get("editor_platform_versions", {})
        topic = self.context.shared_data.get("writer_topic", "")
        goals = self.context.goals
        memory = self.context.memory
        
        # Check for repetition
        repetition_check = None
        if memory and platform_versions:
            for platform, content in platform_versions.items():
                is_repetition, similar_entry = memory.check_repetition(content, threshold=0.85)
                if is_repetition:
                    repetition_check = {
                        "is_repetition": True,
                        "similar_entry": similar_entry.id if similar_entry else None,
                        "platform": platform
                    }
                    break
        
        observation_data = {
            "platform_versions": platform_versions,
            "topic": topic,
            "min_quality_score": goals.min_content_quality_score if goals else 0.7,
            "repetition_check": repetition_check,
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about content quality."""
        platform_versions = observation.data.get("platform_versions", {})
        min_score = observation.data.get("min_quality_score", 0.7)
        repetition = observation.data.get("repetition_check")
        
        if not platform_versions:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No content to evaluate",
                considerations={"skip": True, "approved": False}
            )
        
        # Check repetition first
        if repetition and repetition.get("is_repetition"):
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="Content is too similar to existing content",
                considerations={
                    "skip": False,
                    "approved": False,
                    "reason": "repetition",
                    "quality_score": 0.0
                }
            )
        
        # Check banality filter
        banality_filter = self.context.banality_filter
        topic = observation.data.get("topic", "")
        if banality_filter and platform_versions:
            content_to_check = list(platform_versions.values())[0]
            is_banal, banality_reason = banality_filter.should_reject(content_to_check, topic)
            if is_banal:
                return Thought(
                    timestamp=get_timestamp(),
                    observation=observation,
                    analysis=f"Content is too banal: {banality_reason}",
                    considerations={
                        "skip": False,
                        "approved": False,
                        "reason": "banality",
                        "quality_score": 0.0
                    }
                )
        
        # Check semantic density
        density_checker = self.context.density_checker
        if density_checker and platform_versions:
            content_to_check = list(platform_versions.values())[0]
            is_dense_enough, density = density_checker.is_dense_enough(content_to_check, threshold=0.3)
            if not is_dense_enough:
                return Thought(
                    timestamp=get_timestamp(),
                    observation=observation,
                    analysis=f"Content lacks semantic density: {density:.2f}",
                    considerations={
                        "skip": False,
                        "approved": False,
                        "reason": "low_density",
                        "quality_score": density
                    }
                )
        
        # Check meta-critic recommendations
        meta_issues = self.context.shared_data.get("meta_critic_issues", [])
        meta_recommendations = self.context.shared_data.get("meta_critic_recommendations", [])
        
        # Adjust evaluation based on meta-critic feedback
        if "too_soft" in meta_issues:
            min_score += 0.1  # Be stricter
        elif "too_strict" in meta_issues:
            min_score -= 0.1  # Be more lenient
        
        # Evaluate quality using AI
        ai_router = self.context.ai_router
        
        # Evaluate first platform version (simplified)
        content_to_evaluate = list(platform_versions.values())[0] if platform_versions else ""
        
        prompt = f"""Ты - Critic, агент, который оценивает качество контента.

Оцени этот контент по следующим критериям:
- Оригинальность
- Интересность
- Качество написания
- Соответствие теме
- Общее впечатление

Контент:
{content_to_evaluate[:2000]}

Ответь в формате JSON:
{{
    "quality_score": 0.0-1.0,
    "approved": true/false,
    "reasoning": "обоснование",
    "strengths": ["сильная сторона 1", ...],
    "weaknesses": ["слабая сторона 1", ...]
}}

Минимальный проходной балл: {min_score}"""

        try:
            response_text = await ai_router.generate(
                prompt=prompt,
                task_type="deep_analysis",
                system_instruction="Ты строгий критик контента. Оценивай объективно и справедливо."
            )
            
            # Parse response
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                evaluation = {
                    "quality_score": 0.5,
                    "approved": False,
                    "reasoning": "Could not parse evaluation",
                    "strengths": [],
                    "weaknesses": []
                }
        except Exception as e:
            self.logger.error(f"Error in critique: {e}")
            evaluation = {
                "quality_score": 0.5,
                "approved": False,
                "reasoning": f"Error: {str(e)}",
                "strengths": [],
                "weaknesses": []
            }
        
        quality_score = evaluation.get("quality_score", 0.5)
        
        # Additional check: semantic density
        density_checker = self.context.density_checker
        if density_checker and platform_versions:
            content_to_check = list(platform_versions.values())[0]
            is_dense, density_score = density_checker.is_dense_enough(content_to_check, threshold=0.3)
            if not is_dense:
                approved = False
                quality_score = min(quality_score, density_score)
            else:
                # Combine quality and density scores
                quality_score = (quality_score * 0.7 + density_score * 0.3)
        else:
            approved = evaluation.get("approved", False) and quality_score >= min_score
        
        approved = approved and quality_score >= min_score
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=evaluation.get("reasoning", ""),
            considerations={
                "quality_score": quality_score,
                "approved": approved,
                "strengths": evaluation.get("strengths", []),
                "weaknesses": evaluation.get("weaknesses", []),
                "skip": False
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent based on critique."""
        if thought.considerations.get("skip"):
            return Intent(
                timestamp=get_timestamp(),
                thought=thought,
                action_type="skip",
                parameters={},
                confidence=0.0
            )
        
        approved = thought.considerations.get("approved", False)
        action_type = "approve" if approved else "reject"
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type=action_type,
            parameters={
                "quality_score": thought.considerations.get("quality_score", 0.0),
                "reasoning": thought.analysis,
                "strengths": thought.considerations.get("strengths", []),
                "weaknesses": thought.considerations.get("weaknesses", [])
            },
            confidence=0.9
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute critique decision."""
        if intent.action_type == "skip":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("critic_"),
                executed=False
            )
        
        self.context.shared_data["critic_decision"] = intent.action_type
        self.context.shared_data["critic_quality_score"] = intent.parameters.get("quality_score", 0.0)
        self.context.shared_data["critic_reasoning"] = intent.parameters.get("reasoning", "")
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("critic_"),
            executed=True
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on critique."""
        decision = action.intent.action_type
        score = action.intent.parameters.get("quality_score", 0.0)
        learnings = f"Content {decision}ed with quality score {score:.2f}"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=False
        )

