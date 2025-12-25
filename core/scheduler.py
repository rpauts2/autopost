"""Task scheduler for autonomous operation."""

import asyncio
from typing import Callable, Optional
from datetime import datetime, timedelta

from utils.logger import get_logger
from config.defaults import SCHEDULER_CHECK_INTERVAL
from core.internal_monitor import InternalStateMonitor

logger = get_logger(__name__)


class Scheduler:
    """Scheduler for autonomous task execution."""
    
    def __init__(self, check_interval: int = SCHEDULER_CHECK_INTERVAL, internal_monitor: Optional[InternalStateMonitor] = None):
        self.check_interval = check_interval
        self.tasks: list[dict] = []
        self.running = False
        self._task = None
        self.logger = logger
        self.internal_monitor = internal_monitor
        self._last_trigger_check = None
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        interval: int,
        enabled: bool = True
    ):
        """Add a scheduled task."""
        task = {
            "name": name,
            "callback": callback,
            "interval": interval,
            "enabled": enabled,
            "last_run": None,
            "next_run": datetime.now() if enabled else None
        }
        self.tasks.append(task)
        self.logger.info(f"Added scheduled task: {name} (interval: {interval}s)")
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        self.logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Scheduler stopped")
    
    async def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now()
                
                # Check internal triggers (autonomous will)
                if self.internal_monitor:
                    try:
                        triggers = await self.internal_monitor.check_state()
                        if triggers:
                            urgent_trigger = self.internal_monitor.get_most_urgent_trigger()
                            if urgent_trigger and urgent_trigger.urgency >= 0.6:
                                self.logger.info(f"Internal trigger activated: {urgent_trigger.name} (urgency: {urgent_trigger.urgency:.2f})")
                                # Trigger content creation cycle if available
                                content_task = next((t for t in self.tasks if t["name"] == "content_creation_cycle"), None)
                                if content_task and content_task["enabled"]:
                                    content_task["next_run"] = now  # Execute immediately
                    except Exception as e:
                        self.logger.error(f"Error checking internal triggers: {e}", exc_info=True)
                
                for task in self.tasks:
                    if not task["enabled"]:
                        continue
                    
                    # Check if it's time to run
                    if task["next_run"] is None:
                        task["next_run"] = now
                    
                    if now >= task["next_run"]:
                        try:
                            self.logger.info(f"Running scheduled task: {task['name']}")
                            if asyncio.iscoroutinefunction(task["callback"]):
                                await task["callback"]()
                            else:
                                task["callback"]()
                            
                            task["last_run"] = now
                            task["next_run"] = now + timedelta(seconds=task["interval"])
                        except Exception as e:
                            self.logger.error(f"Error in scheduled task {task['name']}: {e}", exc_info=True)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    def enable_task(self, name: str):
        """Enable a task."""
        for task in self.tasks:
            if task["name"] == name:
                task["enabled"] = True
                task["next_run"] = datetime.now()
                self.logger.info(f"Enabled task: {name}")
                return
    
    def disable_task(self, name: str):
        """Disable a task."""
        for task in self.tasks:
            if task["name"] == name:
                task["enabled"] = False
                task["next_run"] = None
                self.logger.info(f"Disabled task: {name}")
                return

