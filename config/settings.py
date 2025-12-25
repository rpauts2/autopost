"""System settings management."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .defaults import BASE_DIR, DATA_DIR

SETTINGS_FILE = DATA_DIR / "settings.json"


class SystemSettings(BaseModel):
    """System-wide settings."""
    
    # AI Configuration
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    default_model: str = Field(default="gemini-2.0-flash-exp")
    fallback_model: str = Field(default="gemini-1.5-pro")
    
    # Agent Configuration
    enable_thinker: bool = Field(default=True)
    enable_writer: bool = Field(default=True)
    enable_editor: bool = Field(default=True)
    enable_critic: bool = Field(default=True)
    enable_publisher: bool = Field(default=True)
    enable_archivist: bool = Field(default=True)
    
    # Scheduler
    auto_start: bool = Field(default=False)
    scheduler_interval: int = Field(default=60)  # seconds
    
    # Platform Configuration
    enabled_platforms: list[str] = Field(default_factory=list)
    
    # Memory
    memory_enabled: bool = Field(default=True)
    embeddings_enabled: bool = Field(default=True)
    
    # UI
    ui_theme: str = Field(default="dark")
    ui_language: str = Field(default="ru")


class SettingsManager:
    """Manages system settings."""
    
    def __init__(self, settings_file: Path = SETTINGS_FILE):
        self.settings_file = settings_file
        self._settings: Optional[SystemSettings] = None
    
    def load(self) -> SystemSettings:
        """Load settings from file."""
        if self._settings is not None:
            return self._settings
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = SystemSettings(**data)
            except Exception as e:
                print(f"Error loading settings: {e}, using defaults")
                self._settings = SystemSettings()
        else:
            self._settings = SystemSettings()
        
        return self._settings
    
    def save(self, settings: Optional[SystemSettings] = None) -> None:
        """Save settings to file."""
        if settings is None:
            settings = self._settings
        
        if settings is None:
            return
        
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
            self._settings = settings
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self) -> SystemSettings:
        """Get current settings."""
        return self.load()
    
    def update(self, **kwargs) -> SystemSettings:
        """Update settings."""
        settings = self.load()
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        self.save(settings)
        return settings


# Global settings manager instance
_settings_manager = SettingsManager()


def get_settings() -> SystemSettings:
    """Get system settings."""
    return _settings_manager.get()


def update_settings(**kwargs) -> SystemSettings:
    """Update system settings."""
    return _settings_manager.update(**kwargs)


def save_settings() -> None:
    """Save current settings."""
    _settings_manager.save()

