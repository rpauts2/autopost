"""Main entity - autonomous AI content system."""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from utils.logger import get_logger
from config.settings import get_settings, update_settings
from config.goals import get_goals
from agents.base import AgentContext
from core.orchestrator import Orchestrator
from core.scheduler import Scheduler
from ai.router import AIRouter
from ai.gemini_client import GeminiClient
from memory.storage import MemoryStorage
from memory.index import MemoryIndex
from core.internal_monitor import InternalStateMonitor
from core.explanation import ExplanationTracker
from core.personality import PersonalityManager
from core.platform_manager import PlatformManager
from ai.image_generator import ImageGenerator
from content.banality_filter import BanalityFilter, SemanticDensityChecker
from content.cluster_manager import ClusterManager
from content.style_profiles import StyleProfileManager
from content.deferred_thinking import DeferredThinkingManager
from content.silent_mode import SilentModeManager
from content.ab_testing import ABTester
from memory.refactoring import MemoryRefactoring

logger = get_logger(__name__)


class Entity:
    """Main autonomous entity."""
    
    def __init__(self):
        self.logger = logger
        self.settings = get_settings()
        self.goals = get_goals()
        
        # Initialize core components
        self.ai_client = GeminiClient(api_key=self.settings.gemini_api_key)
        self.ai_router = AIRouter(self.ai_client, self.settings.gemini_api_key)
        self.memory_storage = MemoryStorage()
        self.memory_index = MemoryIndex(self.memory_storage)
        
        # Personality manager (drift over time) - needs to be early for context
        self.personality_manager = PersonalityManager()
        
        # Platform manager
        self.platform_manager = PlatformManager()
        
        # Image generator
        self.image_generator = ImageGenerator(self.ai_router)
        
        # Content modules
        self.banality_filter = BanalityFilter()
        self.density_checker = SemanticDensityChecker()
        self.cluster_manager = ClusterManager(memory_index=self.memory_index)
        self.style_profile_manager = StyleProfileManager(memory_index=self.memory_index)
        self.deferred_thinking = DeferredThinkingManager()
        self.silent_mode = SilentModeManager()
        self.ab_tester = ABTester(ai_router=self.ai_router)
        self.memory_refactoring = MemoryRefactoring(
            memory_storage=self.memory_storage,
            memory_index=self.memory_index
        )
        
        # Agent context
        self.context = AgentContext()
        self.context.memory = self.memory_index
        self.context.ai_router = self.ai_router
        self.context.goals = self.goals
        self.context.settings = self.settings
        self.context.personality = self.personality_manager.get_personality()
        self.context.banality_filter = self.banality_filter
        self.context.density_checker = self.density_checker
        self.context.cluster_manager = self.cluster_manager
        self.context.style_profile_manager = self.style_profile_manager
        self.context.deferred_thinking = self.deferred_thinking
        self.context.silent_mode = self.silent_mode
        self.context.ab_tester = self.ab_tester
        
        # Orchestrator
        self.orchestrator = Orchestrator(self.context)
        
        # Internal state monitor (autonomous triggers)
        self.internal_monitor = InternalStateMonitor(
            memory_index=self.memory_index,
            goals=self.goals
        )
        
        # Explanation tracker (self-explanation mode)
        self.explanation_tracker = ExplanationTracker(memory_storage=self.memory_storage)
        self.context.explanation_tracker = self.explanation_tracker
        
        # Scheduler with internal monitor
        self.scheduler = Scheduler(internal_monitor=self.internal_monitor)
        
        # State
        self.running = False
        self.current_intent: Optional[str] = None
        self.status = "initialized"
        self.initialized = False
        
        # Metrics
        self.metrics = {
            "cycles_completed": 0,
            "content_created": 0,
            "content_published": 0,
            "content_rejected": 0,
        }
    
    async def initialize(self):
        """Initialize the entity."""
        self.logger.info("Initializing entity...")
        
        # Configure AI if key is set
        if self.settings.gemini_api_key:
            try:
                self.ai_client.configure(self.settings.gemini_api_key)
            except Exception as e:
                self.logger.error(f"Failed to configure AI: {e}")
        
        # Setup scheduler
        self.scheduler.add_task(
            name="content_creation_cycle",
            callback=self._content_creation_cycle,
            interval=3600,  # 1 hour default
            enabled=self.settings.auto_start
        )
        
        # Setup memory refactoring (weekly)
        self.scheduler.add_task(
            name="memory_refactoring",
            callback=self._memory_refactoring_cycle,
            interval=604800,  # 7 days
            enabled=True
        )
        
        self.status = "ready"
        self.initialized = True
        self.logger.info("Entity initialized")
    
    async def start(self):
        """Start the entity."""
        if self.running:
            self.logger.warning("Entity already running")
            return
        
        # Initialize if needed
        if not self.initialized:
            await self.initialize()
        
        self.running = True
        self.status = "running"
        
        # Start scheduler
        await self.scheduler.start()
        
        # Trigger initial content creation cycle immediately
        asyncio.create_task(self._content_creation_cycle())
        
        self.logger.info("Entity started - initial cycle triggered")
    
    async def stop(self):
        """Stop the entity."""
        self.running = False
        self.status = "stopping"
        
        # Stop scheduler
        await self.scheduler.stop()
        
        self.status = "stopped"
        self.logger.info("Entity stopped")
    
    async def _content_creation_cycle(self):
        """Main content creation cycle."""
        self.logger.info("Starting content creation cycle")
        self.current_intent = "create_content"
        
        try:
            context = {
                "entity": self,
                "goals": self.goals,
                "settings": self.settings,
                "timestamp": self.context.shared_data.get("timestamp")
            }
            
            # Store entity in shared_data for agents
            self.context.shared_data["entity"] = self
            
            result = await self.orchestrator.execute_content_creation_pipeline(context)
            
            self.metrics["cycles_completed"] += 1
            if result.get("content_created"):
                self.metrics["content_created"] += 1
            if result.get("content_published"):
                self.metrics["content_published"] += 1
            if result.get("content_rejected"):
                self.metrics["content_rejected"] += 1
            
            self.current_intent = None
            self.logger.info("Content creation cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in content creation cycle: {e}", exc_info=True)
            self.current_intent = None
    
    async def _memory_refactoring_cycle(self):
        """Memory refactoring cycle."""
        self.logger.info("Starting memory refactoring cycle")
        try:
            # Refactor old memories
            result = await self.memory_refactoring.refactor_old_memories(days_old=30)
            self.logger.info(f"Memory refactoring completed: {result}")
            
            # Clean redundant topics
            clean_result = await self.memory_refactoring.clean_redundant_topics()
            self.logger.info(f"Topic cleaning completed: {clean_result}")
        except Exception as e:
            self.logger.error(f"Error in memory refactoring: {e}", exc_info=True)
    
    def get_status(self) -> Dict[str, Any]:
        """Get entity status."""
        return {
            "status": self.status,
            "running": self.running,
            "current_intent": self.current_intent,
            "metrics": self.metrics.copy(),
            "agents": {
                name: agent.get_metrics()
                for name, agent in self.orchestrator.agents.items()
            }
        }
    
    def update_settings(self, **kwargs):
        """Update settings."""
        self.settings = update_settings(**kwargs)
        self.context.settings = self.settings
        if "gemini_api_key" in kwargs:
            try:
                self.ai_client.configure(kwargs["gemini_api_key"])
            except Exception as e:
                self.logger.error(f"Failed to update AI key: {e}")
    
    def update_goals(self, **kwargs):
        """Update goals."""
        from config.goals import update_goals as update_goals_func
        self.goals = update_goals_func(**kwargs)
        self.context.goals = self.goals

