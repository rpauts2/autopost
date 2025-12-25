"""Self-explanation system for actions."""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


@dataclass
class Explanation:
    """Self-explanation for an action."""
    action_id: str
    agent_name: str
    why: str  # Why this action
    why_now: str  # Why now
    why_this_form: str  # Why in this form
    timestamp: str = field(default_factory=get_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExplanationTracker:
    """Tracks explanations for all actions."""
    
    def __init__(self, memory_storage=None):
        self.memory_storage = memory_storage
        self.explanations: Dict[str, Explanation] = {}
        self.logger = logger
    
    def add_explanation(
        self,
        action_id: str,
        agent_name: str,
        why: str,
        why_now: str = "",
        why_this_form: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add an explanation for an action."""
        explanation = Explanation(
            action_id=action_id,
            agent_name=agent_name,
            why=why or "No explanation provided",
            why_now=why_now or "Triggered by standard cycle",
            why_this_form=why_this_form or "Standard form",
            metadata=metadata or {}
        )
        
        self.explanations[action_id] = explanation
        
        # Store in memory if available
        if self.memory_storage:
            try:
                from memory.models import MemoryEntry
                entry = MemoryEntry(
                    id=f"explanation_{action_id}",
                    timestamp=explanation.timestamp,
                    entry_type="explanation",
                    data={
                        "action_id": action_id,
                        "agent_name": agent_name,
                        "why": why,
                        "why_now": why_now,
                        "why_this_form": why_this_form,
                        "metadata": metadata or {}
                    },
                    tags=["explanation", agent_name]
                )
                self.memory_storage.add_entry(entry)
            except Exception as e:
                self.logger.error(f"Error storing explanation: {e}")
        
        self.logger.debug(f"Explanation added for action {action_id}: {why[:50]}...")
    
    def get_explanation(self, action_id: str) -> Optional[Explanation]:
        """Get explanation for an action."""
        return self.explanations.get(action_id)
    
    def get_explanations_for_agent(self, agent_name: str) -> list[Explanation]:
        """Get all explanations for an agent."""
        return [e for e in self.explanations.values() if e.agent_name == agent_name]
    
    def format_explanation(self, action_id: str) -> str:
        """Format explanation as readable text."""
        explanation = self.get_explanation(action_id)
        if not explanation:
            return f"No explanation for action {action_id}"
        
        return f"""
Action: {action_id} ({explanation.agent_name})
Why: {explanation.why}
Why Now: {explanation.why_now}
Why This Form: {explanation.why_this_form}
"""

