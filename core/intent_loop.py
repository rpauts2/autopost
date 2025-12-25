"""Intent loop implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Observation:
    """Observation phase data."""
    timestamp: str
    context: Dict[str, Any]
    data: Any
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Thought:
    """Thought phase data."""
    timestamp: str
    observation: Observation
    analysis: str
    considerations: Dict[str, Any]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Intent:
    """Intent with type and payload."""
    type: str
    payload: dict
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Decision:
    """Decision with optional intent."""
    intent: Optional[Intent] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.intent is None:
            logger.warning("Decision created without an intent")


@dataclass
class Action:
    """Action phase data."""
    timestamp: str
    intent: Intent
    action_id: str
    executed: bool = False
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Result:
    """Action result."""
    action: Action
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Reflection:
    """Reflection phase data."""
    timestamp: str
    action: Action
    result: Result
    learnings: str
    should_retry: bool = False
    next_intent: Optional[Intent] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class IntentLoop(ABC):
    """Base class for intent loop implementation."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")
        self._current_cycle: Optional[Dict[str, Any]] = None
    
    async def run_cycle(self, context: Dict[str, Any]) -> Reflection:
        """Execute a full intent loop cycle."""
        cycle_id = f"{self.name}_{datetime.now(timezone.utc).timestamp()}"
        self.logger.info(f"Starting intent cycle: {cycle_id}")
        
        try:
            # 1. Observation
            self.logger.debug("Phase: Observation")
            observation = await self.observe(context)
            self.logger.debug(f"Observation completed: {type(observation.data).__name__}")
            
            # 2. Thought
            self.logger.debug("Phase: Thought")
            thought = await self.think(observation)
            self.logger.debug(f"Thought completed: {thought.analysis[:100]}...")
            
            # 3. Intent
            self.logger.debug("Phase: Intent")
            intent = await self.form_intent(thought)
            self.logger.info(f"Intent formed: {intent.action_type} (confidence: {intent.confidence})")
            
            # 4. Action
            self.logger.debug("Phase: Action")
            action = await self.act(intent)
            self.logger.info(f"Action executed: {action.action_id}")
            
            # 5. Reflection
            self.logger.debug("Phase: Reflection")
            # Get data from action or context if available
            action_data = getattr(action, 'result_data', None)
            result = Result(
                action=action,
                success=action.executed,
                data=action_data
            )
            reflection = await self.reflect(action, result)
            self.logger.info(f"Reflection completed: {reflection.learnings[:100]}...")
            
            return reflection
            
        except Exception as e:
            self.logger.error(f"Error in intent cycle {cycle_id}: {e}", exc_info=True)
            # Create error reflection
            if self._current_cycle and 'action' in self._current_cycle:
                action = self._current_cycle['action']
                result = Result(
                    action=action,
                    success=False,
                    data=None,
                    error=str(e)
                )
                from utils.helpers import get_timestamp
                return Reflection(
                    timestamp=get_timestamp(),
                    action=action,
                    result=result,
                    learnings=f"Error occurred: {str(e)}",
                    should_retry=False
                )
            raise
    
    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Observation:
        """Observe the current state."""
        pass
    
    @abstractmethod
    async def think(self, observation: Observation) -> Thought:
        """Analyze observation and form thoughts."""
        pass
    
    @abstractmethod
    async def form_intent(self, thought: Thought) -> Intent:
        """Form an intent based on thought."""
        pass
    
    @abstractmethod
    async def act(self, intent: Intent) -> Action:
        """Execute the intent."""
        pass
    
    @abstractmethod
    async def reflect(self, action: Action, result: Result) -> Reflection:
        """Reflect on the action and result."""
        pass

