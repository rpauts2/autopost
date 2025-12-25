"""Base agent class."""

from abc import ABC
from typing import Dict, Any, Optional
from core.intent_loop import IntentLoop, Observation, Thought, Intent, Action, Result, Reflection
from utils.logger import get_logger
from utils.helpers import generate_id, get_timestamp


class AgentContext:
    """Context shared between agents."""
    
    def __init__(self):
        self.memory = None  # Will be set by Entity
        self.ai_router = None  # Will be set by Entity
        self.goals = None  # Will be set by Entity
        self.settings = None  # Will be set by Entity
        self.explanation_tracker = None  # Will be set by Entity
        self.personality = None  # Will be set by Entity
        self.banality_filter = None  # Will be set by Entity
        self.density_checker = None  # Will be set by Entity
        self.cluster_manager = None  # Will be set by Entity
        self.style_profile_manager = None  # Will be set by Entity
        self.deferred_thinking = None  # Will be set by Entity
        self.silent_mode = None  # Will be set by Entity
        self.ab_tester = None  # Will be set by Entity
        self.shared_data: Dict[str, Any] = {}


class BaseAgent(IntentLoop, ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, context: AgentContext):
        super().__init__(name)
        self.context = context
        self.logger = get_logger(f"agent.{name}")
        self.enabled = True
        self.metrics = {
            "cycles_completed": 0,
            "cycles_failed": 0,
            "last_cycle_time": None,
        }
    
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Default observation - can be overridden."""
        return Observation(
            timestamp=get_timestamp(),
            context=context,
            data={}
        )
    
    async def think(self, observation: Observation) -> Thought:
        """Default thinking - must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement think()")
    
    async def form_intent(self, thought: Thought) -> Intent:
        """Default intent formation - can be overridden."""
        return Intent(
            timestamp=get_timestamp(),
            thought=thought,
            action_type="no_action",
            parameters={},
            confidence=0.0
        )
    
    async def act(self, intent: Intent) -> Action:
        """Default action - must be overridden by subclasses."""
        action = Action(
            timestamp=get_timestamp(),
            intent=intent,
            action_id=generate_id(f"{self.name}_"),
            executed=False
        )
        return action
    
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Default reflection."""
        learnings = f"Action {action.action_id} completed with success={result.success}"
        if result.error:
            learnings += f". Error: {result.error}"
        
        return Reflection(
            timestamp=get_timestamp(),
            action=action,
            result=result,
            learnings=learnings,
            should_retry=not result.success and result.error and "timeout" not in result.error.lower()
        )
    
    def is_enabled(self) -> bool:
        """Check if agent is enabled."""
        return self.enabled
    
    def disable(self):
        """Disable the agent."""
        self.enabled = False
        self.logger.info(f"Agent {self.name} disabled")
    
    def enable(self):
        """Enable the agent."""
        self.enabled = True
        self.logger.info(f"Agent {self.name} enabled")
    
    def update_metrics(self, success: bool, duration: float):
        """Update agent metrics."""
        if success:
            self.metrics["cycles_completed"] += 1
        else:
            self.metrics["cycles_failed"] += 1
        self.metrics["last_cycle_time"] = duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return self.metrics.copy()

