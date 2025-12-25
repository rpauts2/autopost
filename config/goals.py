"""Goals management."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .defaults import DATA_DIR

GOALS_FILE = DATA_DIR / "goals.json"


class ContentGoal(BaseModel):
    """Individual content goal."""
    
    id: str
    description: str
    priority: int = Field(default=5, ge=1, le=10)  # 1-10
    active: bool = Field(default=True)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default="")
    updated_at: str = Field(default="")


class SystemGoals(BaseModel):
    """System goals configuration."""
    
    global_quality: str = Field(default="high")  # high, medium, low
    posting_frequency: str = Field(default="moderate")  # frequent, moderate, rare
    style_preference: str = Field(default="authentic")
    preferred_topics: List[str] = Field(default_factory=list)
    avoid_repetition: bool = Field(default=True)
    platform_optimization: bool = Field(default=True)
    
    content_goals: List[ContentGoal] = Field(default_factory=list)
    
    # Constraints
    max_posts_per_day: Optional[int] = Field(default=None)
    min_time_between_posts: int = Field(default=3600)  # seconds
    avoid_topics: List[str] = Field(default_factory=list)
    
    # Quality thresholds
    min_content_quality_score: float = Field(default=0.7, ge=0.0, le=1.0)
    require_critic_approval: bool = Field(default=True)


class GoalsManager:
    """Manages system goals."""
    
    def __init__(self, goals_file: Path = GOALS_FILE):
        self.goals_file = goals_file
        self._goals: Optional[SystemGoals] = None
    
    def load(self) -> SystemGoals:
        """Load goals from file."""
        if self._goals is not None:
            return self._goals
        
        if self.goals_file.exists():
            try:
                with open(self.goals_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._goals = SystemGoals(**data)
            except Exception as e:
                print(f"Error loading goals: {e}, using defaults")
                self._goals = SystemGoals()
        else:
            self._goals = SystemGoals()
        
        return self._goals
    
    def save(self, goals: Optional[SystemGoals] = None) -> None:
        """Save goals to file."""
        if goals is None:
            goals = self._goals
        
        if goals is None:
            return
        
        try:
            self.goals_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.goals_file, "w", encoding="utf-8") as f:
                json.dump(goals.model_dump(), f, indent=2, ensure_ascii=False)
            self._goals = goals
        except Exception as e:
            print(f"Error saving goals: {e}")
    
    def get(self) -> SystemGoals:
        """Get current goals."""
        return self.load()
    
    def add_content_goal(self, goal: ContentGoal) -> None:
        """Add a content goal."""
        goals = self.load()
        goals.content_goals.append(goal)
        self.save(goals)
    
    def remove_content_goal(self, goal_id: str) -> bool:
        """Remove a content goal."""
        goals = self.load()
        goals.content_goals = [g for g in goals.content_goals if g.id != goal_id]
        self.save(goals)
        return True
    
    def update_content_goal(self, goal_id: str, **kwargs) -> bool:
        """Update a content goal."""
        goals = self.load()
        for goal in goals.content_goals:
            if goal.id == goal_id:
                for key, value in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                self.save(goals)
                return True
        return False


# Global goals manager instance
_goals_manager = GoalsManager()


def get_goals() -> SystemGoals:
    """Get system goals."""
    return _goals_manager.get()


def update_goals(**kwargs) -> SystemGoals:
    """Update system goals."""
    goals = _goals_manager.get()
    for key, value in kwargs.items():
        if hasattr(goals, key):
            setattr(goals, key, value)
    _goals_manager.save(goals)
    return goals

