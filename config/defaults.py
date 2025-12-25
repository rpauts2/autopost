"""Default configuration values."""

from pathlib import Path
from typing import Dict, Any

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
SESSIONS_DIR = BASE_DIR / "sessions"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, SESSIONS_DIR]:
    directory.mkdir(exist_ok=True)

# AI Configuration
DEFAULT_AI_MODEL = "gemini-2.0-flash-exp"
FALLBACK_AI_MODEL = "gemini-1.5-pro"
AI_RATE_LIMIT_REQUESTS = 60  # per minute
AI_RATE_LIMIT_TOKENS = 1000000  # per minute

# Memory Configuration
MEMORY_DB_PATH = DATA_DIR / "memory.db"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight

# Agent Configuration
AGENT_THINKING_TIMEOUT = 30.0  # seconds
AGENT_ACTION_TIMEOUT = 120.0  # seconds

# Scheduler Configuration
SCHEDULER_CHECK_INTERVAL = 60  # seconds
MIN_POST_INTERVAL = 3600  # 1 hour between posts (anti-spam)

# Platform Configuration
VK_API_VERSION = "5.154"
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
DZEN_BROWSER_TIMEOUT = 30  # seconds

# Security
ENCRYPTION_KEY_FILE = DATA_DIR / ".encryption_key"
TOKEN_STORAGE_FILE = DATA_DIR / "tokens.encrypted"

# Default Goals
DEFAULT_GOALS = {
    "content_quality": "high",
    "posting_frequency": "moderate",  # moderate, frequent, rare
    "style": "authentic",
    "topics": [],  # Empty = any topic
    "avoid_repetition": True,
    "platform_optimization": True,
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "entity.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

