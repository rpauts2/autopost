"""Memory data models."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: str
    timestamp: str
    entry_type: str  # topic, content, decision, rejection, etc.
    data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "entry_type": self.entry_type,
            "data": self.data,
            "embedding": self.embedding,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            entry_type=data["entry_type"],
            data=data["data"],
            embedding=data.get("embedding"),
            tags=data.get("tags", [])
        )


@dataclass
class ContentMemory:
    """Content memory entry."""
    id: str
    timestamp: str
    topic: str
    content: str
    platform: str
    style: str
    quality_score: Optional[float] = None
    published: bool = False
    rejected: bool = False
    rejection_reason: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionMemory:
    """Decision memory entry."""
    id: str
    timestamp: str
    decision_type: str
    context: Dict[str, Any]
    decision: str
    reasoning: str
    outcome: Optional[str] = None

