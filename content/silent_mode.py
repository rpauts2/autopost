"""Silent mode - сознательное молчание для повышения ценности."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


@dataclass
class SilentPeriod:
    """Period of conscious silence."""
    start_time: str
    end_time: str
    reason: str
    duration_hours: int


class SilentModeManager:
    """Manages silent periods."""
    
    def __init__(self):
        self.current_silent_period: Optional[SilentPeriod] = None
        self.silent_periods_history: List[SilentPeriod] = []
        self.logger = logger
    
    def start_silent_period(self, duration_hours: int = 24, reason: str = "Повышение ценности постов"):
        """Start a silent period."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(hours=duration_hours)
        
        self.current_silent_period = SilentPeriod(
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            reason=reason,
            duration_hours=duration_hours
        )
        
        self.logger.info(f"Started silent period: {reason} (until {end.isoformat()})")
    
    def is_silent(self) -> bool:
        """Check if currently in silent mode."""
        if not self.current_silent_period:
            return False
        
        try:
            end_time = datetime.fromisoformat(self.current_silent_period.end_time.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if now >= end_time:
                # Silent period ended
                self.silent_periods_history.append(self.current_silent_period)
                self.current_silent_period = None
                self.logger.info("Silent period ended")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking silent mode: {e}")
            return False
    
    def should_publish_during_silence(self) -> tuple[bool, str]:
        """Check if should publish during silence (only for exceptional content)."""
        if not self.is_silent():
            return True, ""
        
        # During silence, only publish exceptional content
        return False, f"Тихий режим активен: {self.current_silent_period.reason} (до {self.current_silent_period.end_time})"
    
    def auto_trigger_silence(
        self,
        recent_publications: int,
        quality_trend: float,
        hours_since_last: float
    ):
        """Automatically trigger silent period based on metrics."""
        # Trigger silence if:
        # 1. Too many publications recently (low value)
        # 2. Quality is declining
        # 3. Publishing too frequently
        
        should_silence = False
        reason = ""
        
        if recent_publications > 5:  # Too many in short time
            should_silence = True
            reason = "Слишком много публикаций - нужна пауза для повышения ценности"
        elif quality_trend < 0.6 and hours_since_last < 12:
            should_silence = True
            reason = "Качество падает при частых публикациях - тихий режим"
        
        if should_silence and not self.is_silent():
            self.start_silent_period(duration_hours=24, reason=reason)
    
    def get_status(self) -> Dict[str, Any]:
        """Get silent mode status."""
        return {
            "is_silent": self.is_silent(),
            "current_period": {
                "start": self.current_silent_period.start_time if self.current_silent_period else None,
                "end": self.current_silent_period.end_time if self.current_silent_period else None,
                "reason": self.current_silent_period.reason if self.current_silent_period else None
            } if self.current_silent_period else None,
            "total_periods": len(self.silent_periods_history)
        }

