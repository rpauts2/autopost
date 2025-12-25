"""Main entry point."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from core.entity import Entity
from agents.thinker import ThinkerAgent
from agents.writer import WriterAgent
from agents.editor import EditorAgent
from agents.critic import CriticAgent
from agents.meta_critic import MetaCriticAgent
from agents.sense_editor import SenseEditorAgent
from agents.publisher import PublisherAgent
from agents.archivist import ArchivistAgent
from ui.main import run_ui

logger = get_logger(__name__)


async def initialize_entity():
    """Initialize the entity with all agents."""
    logger.info("Initializing entity...")
    
    entity = Entity()
    
    # Initialize entity
    await entity.initialize()
    
    # Register agents
    entity.orchestrator.register_agent(ThinkerAgent(entity.context))
    entity.orchestrator.register_agent(WriterAgent(entity.context))
    entity.orchestrator.register_agent(SenseEditorAgent(entity.context))  # Sense Editor
    entity.orchestrator.register_agent(EditorAgent(entity.context))
    entity.orchestrator.register_agent(CriticAgent(entity.context))
    entity.orchestrator.register_agent(MetaCriticAgent(entity.context))  # Meta-critic
    entity.orchestrator.register_agent(PublisherAgent(entity.context))
    entity.orchestrator.register_agent(ArchivistAgent(entity.context))
    
    logger.info("Entity initialized with all agents")
    
    return entity


def main():
    """Main entry point."""
    logger.info("Starting AutoPosst...")
    
    # Create event loop
    if sys.platform == 'win32':
        # Windows needs specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Initialize entity
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    entity = loop.run_until_complete(initialize_entity())
    
    # Run UI (blocking)
    try:
        run_ui(entity=entity)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Cleanup
        if entity and entity.running:
            loop.run_until_complete(entity.stop())
        loop.close()
    
    logger.info("AutoPosst stopped")


if __name__ == "__main__":
    main()

