"""Personality drift system."""

from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from utils.logger import get_logger
from utils.helpers import get_timestamp
from config.defaults import DATA_DIR

logger = get_logger(__name__)

PERSONALITY_FILE = DATA_DIR / "personality.json"


@dataclass
class Personality:
    """Personality traits that drift over time."""
    tension: float = 0.5  # 0.0 = relaxed, 1.0 = tense
    boldness: float = 0.5  # 0.0 = cautious, 1.0 = bold
    depth: float = 0.5  # 0.0 = surface, 1.0 = deep
    
    # Evolution parameters
    last_update: str = field(default_factory=get_timestamp)
    drift_rate: float = 0.01  # How fast personality changes
    
    def drift(self, experience: Dict[str, Any]):
        """Drift personality based on experience."""
        # Experience factors
        rejection_rate = experience.get("rejection_rate", 0.5)
        quality_avg = experience.get("quality_avg", 0.5)
        publication_success = experience.get("publication_success", True)
        
        # Tension increases with rejections, decreases with success
        tension_change = (rejection_rate - 0.5) * self.drift_rate
        self.tension = max(0.0, min(1.0, self.tension + tension_change))
        
        # Boldness increases with success, decreases with repeated failures
        boldness_change = (quality_avg - 0.5) * self.drift_rate if publication_success else -self.drift_rate * 0.5
        self.boldness = max(0.0, min(1.0, self.boldness + boldness_change))
        
        # Depth increases over time (learning)
        self.depth = min(1.0, self.depth + self.drift_rate * 0.1)
        
        self.last_update = get_timestamp()
        logger.debug(f"Personality drifted: tension={self.tension:.2f}, boldness={self.boldness:.2f}, depth={self.depth:.2f}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tension": self.tension,
            "boldness": self.boldness,
            "depth": self.depth,
            "last_update": self.last_update,
            "drift_rate": self.drift_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Personality":
        """Create from dictionary."""
        return cls(
            tension=data.get("tension", 0.5),
            boldness=data.get("boldness", 0.5),
            depth=data.get("depth", 0.5),
            last_update=data.get("last_update", get_timestamp()),
            drift_rate=data.get("drift_rate", 0.01)
        )
    
    def get_style_modifiers(self) -> Dict[str, Any]:
        """Get style modifiers based on personality."""
        return {
            "risk_taking": self.boldness,
            "detail_level": self.depth,
            "urgency": self.tension,
            "experimentation": self.boldness * (1 - self.tension)
        }


class PersonalityManager:
    """Manages personality drift."""
    
    def __init__(self, personality_file: Path = PERSONALITY_FILE):
        self.personality_file = personality_file
        self.personality = self._load()
        self.logger = logger
    
    def _load(self) -> Personality:
        """Load personality from file."""
        if self.personality_file.exists():
            try:
                with open(self.personality_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Personality.from_dict(data)
            except Exception as e:
                self.logger.error(f"Error loading personality: {e}")
        
        return Personality()
    
    def save(self):
        """Save personality to file."""
        try:
            self.personality_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.personality_file, "w", encoding="utf-8") as f:
                json.dump(self.personality.to_dict(), f, indent=2, ensure_ascii=False)
            self.logger.debug("Personality saved")
        except Exception as e:
            self.logger.error(f"Error saving personality: {e}")
    
    def update_from_experience(self, experience: Dict[str, Any]):
        """Update personality based on experience."""
        self.personality.drift(experience)
        self.save()
    
    def get_personality(self) -> Personality:
        """Get current personality."""
        return self.personality
    
    def get_style_modifiers(self) -> Dict[str, Any]:
        """Get style modifiers for content generation."""
        return self.personality.get_style_modifiers()

