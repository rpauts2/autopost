"""Archivist agent - manages memory."""

from typing import Dict, Any
from core.intent_loop import Observation, Thought, Intent, Action, Result, Reflection
from agents.base import BaseAgent
from utils.helpers import generate_id, get_timestamp
from memory.models import MemoryEntry, ContentMemory, DecisionMemory

class ArchivistAgent(BaseAgent):
    """Agent that archives decisions and content with memory pressure."""
    
    def __init__(self, context):
        super().__init__("archivist", context)
        self.memory_pressure_threshold = 0.85  # Similarity threshold for blocking
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe all agent decisions."""
        memory_data = {
            "thinker_decision": self.context.shared_data.get("thinker_decision", {}),
            "writer_content": self.context.shared_data.get("writer_content", ""),
            "writer_topic": self.context.shared_data.get("writer_topic", ""),
            "editor_platform_versions": self.context.shared_data.get("editor_platform_versions", {}),
            "critic_decision": self.context.shared_data.get("critic_decision", "reject"),
            "critic_quality_score": self.context.shared_data.get("critic_quality_score", 0.0),
            "critic_reasoning": self.context.shared_data.get("critic_reasoning", ""),
            "published": self.context.shared_data.get("published", False),
            "published_platforms": self.context.shared_data.get("published_platforms", []),
        }
        
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data=memory_data
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Think about what to archive."""
        topic = observation.data.get("writer_topic")
        content = observation.data.get("writer_content", "")
        approved = observation.data.get("critic_decision") == "approve"
        published = observation.data.get("published", False)
        quality_score = observation.data.get("critic_quality_score", 0.0)
        reasoning = observation.data.get("critic_reasoning", "")
        
        if not topic and not content:
            return Thought(
                timestamp=get_timestamp(),
                observation=observation,
                analysis="No content to archive",
                considerations={"skip": True}
            )
        
        return Thought(
            timestamp=get_timestamp(),
            observation=observation,
            analysis=f"Archiving content cycle: topic={topic}, approved={approved}, published={published}",
            considerations={
                "topic": topic,
                "content": content,
                "approved": approved,
                "published": published,
                "quality_score": quality_score,
                "reasoning": reasoning,
                "platforms": observation.data.get("published_platforms", []),
                "skip": False
            }
        )
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Form intent to archive."""
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
            action_type="archive_content",
            parameters={
                "topic": thought.considerations.get("topic"),
                "content": thought.considerations.get("content"),
                "approved": thought.considerations.get("approved"),
                "published": thought.considerations.get("published"),
                "quality_score": thought.considerations.get("quality_score"),
                "reasoning": thought.considerations.get("reasoning"),
                "platforms": thought.considerations.get("platforms", [])
            },
            confidence=1.0
        )
    
    async def act(self, intent: Intent) -> Action:
        """Execute archiving."""
        if intent.action_type == "skip":
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("archivist_"),
                executed=False
            )
        
        memory_index = self.context.memory
        if not memory_index:
            self.logger.warning("Memory index not available")
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("archivist_"),
                executed=False
            )
        
        topic = intent.parameters.get("topic", "")
        content = intent.parameters.get("content", "")
        approved = intent.parameters.get("approved", False)
        published = intent.parameters.get("published", False)
        quality_score = intent.parameters.get("quality_score", 0.0)
        reasoning = intent.parameters.get("reasoning", "")
        platforms = intent.parameters.get("platforms", [])
        
        timestamp = get_timestamp()
        
        try:
            # Archive topic
            if topic:
                topic_entry = MemoryEntry(
                    id=generate_id("topic_"),
                    timestamp=timestamp,
                    entry_type="topic",
                    data={"topic": topic, "content_length": len(content)},
                    tags=["content_creation"]
                )
                memory_index.add_with_embedding(topic_entry)
            
            # Archive content
            if content:
                content_memory = ContentMemory(
                    id=generate_id("content_"),
                    timestamp=timestamp,
                    topic=topic,
                    content=content[:1000],  # Limit length
                    platform=",".join(platforms) if platforms else "none",
                    style="default",
                    quality_score=quality_score,
                    published=published,
                    rejected=not approved,
                    rejection_reason=reasoning if not approved else None,
                    metrics={"content_length": len(content)}
                )
                memory_index.storage.add_content(content_memory)
            
            # Archive decision
            decision_memory = DecisionMemory(
                id=generate_id("decision_"),
                timestamp=timestamp,
                decision_type="content_creation",
                context={
                    "topic": topic,
                    "approved": approved,
                    "published": published
                },
                decision="approved" if approved else "rejected",
                reasoning=reasoning,
                outcome="published" if published else "not_published"
            )
            memory_index.storage.add_decision(decision_memory)
            
            self.logger.info(f"Archived content cycle: {topic}")
            
            return Action(
                timestamp=timestamp,
                intent=intent,
                action_id=generate_id("archivist_"),
                executed=True
            )
        except Exception as e:
            self.logger.error(f"Error archiving: {e}", exc_info=True)
            return Action(
                timestamp=get_timestamp(),
                intent=intent,
                action_id=generate_id("archivist_"),
                executed=False
            )
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on archiving."""
        learnings = f"Archived content cycle: {action.intent.parameters.get('topic', 'N/A')}"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=not result.success
        )

