"""Internal state monitor for autonomous triggers."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


@dataclass
class InternalTrigger:
    """Internal trigger condition."""
    name: str
    condition: str
    urgency: float  # 0.0 - 1.0
    metadata: Dict[str, Any]
    timestamp: str


class InternalStateMonitor:
    """Monitors internal state and generates triggers for autonomous action."""
    
    def __init__(self, memory_index=None, goals=None):
        self.memory_index = memory_index
        self.goals = goals
        self.logger = logger
        self.triggers: List[InternalTrigger] = []
    
    async def check_state(self) -> List[InternalTrigger]:
        """Check internal state and generate triggers."""
        triggers = []
        
        # 1. Check last publication time
        triggers.extend(await self._check_publication_silence())
        
        # 2. Check repetition patterns
        triggers.extend(await self._check_repetition())
        
        # 3. Check goal progress
        triggers.extend(await self._check_goal_progress())
        
        # 4. Check safety/conservatism
        triggers.extend(await self._check_too_safe())
        
        # 5. Check content quality degradation
        triggers.extend(await self._check_quality_trend())
        
        self.triggers = triggers
        return triggers
    
    async def _check_publication_silence(self) -> List[InternalTrigger]:
        """Trigger: "я давно не публиковал"."""
        if not self.memory_index or not self.memory_index.storage:
            return []
        
        try:
            recent_content = self.memory_index.storage.get_recent_content(limit=10)
            published_content = [c for c in recent_content if c.published]
            
            if not published_content:
                # Never published - medium urgency
                return [InternalTrigger(
                    name="no_publications",
                    condition="never_published",
                    urgency=0.5,
                    metadata={"message": "Никогда не публиковал контент"},
                    timestamp=get_timestamp()
                )]
            
            # Get most recent publication
            last_published = max(published_content, key=lambda x: x.timestamp)
            last_time = datetime.fromisoformat(last_published.timestamp.replace('Z', '+00:00'))
            hours_since = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
            
            # Calculate urgency based on posting frequency goal
            if self.goals:
                frequency = self.goals.posting_frequency
                expected_interval = {
                    "frequent": 6,  # hours
                    "moderate": 24,
                    "rare": 72
                }.get(frequency, 24)
                
                if hours_since > expected_interval * 1.5:
                    urgency = min(0.9, 0.5 + (hours_since / expected_interval - 1.5) * 0.2)
                    return [InternalTrigger(
                        name="publication_silence",
                        condition="too_long_since_last",
                        urgency=urgency,
                        metadata={
                            "message": f"Не публиковал {hours_since:.1f} часов",
                            "hours_since": hours_since,
                            "expected_interval": expected_interval
                        },
                        timestamp=get_timestamp()
                    )]
        except Exception as e:
            self.logger.error(f"Error checking publication silence: {e}")
        
        return []
    
    async def _check_repetition(self) -> List[InternalTrigger]:
        """Trigger: "я повторяюсь"."""
        if not self.memory_index or not self.memory_index.storage:
            return []
        
        try:
            recent_content = self.memory_index.storage.get_recent_content(limit=20)
            topics = [c.topic for c in recent_content if c.topic]
            
            # Count topic frequency
            topic_counts = {}
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Find repeated topics
            repeated_topics = {t: c for t, c in topic_counts.items() if c >= 3}
            
            if repeated_topics:
                max_repeats = max(repeated_topics.values())
                urgency = min(0.8, 0.4 + (max_repeats - 3) * 0.2)
                
                return [InternalTrigger(
                    name="topic_repetition",
                    condition="too_many_repeats",
                    urgency=urgency,
                    metadata={
                        "message": f"Повторяюсь: тема '{max(repeated_topics, key=repeated_topics.get)}' {max_repeats} раз(а)",
                        "repeated_topics": repeated_topics
                    },
                    timestamp=get_timestamp()
                )]
        except Exception as e:
            self.logger.error(f"Error checking repetition: {e}")
        
        return []
    
    async def _check_goal_progress(self) -> List[InternalTrigger]:
        """Trigger: "цель не продвигается"."""
        if not self.goals or not self.goals.content_goals:
            return []
        
        triggers = []
        
        try:
            for goal in self.goals.content_goals:
                if not goal.active:
                    continue
                
                # Simple check: if goal exists but no content created for it
                # In full implementation, would track goal-specific metrics
                created_at = datetime.fromisoformat(goal.created_at.replace('Z', '+00:00')) if goal.created_at else datetime.now(timezone.utc)
                days_since = (datetime.now(timezone.utc) - created_at).total_seconds() / 86400
                
                if days_since > 7 and goal.priority >= 7:
                    triggers.append(InternalTrigger(
                        name="goal_stagnation",
                        condition="high_priority_goal_inactive",
                        urgency=0.6,
                        metadata={
                            "message": f"Высокоприоритетная цель '{goal.description}' не продвигается",
                            "goal_id": goal.id,
                            "days_since": days_since
                        },
                        timestamp=get_timestamp()
                    ))
        except Exception as e:
            self.logger.error(f"Error checking goal progress: {e}")
        
        return triggers
    
    async def _check_too_safe(self) -> List[InternalTrigger]:
        """Trigger: "слишком безопасно"."""
        if not self.memory_index or not self.memory_index.storage:
            return []
        
        try:
            recent_content = self.memory_index.storage.get_recent_content(limit=10)
            if len(recent_content) < 5:
                return []
            
            # Check rejection rate
            rejected = sum(1 for c in recent_content if c.rejected)
            rejection_rate = rejected / len(recent_content)
            
            # Check if rejection is due to low semantic density (too conservative)
            density_rejections = sum(
                1 for c in recent_content 
                if c.rejected and c.rejection_reason and "density" in c.rejection_reason.lower()
            )
            
            # If rejection rate is too high, might be too conservative
            if rejection_rate > 0.8:
                trigger_message = f"Слишком консервативно: отклонено {rejection_rate*100:.0f}% контента"
                if density_rejections > 0:
                    trigger_message += f" (в т.ч. {density_rejections} из-за низкой плотности)"
                
                return [InternalTrigger(
                    name="too_conservative",
                    condition="high_rejection_rate",
                    urgency=0.7,
                    metadata={
                        "message": trigger_message,
                        "rejection_rate": rejection_rate,
                        "density_rejections": density_rejections
                    },
                    timestamp=get_timestamp()
                )]
        except Exception as e:
            self.logger.error(f"Error checking safety: {e}")
        
        return []
    
    async def _check_quality_trend(self) -> List[InternalTrigger]:
        """Trigger: degradation in quality."""
        if not self.memory_index or not self.memory_index.storage:
            return []
        
        try:
            recent_content = self.memory_index.storage.get_recent_content(limit=10)
            content_with_scores = [c for c in recent_content if c.quality_score is not None]
            
            if len(content_with_scores) < 5:
                return []
            
            # Check if quality is declining
            scores = [c.quality_score for c in content_with_scores[:5]]
            recent_avg = sum(scores[:3]) / len(scores[:3])
            older_avg = sum(scores[3:]) / len(scores[3:])
            
            if recent_avg < older_avg - 0.1:  # Significant drop
                return [InternalTrigger(
                    name="quality_degradation",
                    condition="quality_dropping",
                    urgency=0.6,
                    metadata={
                        "message": f"Качество падает: было {older_avg:.2f}, стало {recent_avg:.2f}",
                        "recent_avg": recent_avg,
                        "older_avg": older_avg
                    },
                    timestamp=get_timestamp()
                )]
        except Exception as e:
            self.logger.error(f"Error checking quality trend: {e}")
        
        return []
    
    def get_most_urgent_trigger(self) -> Optional[InternalTrigger]:
        """Get the most urgent trigger."""
        if not self.triggers:
            return None
        return max(self.triggers, key=lambda t: t.urgency)
    
    def has_triggers(self, min_urgency: float = 0.5) -> bool:
        """Check if there are triggers above urgency threshold."""
        return any(t.urgency >= min_urgency for t in self.triggers)

