"""AI model configuration."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
from config.defaults import DEFAULT_AI_MODEL, FALLBACK_AI_MODEL


class ModelType(Enum):
    """Model type enumeration."""
    FAST = "fast"  # For quick operations
    DEEP = "deep"  # For deep analysis
    LONG = "long"  # For long context


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    model_type: ModelType
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    description: str


# Model configurations
MODELS = {
    "gemini-2.0-flash-exp": ModelConfig(
        name="gemini-2.0-flash-exp",
        model_type=ModelType.FAST,
        max_tokens=8192,
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        description="Fast model for quick thinking and generation"
    ),
    "gemini-1.5-pro": ModelConfig(
        name="gemini-1.5-pro",
        model_type=ModelType.DEEP,
        max_tokens=8192,
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        description="Deep model for analysis, memory, and complex tasks"
    ),
    "gemini-1.5-flash": ModelConfig(
        name="gemini-1.5-flash",
        model_type=ModelType.FAST,
        max_tokens=8192,
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        description="Fallback fast model"
    ),
}


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get model configuration by name."""
    return MODELS.get(model_name)


def get_default_model() -> ModelConfig:
    """Get default model configuration."""
    return MODELS[DEFAULT_AI_MODEL]


def get_fallback_model() -> ModelConfig:
    """Get fallback model configuration."""
    return MODELS[FALLBACK_AI_MODEL]

