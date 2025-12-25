"""Meta-Critic agent - evaluates the Critic itself."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp

class MetaCriticAgent(BaseAgent):
    """Agent that critiques the Critic agent and monitors style degradation."""
    
    def __init__(self, context):
        super().__init__("meta_critic", context)
        self.critic_history: list[Dict[str, Any]] = []
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe Critic's decisions and overall style evolution."""
        memory = self.context.memory
        critic_reflection = context.get("critic_reflection")
        
        # Get recent content quality scores
        quality_trend = []
        style_consistency = []
        
        if memory and memory.storage:
            recent_content = memory.storage.get_recent_content(limit=20)
            quality_trend = [c.quality_score for c in recent_content if c.quality_score is not None]
            style_consistency = [c.style for c in recent_content if c.style]
        
        observation_data = {
            "critic_reflection": critic_reflection,
            "quality_trend": quality_trend,
            "style_consistency": style_consistency,
            "recent_decisions": self.critic_history[-10:] if self.critic_history else []
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=observation_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Analyze Critic's performance and style evolution."""
        quality_trend = observation.data.get("quality_trend", [])
        style_consistency = observation.data.get("style_consistency", [])
        recent_decisions = observation.data.get("recent_decisions", [])
        
        if not quality_trend or len(quality_trend) < 5:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="Insufficient data for meta-critique",
                considerations={"skip": True}
            )
        
        # Analyze trends
        recent_scores = quality_trend[:5]
        older_scores = quality_trend[5:10] if len(quality_trend) > 5 else []
        
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        older_avg = sum(older_scores) / len(older_scores) if older_scores else recent_avg
        
        # Check for style drift
        unique_styles = set(style_consistency)
        style_drift = len(unique_styles) > 3  # Too many style changes
        
        # Check for consistency issues
        score_variance = sum((s - recent_avg) ** 2 for s in recent_scores) / len(recent_scores) if recent_scores else 0
        inconsistent = score_variance > 0.05
        
        # Analyze Critic's decisions
        approval_rate = sum(1 for d in recent_decisions if d.get("approved", False)) / len(recent_decisions) if recent_decisions else 0.5
        
        # Check for degradation in novelty
        novelty_degradation = self._check_novelty_degradation(quality_trend, recent_content if 'recent_content' in dir() else [])
        
        analysis_parts = []
        issues = []
        
        if recent_avg < older_avg - 0.1:
            analysis_parts.append(f"Качество падает: {recent_avg:.2f} vs {older_avg:.2f}")
            issues.append("quality_degradation")
        
        if novelty_degradation:
            analysis_parts.append("Новизна падает - контент становится предсказуемым")
            issues.append("novelty_degradation")
        
        if style_drift:
            analysis_parts.append("Стиль нестабилен")
            issues.append("style_drift")
        
        if inconsistent:
            analysis_parts.append("Критик непоследователен")
            issues.append("inconsistency")
        
        if approval_rate > 0.9:
            analysis_parts.append("Критик слишком мягкий")
            issues.append("too_soft")
        elif approval_rate < 0.1:
            analysis_parts.append("Критик слишком строгий")
            issues.append("too_strict")
        
        analysis = "; ".join(analysis_parts) if analysis_parts else "Критик работает нормально"
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=analysis,
            considerations={
                "issues": issues,
                "quality_trend": {
                    "recent": recent_avg,
                    "older": older_avg,
                    "trend": "declining" if recent_avg < older_avg - 0.1 else "stable"
                },
                "approval_rate": approval_rate,
                "style_drift": style_drift,
                "skip": len(issues) == 0
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent based on meta-critique."""
        if thought.considerations.get("skip"):
            return Intent(
                timestamp=get_timestamp(),
                thought=thought,
                action_type="no_action",
                parameters={},
                confidence=0.0
            )
        
        issues = thought.considerations.get("issues", [])
        action_type = "adjust_critic" if issues else "no_action"
        
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type=action_type,
            parameters={
                "issues": issues,
                "recommendations": self._generate_recommendations(issues, thought.considerations)
            },
            confidence=0.8
        )
    
    def _generate_recommendations(self, issues: list, considerations: Dict[str, Any]) -> list[str]:
        """Generate recommendations based on identified issues."""
        recommendations = []
        
        if "quality_degradation" in issues:
            recommendations.append("Повысить стандарты качества")
        
        if "style_drift" in issues:
            recommendations.append("Стабилизировать стиль")
        
        if "inconsistency" in issues:
            recommendations.append("Улучшить консистентность оценок")
        
        if "too_soft" in issues:
            recommendations.append("Быть более строгим")
        
        if "too_strict" in issues:
            recommendations.append("Быть менее строгим")
        
        return recommendations
    
    async def act(self, intent: Intent) -> Action:
        """Execute meta-critique action."""
        if intent.action_type == "no_action":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("meta_critic_"),
                executed=False
            )
        
        # Store recommendations in context
        self.context.shared_data["meta_critic_issues"] = intent.parameters.get("issues", [])
        self.context.shared_data["meta_critic_recommendations"] = intent.parameters.get("recommendations", [])
        
        # Record decision
        self.critic_history.append({
            "timestamp": get_timestamp(),
            "issues": intent.parameters.get("issues", []),
            "approved": False  # Meta-critic found issues
        })
        
        self.logger.warning(f"Meta-Critic identified issues: {intent.parameters.get('issues', [])}")
        
        return Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id("meta_critic_"),
            executed=True
        )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on meta-critique."""
        issues = action.intent.parameters.get("issues", [])
        learnings = f"Meta-critique completed. Issues: {', '.join(issues) if issues else 'none'}"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=False
        )

