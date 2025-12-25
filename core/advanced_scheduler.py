"""Advanced scheduler with schedule and night mode."""

import asyncio
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timedelta, time

from utils.logger import get_logger
from config.defaults import SCHEDULER_CHECK_INTERVAL

logger = get_logger(__name__)


class AdvancedScheduler:
    """Advanced scheduler with schedule and night mode."""
    
    def __init__(self, check_interval: int = SCHEDULER_CHECK_INTERVAL):
        self.check_interval = check_interval
        self.tasks: List[Dict[str, Any]] = []
        self.running = False
        self._task = None
        self.logger = logger
        
        # Night mode settings
        self.night_mode_enabled = False
        self.night_mode_start = time(22, 0)  # 22:00
        self.night_mode_end = time(8, 0)  # 8:00
        
        # Schedule patterns
        self.schedule_patterns: Dict[str, List[time]] = {
            "morning": [time(9, 0), time(10, 0), time(11, 0)],
            "afternoon": [time(14, 0), time(15, 0), time(16, 0)],
            "evening": [time(19, 0), time(20, 0)],
        }
        self.active_schedule = "moderate"  # moderate, frequent, rare, custom
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        interval: Optional[int] = None,
        schedule_times: Optional[List[time]] = None,
        enabled: bool = True,
        skip_night_mode: bool = False
    ):
        """Add a scheduled task."""
        task = {
            "name": name,
            "callback": callback,
            "interval": interval,
            "schedule_times": schedule_times,  # Specific times to run
            "enabled": enabled,
            "skip_night_mode": skip_night_mode,
            "last_run": None,
            "next_run": None,
        }
        self.tasks.append(task)
        self.logger.info(f"Added scheduled task: {name}")
    
    def set_night_mode(self, enabled: bool, start_time: time = None, end_time: time = None):
        """Configure night mode."""
        self.night_mode_enabled = enabled
        if start_time:
            self.night_mode_start = start_time
        if end_time:
            self.night_mode_end = end_time
        self.logger.info(f"Night mode: {'enabled' if enabled else 'disabled'}")
    
    def set_schedule(self, schedule_type: str):
        """Set schedule pattern."""
        self.active_schedule = schedule_type
        self.logger.info(f"Schedule set to: {schedule_type}")
    
    def is_night_mode(self) -> bool:
        """Check if currently in night mode."""
        if not self.night_mode_enabled:
            return False
        
        now = datetime.now().time()
        
        # Handle night mode that spans midnight
        if self.night_mode_start > self.night_mode_end:
            # Night mode spans midnight (e.g., 22:00 to 8:00)
            return now >= self.night_mode_start or now <= self.night_mode_end
        else:
            # Normal time range
            return self.night_mode_start <= now <= self.night_mode_end
    
    def get_next_schedule_time(self, schedule_times: List[time]) -> Optional[datetime]:
        """Get next scheduled time from list."""
        if not schedule_times:
            return None
        
        now = datetime.now()
        today_times = [datetime.combine(now.date(), t) for t in schedule_times]
        
        # Find next time today
        for scheduled_time in sorted(today_times):
            if scheduled_time > now:
                return scheduled_time
        
        # If no time today, use first time tomorrow
        if today_times:
            first_time_tomorrow = datetime.combine(
                now.date() + timedelta(days=1),
                min(schedule_times)
            )
            return first_time_tomorrow
        
        return None
    
    def should_run_task(self, task: Dict[str, Any]) -> bool:
        """Determine if task should run now."""
        if not task["enabled"]:
            return False
        
        # Check night mode
        if self.is_night_mode() and not task.get("skip_night_mode", False):
            return False
        
        now = datetime.now()
        
        # Check schedule times
        if task.get("schedule_times"):
            next_time = self.get_next_schedule_time(task["schedule_times"])
            if next_time and now >= next_time:
                return True
            return False
        
        # Check interval
        if task.get("interval"):
            if task["next_run"] is None:
                task["next_run"] = now
            return now >= task["next_run"]
        
        return False
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        self.logger.info("Advanced scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Advanced scheduler stopped")
    
    async def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now()
                
                for task in self.tasks:
                    if self.should_run_task(task):
                        try:
                            self.logger.info(f"Running scheduled task: {task['name']}")
                            if asyncio.iscoroutinefunction(task["callback"]):
                                await task["callback"]()
                            else:
                                task["callback"]()
                            
                            task["last_run"] = now
                            
                            # Set next run time
                            if task.get("schedule_times"):
                                task["next_run"] = self.get_next_schedule_time(task["schedule_times"])
                            elif task.get("interval"):
                                task["next_run"] = now + timedelta(seconds=task["interval"])
                        except Exception as e:
                            self.logger.error(f"Error in scheduled task {task['name']}: {e}", exc_info=True)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

