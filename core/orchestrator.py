# core/orchestrator.py

from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """
    Simple, WORKING orchestrator.
    Executes agents sequentially.
    """

    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.pipeline = [
            "thinker",
            "writer",
            "editor",
            "critic",
            "publisher",
            "archivist",
        ]

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.warning("=== CONTENT PIPELINE STARTED ===")
        shared_data = context.copy()

        for name in self.pipeline:
            agent = self.agents.get(name)
            if not agent:
                logger.warning(f"Agent '{name}' not found, skipping")
                continue

            logger.warning(f">>> Agent: {name}")

            try:
                result = await agent.act(shared_data)
                if isinstance(result, dict):
                    shared_data.update(result)
            except Exception as e:
                logger.error(f"Agent {name} failed: {e}", exc_info=True)
                break

        logger.warning("=== CONTENT PIPELINE FINISHED ===")
        return shared_data
