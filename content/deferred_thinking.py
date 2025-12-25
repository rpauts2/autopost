"""Deferred thinking - идеи отлеживаются и возвращаются."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from utils.logger import get_logger
from utils.helpers import get_timestamp
from memory.embeddings import generate_embedding
from config.defaults import DATA_DIR

logger = get_logger(__name__)

DEFERRED_IDEAS_FILE = DATA_DIR / "deferred_ideas.json"


@dataclass
class DeferredIdea:
    """Idea that is deferred for later consideration."""
    id: str
    topic: str
    reasoning: str
    created_at: str
    defer_days: int  # Days to defer
    should_use_at: str  # When to reconsider
    cluster_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeferredThinkingManager:
    """Manages deferred ideas."""
    
    def __init__(self):
        self.ideas: Dict[str, DeferredIdea] = {}
        self.logger = logger
        self._load_ideas()
    
    def _load_ideas(self):
        """Load deferred ideas from file."""
        if DEFERRED_IDEAS_FILE.exists():
            try:
                with open(DEFERRED_IDEAS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for idea_id, idea_data in data.items():
                        self.ideas[idea_id] = DeferredIdea(**idea_data)
                self.logger.info(f"Loaded {len(self.ideas)} deferred ideas")
            except Exception as e:
                self.logger.error(f"Error loading deferred ideas: {e}")
    
    def _save_ideas(self):
        """Save deferred ideas to file."""
        try:
            DEFERRED_IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                idea_id: {
                    "id": idea.id,
                    "topic": idea.topic,
                    "reasoning": idea.reasoning,
                    "created_at": idea.created_at,
                    "defer_days": idea.defer_days,
                    "should_use_at": idea.should_use_at,
                    "cluster_id": idea.cluster_id,
                    "metadata": idea.metadata
                }
                for idea_id, idea in self.ideas.items()
            }
            with open(DEFERRED_IDEAS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving deferred ideas: {e}")
    
    def defer_idea(
        self,
        topic: str,
        reasoning: str,
        defer_days: int = 3,
        cluster_id: Optional[str] = None
    ) -> DeferredIdea:
        """Defer an idea for later."""
        from utils.helpers import generate_id
        
        created_at = datetime.now(timezone.utc)
        should_use_at = (created_at + timedelta(days=defer_days)).isoformat()
        
        idea = DeferredIdea(
            id=generate_id("idea_"),
            topic=topic,
            reasoning=reasoning,
            created_at=created_at.isoformat(),
            defer_days=defer_days,
            should_use_at=should_use_at,
            cluster_id=cluster_id
        )
        
        self.ideas[idea.id] = idea
        self._save_ideas()
        self.logger.info(f"Deferred idea: {topic} (will reconsider in {defer_days} days)")
        
        return idea
    
    def get_ready_ideas(self) -> List[DeferredIdea]:
        """Get ideas that are ready to be reconsidered."""
        now = datetime.now(timezone.utc)
        ready = []
        
        for idea in self.ideas.values():
            try:
                use_at = datetime.fromisoformat(idea.should_use_at.replace('Z', '+00:00'))
                if now >= use_at:
                    ready.append(idea)
            except Exception as e:
                self.logger.error(f"Error parsing date for idea {idea.id}: {e}")
        
        return sorted(ready, key=lambda x: x.should_use_at)
    
    def use_idea(self, idea_id: str) -> Optional[DeferredIdea]:
        """Mark idea as used and remove it."""
        if idea_id in self.ideas:
            idea = self.ideas.pop(idea_id)
            self._save_ideas()
            self.logger.info(f"Used deferred idea: {idea.topic}")
            return idea
        return None
    
    def extend_deferral(self, idea_id: str, additional_days: int = 3):
        """Extend deferral period for an idea."""
        if idea_id in self.ideas:
            idea = self.ideas[idea_id]
            current_date = datetime.fromisoformat(idea.should_use_at.replace('Z', '+00:00'))
            new_date = current_date + timedelta(days=additional_days)
            idea.should_use_at = new_date.isoformat()
            idea.defer_days += additional_days
            self._save_ideas()
            self.logger.info(f"Extended deferral for idea {idea_id} by {additional_days} days")

