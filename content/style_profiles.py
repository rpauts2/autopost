"""Personal style profiles - AI выбирает роль."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import random

from utils.logger import get_logger

logger = get_logger(__name__)


class StyleProfile(Enum):
    """Style profiles."""
    PHILOSOPHER = "philosopher"  # Философ - глубокие размышления
    OBSERVER = "observer"  # Наблюдатель - заметки о жизни
    PROVOCATEUR = "provocateur"  # Провокатор - острые темы
    ANALYST = "analyst"  # Аналитик - разбор явлений
    STORYTELLER = "storyteller"  # Рассказчик - истории и примеры
    MINIMALIST = "minimalist"  # Минималист - кратко и по делу


@dataclass
class ProfileDefinition:
    """Definition of a style profile."""
    profile: StyleProfile
    name: str
    description: str
    characteristics: List[str]
    tone: str
    length_preference: str  # short, medium, long
    emoji_usage: str  # none, minimal, moderate, frequent


PROFILES = {
    StyleProfile.PHILOSOPHER: ProfileDefinition(
        profile=StyleProfile.PHILOSOPHER,
        name="Философ",
        description="Глубокие размышления о смысле, существовании, реальности",
        characteristics=["глубина", "рефлексия", "вопросы без ответов", "абстракция"],
        tone="вдумчивый, медитативный",
        length_preference="long",
        emoji_usage="minimal"
    ),
    StyleProfile.OBSERVER: ProfileDefinition(
        profile=StyleProfile.OBSERVER,
        name="Наблюдатель",
        description="Заметки о жизни, людях, событиях",
        characteristics=["конкретика", "детали", "наблюдения", "жизненность"],
        tone="спокойный, внимательный",
        length_preference="medium",
        emoji_usage="moderate"
    ),
    StyleProfile.PROVOCATEUR: ProfileDefinition(
        profile=StyleProfile.PROVOCATEUR,
        name="Провокатор",
        description="Острые темы, неудобные вопросы, вызов",
        characteristics=["острота", "вызов", "конфликт", "неудобство"],
        tone="резкий, прямой",
        length_preference="medium",
        emoji_usage="moderate"
    ),
    StyleProfile.ANALYST: ProfileDefinition(
        profile=StyleProfile.ANALYST,
        name="Аналитик",
        description="Разбор явлений, причинно-следственные связи",
        characteristics=["анализ", "структура", "логика", "факты"],
        tone="объективный, структурированный",
        length_preference="long",
        emoji_usage="none"
    ),
    StyleProfile.STORYTELLER: ProfileDefinition(
        profile=StyleProfile.STORYTELLER,
        name="Рассказчик",
        description="Истории, примеры, нарративы",
        characteristics=["истории", "примеры", "нарратив", "персонажи"],
        tone="живой, образный",
        length_preference="long",
        emoji_usage="frequent"
    ),
    StyleProfile.MINIMALIST: ProfileDefinition(
        profile=StyleProfile.MINIMALIST,
        name="Минималист",
        description="Кратко, по делу, без лишнего",
        characteristics=["краткость", "суть", "ясность", "лаконичность"],
        tone="прямой, четкий",
        length_preference="short",
        emoji_usage="none"
    ),
}


class StyleProfileManager:
    """Manages style profile selection and usage."""
    
    def __init__(self, memory_index=None):
        self.memory_index = memory_index
        self.current_profile: Optional[StyleProfile] = None
        self.profile_history: List[StyleProfile] = []
        self.logger = logger
    
    def select_profile_for_topic(self, topic: str, recent_profiles: List[StyleProfile] = None) -> StyleProfile:
        """Select appropriate profile for topic."""
        recent_profiles = recent_profiles or self.profile_history[-5:]
        
        # Avoid repeating the same profile too often
        available_profiles = [p for p in StyleProfile if p not in recent_profiles[-2:]]
        if not available_profiles:
            available_profiles = list(StyleProfile)
        
        # For now, random selection (in production would use AI to match topic to profile)
        selected = random.choice(available_profiles)
        self.current_profile = selected
        self.profile_history.append(selected)
        
        # Keep history limited
        if len(self.profile_history) > 20:
            self.profile_history = self.profile_history[-20:]
        
        self.logger.info(f"Selected style profile: {PROFILES[selected].name}")
        return selected
    
    def get_profile_definition(self, profile: StyleProfile) -> ProfileDefinition:
        """Get profile definition."""
        return PROFILES[profile]
    
    def get_current_profile(self) -> Optional[StyleProfile]:
        """Get current profile."""
        return self.current_profile
    
    def get_profile_instructions(self, profile: StyleProfile) -> str:
        """Get instructions for AI based on profile."""
        definition = PROFILES[profile]
        
        return f"""Используй стиль профиля "{definition.name}":

Описание: {definition.description}
Характеристики: {', '.join(definition.characteristics)}
Тон: {definition.tone}
Длина: {definition.length_preference}
Эмодзи: {definition.emoji_usage}

Следуй этому стилю при создании контента."""

